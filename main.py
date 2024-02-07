import pygame
import os
import sqlite3
import random
from pygame import mixer

pygame.init()

WIDTH = 750
HEIGHT = 750
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))  # width, height
pygame.display.set_caption("Space Invaders")

# ---------- load images ---------
# NPC
RED_SPACE_SHIP = pygame.image.load(os.path.join("assests", "pixel_ship_red_small.png"))
GREEN_SPACE_SHIP = pygame.image.load(os.path.join("assests", "pixel_ship_green_small.png"))
BLUE_SPACE_SHIP = pygame.image.load(os.path.join("assests", "pixel_ship_blue_small.png"))

# player ship
YELLOW_SPACE_SHIP = pygame.image.load(os.path.join("assests", "pixel_ship_yellow.png"))

# lasers
RED_LASER = pygame.image.load(os.path.join("assests", "pixel_laser_red.png"))
GREEN_LASER = pygame.image.load(os.path.join("assests", "pixel_laser_green.png"))
BLUE_LASER = pygame.image.load(os.path.join("assests", "pixel_laser_blue.png"))
YELLOW_LASER = pygame.image.load(os.path.join("assests", "pixel_laser_yellow.png"))

# background
BG = pygame.transform.scale(pygame.image.load(os.path.join("assests", "background-black.png")), (WIDTH, HEIGHT))


# Initialize database
connection = sqlite3.connect('scores.db')
cursor = connection.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS high_scores (score INTEGER)')
connection.commit()
connection.close()


class Laser:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def move(self, velocity):
        self.y += velocity

    def off_screen(self, height):
        return not (self.y <= height and self.y >= 0)

    def collision(self, obj):
        return collide(self, obj)


class Ship:
    COOLDOWN = 30

    def __init__(self, x, y, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.ship_img = None
        self.laser_img = None
        self.lasers = []
        self.cool_down_counter = 0

    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

    def move_lasers(self, velocity, obj):
        self.cooldown()
        for laser in self.lasers:
            laser.move(velocity)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(obj):
                obj.health -= 10
                self.lasers.remove(laser)

    def cooldown(self):
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()


class Player(Ship):
    def __init__(self, x, y, health=100):
        super().__init__(x, y, health)
        self.ship_img = YELLOW_SPACE_SHIP
        self.laser_img = YELLOW_LASER
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health
        self.score = 0  # initialize the score

    def move_lasers(self, velocity, objects):
        self.cooldown()
        for laser in self.lasers:
            laser.move(velocity)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                for obj in objects:
                    if laser.collision(obj):
                        objects.remove(obj)
                        if laser in self.lasers:
                            self.lasers.remove(laser)
                            self.score += 10  # Increment score when player shoots an enemy

    def display_score(self, window):  # define display score method
        main_font = pygame.font.SysFont("freesansbold.ttf", 40)
        score_label = main_font.render(f"Score: {self.score}", 1, (255, 255, 255))
        window.blit(score_label, (10, 40))

        highest_score = get_highest_score()
        highest_score_label = main_font.render(f"Highest Score: {highest_score}", 1, (255, 255, 255))
        window.blit(highest_score_label, (10, 10))

    def draw(self, window):
        super().draw(window)
        self.healthbar(window)
        self.display_score(window)  # call display score method

    def healthbar(self, window):
        pygame.draw.rect(window, (255, 0, 0),
                         (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width(), 10))
        pygame.draw.rect(window, (0, 255, 0), (self.x, self.y + self.ship_img.get_height() + 10,
                                               self.ship_img.get_width() * (
                                                       1 - ((self.max_health - self.health) / self.max_health)), 10))


class Enemy(Ship):
    COLOR_MAP = {
        "red": (RED_SPACE_SHIP, RED_LASER),
        "green": (GREEN_SPACE_SHIP, GREEN_LASER),
        "blue": (BLUE_SPACE_SHIP, BLUE_LASER)
    }

    def __init__(self, x, y, color, health=100):
        super().__init__(x, y, health)
        self.ship_img, self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)

    def move(self, velocity):
        self.y += velocity

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x - 15, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1


def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) is not None


def get_highest_score():
    connection = sqlite3.connect('scores.db')
    cursor = connection.cursor()
    cursor.execute('SELECT MAX(score) FROM high_scores')
    highest_score = cursor.fetchone()[0]
    connection.close()
    return highest_score if highest_score else 0


def update_highest_score(score):
    connection = sqlite3.connect('scores.db')
    cursor = connection.cursor()
    cursor.execute('INSERT INTO high_scores (score) VALUES (?)', (score,))
    connection.commit()
    connection.close()


def main():
    run = True
    FPS = 60
    level = 0
    lives = 5
    player_velocity = 8
    main_font = pygame.font.SysFont("freesansbold.ttf", 40)
    lost_font = pygame.font.SysFont("freesansbold.ttf", 40)

    enemies = []
    wave_length = 5
    enemy_velocity = 1
    laser_velocity = 8

    lost = False
    lost_count = 0

    player = Player(300, 630)

    clock = pygame.time.Clock()

    def redraw_window():
        WINDOW.blit(BG, (0, 0))

        # draw text
        lives_label = main_font.render(f"Lives: {lives}", 1, (255, 255, 255))
        level_label = main_font.render(f"Level: {level}", 1, (255, 255, 255))

        WINDOW.blit(lives_label, (WIDTH - lives_label.get_width() - 10, 10))
        WINDOW.blit(level_label, (WIDTH - level_label.get_width() - 10, 700))

        for enemy in enemies:
            enemy.draw(WINDOW)

        player.draw(WINDOW)

        if lost:
            lost_label = lost_font.render("You Lost!!", 1, (255, 255, 255))
            WINDOW.blit(lost_label, (WIDTH / 2 - lost_label.get_width() / 2, 350))

        pygame.display.update()

    while run:
        clock.tick(FPS)
        redraw_window()

        if lives <= 0 or player.health <= 0:
            lost = True
            lost_count += 1
            if lost_count == 1:  # Only update highest score once when lost
                highest_score = get_highest_score()
                if player.score > highest_score:
                    update_highest_score(player.score)

        if lost:
            if lost_count > FPS * 3:
                run = False
            else:
                continue

        if len(enemies) == 0:
            level += 1
            wave_length += 5
            for _ in range(wave_length):
                enemy = Enemy(random.randrange(50, WIDTH - 100), random.randrange(-1500, -100),
                              random.choice(["red", "blue", "green"]))
                enemies.append(enemy)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player.x - player_velocity > 0:  # left-arrow-key
            player.x -= player_velocity
        if keys[pygame.K_RIGHT] and player.x + player_velocity + player.get_width() < WIDTH:  # right-arrow-key
            player.x += player_velocity
        if keys[pygame.K_UP] and player.y - player_velocity > 0:  # up-arrow-key
            player.y -= player_velocity
        if keys[pygame.K_DOWN] and player.y + player_velocity + player.get_height() + 10 < HEIGHT:  # down-arrow-key
            player.y += player_velocity
        if keys[pygame.K_SPACE]:
            player.shoot()

        for enemy in enemies[:]:
            enemy.move(enemy_velocity)
            enemy.move_lasers(laser_velocity, player)

            if random.randrange(0, 2 * 60) == 1:
                enemy.shoot()
            if collide(enemy, player):
                player.health -= 10
                enemies.remove(enemy)
            elif enemy.y + enemy.get_height() > HEIGHT:
                lives -= 1
                enemies.remove(enemy)

        player.move_lasers(-laser_velocity, enemies)


def main_menu():
    title_font = pygame.font.SysFont("freesansbold.ttf", 40)
    run = True
    while run:
        WINDOW.blit(BG, (0, 0))
        title_label = title_font.render("Press the mouse to begin...", 1, (255, 255, 255))
        WINDOW.blit(title_label, (WIDTH / 2 - title_label.get_width() / 2, 350))

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                highest_score = get_highest_score()
                print(f'Highest Score: {highest_score}')  # Display highest score in console
                main()

    pygame.quit()


main_menu()
