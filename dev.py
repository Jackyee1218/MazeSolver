"""Local dev runner for MazeSolver."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"


class ServiceRunner:
    def __init__(self, name: str, command: str, cwd: Path) -> None:
        self.name = name
        self.command = command
        self.cwd = cwd
        self.process: subprocess.Popen[str] | None = None

    def start(self) -> None:
        print(f"Starting {self.name}...")
        self.process = subprocess.Popen(
            self.command,
            shell=True,
            cwd=self.cwd,
            env=os.environ.copy(),
        )

    def stop(self) -> None:
        if self.process and self.process.poll() is None:
            print(f"Stopping {self.name}...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

    def ensure_running(self) -> None:
        if self.process and self.process.poll() is not None:
            raise RuntimeError(f"{self.name} exited with code {self.process.returncode}")


def _run(command: str, cwd: Path) -> None:
    print(f"Running: {command}")
    subprocess.run(command, cwd=cwd, check=True, shell=True)


def _ensure_deps() -> None:
    if not (BACKEND_DIR / ".venv").exists():
        print("Backend .venv not found, running uv sync...")
        _run("uv sync", BACKEND_DIR)

    if not (FRONTEND_DIR / "node_modules").exists():
        print("node_modules not found, running npm install...")
        _run("npm install", FRONTEND_DIR)


def main() -> None:
    _ensure_deps()

    runners = [
        ServiceRunner(
            name="backend",
            command="uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000",
            cwd=BACKEND_DIR,
        ),
        ServiceRunner(
            name="frontend",
            command="npm run dev -- --host",
            cwd=FRONTEND_DIR,
        ),
    ]

    try:
        for runner in runners:
            runner.start()

        print("\nDev stack is running.")
        print("  Backend:  http://localhost:8000")
        print("  Frontend: http://localhost:5173")
        print("\nPress Ctrl+C to stop.\n")

        while True:
            for runner in runners:
                runner.ensure_running()
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        for runner in reversed(runners):
            runner.stop()


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(f"Error: {exc}")
        sys.exit(1)
