# maze_model.py
from PIL import Image, ImageDraw
import numpy as np
import cv2
from queue import Queue
import timeit
from skimage.morphology import skeletonize


class MazeModel:
    def __init__(self):
        # Original image
        self.original_image = None
        # left image
        self.display_image = None
        # right image(thresholding, skeletonizated image)
        self.maze_image = None
        # backup of the right image(reset without re-preprocessing)
        self.processed_maze_backup = None

        self.start_pos = None
        self.end_pos = None

        self.start_color = (107, 154, 205)
        self.end_color = (174, 205, 107)

    def load_image(self, file_path):
        if not file_path:
            return False, None, None

        img = Image.open(file_path).convert('RGB')
        img = self._resize_image(img, 512)
        
        self.original_image = img.copy()
        self.display_image = img.copy()

        # image preprocessing
        maze_np = np.array(img.convert("L"))
        maze_np = cv2.medianBlur(maze_np, 3)
        # Thresholding
        # threshold_value = np.mean(maze_np) * 0.8 
        # maze_np = ((maze_np > threshold_value) * 255).astype(np.uint8)

        # using OTSU thresholding tech
        _, maze_np = cv2.threshold(maze_np, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)


        # medianBlur & fill edge
        edge = self._find_maze_bounds(maze_np)
        maze_np = self._build_edge_barrier(maze_np, edge)
        maze_np = cv2.medianBlur(maze_np, 3)

        self.maze_image = Image.fromarray(maze_np).convert("RGB")
        self.processed_maze_backup = self.maze_image.copy()

        self.reset_points()
        return True, self.display_image, self.maze_image
    
    def set_point(self, pos):
        if self.display_image is None:
            return None
            
        draw = ImageDraw.Draw(self.display_image)
        radius = 5
        
        if self.start_pos is None:
            self.start_pos = pos
            draw.ellipse((pos[0]-radius, pos[1]-radius, pos[0]+radius, pos[1]+radius), fill=self.start_color)
            return self.display_image
        elif self.end_pos is None:
            self.end_pos = pos
            draw.ellipse((pos[0]-radius, pos[1]-radius, pos[0]+radius, pos[1]+radius), fill=self.end_color)
            return self.display_image
        return None

    def reset(self):
        if self.original_image:
            self.display_image = self.original_image.copy()
            self.maze_image = self.processed_maze_backup.copy()
            self.reset_points()
            return self.display_image, self.maze_image
        return None, None
        
    def reset_points(self):
        self.start_pos = None
        self.end_pos = None

    def skeletonize(self):
        if self.processed_maze_backup is None:
            return None, 0.0

        start_time = timeit.default_timer()

        I = np.array(self.processed_maze_backup.convert("L"))

        binary = I > 0

        skeleton = skeletonize(binary)
        # skeleton = ~skeleton

        skeleton_img = (skeleton.astype(np.uint8)) * 255

        self.maze_image = Image.fromarray(skeleton_img).convert("RGB")

        elapsed_time = timeit.default_timer() - start_time
        return self.maze_image, elapsed_time

    def solve_maze(self):
        if self.start_pos is None or self.end_pos is None:
            return None, None, 0.0, False

        start_time = timeit.default_timer()
        
        maze_np = np.array(self.maze_image.convert("L"))
        
        start_on_path = self._find_nearest_path_point(maze_np, (self.start_pos[1], self.start_pos[0])) # (y,x) for numpy
        end_on_path = self._find_nearest_path_point(maze_np, (self.end_pos[1], self.end_pos[0]))
        
        path, visited_nodes = self._bfs(maze_np, start_on_path, end_on_path)
        
        solve_time = timeit.default_timer() - start_time
        
        return path, visited_nodes, solve_time
    

    def _resize_image(self, img, max_size=512):
        width, height = img.size
        if max(width, height) > max_size:
            if height >= width:
                ratio = height / max_size
                width = int(width / ratio)
                height = max_size
            else:
                ratio = width / max_size
                height = int(height / ratio)
                width = max_size
            return img.resize((width, height), Image.Resampling.LANCZOS)
        return img

    def _find_maze_bounds(self, img_np):
        """judgement"""
        rows, cols = np.where(img_np == 0)
        if len(rows) == 0: 
            return 0, img_np.shape[1], 0, img_np.shape[0]
        return np.min(cols), np.max(cols), np.min(rows), np.max(rows)

    def _build_edge_barrier(self, img_np, bounds):
        """to avoid final path driven from outside"""
        left, right, top, bottom = bounds
        result = img_np.copy()
        result[:top, :] = 0
        result[bottom+1:, :] = 0
        result[:, :left] = 0
        result[:, right+1:] = 0
        return result

    def _find_nearest_path_point(self, img_np, point_yx):
        """to deal with point that"""
        if img_np[point_yx[0], point_yx[1]] == 255:
            return point_yx
        
        y, x = point_yx
        search_radius = 200
        
        top = max(0, y - search_radius)
        bottom = min(img_np.shape[0], y + search_radius)
        left = max(0, x - search_radius)
        right = min(img_np.shape[1], x + search_radius)
        
        path_y, path_x = np.where(img_np[top:bottom, left:right] == 255)
        
        if path_y.size == 0: 
            return point_yx 
        path_y += top
        path_x += left
        
        distances = (path_y - y)**2 + (path_x - x)**2
        min_index = np.argmin(distances)
        
        return (path_y[min_index], path_x[min_index])

    def _bfs(self, img_np, start_yx, end_yx):
        height, width = img_np.shape
        visited = np.zeros_like(img_np, dtype=bool)
        q = Queue()

        q.put((start_yx, [start_yx]))
        visited[start_yx] = True
        
        all_visited_nodes = [start_yx]
        
        moves = [(-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (1, -1), (-1, 1), (-1, -1)] 

        while not q.empty():
            (current_y, current_x), path = q.get()

            if (current_y, current_x) == end_yx:
                return path, all_visited_nodes

            for dy, dx in moves:
                next_y, next_x = current_y + dy, current_x + dx

                if 0 <= next_y < height and 0 <= next_x < width and img_np[next_y, next_x] == 255 and not visited[next_y, next_x]:
                    
                    visited[next_y, next_x] = True
                    all_visited_nodes.append((next_y, next_x))
                    new_path = path + [(next_y, next_x)]
                    q.put(((next_y, next_x), new_path))
        
        return [], all_visited_nodes # no path found

    @staticmethod
    def _gradient(start_rgb, end_rgb, t):
        r = int(start_rgb[0] + t * (end_rgb[0] - start_rgb[0]))
        g = int(start_rgb[1] + t * (end_rgb[1] - start_rgb[1]))
        b = int(start_rgb[2] + t * (end_rgb[2] - start_rgb[2]))
        return (r, g, b)