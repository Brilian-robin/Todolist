import tkinter as tk
from tkinter import messagebox, colorchooser, filedialog
import tkinter.font as tkfont
import json
import os
import sys
import time

APP_NAME = "悬浮待办看板"
VERSION = "1.0.0"

# 颜色方案（可按需微调）
STATUS_COLORS = {
    "green": "#d1f2d1",   # 已完成
    "yellow": "#fff3cd",  # 临近节点
    "red": "#f8d7da",     # 延期
    "blue": "#d1ecf1",    # 正常进行
}
STATUS_LABELS = {
    "green": "已完成（绿）",
    "yellow": "临近（黄）",
    "red": "延期（红）",
    "blue": "正常（蓝）",
}

# 数据与设置文件保存在程序同目录
def app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(app_dir(), "data")
os.makedirs(DATA_DIR, exist_ok=True)
SAVE_FILE = os.path.join(DATA_DIR, "todos.json")

DEFAULT_SETTINGS = {
    "bg_color": "#fdf6e3",  # 默认背景色（米色系）
    "topmost": True,
    "width": 420,
    "height": 520,
    "x": None,
    "y": None,
    "font_family": "Microsoft YaHei",
    "font_size": 11,
    "auto_save_sec": 60
}

def load_state():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"text": "", "styles": {}, "settings": DEFAULT_SETTINGS.copy()}
    return {"text": "", "styles": {}, "settings": DEFAULT_SETTINGS.copy()}

def save_state(text_content, line_styles, settings):
    state = {
        "text": text_content,
        "styles": line_styles,
        "settings": settings
    }
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

class FloatingTodoApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_NAME)
        self.state = load_state()
        self.settings = {**DEFAULT_SETTINGS, **self.state.get("settings", {})}
        self.last_saved_time = None

        # 字体
        try:
            self.app_font = tkfont.Font(family=self.settings["font_family"], size=self.settings["font_size"])
        except Exception:
            self.app_font = tkfont.Font(size=self.settings["font_size"])  # 回退默认字体

        # 置顶
        self.root.wm_attributes("-topmost", bool(self.settings.get("topmost", True)))

        # 尺寸与位置
        w = int(self.settings.get("width", 420))
        h = int(self.settings.get("height", 520))
        x = self.settings.get("x")
        y = self.settings.get("y")
        geo = f"{w}x{h}"
        if x is not None and y is not None:
            geo += f"+{int(x)}+{int(y)}"
        self.root.geometry(geo)
        self.root.minsize(300, 260)

        # 外层框架
        self.container = tk.Frame(self.root, bg=self.settings["bg_color"])
        self.container.pack(fill="both", expand=True)

        # 工具栏
        self._build_toolbar(self.container)

        # 文本编辑区
        self.text = tk.Text(
            self.container,
            wrap="word",
            undo=True,
            font=self.app_font,
            relief="flat",
            bg=self.settings["bg_color"]
        )
        self.text.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        # 滚动条
        yscroll = tk.Scrollbar(self.text, command=self.text.yview)
        self.text.configure(yscrollcommand=yscroll.set)
        yscroll.pack(side="right", fill="y")

        # 定义状态标签
        for key, color in STATUS_COLORS.items():
            self.text.tag_configure(f"status_{key}", background=color)

        # 右键菜单
        self._build_context_menu()

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        self.status_bar = tk.Label(self.container, textvariable=self.status_var, anchor="w", bg=self.settings["bg_color"])
        self.status_bar.pack(fill="x", padx=10, pady=(0, 8))

        # 载入文本与样式
        self._load_from_state()

        # 绑定快捷键
        self._bind_hotkeys()

        # 自动保存
        self._schedule_auto_save()

        # 退出时保存
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------- UI 构建 ----------
    def _build_toolbar(self, parent):
        bar = tk.Frame(parent, bg=self.settings["bg_color"])
        bar.pack(fill="x", padx=10, pady=(10, 6))

        def btn(text, cmd, bg=None):
            return tk.Button(bar, text=text, command=cmd, width=6, padx=6)

        btn("绿", lambda: self.apply_status("green")).pack(side="left")
        btn("黄", lambda: self.apply_status("yellow")).pack(side="left", padx=(6, 0))
        btn("红", lambda: self.apply_status("red")).pack(side="left", padx=(6, 0))
        btn("蓝", lambda: self.apply_status("blue")).pack(side="left", padx=(6, 0))
        btn("清除", self.clear_status).pack(side="left", padx=(12, 0))

        btn("保存", self.save).pack(side="right")
        btn("载入", self.load_from_file).pack(side="right", padx=(0, 6))

        btn("背景色", self.pick_bg).pack(side="right", padx=(0, 12))
        self.topmost_var = tk.BooleanVar(value=bool(self.settings.get("topmost", True)))
        top_cb = tk.Checkbutton(bar, text="置顶", var=self.topmost_var, command=self.toggle_topmost, bg=self.settings["bg_color"])
        top_cb.pack(side="right", padx=(0, 12))

    def _build_context_menu(self):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="剪切", command=lambda: self.root.focus_get().event_generate("<<Cut>>"))
        menu.add_command(label="复制", command=lambda: self.root.focus_get().event_generate("<<Copy>>"))
        menu.add_command(label="粘贴", command=lambda: self.root.focus_get().event_generate("<<Paste>>"))
        menu.add_separator()
        menu.add_command(label="全选", command=lambda: (self.text.tag_add("sel", "1.0", "end-1c")))
        menu.add_separator()

        # 状态快捷
        for k in ["green", "yellow", "red", "blue"]:
            menu.add_command(label=f"标为{STATUS_LABELS[k]}", command=lambda kk=k: self.apply_status(kk))
        menu.add_command(label="清除行状态", command=self.clear_status)

        self.context_menu = menu
        self.text.bind("<Button-3>", self._show_context_menu)  # Windows 右键
        self.text.bind("<Button-2>", self._show_context_menu)  # mac 中键备用

    def _show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    # ---------- 数据载入/保存 ----------
    def _load_from_state(self):
        self.text.delete("1.0", "end")
        content = self.state.get("text", "")
        self.text.insert("1.0", content)

        # 应用行级状态
        styles = self.state.get("styles", {})
        last_line = int(float(self.text.index("end-1c").split(".")[0]))
        for i in range(1, last_line + 1):
            key = str(i)
            status = styles.get(key)
            if status in STATUS_COLORS:
                self._apply_status_to_line(i, status)

        self._update_status("已载入")

    def save(self):
        text_content = self.text.get("1.0", "end-1c")
        line_styles = self._collect_line_styles()
        # 保存当前窗口设置
        w, h, x, y = self._current_geometry()
        settings = {
            **self.settings,
            "bg_color": self.settings.get("bg_color", DEFAULT_SETTINGS["bg_color"]),
            "topmost": bool(self.topmost_var.get()),
            "width": w,
            "height": h,
            "x": x,
            "y": y
        }
        save_state(text_content, line_styles, settings)
        self.last_saved_time = time.strftime("%H:%M:%S")
        self._update_status(f"已保存 ({self.last_saved_time})")

    def _schedule_auto_save(self):
        sec = int(self.settings.get("auto_save_sec", 60))
        if sec <= 0:
            return
        self.save()
        self.root.after(sec * 1000, self._schedule_auto_save)

    def _collect_line_styles(self):
        """获取每一行的状态（如果有），返回 dict: 行号字符串 → status_key"""
        styles = {}
        last_line = int(float(self.text.index("end-1c").split(".")[0]))
        for i in range(1, last_line + 1):
            tags = self.text.tag_names(f"{i}.0")
            for k in STATUS_COLORS:
                if f"status_{k}" in tags:
                    styles[str(i)] = k
                    break
        return styles

    def load_from_file(self):
        path = filedialog.askopenfilename(
            title="选择一个文本文件以导入",
            filetypes=[("Text", "*.txt"), ("All Files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.text.delete("1.0", "end")
            self.text.insert("1.0", content)
            # 清除所有状态标签
            self._clear_all_status_tags()
            self._update_status(f"已载入外部文件：{os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("载入失败", str(e))

    # ---------- 状态应用 ----------
    def apply_status(self, status_key: str):
        if status_key not in STATUS_COLORS:
            return
        # 如果选择了文本，则对这些行应用；否则对光标所在行应用
        try:
            start = self.text.index("sel.first")
            end = self.text.index("sel.last")
            s_line = int(start.split(".")[0])
            e_line = int(end.split(".")[0])
        except tk.TclError:
            s_line = e_line = int(self.text.index("insert").split(".")[0])

        for ln in range(s_line, e_line + 1):
            self._apply_status_to_line(ln, status_key)

        self._update_status(f"已标注为 {STATUS_LABELS[status_key]}")

    def _apply_status_to_line(self, line: int, status_key: str):
        # 清掉该行的其他状态
        for k in STATUS_COLORS:
            self.text.tag_remove(f"status_{k}", f"{line}.0", f"{line}.end")
        # 应用新状态
        self.text.tag_add(f"status_{status_key}", f"{line}.0", f"{line}.end")

    def clear_status(self):
        # 同样逻辑：选区行 or 当前行
        try:
            start = self.text.index("sel.first")
            end = self.text.index("sel.last")
            s_line = int(start.split(".")[0])
            e_line = int(end.split(".")[0])
        except tk.TclError:
            s_line = e_line = int(self.text.index("insert").split(".")[0])

        for ln in range(s_line, e_line + 1):
            for k in STATUS_COLORS:
                self.text.tag_remove(f"status_{k}", f"{ln}.0", f"{ln}.end")

        self._update_status("已清除行状态")

    def _clear_all_status_tags(self):
        for k in STATUS_COLORS:
            self.text.tag_remove(f"status_{k}", "1.0", "end")

    # ---------- 设置/外观 ----------
    def pick_bg(self):
        color = colorchooser.askcolor(color=self.settings["bg_color"], title="选择背景色")[1]
        if color:
            self.settings["bg_color"] = color
            self.container.configure(bg=color)
            self.text.configure(bg=color)
            self.status_bar.configure(bg=color)
            self._update_status(f"背景色已更新：{color}")

    def toggle_topmost(self):
        val = bool(self.topmost_var.get())
        self.root.wm_attributes("-topmost", val)
        self._update_status("已置顶" if val else "已取消置顶")

    # ---------- 快捷键 ----------
    def _bind_hotkeys(self):
        self.root.bind("<Control-s>", lambda e: (self.save(), "break"))
        self.root.bind("<Control-S>", lambda e: (self.save(), "break"))
        self.root.bind("<Control-o>", lambda e: (self.load_from_file(), "break"))
        self.root.bind("<F2>", lambda e: (self.topmost_var.set(not self.topmost_var.get()), self.toggle_topmost(), "break"))

        self.root.bind("<Control-Key-1>", lambda e: (self.apply_status("green"), "break"))
        self.root.bind("<Control-Key-2>", lambda e: (self.apply_status("yellow"), "break"))
        self.root.bind("<Control-Key-3>", lambda e: (self.apply_status("red"), "break"))
        self.root.bind("<Control-Key-4>", lambda e: (self.apply_status("blue"), "break"))
        self.root.bind("<Control-Key-0>", lambda e: (self.clear_status(), "break"))

        # 打开设置：背景色
        self.root.bind("<Control-comma>", lambda e: (self.pick_bg(), "break"))

    # ---------- 工具 ----------
    def _current_geometry(self):
        self.root.update_idletasks()
        geo = self.root.geometry()  # e.g., '420x520+100+200'
        size, _, pos = geo.partition("+")
        w, h = size.split("x")
        x, y = pos.split("+") if "+" in pos else (None, None)
        return int(w), int(h), (int(x) if x else None), (int(y) if y else None)

    def _update_status(self, msg: str):
        self.status_var.set(msg)

    def on_close(self):
        self.save()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = FloatingTodoApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
