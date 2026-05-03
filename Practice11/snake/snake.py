from __future__ import annotations

import random

import pygame


CELL_SIZE = 25
GRID_COLS = 24
GRID_ROWS = 24
HUD_HEIGHT = 70

WINDOW_WIDTH = GRID_COLS * CELL_SIZE
WINDOW_HEIGHT = HUD_HEIGHT + GRID_ROWS * CELL_SIZE

BASE_SPEED = 7
FOODS_PER_LEVEL = 4
FOOD_LIFETIME_MS = 5000


def is_wall(cell: tuple[int, int]) -> bool:
    """Return True when a cell is on the border wall."""
    x, y = cell
    return x == 0 or y == 0 or x == GRID_COLS - 1 or y == GRID_ROWS - 1


def is_opposite_direction(a: tuple[int, int], b: tuple[int, int]) -> bool:
    """Prevent direct reverse direction to avoid instant self-collision."""
    return a[0] == -b[0] and a[1] == -b[1]


class SnakeGame:
    """Practice 11 Snake: weighted food + disappearing timer."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Practice 11 - Snake")

        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        self.title_font = pygame.font.SysFont("arial", 32, bold=True)
        self.hud_font = pygame.font.SysFont("consolas", 24, bold=True)
        self.help_font = pygame.font.SysFont("arial", 20)
        self.food_font = pygame.font.SysFont("arial", 16, bold=True)

        self.reset_game()

    def reset_game(self) -> None:
        # Snake starts with 3 body parts in center.
        start_x = GRID_COLS // 2
        start_y = GRID_ROWS // 2
        self.snake = [(start_x, start_y), (start_x - 1, start_y), (start_x - 2, start_y)]

        self.direction = (1, 0)
        self.next_direction = (1, 0)

        self.score = 0
        self.level = 1
        self.speed = BASE_SPEED
        self.game_over = False

        self.food = self.generate_food()

    def generate_food_position(self) -> tuple[int, int]:
        """Food cannot spawn on wall border or on snake body."""
        snake_cells = set(self.snake)
        free_cells: list[tuple[int, int]] = []

        for x in range(1, GRID_COLS - 1):
            for y in range(1, GRID_ROWS - 1):
                cell = (x, y)
                if cell not in snake_cells:
                    free_cells.append(cell)

        if not free_cells:
            return (1, 1)
        return random.choice(free_cells)

    def generate_food(self) -> dict[str, object]:
        """Create weighted food with random color/value and start timer."""
        weight, color = random.choice(
            [
                (1, (230, 70, 70)),    # common
                (2, (255, 170, 40)),   # medium
                (3, (180, 80, 255)),   # rare
            ]
        )
        return {
            "pos": self.generate_food_position(),
            "weight": weight,
            "color": color,
            "spawn_time": pygame.time.get_ticks(),
        }

    def update_level_and_speed(self) -> None:
        # Level uses score.
        new_level = 1 + (self.score // FOODS_PER_LEVEL)
        if new_level != self.level:
            self.level = new_level
            self.speed = BASE_SPEED + (self.level - 1) * 2

    def get_food_seconds_left(self) -> float:
        now = pygame.time.get_ticks()
        elapsed = now - int(self.food["spawn_time"])
        left_ms = max(0, FOOD_LIFETIME_MS - elapsed)
        return left_ms / 1000.0

    def handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

                if self.game_over and event.key == pygame.K_r:
                    self.reset_game()
                    continue

                wanted_direction = self.next_direction
                if event.key == pygame.K_LEFT:
                    wanted_direction = (-1, 0)
                elif event.key == pygame.K_RIGHT:
                    wanted_direction = (1, 0)
                elif event.key == pygame.K_UP:
                    wanted_direction = (0, -1)
                elif event.key == pygame.K_DOWN:
                    wanted_direction = (0, 1)

                if not is_opposite_direction(wanted_direction, self.direction):
                    self.next_direction = wanted_direction

        return True

    def update_game(self) -> None:
        if self.game_over:
            return

        # Food disappears after timer expires.
        if self.get_food_seconds_left() <= 0:
            self.food = self.generate_food()

        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        if is_wall(new_head):
            self.game_over = True
            return

        if new_head in self.snake:
            self.game_over = True
            return

        self.snake.insert(0, new_head)

        food_pos = tuple(self.food["pos"])  # type: ignore[arg-type]
        food_weight = int(self.food["weight"])
        if new_head == food_pos:
            # Weighted food gives weighted score points.
            self.score += food_weight
            self.update_level_and_speed()
            self.food = self.generate_food()
        else:
            self.snake.pop()

    def draw_grid(self) -> None:
        play_area = pygame.Rect(0, HUD_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT - HUD_HEIGHT)
        pygame.draw.rect(self.screen, (18, 18, 20), play_area)

        for x in range(GRID_COLS):
            for y in range(GRID_ROWS):
                if is_wall((x, y)):
                    cell_rect = pygame.Rect(
                        x * CELL_SIZE,
                        HUD_HEIGHT + y * CELL_SIZE,
                        CELL_SIZE,
                        CELL_SIZE,
                    )
                    pygame.draw.rect(self.screen, (80, 80, 90), cell_rect)

    def draw_food(self) -> None:
        fx, fy = tuple(self.food["pos"])  # type: ignore[arg-type]
        food_color = tuple(self.food["color"])  # type: ignore[arg-type]
        food_weight = int(self.food["weight"])

        center_x = fx * CELL_SIZE + CELL_SIZE // 2
        center_y = HUD_HEIGHT + fy * CELL_SIZE + CELL_SIZE // 2

        pygame.draw.circle(self.screen, food_color, (center_x, center_y), CELL_SIZE // 2 - 3)
        label = self.food_font.render(str(food_weight), True, (255, 255, 255))
        label_rect = label.get_rect(center=(center_x, center_y))
        self.screen.blit(label, label_rect)

    def draw_snake(self) -> None:
        for index, (x, y) in enumerate(self.snake):
            rect = pygame.Rect(
                x * CELL_SIZE + 2,
                HUD_HEIGHT + y * CELL_SIZE + 2,
                CELL_SIZE - 4,
                CELL_SIZE - 4,
            )

            if index == 0:
                pygame.draw.rect(self.screen, (90, 245, 110), rect, border_radius=5)
            else:
                pygame.draw.rect(self.screen, (45, 185, 70), rect, border_radius=5)

    def draw_hud(self) -> None:
        pygame.draw.rect(self.screen, (36, 36, 42), (0, 0, WINDOW_WIDTH, HUD_HEIGHT))

        title = self.title_font.render("SNAKE", True, (240, 240, 240))
        self.screen.blit(title, (14, 14))

        score_text = self.hud_font.render(f"Score: {self.score}", True, (245, 245, 245))
        level_text = self.hud_font.render(f"Level: {self.level}", True, (245, 245, 245))
        speed_text = self.help_font.render(f"Speed: {self.speed}", True, (212, 212, 212))
        food_timer = self.help_font.render(
            f"Food timer: {self.get_food_seconds_left():.1f}s",
            True,
            (255, 215, 128),
        )

        self.screen.blit(score_text, (170, 20))
        self.screen.blit(level_text, (340, 20))
        self.screen.blit(speed_text, (500, 10))
        self.screen.blit(food_timer, (500, 34))

    def draw_game_over_overlay(self) -> None:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 145))
        self.screen.blit(overlay, (0, 0))

        text1 = self.title_font.render("GAME OVER", True, (255, 255, 255))
        text2 = self.hud_font.render("Press R to Restart", True, (255, 255, 255))
        text3 = self.help_font.render("Press ESC to Quit", True, (230, 230, 230))

        self.screen.blit(text1, text1.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 30)))
        self.screen.blit(text2, text2.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 15)))
        self.screen.blit(text3, text3.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50)))

    def draw(self) -> None:
        self.screen.fill((0, 0, 0))
        self.draw_hud()
        self.draw_grid()
        self.draw_food()
        self.draw_snake()

        if self.game_over:
            self.draw_game_over_overlay()

    def run(self) -> None:
        running = True

        while running:
            running = self.handle_events()
            self.update_game()
            self.draw()

            pygame.display.flip()

            if self.game_over:
                self.clock.tick(20)
            else:
                self.clock.tick(self.speed)

        pygame.quit()


def run_snake_game() -> None:
    game = SnakeGame()
    game.run()