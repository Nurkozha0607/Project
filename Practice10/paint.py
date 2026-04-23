import pygame

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Paint with UI")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (220, 220, 220)
# Список цветов для палитры
COLORS = [BLACK, (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 165, 0)]

active_color = BLACK
active_tool = 'brush'
drawing = False
start_pos = None

screen.fill(WHITE)

def draw_ui():
    # Рисуем серую панель управления сверху
    pygame.draw.rect(screen, GRAY, (0, 0, WIDTH, 50))
    pygame.draw.line(screen, BLACK, (0, 50), (WIDTH, 50), 2)

    # 1. Отрисовка палитры цветов
    for i, color in enumerate(COLORS):
        rect = pygame.Rect(10 + i * 35, 10, 30, 30)
        pygame.draw.rect(screen, color, rect)
        if active_color == color: # Подсвечиваем выбранный цвет
            pygame.draw.rect(screen, WHITE, rect, 3)

    # 2. Отрисовка кнопок инструментов (текстовые кнопки для простоты)
    font = pygame.font.SysFont("Arial", 14)
    tools = ["Brush", "Eraser", "Rect", "Circle"]
    for i, tool in enumerate(tools):
        rect = pygame.Rect(250 + i * 75, 10, 70, 30)
        # Если инструмент активен, кнопка темнее
        color = (150, 150, 150) if active_tool == tool.lower() else (200, 200, 200)
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, BLACK, rect, 1)
        
        text = font.render(tool, True, BLACK)
        screen.blit(text, (260 + i * 75, 18))

def get_ui_click(pos):
    """Проверяет, куда нажал пользователь в области UI"""
    global active_color, active_tool
    
    # Проверка палитры
    for i, color in enumerate(COLORS):
        rect = pygame.Rect(10 + i * 35, 10, 30, 30)
        if rect.collidepoint(pos):
            active_color = color
            return True

    # Проверка инструментов
    tools = ["brush", "eraser", "rectangle", "circle"]
    for i, tool in enumerate(tools):
        rect = pygame.Rect(250 + i * 75, 10, 70, 30)
        if rect.collidepoint(pos):
            active_tool = tool
            return True
    return False

run = True
while run:
    # Важно: Рисуем UI в каждом кадре, чтобы видеть изменения
    draw_ui()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Если кликнули в зоне меню (выше 50 пикселей)
            if event.pos[1] < 50:
                get_ui_click(event.pos)
            else:
                drawing = True
                start_pos = event.pos
        
        if event.type == pygame.MOUSEBUTTONUP:
            if drawing and start_pos and event.pos[1] > 50:
                if active_tool == 'rectangle':
                    w, h = event.pos[0] - start_pos[0], event.pos[1] - start_pos[1]
                    pygame.draw.rect(screen, active_color, [start_pos[0], start_pos[1], w, h], 2)
                elif active_tool == 'circle':
                    import math
                    r = int(math.hypot(event.pos[0] - start_pos[0], event.pos[1] - start_pos[1]))
                    pygame.draw.circle(screen, active_color, start_pos, r, 2)
            drawing = False
            start_pos = None

        if event.type == pygame.MOUSEMOTION and drawing and event.pos[1] > 50:
            if active_tool == 'brush':
                pygame.draw.circle(screen, active_color, event.pos, 10)
            elif active_tool == 'eraser':
                pygame.draw.circle(screen, WHITE, event.pos, 20)

    pygame.display.flip()

pygame.quit()