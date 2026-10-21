# -*- coding: utf-8 -*-
"""
连连看 —— Python + Pygame 单文件实现

玩法：
    点击两个图案相同的方块，若它们之间存在一条不超过两次转弯的通路，
    即可消除。清空全部方块即为通关。

快捷键：
    鼠标左键  选牌 / 消除
    R         重排
    H         提示
    N         新游戏
    Esc       退出
"""

import os
import sys
import random
from collections import deque

import pygame

import base64
import io

import asyncio
def app_dir():
    """资源所在目录：打包成 exe 后是 exe 所在目录，源码运行时是脚本目录。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

# ==================== 全局配置 ====================
import sys
IS_WEB = sys.platform == "emscripten"

if IS_WEB:
    ROWS, COLS = 8, 8        # 棋盘行数、列数
    TILE = 40
else:
    ROWS, COLS = 8, 10
    TILE = 96

# 以下全部按 TILE 比例推导，改 TILE 会自动适配
TILE_PAD = max(2, int(TILE * 0.047))     # 方块贴图内边距
MARGIN   = int(TILE * 0.625)             # 棋盘外留白
HUD_H    = int(TILE * 1.5)               # 顶部信息栏高度

BOARD_W = COLS * TILE
BOARD_H = ROWS * TILE
WIDTH = BOARD_W + MARGIN * 2
HEIGHT = BOARD_H + MARGIN * 2 + HUD_H
BOARD_X = MARGIN
BOARD_Y = HUD_H + MARGIN

FPS = 60
TOTAL_TIME = 240.0
WINDOW_TITLE = "连连看 · Python + Pygame"
BG = (26, 30, 42)           # 窗口背景色
PANEL = (38, 44, 60)        # 棋盘底板色
GRID_LINE = (46, 52, 70)    # 棋盘格纹色
TEXT = (236, 240, 248)
ACCENT = (255, 209, 102)
HINT_COLOR = (110, 230, 255)

PALETTE = [
    (239, 71, 111),
    (255, 193, 7),
    (6, 214, 160),
    (17, 138, 178),
    (131, 56, 236),
    (255, 140, 66),
    (0, 187, 249),
    (247, 37, 133),
]
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))

FONT_NAMES = ("microsoftyahei,msyh,simhei,simsun,notosanscjksc,"
              "notosanscjk,wenquanyimicrohei,pingfangsc,arial")


# ============================================================
# ★ 可变元素①：把方块图案换成你自己的图片 ★
# ------------------------------------------------------------
# 用法（二选一，也可以同时用）：
#
#   方式 A（最省事，推荐）：在本文件旁边新建一个文件夹 tiles/，
#           把图片丢进去即可，程序会自动扫描并按文件名排序读取。
#           支持 .png / .jpg / .jpeg / .bmp / .webp / .gif
#
#   方式 B：把下面的 TILE_IMAGES 填成你自己的图片路径列表。
#
# 说明：
#   · 图案的"种类数"会自动等于图片数量（上限 26 种），
#     所以你放 6 张图就有 6 种方块，不用改任何其它代码；
#   · 图片非正方形会自动等比缩放并居中，不会被拉变形；
#   · 建议用背景透明的 PNG，图片四周留白会自动用彩色底板兜底；
#   · 两种方式都没有提供图片时，自动回退到内置的彩色字母方块。
# ============================================================
TILE_IMAGE_DIR = os.path.join(app_dir(), "tiles")
# TILE_IMAGE_DIR = "tiles"    # 图片文件夹；设为 None 表示不自动扫描
TILE_IMAGES = [
    # 方式 B 示例（取消注释并改成你的路径即可）：
    # "images/apple.png",
    # "images/banana.png",
    # "images/cherry.png",
    # "images/grape.png",
    # "images/lemon.png",
    # "images/peach.png",
]
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif")
# PIC_PADDING = 0             # 图片与方块边缘的留白（像素），改小可让图片更满
# PIC_RADIUS = 14             # 方块圆角半径
# PIC_PADDING = max(3, int(TILE * 0.125))
PIC_PADDING = 1
PIC_RADIUS  = max(6, int(TILE * 0.22))
# ============================================================


# ==================== 工具函数 ====================
FONT_NAMES = ("microsoftyahei", "msyh", "simhei", "simsun",
              "notosanscjksc", "notosanscjk", "notosanssc",
              "wenquanyimicrohei", "pingfangsc", "arial")

# ★ 随包分发的字体文件（放在 exe 同目录，或项目根目录）
BUNDLED_FONT_FILES = [
    os.path.join(app_dir(), "font.otf"),
    os.path.join(app_dir(), "font.ttf"),
    os.path.join(app_dir(), "fonts", "NotoSansCJKsc-Regular.otf"),
    os.path.join(app_dir(), "fonts", "LXGWWenKai-Regular.ttf"),
]


def load_font(size, bold=False):
    """按优先级加载字体，保证一定返回一个 Font 对象，绝不返回 None。"""

    # 1) 内嵌字体（网页版 / 打包版最可靠）
    try:
        from embedded_tiles import FONT_B64
        raw = base64.b64decode(FONT_B64.split(",", 1)[1])
        return pygame.font.Font(io.BytesIO(raw), size)
    except Exception:
        pass   # 没有内嵌字体或解码失败，继续往下走

    # 2) 随包字体文件
    for fp in BUNDLED_FONT_FILES:
        if os.path.isfile(fp):
            try:
                return pygame.font.Font(fp, size)
            except Exception:
                continue

    # 3) 系统字体名逐个尝试
    for name in FONT_NAMES:
        try:
            path = pygame.font.match_font(name, bold=bold)
            if path:
                try:
                    return pygame.font.Font(path, size)
                except Exception:
                    continue
        except Exception:
            continue

    # 4) Windows 下直接查 Fonts 目录
    if sys.platform == "win32":
        windir = os.environ.get("WINDIR", r"C:\Windows")
        for fn in ("msyh.ttc", "msyhbd.ttc", "simhei.ttf", "simsun.ttc"):
            p = os.path.join(windir, "Fonts", fn)
            if os.path.isfile(p):
                try:
                    return pygame.font.Font(p, size)
                except Exception:
                    continue

    # 5) 最终兜底：默认字体，保证不返回 None
    return pygame.font.Font(None, size)


def text_color_for(bg):
    """根据背景亮度决定用深色还是浅色字。"""
    lum = 0.299 * bg[0] + 0.587 * bg[1] + 0.114 * bg[2]
    return (30, 30, 40) if lum > 140 else (250, 250, 255)


# def cell_topleft(r, c):
#     """格子 (r, c) 中方块贴图的左上角像素坐标。"""
#     return (BOARD_X + (c - 1) * TILE + 3,
#             BOARD_Y + (r - 1) * TILE + 3)
def cell_topleft(r, c):
    return (BOARD_X + (c - 1) * TILE + TILE_PAD,
            BOARD_Y + (r - 1) * TILE + TILE_PAD)


def cell_center(r, c):
    """格子 (r, c) 的中心像素坐标。"""
    return (BOARD_X + (c - 1) * TILE + TILE // 2,
            BOARD_Y + (r - 1) * TILE + TILE // 2)


# def collect_tile_image_paths():
#     """★ 汇总所有自定义图片路径（方式 A + 方式 B）。"""
#     paths = []
#     for p in TILE_IMAGES:
#         if os.path.isfile(p):
#             paths.append(p)
#         else:
#             print(f"[提示] 找不到图片：{p}")
#
#     if TILE_IMAGE_DIR and os.path.isdir(TILE_IMAGE_DIR):
#         for name in sorted(os.listdir(TILE_IMAGE_DIR)):
#             if name.lower().endswith(IMAGE_EXTS):
#                 full = os.path.join(TILE_IMAGE_DIR, name)
#                 if full not in paths:
#                     paths.append(full)
#     return paths
#
#
# def load_images(paths):
#     """★ 加载图片，失败的单张会被跳过而不是让程序崩溃。"""
#     imgs = []
#     for p in paths:
#         try:
#             imgs.append(pygame.image.load(p).convert_alpha())
#         except Exception as e:
#             print(f"[提示] 图片加载失败：{p} （{e}）")
#     return imgs
def load_tile_images():
    """优先从内嵌 base64 加载（网页版），失败再读本地文件（桌面版）。"""
    imgs = []
    try:
        from embedded_tiles import TILES_B64
        for data in TILES_B64:
            raw = base64.b64decode(data.split(",", 1)[1])
            imgs.append(pygame.image.load(io.BytesIO(raw)).convert_alpha())
        if imgs:
            print(f"[OK] 从内嵌数据加载 {len(imgs)} 张图")
            return imgs
    except ImportError:
        pass
    except Exception as e:
        print(f"[warn] 内嵌图片加载失败：{e}")

    # 桌面版回退：读本地文件
    paths = collect_tile_image_paths()
    return load_images(paths)

# ==================== 核心算法：路径判定 ====================
def find_path(grid, rows, cols, a, b):
    """
    在带一圈空边框的网格 grid 中，寻找 a -> b 的连通路径。

    grid 尺寸为 (rows+2) x (cols+2)，下标 1..rows / 1..cols 是棋盘内部，
    第 0 行/列与最后一行/列是永远为空的“外圈”，允许连线绕出去。
    grid[r][c] == -1 表示空格。

    规则：路径只能走空格（终点 b 除外），拐弯次数 <= 2。

    返回：从 a 到 b 经过的所有格子坐标列表（含首尾），无解返回 None。
    """
    H, W = rows + 2, cols + 2
    INF = 99
    best = [[[INF] * 4 for _ in range(W)] for _ in range(H)]
    parent = {}

    start = (a[0], a[1], -1)
    parent[start] = None
    dq = deque([(a[0], a[1], -1, 0)])

    while dq:
        r, c, d, turns = dq.popleft()
        for nd, (dr, dc) in enumerate(DIRS):
            nr, nc = r + dr, c + dc
            if not (0 <= nr < H and 0 <= nc < W):
                continue

            nt = turns if (d == -1 or d == nd) else turns + 1
            if nt > 2:
                continue

            if (nr, nc) == b:
                path = []
                cur, seen = (r, c, d), set()
                while cur is not None and cur not in seen:
                    seen.add(cur)
                    path.append((cur[0], cur[1]))
                    cur = parent.get(cur)
                path.reverse()
                path.append(b)
                return path

            if grid[nr][nc] != -1:
                continue

            if nt < best[nr][nc][nd]:
                best[nr][nc][nd] = nt
                parent[(nr, nc, nd)] = (r, c, d)
                dq.append((nr, nc, nd, nt))

    return None

# 游戏交互按钮
class Button:
    """简单的悬停高亮按钮，按下即触发。"""

    def __init__(self, x, y, w, h, text, action, base_color, hover_color):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.action = action
        self.base_color = base_color
        self.hover_color = hover_color
        self.enabled = True

    def draw(self, screen, font, mouse_pos):
        hovered = self.enabled and self.rect.collidepoint(mouse_pos)

        if not self.enabled:
            bg, fg = (56, 62, 78), (108, 114, 132)
        elif hovered:
            bg, fg = self.hover_color, (26, 30, 42)
        else:
            bg, fg = self.base_color, (240, 244, 252)

        pygame.draw.rect(screen, bg, self.rect, border_radius=9)
        if hovered:
            pygame.draw.rect(screen, (255, 255, 255), self.rect, 2,
                             border_radius=9)

        txt = font.render(self.text, True, fg)
        screen.blit(txt, txt.get_rect(center=self.rect.center))

# ==================== 游戏主体 ====================
class LinkGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(WINDOW_TITLE)
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
        self.clock = pygame.time.Clock()


        self.f_big = load_font(int(TILE * 0.69), bold=True)
        self.f_mid = load_font(int(TILE * 0.34), bold=True)
        self.f_small = load_font(int(TILE * 0.27))
        self.f_tile = load_font(int(TILE * 0.5), bold=True)
        self.f_btn = load_font(int(TILE * 0.27), bold=True)

        # ---------- ★ 加载自定义方块图片 ----------
        # image_paths = collect_tile_image_paths()
        # self.tile_images = load_images(image_paths)
        self.tile_images = load_tile_images()

        if self.tile_images:
            limit = max(2, min(len(LETTERS), ROWS * COLS // 2))
            self.num_kinds = min(limit, len(self.tile_images))
            self.tile_images = self.tile_images[:self.num_kinds]
            print(f"[OK] 已加载 {self.num_kinds} 种自定义方块图案。")
            if self.num_kinds < 4:
                print("[提示] 图案种类偏少，建议至少 4 种，否则棋盘会显得很单调。")
        else:
            self.num_kinds = DEFAULT_KINDS
            print("[提示] 未找到自定义图片，使用内置的彩色字母方块。")
        # ------------------------------------------

        self.tile_surfs = [self._make_tile_surface(k)
                           for k in range(self.num_kinds)]

        self.f_btn = load_font(17, bold=True)


        bw = int(TILE * 1.70)
        bh = int(TILE * 0.53)
        gap = int(TILE * 0.25)
        total_w = bw * 3 + gap * 2
        bx = (WIDTH - total_w) // 2
        by = int(HUD_H * 0.52)

        self.buttons = [
            Button(bx,                 by, bw, bh, "重排R", "reshuffle",
                   (230, 150, 70),  (255, 185, 105)),
            Button(bx + bw + gap,      by, bw, bh, "提示H", "hint",
                   (70, 170, 200),  (110, 210, 235)),
            Button(bx + (bw + gap) * 2, by, bw, bh, "新游戏N", "new_game",
                   (70, 180, 140),  (110, 215, 170)),
        ]

        self.new_game()


    # ---------- 方块贴图 ----------
    def _make_tile_surface(self, kind):
        """生成一张方块贴图：有图片用图片，没图片就画彩色字母。"""
        # s = TILE - 6
        s = TILE - TILE_PAD * 2
        surf = pygame.Surface((s, s), pygame.SRCALPHA)
        rect = pygame.Rect(0, 0, s, s)
        base = PALETTE[kind % len(PALETTE)]

        # 阴影
        pygame.draw.rect(surf, (0, 0, 0, 70), rect.move(0, 3),
                         border_radius=PIC_RADIUS)

        # ==================== ★ 分支一：使用你自己的图片 ====================
        if kind < len(self.tile_images):
            # 彩色底板（当图片带透明区域时会露出来）
            pygame.draw.rect(surf, base, rect, border_radius=PIC_RADIUS)
            pygame.draw.rect(surf, tuple(min(255, v + 45) for v in base),
                             rect.inflate(-8, -8), border_radius=PIC_RADIUS - 3,
                             width=3)

            img = self.tile_images[kind]
            iw, ih = img.get_size()


            scale = max((s - PIC_PADDING * 2) / iw,
                        (s - PIC_PADDING * 2) / ih)
            nw = max(1, int(iw * scale))
            nh = max(1, int(ih * scale))

            pic = pygame.transform.smoothscale(img, (nw, nh))

            layer = pygame.Surface((s, s), pygame.SRCALPHA)
            layer.blit(pic, ((s - nw) // 2, (s - nh) // 2))
            # 圆角遮罩，让图片四角跟底板圆角一致
            mask = pygame.Surface((s, s), pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), rect,
                             border_radius=PIC_RADIUS)
            layer.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(layer, (0, 0))
            return surf
        # ==================================================================

        # ==================== ★ 分支二：内置彩色字母方块 ====================
        pygame.draw.rect(surf, base, rect, border_radius=PIC_RADIUS)
        top = tuple(min(255, v + 45) for v in base)
        pygame.draw.rect(surf, top, rect.inflate(-8, -8),
                         border_radius=PIC_RADIUS - 3, width=3)

        ch = LETTERS[kind % len(LETTERS)]
        txt = self.f_tile.render(ch, True, text_color_for(base))
        surf.blit(txt, txt.get_rect(center=(s // 2, s // 2)))
        return surf
        # ==================================================================

    # ---------- 初始化 ----------
    def new_game(self):
        self.grid = [[-1] * (COLS + 2) for _ in range(ROWS + 2)]

        total = ROWS * COLS
        pool = []
        for i in range(total // 2):
            k = i % self.num_kinds
            pool.extend((k, k))
        random.shuffle(pool)

        idx = 0
        for r in range(1, ROWS + 1):
            for c in range(1, COLS + 1):
                self.grid[r][c] = pool[idx]
                idx += 1

        self.selected = None
        self.effects = []
        self.hint = None
        self.hint_timer = 0.0
        self.hint_path = None  # ✅ 新增这一行
        self.score = 0
        self.time_left = TOTAL_TIME
        self.state = "playing"
        self.message = ""
        self.message_timer = 0.0

        self.ensure_solvable()

    # ---------- 棋盘查询 ----------
    def remaining(self):
        return sum(1 for r in range(1, ROWS + 1)
                   for c in range(1, COLS + 1) if self.grid[r][c] != -1)

    def find_any_pair(self):
        groups = {}
        for r in range(1, ROWS + 1):
            for c in range(1, COLS + 1):
                k = self.grid[r][c]
                if k != -1:
                    groups.setdefault(k, []).append((r, c))

        for pts in groups.values():
            n = len(pts)
            for i in range(n):
                for j in range(i + 1, n):
                    p = find_path(self.grid, ROWS, COLS, pts[i], pts[j])
                    if p is not None:
                        return (pts[i], pts[j], p)
        return None

    # ---------- 重排 ----------
    def _shuffle_values(self):
        cells = [(r, c) for r in range(1, ROWS + 1) for c in range(1, COLS + 1)
                 if self.grid[r][c] != -1]
        vals = [self.grid[r][c] for r, c in cells]
        random.shuffle(vals)
        for (r, c), v in zip(cells, vals):
            self.grid[r][c] = v

    def ensure_solvable(self):
        for _ in range(40):
            if self.find_any_pair() is not None:
                return
            self._shuffle_values()

    def do_reshuffle(self):
        if self.remaining() < 2:
            return
        for _ in range(60):
            self._shuffle_values()
            if self.find_any_pair() is not None:
                break
        self.selected = None

        self.hint = None  # ✅ 新增
        self.hint_timer = 0.0  # ✅ 新增
        self.hint_path = None  # ✅ 新增

    # ---------- 交互 ----------
    def pos_to_cell(self, mx, my):
        if not (BOARD_X <= mx < BOARD_X + BOARD_W and
                BOARD_Y <= my < BOARD_Y + BOARD_H):
            return None
        c = int((mx - BOARD_X) // TILE) + 1
        r = int((my - BOARD_Y) // TILE) + 1
        return (r, c)

    def on_click(self, pos):
        cell = self.pos_to_cell(*pos)
        if cell is None:
            self.selected = None
            return

        r, c = cell
        if self.grid[r][c] == -1:
            self.selected = None
            return

        if self.selected is None:
            self.selected = (r, c)
            return
        if self.selected == (r, c):
            self.selected = None
            return

        a = self.selected
        if self.grid[a[0]][a[1]] == self.grid[r][c]:
            path = find_path(self.grid, ROWS, COLS, a, (r, c))
            if path is not None:
                self.clear_pair(a, (r, c), path)
                self.selected = None
                return
        self.selected = (r, c)

    def clear_pair(self, a, b, path):
        kind = self.grid[a[0]][a[1]]
        self.grid[a[0]][a[1]] = -1
        self.grid[b[0]][b[1]] = -1

        self.effects.append({"type": "path", "path": path, "t": 0.0, "life": 0.30})
        for cell in (a, b):
            self.effects.append({"type": "pop", "cell": cell, "kind": kind,
                                 "t": 0.0, "life": 0.30})

        self.score += 10

        if self.remaining() == 0:
            self.score += int(self.time_left) * 5
            self.state = "won"
        elif self.find_any_pair() is None:
            self.do_reshuffle()
            self.set_message("无可消对，自动重排！")

    def show_hint(self):
        pair = self.find_any_pair()
        if pair:
            self.hint = (pair[0], pair[1])
            self.hint_path = pair[2]  # ✅ 记录路径
            self.hint_timer = 2.0

    def set_message(self, text, duration=1.6):
        self.message = text
        self.message_timer = duration

    def toggle_fullscreen(self):
        self.fullscreen = not getattr(self, "fullscreen", False)
        if self.fullscreen:
            self.screen = pygame.display.set_mode(
                (0, 0), pygame.FULLSCREEN | pygame.SCALED)
        else:
            self.screen = pygame.display.set_mode(
                (WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)

    def _on_button(self, action):
        if action == "new_game":
            self.new_game()
        elif action == "reshuffle" and self.state == "playing":
            self.do_reshuffle()
            self.set_message("已重排")
        elif action == "hint" and self.state == "playing":
            self.show_hint()

    def _update_buttons(self):
        playing = (self.state == "playing")
        for btn in self.buttons:
            # 新游戏永远可用；重排/提示只在游戏进行中可用
            btn.enabled = True if btn.action == "new_game" else playing

    # ---------- 每帧更新 ----------
    def update(self, dt):
        self._update_buttons()  # ✅ 新增
        for e in self.effects:
            e["t"] += dt
        self.effects = [e for e in self.effects if e["t"] < e["life"]]

        if self.hint_timer > 0:
            self.hint_timer -= dt
            if self.hint_timer <= 0:
                self.hint = None
                self.hint_path = None  # ✅ 新增

        if self.message_timer > 0:
            self.message_timer -= dt

        if self.state == "playing":
            self.time_left -= dt
            if self.time_left <= 0:
                self.time_left = 0
                self.state = "lost"

    # ---------- 绘制 ----------
    def draw(self):
        self.screen.fill(BG)

        pygame.draw.rect(self.screen, PANEL,
                         (BOARD_X - 10, BOARD_Y - 10, BOARD_W + 20, BOARD_H + 20),
                         border_radius=20)

        for r in range(1, ROWS + 1):
            for c in range(1, COLS + 1):
                if (r + c) % 2 == 0:
                    x = BOARD_X + (c - 1) * TILE
                    y = BOARD_Y + (r - 1) * TILE
                    pygame.draw.rect(self.screen, GRID_LINE, (x, y, TILE, TILE))

        for r in range(1, ROWS + 1):
            for c in range(1, COLS + 1):
                k = self.grid[r][c]
                if k != -1:
                    self.screen.blit(self.tile_surfs[k], cell_topleft(r, c))

        if self.selected:
            r, c = self.selected
            x, y = cell_topleft(r, c)
            pygame.draw.rect(self.screen, ACCENT,
                             (x - 2, y - 2, TILE - 2, TILE - 2), 3,
                             border_radius=16)

        if self.hint:
            for (r, c) in self.hint:
                x, y = cell_topleft(r, c)
                pygame.draw.rect(self.screen, HINT_COLOR,
                                 (x - 2, y - 2, TILE - 2, TILE - 2), 3,
                                 border_radius=16)
            if self.hint_path:  # ✅ 新增
                pts = [cell_center(r, c) for r, c in self.hint_path]  # ✅ 新增
                if len(pts) >= 2:  # ✅ 新增
                    pygame.draw.lines(self.screen, HINT_COLOR, False, pts, 3)  # ✅ 新增f):
        self._draw_effects()
        self._draw_hud()

        if self.message_timer > 0:
            self._draw_center_message(self.message)
        if self.state != "playing":
            self._draw_gameover()

    def _draw_effects(self):
        for e in self.effects:
            p = min(1.0, e["t"] / e["life"])

            if e["type"] == "pop":
                r, c = e["cell"]
                cx, cy = cell_center(r, c)
                base = self.tile_surfs[e["kind"]]
                scale = 1.0 + 0.6 * p
                w = max(4, int(base.get_width() * scale))
                surf = pygame.transform.smoothscale(base, (w, w))
                surf.set_alpha(int(255 * (1 - p)))
                self.screen.blit(surf, surf.get_rect(center=(cx, cy)))

            elif e["type"] == "path":
                pts = [cell_center(r, c) for r, c in e["path"]]
                if len(pts) < 2:
                    continue
                alpha = int(255 * (1 - p))
                xs = [q[0] for q in pts]
                ys = [q[1] for q in pts]
                x0, y0 = min(xs) - 8, min(ys) - 8
                w = max(xs) - x0 + 16
                h = max(ys) - y0 + 16
                layer = pygame.Surface((w, h), pygame.SRCALPHA)
                pygame.draw.lines(layer, (*ACCENT, alpha), False,
                                  [(q[0] - x0, q[1] - y0) for q in pts], 4)
                self.screen.blit(layer, (x0, y0))


    def _draw_hud(self):
        pygame.draw.rect(self.screen, (34, 39, 54), (0, 0, WIDTH, HUD_H))
        pygame.draw.line(self.screen, (58, 65, 86),
                         (0, HUD_H - 1), (WIDTH, HUD_H - 1), 2)


        row1_y = int(HUD_H * 0.12)

        score = self.f_mid.render(f"分数  {self.score}", True, TEXT)
        self.screen.blit(score, (MARGIN, row1_y))

        tcol = (255, 110, 110) if self.time_left < 30 else TEXT
        tm = self.f_mid.render(f"时间  {int(self.time_left):03d}s", True, tcol)
        self.screen.blit(tm, tm.get_rect(midtop=(WIDTH // 2, row1_y)))

        left = self.f_mid.render(f"剩余  {self.remaining()}", True, TEXT)
        self.screen.blit(left, left.get_rect(topright=(WIDTH - MARGIN, row1_y)))

        # 第二行：按钮
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            btn.draw(self.screen, self.f_btn, mouse_pos)

    def _draw_center_message(self, text):
        surf = self.f_mid.render(text, True, (25, 25, 35))
        pad_x, pad_y = 22, 12
        box = pygame.Surface((surf.get_width() + pad_x * 2,
                              surf.get_height() + pad_y * 2), pygame.SRCALPHA)
        pygame.draw.rect(box, (*ACCENT, 235), box.get_rect(), border_radius=14)
        box.blit(surf, surf.get_rect(center=box.get_rect().center))
        self.screen.blit(box, box.get_rect(
            center=(WIDTH // 2, BOARD_Y + BOARD_H // 2)))

    def _draw_gameover(self):
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((10, 12, 20, 180))
        self.screen.blit(veil, (0, 0))

        if self.state == "won":
            title, color = "恭喜通关！", (110, 240, 180)
        else:
            title, color = "时间到，游戏结束", (255, 130, 130)

        t = self.f_big.render(title, True, color)
        self.screen.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 55)))

        s = self.f_mid.render(f"最终得分：{self.score}", True, TEXT)
        self.screen.blit(s, s.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 5)))

        # r = self.f_small.render("点击任意位置 / 按 N 重新开始", True, (180, 186, 205))
        r = self.f_small.render("点击上方【新游戏】按钮重新开始", True, (180, 186, 205))
        self.screen.blit(r, r.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50)))

    # ---------- 主循环 ----------
    # def run(self):
    #     while True:
    #         dt = self.clock.tick(FPS) / 1000.0
    #
    #         for event in pygame.event.get():
    #             if event.type == pygame.QUIT:
    #                 pygame.quit()
    #                 sys.exit()
    #
    #
    #             elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
    #                 # 1) 先检查按钮
    #                 clicked = None
    #                 for btn in self.buttons:
    #                     if btn.enabled and btn.rect.collidepoint(event.pos):
    #                         clicked = btn
    #                         break
    #
    #                 if clicked is not None:
    #                     self._on_button(clicked.action)
    #                 elif self.state == "playing":
    #                     # 2) 没点按钮，且游戏进行中，才处理棋盘点击
    #                     self.on_click(event.pos)
    #                 # 游戏结束后点空白处不响应，只能点"新游戏"
    #
    #             elif event.type == pygame.KEYDOWN:
    #                 # ---- 调试用，确认按键真的进来了 ----
    #                 print(f"[KEY] key={event.key}  scancode={event.scancode}  "
    #                       f"unicode={event.unicode!r}  state={self.state}")
    #                 # -----------------------------------
    #
    #                 if event.key == pygame.K_ESCAPE:
    #                     pygame.quit()
    #                     sys.exit()
    #                 elif event.key == pygame.K_n:
    #                     self.new_game()
    #                 elif event.key == pygame.K_r and self.state == "playing":
    #                     self.do_reshuffle()
    #                     self.set_message("已重排")
    #                 elif event.key == pygame.K_h and self.state == "playing":
    #                     self.show_hint()
    #                 elif event.key == pygame.K_F11:
    #                     self.toggle_fullscreen()
    #
    #         self.update(dt)
    #         self.draw()
    #         pygame.display.flip()
    async def run(self):
        running = True
        try:
            while running:
                dt = self.clock.tick(FPS) / 1000.0

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False  # ✅
                        break
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        clicked = None
                        for btn in self.buttons:
                            if btn.enabled and btn.rect.collidepoint(event.pos):
                                clicked = btn
                                break
                        if clicked is not None:
                            self._on_button(clicked.action)
                        elif self.state == "playing":
                            self.on_click(event.pos)
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False  # ✅ 不用 sys.exit
                            break
                        elif event.key == pygame.K_n:
                            self.new_game()
                        elif event.key == pygame.K_r and self.state == "playing":
                            self.do_reshuffle()
                            self.set_message("已重排")
                        elif event.key == pygame.K_h and self.state == "playing":
                            self.show_hint()
                        elif event.key == pygame.K_F11:
                            self.toggle_fullscreen()

                self.update(dt)
                self.draw()
                pygame.display.flip()
                await asyncio.sleep(0)

        except asyncio.CancelledError:
            pass  # ✅ 安静退出
        finally:
            pygame.quit()


if __name__ == "__main__":
    try:
        asyncio.run(LinkGame().run())
    except KeyboardInterrupt:
        pass