# main.py
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk,  ImageDraw
import os
from dotenv import load_dotenv
load_dotenv()


from MazeModel import MazeModel
from MainView import MainView


class MazeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        

        self.model = MazeModel()
        self.view = MainView(self, self) # self 作為 controller 傳入

        # --- 視窗設定 ---
        self.title("Maze Solver (Refactored)")
        self.geometry("1520x780+0+0")
        self.configure(bg='#1c1d20')
        icon_path = os.getenv("ICON_PATH")
        self.icon = ImageTk.PhotoImage(Image.open(os.path.join(icon_path, 'maze_icon.png')))
        self.wm_iconphoto(False, self.icon)

        # --- 變數 ---
        self.is_setting_points = False
        self.skeletonize_time = 0.0

        # --- 綁定事件 ---
        self.view.image_display_frame.image_label.bind("<Button-1>", self.on_image_click)

    def open_file(self):
        """處理 'Open' 按鈕點擊"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.tif *.tiff")]
        )
        if not file_path:
            return

        success, display_img, maze_img = self.model.load_image(file_path)
        if success:
            self.view.image_display_frame.update_image(
                self.view.image_display_frame.image_label, display_img
            )
            self.view.image_display_frame.update_image(
                self.view.image_display_frame.maze_image_label, maze_img
            )
            self.reset_ui_state()

    def set_point_mode(self):
        """處理 'Set' 按鈕點擊，進入/退出設置點模式"""
        self.is_setting_points = True
        # 可以增加視覺提示，例如改變滑鼠指標
        self.config(cursor="crosshair")
        # 清除舊的點，以便重新設置
        self.model.reset_points()
        # 恢復到沒有畫點的原始圖片
        if self.model.original_image:
             self.view.image_display_frame.update_image(
                self.view.image_display_frame.image_label, self.model.original_image
            )

    def on_image_click(self, event):
        """處理在圖片上的點擊，用來設置起點和終點"""
        if not self.is_setting_points:
            return
        
        # 傳遞點擊的座標 (x, y)
        updated_image = self.model.set_point((event.x, event.y))
        
        if updated_image:
            self.view.image_display_frame.update_image(
                self.view.image_display_frame.image_label, updated_image
            )
        
        # 如果終點已經設置，退出設置模式
        if self.model.end_pos is not None:
            self.is_setting_points = False
            self.config(cursor="")
            maze_img, elapsed_time = self.model.skeletonize()
            if maze_img:
                self.view.image_display_frame.update_image(
                    self.view.image_display_frame.maze_image_label, maze_img
                )
                self.skeletonize_time = elapsed_time
                self.view.time_frame.set_time(self.skeletonize_time)

    def reset_maze(self):
        """處理 'Reset' 按鈕點擊"""
        display_img, maze_img = self.model.reset()
        if display_img:
            self.view.image_display_frame.update_image(
                self.view.image_display_frame.image_label, display_img
            )
            self.view.image_display_frame.update_image(
                self.view.image_display_frame.maze_image_label, maze_img
            )
        self.reset_ui_state()

    def start_solving(self):
        if self.model.start_pos is None or self.model.end_pos is None:
            print("Error: Start and end points must be set.")
            return

        self.view.status_frame.set_status('wait')
        self.update_idletasks()

        path, visited_nodes, solve_time = self.model.solve_maze()
        self.view.time_frame.set_time(solve_time)
        self.update_idletasks()
        if not path:
            self.view.status_frame.set_status('wa')
            total_time = self.skeletonize_time + solve_time
            self.view.time_frame.set_time(total_time)
            self.update_idletasks()
            return
        
        self.anim_display_img = self.model.display_image.copy()
        self.anim_maze_img = self.model.maze_image.copy()

        # 2. 啟動第一個動畫（顯示搜索過程）
        self.total_solve_time = solve_time
        self._animate_search(visited_nodes, path)

    def _animate_search(self, visited_nodes, final_path, index=0, chunk_size=50):
        """逐步繪製BFS的搜索過程"""
        # 繪製一小部分點
        draw_maze = ImageDraw.Draw(self.anim_maze_img)
        
        end_index = min(index + chunk_size, len(visited_nodes))
        
        for i in range(index, end_index):
            r, c = visited_nodes[i]
            t = i / (len(visited_nodes) - 1) if len(visited_nodes) > 1 else 0
            color = self.model._gradient(self.model.start_color, self.model.end_color, t)
            draw_maze.point((c, r), fill=color)

        # 更新迷宮圖片標籤
        self.view.image_display_frame.update_image(
            self.view.image_display_frame.maze_image_label, self.anim_maze_img
        )

        # 如果還有點要畫，安排下一次繪製
        if end_index < len(visited_nodes):
            self.after(1, self._animate_search, visited_nodes, final_path, end_index, chunk_size)
        else:
            # 搜索過程動畫結束，開始繪製最終路徑
            self._animate_path(final_path)

    def _animate_path(self, path, index=0):
        """逐步繪製最終找到的路徑"""
        if index >= len(path) - 1:
            # 所有路徑都畫完了
            self.view.status_frame.set_status('ac')
            total_time = self.skeletonize_time + self.total_solve_time
            self.view.time_frame.set_time(total_time)
            self.update_idletasks()
            return

        draw_display = ImageDraw.Draw(self.anim_display_img)

        # 繪製一小段路徑
        start_point = (path[index][1], path[index][0])
        end_point = (path[index + 1][1], path[index + 1][0])
        draw_display.line([start_point, end_point], fill="#009900", width=5)
        
        # 更新主圖片標籤
        self.view.image_display_frame.update_image(
            self.view.image_display_frame.image_label, self.anim_display_img
        )

        # 安排下一次繪製
        self.after(1, self._animate_path, path, index + 1)

    def reset_ui_state(self):
        """重置UI元件到初始狀態"""
        self.is_setting_points = False
        self.config(cursor="")
        self.skeletonize_time = 0.0
        self.view.time_frame.set_time(0.0)
        self.view.status_frame.set_status('wait')

if __name__ == "__main__":
    app = MazeApp()
    app.mainloop()