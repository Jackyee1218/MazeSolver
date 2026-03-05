# MazeSolver

A web app that solves maze images. Upload a maze, set a start and end point, and watch the solution path animate in real time.

Built with a React frontend and a FastAPI Python backend.

---

## Quick Start

### Development mode

Requires [uv](https://docs.astral.sh/uv/) and [Node.js](https://nodejs.org/) (v20+).

**uv is required** to manage Python dependencies. Install it first:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then simply run:
```bash
python dev.py
```

`dev.py` automatically installs missing dependencies and starts both services.

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000

---

### Docker

Requires [Docker](https://docs.docker.com/get-docker/) with Compose plugin.

```bash
docker compose up --build
```

Open http://localhost. To stop: `docker compose down`

---

## How to Use

1. **Open** — Load a maze image (`.jpg`, `.png`, etc.)
2. **Set Points** — Click the button, then click the **start point** on the image, then the **end point**
3. **Solve** — Animates the solution path on the right panel
4. **Reset** — Clear points and try again

Sample mazes are in the [`samples/`](samples/) directory.

---

## Algorithm

Preprocessing: resize → grayscale → median blur → **Otsu's thresholding** → edge barrier → **skeletonization**

Pathfinding: **BFS** with 8-directional movement on the skeletonized binary maze.
