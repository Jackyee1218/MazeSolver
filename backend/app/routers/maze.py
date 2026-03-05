import asyncio
import json
import uuid
from dataclasses import dataclass, field

import numpy as np
from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from PIL import Image
from pydantic import BaseModel

from app.services import image_processor as ip
from app.services import solver as sv

router = APIRouter(prefix="/api/maze")

# ---------------------------------------------------------------------------
# In-memory session store
# ---------------------------------------------------------------------------

@dataclass
class SessionData:
    display_image: Image.Image
    maze_image: Image.Image
    maze_np: np.ndarray                          # binary, pre-skeletonization
    skel_np: np.ndarray | None = None            # binary, post-skeletonization
    skel_image: Image.Image | None = None
    start_xy: tuple[int, int] | None = None
    end_xy: tuple[int, int] | None = None
    original_display: Image.Image | None = None  # for reset


sessions: dict[str, SessionData] = {}


def _get_session(session_id: str) -> SessionData:
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/upload")
async def upload(file: UploadFile):
    contents = await file.read()
    display_image, maze_image, maze_np = ip.load_image(contents)

    session_id = str(uuid.uuid4())
    sessions[session_id] = SessionData(
        display_image=display_image,
        maze_image=maze_image,
        maze_np=maze_np,
        original_display=display_image.copy(),
    )

    w, h = display_image.size
    return {
        "session_id": session_id,
        "display_image": ip.image_to_b64(display_image),
        "maze_image": ip.image_to_b64(maze_image),
        "width": w,
        "height": h,
    }


class SetPointsRequest(BaseModel):
    session_id: str
    start: list[int]  # [x, y]
    end: list[int]    # [x, y]


@router.post("/set-points")
async def set_points(req: SetPointsRequest):
    session = _get_session(req.session_id)

    start_xy = (req.start[0], req.start[1])
    end_xy = (req.end[0], req.end[1])

    # Draw markers on display image
    display = session.original_display.copy()
    display = ip.draw_point(display, start_xy, ip.START_COLOR)
    display = ip.draw_point(display, end_xy, ip.END_COLOR)
    session.display_image = display

    # Skeletonize on set-points (same timing as original Tkinter app)
    skel_np, skel_image, _elapsed = ip.skeletonize(session.maze_np)
    session.skel_np = skel_np
    session.skel_image = skel_image
    session.start_xy = start_xy
    session.end_xy = end_xy

    return {
        "display_image": ip.image_to_b64(display),
        "maze_image": ip.image_to_b64(skel_image),
    }


CHUNK_SIZE = 50


@router.get("/solve")
async def solve(session_id: str):
    session = _get_session(session_id)

    if session.skel_np is None or session.start_xy is None or session.end_xy is None:
        raise HTTPException(status_code=400, detail="Points not set or image not skeletonized")

    skel_np = session.skel_np
    start_xy = session.start_xy
    end_xy = session.end_xy

    # Convert (x, y) → (y, x) for numpy
    start_yx = sv.find_nearest_path_point(skel_np, (start_xy[1], start_xy[0]))
    end_yx = sv.find_nearest_path_point(skel_np, (end_xy[1], end_xy[0]))

    if start_yx is None or end_yx is None:
        raise HTTPException(status_code=400, detail="Start or end point not on maze path")

    path, visited_nodes, solve_time = sv.bfs(skel_np, start_yx, end_yx)
    total = len(visited_nodes)
    status = "ac" if path else "wa"

    async def event_stream():
        # Stream visited nodes in chunks
        for i in range(0, total, CHUNK_SIZE):
            chunk = visited_nodes[i:i + CHUNK_SIZE]
            data = {"nodes": chunk, "start_index": i, "total": total}
            yield f"event: visited\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0)  # yield control to event loop

        # Send final path
        yield f"event: path\ndata: {json.dumps({'nodes': path})}\n\n"

        # Send completion
        yield f"event: complete\ndata: {json.dumps({'status': status, 'solve_time': solve_time})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


class ResetRequest(BaseModel):
    session_id: str


@router.post("/reset")
async def reset(req: ResetRequest):
    session = _get_session(req.session_id)

    session.display_image = session.original_display.copy()
    session.skel_np = None
    session.skel_image = None
    session.start_xy = None
    session.end_xy = None

    return {
        "display_image": ip.image_to_b64(session.display_image),
        "maze_image": ip.image_to_b64(session.maze_image),
    }
