# 悬浮待办看板（绿色免安装）

一个置顶悬浮的小窗口，方便你随手维护待办事项/时间节点/状态。

功能亮点：
- 置顶悬浮（可开关）
- 自由编辑（剪切/复制/粘贴/全选、右键菜单）
- 按行设置状态：绿=已完成、黄=临近、红=延期、蓝=正常
- 自定义窗口背景色
- 自动保存文本、行状态、窗口大小和位置，下次自动恢复
- 绿色免安装：通过 GitHub Actions 打包单文件 EXE

---

## 快速开始（3 步）

1. **在 GitHub 新建仓库**（例如 `floating-todo-widget`）
2. **把本项目所有文件上传**到仓库根目录（把 zip 解压后，拖拽上传整个文件夹的内容）
3. 打开仓库的 **Actions** → 选择 `Build Windows EXE (Green)` → **Run workflow**
   - 等几分钟，在运行记录底部 **Artifacts** 下载 `floating-todo-exe`
   - 解压后得到 `floating-todo.exe`，**双击即可运行**

---

## 快捷键
- `Ctrl+1..4` 标记 绿/黄/红/蓝
- `Ctrl+0` 清除行状态
- `Ctrl+S` 保存；`Ctrl+O` 从文本文件导入
- `F2` 置顶开关
- `Ctrl+,` 打开背景色选择器

---

## 打包参数
- `--onefile` 单文件 EXE
- `--windowed` GUI 程序隐藏控制台
- `--icon app.ico` 程序图标（可替换）

如需更改 EXE 名称，在工作流 `--name` 以及 `Upload EXE` 的 `path` 同步修改。

