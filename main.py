# Etch-A-Sketch style renderer with Turtle
# Requirements: pillow (PIL). Run: python this_file.py

from turtle import Screen, Turtle
from PIL import Image, ImageOps, ImageFilter

# ------------------- CONFIG -------------------
#
# example:IMAGE_PATH = "/mnt/data/9c77c786-c456-499b-aea8-97dbb23dc414.png"  # your pasted image (if available)
IMAGE_PATH = "<path>"
            # <-- put your image path here
TARGET_WIDTH  = 220                # pixel columns (more = more detail = slower)
TARGET_HEIGHT = 280                # pixel rows
THRESHOLD = 140                    # 0..255 (lower = darker / fewer lines)
LINE_WIDTH = 1                     # “wire” thickness
DRAW_SPEED = 0                     # 0 = fastest
PADDING = 40                       # border around drawing
BG_COLOR = "#d8d2c4"               # “sand” Etch A Sketch backdrop
WIRE_COLOR = "#323232"             # drawing color (dark gray)
CONTINUOUS_MODE = False            # True = continuous serpentine line with edge connectors
# ----------------------------------------------

def load_and_binarize(path):
    im = Image.open(path).convert("L")  # grayscale
    # Boost edges a bit so features pop in line-art
    edges = im.filter(ImageFilter.FIND_EDGES)
    edges = ImageOps.autocontrast(edges, cutoff=2)
    # Blend original + edges for a punchier map
    im = Image.blend(im, edges, 0.35)

    # Fit to target grid (preserve aspect, then pad)
    im = ImageOps.contain(im, (TARGET_WIDTH, TARGET_HEIGHT))
    # Pad to exact size
    canvas = Image.new("L", (TARGET_WIDTH, TARGET_HEIGHT), 255)
    ox = (TARGET_WIDTH - im.width) // 2
    oy = (TARGET_HEIGHT - im.height) // 2
    canvas.paste(im, (ox, oy))

    # Dither to B/W for a crisp “wire” look
    bw = canvas.point(lambda p: 0 if p < THRESHOLD else 255, mode="1")
    return bw

def to_screen_coords(col, row, cell_w, cell_h, origin_x, origin_y):
    # Map pixel grid (0..W-1, 0..H-1) to turtle coordinates
    x = origin_x + col * cell_w
    y = origin_y - row * cell_h
    return x, y

def draw_clean_segments(t, grid, cell_w, cell_h, origin_x, origin_y):
    """Draw horizontal black runs, lifting pen between them (clean mode)."""
    h = len(grid)
    w = len(grid[0])
    for r in range(h):
        c = 0
        while c < w:
            # skip white
            while c < w and not grid[r][c]:
                c += 1
            if c >= w:
                break
            # start of black run
            run_start = c
            while c < w and grid[r][c]:
                c += 1
            run_end = c - 1
            # draw this horizontal segment
            x1, y1 = to_screen_coords(run_start, r, cell_w, cell_h, origin_x, origin_y)
            x2, y2 = to_screen_coords(run_end + 1, r, cell_w, cell_h, origin_x, origin_y)
            t.penup(); t.goto(x1, y1); t.pendown()
            t.goto(x2, y2)

def draw_continuous_serpentine(t, grid, cell_w, cell_h, origin_x, origin_y):
    """
    Draw rows in a single serpentine path.
    We add short vertical edge connectors along the right/left border
    to move between rows without cutting through the drawing interior.
    """
    h = len(grid)
    w = len(grid[0])
    # Start at top-left border
    left_edge_x, top_y = to_screen_coords(0, 0, cell_w, cell_h, origin_x, origin_y)
    right_edge_x, _ = to_screen_coords(w, 0, cell_w, cell_h, origin_x, origin_y)
    t.penup(); t.goto(left_edge_x, top_y - cell_h/2); t.pendown()

    for r in range(h):
        row_y = to_screen_coords(0, r, cell_w, cell_h, origin_x, origin_y)[1] - cell_h/2
        # Determine direction (even rows L->R, odd rows R->L)
        left_to_right = (r % 2 == 0)
        c_range = range(w) if left_to_right else range(w-1, -1, -1)

        # Move along the row on the edge first (pen down)
        target_x = left_edge_x if not left_to_right else right_edge_x
        t.goto(target_x, row_y)  # to far edge

        # Scan row: when pixel is black, draw a short 1-cell horizontal dash
        for c in c_range:
            if grid[r][c]:
                x1, y1 = to_screen_coords(c, r, cell_w, cell_h, origin_x, origin_y)
                # center of this cell horizontally
                # draw a 1-cell segment toward direction
                if left_to_right:
                    x2, y2 = to_screen_coords(c+1, r, cell_w, cell_h, origin_x, origin_y)
                else:
                    x2, y2 = to_screen_coords(c, r, cell_w, cell_h, origin_x, origin_y)
                    x1, y1 = to_screen_coords(c+1, r, cell_w, cell_h, origin_x, origin_y)
                t.goto(x1, y1 - cell_h/2)
                t.goto(x2, y2 - cell_h/2)

        # edge connector to next row (drawn along border)
        if r < h - 1:
            next_y = row_y - cell_h
            edge_x = right_edge_x if left_to_right else left_edge_x
            t.goto(edge_x, row_y)
            t.goto(edge_x, next_y)

def main():
    # --- prep image to boolean grid (True = black pixel to draw) ---
    bw = load_and_binarize(IMAGE_PATH)
    W, H = bw.size
    px = bw.load()
    grid = [[(px[x, y] == 0) for x in range(W)] for y in range(H)]

    # --- turtle setup ---
    screen = Screen()
    screen.setup(width=1000, height=1000)
    screen.bgcolor(BG_COLOR)
    screen.title("Etch-A-Sketch style renderer")

    # compute drawing cell size to fit window nicely
    drawable_w = screen.window_width() - 2 * PADDING
    drawable_h = screen.window_height() - 2 * PADDING
    cell_w = drawable_w / W
    cell_h = drawable_h / H
    # origin at top-left corner of drawing area
    origin_x = -drawable_w/2
    origin_y = drawable_h/2

    timmy = Turtle()
    timmy.hideturtle()
    timmy.speed(DRAW_SPEED)
    timmy.pensize(LINE_WIDTH)
    timmy.pencolor(WIRE_COLOR)

    if CONTINUOUS_MODE:
        draw_continuous_serpentine(timmy, grid, cell_w, cell_h, origin_x, origin_y)
    else:
        draw_clean_segments(timmy, grid, cell_w, cell_h, origin_x, origin_y)

    # label
    timmy.penup()
    timmy.goto(0, -drawable_h/2 - 20)
    timmy.pendown()
    timmy.write("Etch-A-Sketch style (axis-aligned lines)", align="center", font=("Arial", 14, "normal"))

    screen.mainloop()

if __name__ == "__main__":
    main()
