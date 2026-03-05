from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import maze

app = FastAPI(title="MazeSolver API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(maze.router)
