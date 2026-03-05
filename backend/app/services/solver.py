import timeit
from collections import deque

import numpy as np

DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
SEARCH_RADIUS = 200


def find_nearest_path_point(maze_np: np.ndarray, point_yx: tuple[int, int]) -> tuple[int, int] | None:
    """
    Snap a (y, x) coordinate to the nearest white pixel within SEARCH_RADIUS.
    Returns None if no white pixel found.
    """
    y, x = point_yx
    rows, cols = maze_np.shape

    if maze_np[y, x] == 255:
        return (y, x)

    for r in range(1, SEARCH_RADIUS + 1):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if abs(dy) != r and abs(dx) != r:
                    continue
                ny, nx = y + dy, x + dx
                if 0 <= ny < rows and 0 <= nx < cols and maze_np[ny, nx] == 255:
                    return (ny, nx)

    return None


def bfs(
    maze_np: np.ndarray,
    start_yx: tuple[int, int],
    end_yx: tuple[int, int],
) -> tuple[list[tuple[int, int]], list[tuple[int, int]], float]:
    """
    BFS on binary maze with 8-directional movement.

    Returns:
        path:          List of (y, x) from start to end. Empty if no solution.
        visited_nodes: All visited (y, x) in discovery order.
        elapsed:       Solve time in seconds.
    """
    t0 = timeit.default_timer()
    rows, cols = maze_np.shape
    visited = np.zeros((rows, cols), dtype=bool)
    visited[start_yx[0], start_yx[1]] = True

    queue: deque[tuple[tuple[int, int], list[tuple[int, int]]]] = deque()
    queue.append((start_yx, [start_yx]))
    visited_nodes: list[tuple[int, int]] = [start_yx]

    while queue:
        (y, x), path = queue.popleft()

        if (y, x) == end_yx:
            elapsed = timeit.default_timer() - t0
            return path, visited_nodes, elapsed

        for dy, dx in DIRECTIONS:
            ny, nx = y + dy, x + dx
            if 0 <= ny < rows and 0 <= nx < cols and not visited[ny, nx] and maze_np[ny, nx] == 255:
                visited[ny, nx] = True
                visited_nodes.append((ny, nx))
                queue.append(((ny, nx), path + [(ny, nx)]))

    elapsed = timeit.default_timer() - t0
    return [], visited_nodes, elapsed
