# 连连看 · Python + Pygame

一个用 Python + Pygame 从零实现的连连看小游戏。
点击两个图案相同的方块，若存在不超过两次转弯的通路即可消除，清空棋盘通关。

## 下载即玩（推荐）

不想装 Python？直接去 **[Releases](../../releases/latest)** 下载对应系统的压缩包，
解压后双击运行即可，无需安装任何环境。

- Windows：下载 `连连看-Windows.zip`，解压后双击 `连连看.exe`
- macOS：下载 `连连看-macOS.zip`（需在"系统设置 → 隐私与安全性"里允许打开）

## 玩法

| 操作 | 说明 |
|---|---|
| 鼠标左键 | 选牌 / 尝试消除 |
| `R` | 重排棋盘 |
| `H` | 提示一对可消方块 |
| `N` | 新游戏 |
| `Esc` | 退出 |

- 8 行 × 10 列，默认 8 种图案
- 每局 240 秒，消除一对 +10 分，通关按剩余时间额外加分
- 棋盘无解时自动重排

## 从源码运行

```bash
pip install -r requirements.txt
python lianliankan.py