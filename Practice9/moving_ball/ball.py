import pygame


def run_ball_game():
    pygame.init()
    pygame.display.set_caption("Practice 09 - Moving Ball")

    width = 800
    height = 600
    step = 20
    radius = 25
    move_speed = 320  # pixels per second (for smooth animation)

    screen = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()

    x = float(width // 2)
    y = float(height // 2)
    move_queue = []

    def in_bounds(next_x, next_y):
        return radius <= next_x <= width - radius and radius <= next_y <= height - radius

    running = True
    while running:
        delta_time = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                dx = 0
                dy = 0

                if event.key == pygame.K_LEFT:
                    dx = -step
                elif event.key == pygame.K_RIGHT:
                    dx = step
                elif event.key == pygame.K_UP:
                    dy = -step
                elif event.key == pygame.K_DOWN:
                    dy = step

                if dx != 0 or dy != 0:
                    if move_queue:
                        start_x, start_y = move_queue[-1]
                    else:
                        start_x, start_y = x, y

                    next_x = start_x + dx
                    next_y = start_y + dy

                    # Ignore input that goes out of screen.
                    if in_bounds(next_x, next_y):
                        move_queue.append((next_x, next_y))

        # Smoothly move to next queued target.
        if move_queue:
            target_x, target_y = move_queue[0]
            diff_x = target_x - x
            diff_y = target_y - y
            distance = (diff_x * diff_x + diff_y * diff_y) ** 0.5
            max_step = move_speed * delta_time

            if distance <= max_step or distance == 0:
                x = target_x
                y = target_y
                move_queue.pop(0)
            else:
                x += (diff_x / distance) * max_step
                y += (diff_y / distance) * max_step

        screen.fill((255, 255, 255))
        pygame.draw.circle(screen, (220, 0, 0), (round(x), round(y)), radius)

        pygame.display.flip()

    pygame.quit()