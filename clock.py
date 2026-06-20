import time
import tkinter as tk
from tkinter import colorchooser


class ClockApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Desktop Clock")
        self.root.geometry("390x220")
        self.root.state("zoomed")

        self.colors = [
            {"bg": "#f5f7fa", "fg": "#1f2937", "button": "#e5e7eb"},
            {"bg": "#111827", "fg": "#f9fafb", "button": "#374151"},
            {"bg": "#fef3c7", "fg": "#92400e", "button": "#fde68a"},
            {"bg": "#ecfdf5", "fg": "#065f46", "button": "#a7f3d0"},
            {"bg": "#eff6ff", "fg": "#1d4ed8", "button": "#bfdbfe"},
        ]
        self.color_index = 0

        current_color = self.colors[self.color_index]
        self.root.configure(bg=current_color["bg"])

        self.time_label = tk.Label(
            root,
            font=("Segoe UI", 42, "bold"),
            fg=current_color["fg"],
            bg=current_color["bg"],
        )
        self.time_label.pack(expand=True)

        self.button_frame = tk.Frame(root, bg=current_color["bg"])
        self.button_frame.pack(pady=(0, 8))

        self.bg_button = tk.Button(
            self.button_frame,
            text="背景颜色",
            font=("Microsoft YaHei UI", 10),
            relief="flat",
            cursor="hand2",
            command=self.choose_background_color,
        )
        self.bg_button.pack(side="left", padx=5)

        self.fg_button = tk.Button(
            self.button_frame,
            text="文字颜色",
            font=("Microsoft YaHei UI", 10),
            relief="flat",
            cursor="hand2",
            command=self.choose_text_color,
        )
        self.fg_button.pack(side="left", padx=5)

        self.preset_button = tk.Button(
            root,
            text="预设切换",
            font=("Microsoft YaHei UI", 10),
            relief="flat",
            cursor="hand2",
            command=self.change_color,
        )
        self.preset_button.pack(pady=(0, 14))

        self.apply_color()
        self.update_time()

    def update_time(self):
        current_time = time.strftime("%H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)

    def change_color(self):
        self.color_index = (self.color_index + 1) % len(self.colors)
        self.apply_color()

    def choose_background_color(self):
        current_color = self.colors[self.color_index]
        selected = colorchooser.askcolor(
            color=current_color["bg"],
            title="选择背景颜色",
        )[1]

        if selected:
            current_color["bg"] = selected
            current_color["button"] = selected
            self.apply_color()

    def choose_text_color(self):
        current_color = self.colors[self.color_index]
        selected = colorchooser.askcolor(
            color=current_color["fg"],
            title="选择文字颜色",
        )[1]

        if selected:
            current_color["fg"] = selected
            self.apply_color()

    def apply_color(self):
        current_color = self.colors[self.color_index]
        self.root.configure(bg=current_color["bg"])
        self.time_label.configure(bg=current_color["bg"], fg=current_color["fg"])
        self.button_frame.configure(bg=current_color["bg"])

        for button in (self.bg_button, self.fg_button, self.preset_button):
            button.configure(
                bg=current_color["button"],
                fg=current_color["fg"],
                activebackground=current_color["fg"],
                activeforeground=current_color["bg"],
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = ClockApp(root)
    root.mainloop()
