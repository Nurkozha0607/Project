import pygame
import time
import random

# Инициализация
pygame.init()

# Цвета
COLOR_BG = (20, 25, 30)       # Глубокий темно-синий для фона
COLOR_SNAKE = (46, 204, 113)   # Яркий зеленый
COLOR_SNAKE_SHADE = (39, 174, 96) # Темно-зеленый для объема
COLOR_FOOD = (231, 76, 60)     # Красное яблоко
COLOR_TEXT = (236, 240, 241)   # Белый для текста
COLOR_LEVEL = (241, 196, 15)   # Золотой для уровня

# Размеры экрана
WIDTH = 600
HEIGHT = 400
dis = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Snake Pro - Pure Code Edition')

clock = pygame.time.Clock()
snake_block = 20
initial_speed = 7

font_style = pygame.font.SysFont("Verdana", 25)
score_font = pygame.font.SysFont("Verdana", 20)

def display_stats(score, level):
    # Рисуем красивую панель счета
    pygame.draw.rect(dis, (44, 62, 80), [0, 0, WIDTH, 40])
    pygame.draw.line(dis, COLOR_LEVEL, (0, 40), (WIDTH, 40), 2)
    
    val_score = score_font.render(f"SCORE: {score}", True, COLOR_TEXT)
    val_level = score_font.render(f"LEVEL: {level}", True, COLOR_LEVEL)
    dis.blit(val_score, [20, 10])
    dis.blit(val_level, [WIDTH - 120, 10])

def draw_snake(snake_list):
    for i, x in enumerate(snake_list):
        # Рисуем основное тело
        pygame.draw.rect(dis, COLOR_SNAKE, [x[0], x[1], snake_block, snake_block])
        # Добавляем внутреннюю рамку для эффекта "звеньев"
        pygame.draw.rect(dis, COLOR_SNAKE_SHADE, [x[0], x[1], snake_block, snake_block], 1)
        
        # Если это голова (последний элемент списка), рисуем "глаза"
        if i == len(snake_list) - 1:
            pygame.draw.rect(dis, COLOR_BG, [x[0] + 4, x[1] + 4, 4, 4])
            pygame.draw.rect(dis, COLOR_BG, [x[0] + 12, x[1] + 4, 4, 4])

def draw_background():
    dis.fill(COLOR_BG)
    # Рисуем тонкую сетку для красоты
    for x in range(0, WIDTH, snake_block):
        pygame.draw.line(dis, (30, 35, 40), (x, 40), (x, HEIGHT))
    for y in range(40, HEIGHT, snake_block):
        pygame.draw.line(dis, (30, 35, 40), (0, y), (WIDTH, y))

def gameLoop():
    game_over = False
    game_close = False

    x1 = WIDTH / 2
    y1 = HEIGHT / 2
    x1_change = 0
    y1_change = 0

    snake_List = []
    Length_of_snake = 1

    # Еда
    foodx = round(random.randrange(0, WIDTH - snake_block) / 20.0) * 20.0
    foody = round(random.randrange(40, HEIGHT - snake_block) / 20.0) * 20.0

    score = 0
    level = 1
    current_speed = initial_speed

    while not game_over:

        while game_close == True:
            dis.fill(COLOR_BG)
            msg = font_style.render("GAME OVER", True, COLOR_FOOD)
            sub_msg = score_font.render("C - Restart | Q - Quit", True, COLOR_TEXT)
            dis.blit(msg, [WIDTH / 2 - 80, HEIGHT / 2 - 40])
            dis.blit(sub_msg, [WIDTH / 2 - 95, HEIGHT / 2 + 10])
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        game_over = True
                        game_close = False
                    if event.key == pygame.K_c:
                        gameLoop()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and x1_change == 0:
                    x1_change = -snake_block
                    y1_change = 0
                elif event.key == pygame.K_RIGHT and x1_change == 0:
                    x1_change = snake_block
                    y1_change = 0
                elif event.key == pygame.K_UP and y1_change == 0:
                    y1_change = -snake_block
                    x1_change = 0
                elif event.key == pygame.K_DOWN and y1_change == 0:
                    y1_change = snake_block
                    x1_change = 0

        # Границы (учитываем панель сверху в 40 пикселей)
        if x1 >= WIDTH or x1 < 0 or y1 >= HEIGHT or y1 < 40:
            game_close = True
        
        x1 += x1_change
        y1 += y1_change
        
        draw_background()
        
        # Рисуем еду как круг (более красиво, чем квадрат)
        pygame.draw.circle(dis, COLOR_FOOD, (int(foodx + 10), int(foody + 10)), 8)
        
        snake_Head = [x1, y1]
        snake_List.append(snake_Head)
        
        if len(snake_List) > Length_of_snake:
            del snake_List[0]

        for x in snake_List[:-1]:
            if x == snake_Head:
                game_close = True

        draw_snake(snake_List)
        display_stats(score, level)

        pygame.display.update()

        if x1 == foodx and y1 == foody:
            while True:
                foodx = round(random.randrange(0, WIDTH - snake_block) / 20.0) * 20.0
                foody = round(random.randrange(40, HEIGHT - snake_block) / 20.0) * 20.0
                if [foodx, foody] not in snake_List:
                    break
            Length_of_snake += 1
            score += 1
            if score % 3 == 0:
                level += 1
                current_speed += 2

        clock.tick(current_speed)

    pygame.quit()
    quit()

gameLoop()