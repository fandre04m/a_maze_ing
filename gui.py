#!/usr/bin/env python3
from mlx import Mlx
from config_parser import ParserError, MazeConfig, load_config

X_EVENT_DESTROY_NOTIFY = 33
X_MASK_NO_EVENT = 0

CELL_SIZE = 40

# ===== Maze Data Contract =====
# maze = {
#   "width": int,
#   "height": int,
#   "cells": List[int],   # length = width * height, each int = wall bitmask
#   "entry": (x, y),
#   "exit": (x, y),
# }
#
# Wall bitmask (proposed):
# 1 = NORTH wall
# 2 = EAST wall
# 4 = SOUTH wall
# 8 = WEST wall


def put_pixel(data, size_line, x, y, color):
    # color is 0xRRGGBB
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF

    idx = y * size_line + x * 4
    data[idx + 0] = b
    data[idx + 1] = g
    data[idx + 2] = r
    data[idx + 3] = 0xFF  # alpha must be 0xFF on your MLX


def generate_fake_maze(width, height):
    """Temporary placeholder maze for renderer testing."""
    cells = [0] * (width * height)

    # Make a simple border: all outer walls closed
    for y in range(height):
        for x in range(width):
            wall = 0
            if y == 0:
                wall |= 1  # NORTH
            if x == width - 1:
                wall |= 2  # EAST
            if y == height - 1:
                wall |= 4  # SOUTH
            if x == 0:
                wall |= 8  # WEST
            cells[y * width + x] = wall

    return {
        "width": width,
        "height": height,
        "cells": cells,
        "entry": (0, 0),
        "exit": (width - 1, height - 1),
    }


def draw_line_h(data, size_line, x0, x1, y, color):
    for x in range(x0, x1):
        put_pixel(data, size_line, x, y, color)


def draw_line_v(data, size_line, x, y0, y1, color):
    for y in range(y0, y1):
        put_pixel(data, size_line, x, y, color)


def draw_cell_walls(ctx, cell_x, cell_y, walls, wall_color=0xFFFFFF):
    # pixel coords
    x0 = cell_x * CELL_SIZE
    y0 = cell_y * CELL_SIZE
    x1 = x0 + CELL_SIZE
    y1 = y0 + CELL_SIZE

    data = ctx["data"]
    size_line = ctx["size_line"]

    # NORTH
    if walls & 1:
        draw_line_h(data, size_line, x0, x1, y0, wall_color)
    # EAST
    if walls & 2:
        draw_line_v(data, size_line, x1 - 1, y0, y1, wall_color)
    # SOUTH
    if walls & 4:
        draw_line_h(data, size_line, x0, x1, y1 - 1, wall_color)
    # WEST
    if walls & 8:
        draw_line_v(data, size_line, x0, y0, y1, wall_color)


def render_maze(ctx, maze_data):
    data = ctx["data"]
    size_line = ctx["size_line"]
    width_px = ctx["win_w"]
    height_px = ctx["win_h"]

    # background (dark gray)
    row = bytes([0x20, 0x20, 0x20, 0xFF]) * width_px
    for y in range(height_px):
        start = y * size_line
        end = start + size_line
        data[start:end] = row

    # draw walls
    w = maze_data["width"]
    h = maze_data["height"]
    cells = maze_data["cells"]

    for y in range(h):
        for x in range(w):
            walls = cells[y * w + x]
            draw_cell_walls(ctx, x, y, walls, wall_color=0xFFFFFF)

    ctx["mlx"].mlx_put_image_to_window(
        ctx["mlx_ptr"], ctx["win_ptr"], ctx["img_ptr"], 0, 0
    )


def on_key(keycode: int, ctx: dict):
    if keycode == 65307:  # ESC
        ctx["mlx"].mlx_loop_exit(ctx["mlx_ptr"])


def on_destroy(ctx: dict):
    ctx["mlx"].mlx_loop_exit(ctx["mlx_ptr"])


def on_expose(ctx: dict):
    render_maze(ctx, ctx["maze"])


def gui_start():
    try:
        cfg: MazeConfig = load_config()
    except ParserError as e:
        print(f"Config error: {e}")
        return 1

    mlx = Mlx()
    mlx_ptr = mlx.mlx_init()
    if not mlx_ptr:
        print("Error: mlx_init failed")
        return 1

    # temporary maze until real data exists
    maze = generate_fake_maze(cfg.width, cfg.height)

    win_w = maze["width"] * CELL_SIZE
    win_h = maze["height"] * CELL_SIZE

    win_ptr = mlx.mlx_new_window(mlx_ptr, win_w, win_h, "a_maze_ing")
    if not win_ptr:
        print("Error: window failed")
        return 1

    img_ptr = mlx.mlx_new_image(mlx_ptr, win_w, win_h)
    if not img_ptr:
        print("Error: image failed")
        return 1

    data, bpp, size_line, endian = mlx.mlx_get_data_addr(img_ptr)

    ctx = {
        "mlx": mlx,
        "mlx_ptr": mlx_ptr,
        "win_ptr": win_ptr,
        "img_ptr": img_ptr,
        "data": data,
        "bpp": bpp,
        "size_line": size_line,
        "endian": endian,
        "win_w": win_w,
        "win_h": win_h,
        "maze": maze,
    }

    mlx.mlx_key_hook(win_ptr, on_key, ctx)
    mlx.mlx_expose_hook(win_ptr, on_expose, ctx)
    mlx.mlx_hook(win_ptr, X_EVENT_DESTROY_NOTIFY, X_MASK_NO_EVENT,
                 on_destroy, ctx)

    # initial draw
    render_maze(ctx, maze)

    mlx.mlx_loop(mlx_ptr)

    mlx.mlx_destroy_image(mlx_ptr, img_ptr)
    mlx.mlx_destroy_window(mlx_ptr, win_ptr)
    mlx.mlx_release(mlx_ptr)
    return 0


if __name__ == "__main__":
    gui_start()
