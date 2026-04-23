import datetime
import math
from pathlib import Path

import pygame


class MickeyClockApp:
    def __init__(self):
        pygame.init()
        self.width = 980
        self.height = 680
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Practice 09 - Mickey's Clock")

        self.clock = pygame.time.Clock()
        self.center_x = self.width // 2
        self.center_y = self.height // 2 + 120

        image_path = Path(__file__).resolve().parent / "images" / "mickey_hand.png"
        self.hand_image = pygame.transform.smoothscale(
            pygame.image.load(str(image_path)).convert_alpha(),
            (90, 90),
        )

        self.title_font = pygame.font.SysFont("verdana", 38, bold=True)
        self.time_font = pygame.font.SysFont("consolas", 72, bold=True)
        self.small_font = pygame.font.SysFont("arial", 24, bold=True)

        self.last_second = -1
        self.minute_angle = 0.0
        self.second_angle = 0.0
        self.time_text = "00:00"

    def update_time(self):
        now = datetime.datetime.now()
        if now.second != self.last_second:
            self.last_second = now.second
            minute = now.minute
            second = now.second

            # 360/60 = 6 degrees per step
            self.minute_angle = minute * 6 + second * 0.1
            self.second_angle = second * 6
            self.time_text = f"{minute:02d}:{second:02d}"

    def draw_hand(self, pivot_pos, angle):
        rotated_hand = pygame.transform.rotate(self.hand_image, -angle)
        hand_rect = rotated_hand.get_rect(center=pivot_pos)
        self.screen.blit(rotated_hand, hand_rect)

    def draw_gradient_background(self):
        top_color = (12, 24, 62)
        bottom_color = (38, 74, 134)

        for y in range(self.height):
            blend = y / self.height
            red = int(top_color[0] * (1 - blend) + bottom_color[0] * blend)
            green = int(top_color[1] * (1 - blend) + bottom_color[1] * blend)
            blue = int(top_color[2] * (1 - blend) + bottom_color[2] * blend)
            pygame.draw.line(self.screen, (red, green, blue), (0, y), (self.width, y))

    def draw_digital_panel(self):
        panel_rect = pygame.Rect(self.center_x - 180, 60, 360, 130)
        pygame.draw.rect(self.screen, (15, 22, 45), panel_rect, border_radius=18)
        pygame.draw.rect(
            self.screen, (245, 203, 66), panel_rect, width=4, border_radius=18
        )

        title = self.title_font.render("MICKEY CLOCK", True, (255, 235, 145))
        title_rect = title.get_rect(center=(self.center_x, 38))
        self.screen.blit(title, title_rect)

        time_surface = self.time_font.render(self.time_text, True, (131, 255, 192))
        time_rect = time_surface.get_rect(center=panel_rect.center)
        self.screen.blit(time_surface, time_rect)

    def draw_small_dial(self, dial_center, label, color):
        cx, cy = dial_center
        pygame.draw.circle(self.screen, (15, 24, 48), (cx, cy), 84)
        pygame.draw.circle(self.screen, color, (cx, cy), 84, 4)
        pygame.draw.circle(self.screen, (229, 233, 244), (cx, cy), 70)
        pygame.draw.circle(self.screen, (45, 57, 87), (cx, cy), 8)

        # Draw marks around dial
        for index in range(60):
            angle = math.radians(index * 6 - 90)
            outer_x = cx + int(math.cos(angle) * 66)
            outer_y = cy + int(math.sin(angle) * 66)
            mark_size = 10 if index % 5 == 0 else 5
            inner_x = cx + int(math.cos(angle) * (66 - mark_size))
            inner_y = cy + int(math.sin(angle) * (66 - mark_size))
            mark_color = (45, 50, 70) if index % 5 == 0 else (95, 102, 130)
            pygame.draw.line(
                self.screen, mark_color, (inner_x, inner_y), (outer_x, outer_y), 2
            )

        label_surface = self.small_font.render(label, True, color)
        label_rect = label_surface.get_rect(center=(cx, cy + 118))
        self.screen.blit(label_surface, label_rect)

    def draw_mickey_body(self):
        body_color = (26, 26, 32)
        face_color = (250, 240, 212)

        # Head
        pygame.draw.circle(
            self.screen, body_color, (self.center_x, self.center_y - 30), 95
        )
        pygame.draw.circle(
            self.screen, body_color, (self.center_x - 86, self.center_y - 126), 52
        )
        pygame.draw.circle(
            self.screen, body_color, (self.center_x + 86, self.center_y - 126), 52
        )
        pygame.draw.circle(
            self.screen, face_color, (self.center_x, self.center_y - 16), 72
        )

        note = self.small_font.render(
            "Right = Minutes   Left = Seconds", True, (240, 240, 240)
        )
        note_rect = note.get_rect(center=(self.center_x, self.height - 28))
        self.screen.blit(note, note_rect)

    def draw_scene(self):
        self.draw_gradient_background()
        self.draw_digital_panel()
        self.draw_mickey_body()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.update_time()
            self.draw_scene()

            right_pivot = (self.center_x + 195, self.center_y + 25)
            left_pivot = (self.center_x - 195, self.center_y + 25)

            self.draw_small_dial(left_pivot, "LEFT HAND = SECONDS", (155, 204, 255))
            self.draw_small_dial(right_pivot, "RIGHT HAND = MINUTES", (255, 212, 123))

            self.draw_hand(right_pivot, self.minute_angle)
            self.draw_hand(left_pivot, self.second_angle)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


def run_clock_app():
    app = MickeyClockApp()
    app.run()
