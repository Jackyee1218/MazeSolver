import base64
import io
import timeit

import cv2
import numpy as np
from PIL import Image, ImageDraw
from skimage.morphology import skeletonize as ski_skeletonize


MAX_SIZE = 512
START_COLOR = (20, 140, 40)   # dark green marker
END_COLOR = (20, 140, 40)     # dark green marker
POINT_RADIUS = 10


def _pil_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _resize(img: Image.Image) -> Image.Image:
    w, h = img.size
    if max(w, h) <= MAX_SIZE:
        return img
    scale = MAX_SIZE / max(w, h)
    return img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)


def _find_maze_bounds(img_np: np.ndarray) -> tuple[int, int, int, int]:
    """Return (left, right, top, bottom) bounding box of maze walls (black pixels)."""
    rows = np.any(img_np == 0, axis=1)
    cols = np.any(img_np == 0, axis=0)
    top, bottom = np.where(rows)[0][[0, -1]]
    left, right = np.where(cols)[0][[0, -1]]
    return int(left), int(right), int(top), int(bottom)


def _build_edge_barrier(img_np: np.ndarray, bounds: tuple[int, int, int, int]) -> np.ndarray:
    left, right, top, bottom = bounds
    result = np.zeros_like(img_np)
    result[top:bottom + 1, left:right + 1] = img_np[top:bottom + 1, left:right + 1]
    return result


def load_image(file_bytes: bytes) -> tuple[Image.Image, Image.Image, np.ndarray]:
    """
    Load and preprocess a maze image.

    Returns:
        display_image: PIL Image (RGB), original resized for display
        maze_image:    PIL Image (RGB), thresholded for display
        maze_np:       np.ndarray (uint8, 0 or 255), binary maze for BFS
    """
    img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    img = _resize(img)
    display_image = img.copy()

    gray = np.array(img.convert("L"))
    blurred = cv2.medianBlur(gray, 3)
    _, thresholded = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    bounds = _find_maze_bounds(thresholded)
    maze_np = _build_edge_barrier(thresholded, bounds)
    maze_np = cv2.medianBlur(maze_np, 3)

    maze_rgb = cv2.cvtColor(maze_np, cv2.COLOR_GRAY2RGB)
    maze_image = Image.fromarray(maze_rgb)

    return display_image, maze_image, maze_np


def skeletonize(maze_np: np.ndarray) -> tuple[np.ndarray, Image.Image, float]:
    """
    Apply skeletonization to binary maze.

    Returns:
        skel_np:    np.ndarray (uint8, 0 or 255)
        maze_image: PIL Image (RGB) of skeleton
        elapsed:    float seconds
    """
    t0 = timeit.default_timer()
    binary = maze_np > 0
    skel = ski_skeletonize(binary)
    skel_np = (skel * 255).astype(np.uint8)
    elapsed = timeit.default_timer() - t0

    maze_rgb = cv2.cvtColor(skel_np, cv2.COLOR_GRAY2RGB)
    maze_image = Image.fromarray(maze_rgb)
    return skel_np, maze_image, elapsed


def draw_point(display_image: Image.Image, pos_xy: tuple[int, int], color: tuple[int, int, int]) -> Image.Image:
    """Draw an X marker on a copy of the display image."""
    img = display_image.copy()
    draw = ImageDraw.Draw(img)
    x, y = pos_xy
    r = POINT_RADIUS
    draw.line([(x - r, y - r), (x + r, y + r)], fill=color, width=4)
    draw.line([(x + r, y - r), (x - r, y + r)], fill=color, width=4)
    return img


def image_to_b64(img: Image.Image) -> str:
    return _pil_to_b64(img)
