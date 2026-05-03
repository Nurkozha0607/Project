import pygame
from collections import deque

# Three brush size options the user can switch between
BRUSH_SIZES = [2, 5, 10]


# Flood fill using BFS — starts at 'start' pixel and fills all
# connected pixels that match the original color with 'fill_color'
def flood_fill(surface, start, fill_color):
    x0, y0 = start
    w, h = surface.get_size()

    # Make sure the click is inside the canvas
    if not (0 <= x0 < w and 0 <= y0 < h):
        return

    # Remember the color we want to replace
    target_color = tuple(surface.get_at((x0, y0))[:3])
    new_color = tuple(fill_color[:3])

    # No work needed if the area is already the right color
    if target_color == new_color:
        return

    # 2D grid to track which pixels we already visited
    visited = [[False] * w for _ in range(h)]

    # BFS queue starts at the clicked pixel
    queue = deque()
    queue.append((x0, y0))
    visited[y0][x0] = True

    while queue:
        x, y = queue.popleft()

        # Skip if this pixel changed color (hit a boundary)
        if tuple(surface.get_at((x, y))[:3]) != target_color:
            continue

        # Paint this pixel
        surface.set_at((x, y), new_color)

        # Check all 4 neighbours
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx]:
                visited[ny][nx] = True
                queue.append((nx, ny))