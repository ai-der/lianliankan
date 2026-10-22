# 连连看 · Python + Pygame

桌面版 + 手机网页版，同一套核心逻辑。

## 在哪里玩

### 桌面版（Windows）
- 下载 **[Releases](../../releases/latest)** 里的 `LianLianKan-Windows-vX.X.zip`
- 解压双击 `LianLianKan.exe`，无需安装任何环境

### 手机版（网页版）
- 浏览器打开 **https://ai-der.github.io/lianliankan/docs/**
- iOS / Android 通用，扫码即玩
- 源码在 [`mobile/`](mobile/) 目录，基于 pygbag 打包

## 项目结构
* lianliankan/
* lianliankan.py # 桌面版主程序
* tiles/ # 桌面版图片
* font.otf # 桌面版字体
* mobile/ # 手机网页版
  * main.py # pygbag 入口
  * linkgame.py # 手机端主程序
  * embedded_tiles.py # 内嵌图片+字体
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
