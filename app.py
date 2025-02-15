import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join
pygame.init()

pygame.display.set_caption("Platformer")

WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5

window = pygame.display.set_mode((WIDTH, HEIGHT))

#bg music
pygame.mixer.music.load(join("assets", "sound", "bg.mp3"))
pygame.mixer.music.set_volume(0.2)  # Set volume to 20%
pygame.mixer.music.play(-1)
# Load game over sound
game_over_sound = pygame.mixer.Sound(join("assets", "sound", "gameover.mp3"))
# load next level sound
next_level_sound = pygame.mixer.Sound(join("assets", "sound", "nextlevel.mp3"))
#collect fruit sound
collect_fruit_sound = pygame.mixer.Sound(join("assets", "sound", "collect.mp3"))
# Load hit sound
hit_sound = pygame.mixer.Sound(join("assets", "sound", "hit.mp3"))
# Load jump sound
jump_sound = pygame.mixer.Sound(join("assets", "sound", "jump.mp3"))

def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "MaskDude", 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.death_timer = 0
        self.dying = False
        self.continuous_hit = False
        self.score = 0  # Add score tracking
        self.max_health = 100
        self.health = self.max_health
        self.damage_cooldown = 0
        self.invincible = False

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        jump_sound.play() 
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        if not self.hit:
            self.hit = True
            self.dying = True
            self.hit_count = 0
            self.death_timer = 0
            self.continuous_hit = True

    def reset_hit(self):
        self.dying = False
        self.death_timer = 0
        self.continuous_hit = False

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.continuous_hit:
            self.death_timer += 1/fps
        
        if self.hit:
            self.hit_count += 1
            if self.hit_count > fps * 2:
                self.hit = False
                self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

        if self.invincible:
            self.damage_cooldown -= 1
            if self.damage_cooldown <= 0:
                self.invincible = False

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))

    def take_damage(self, amount):
        if not self.invincible:
            self.health -= amount
            self.invincible = True
            self.damage_cooldown = 60  # 1 second at 60 FPS


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


class Fruit(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height, fruit_name="Apple"):
        super().__init__(x, y, width, height, "fruit")
        self.fruit_name = fruit_name
        self.sprites = load_sprite_sheets("Items", "Fruits", width, height)
        self.image = self.sprites[fruit_name][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.collected = False

    def loop(self):
        if not self.collected:
            sprites = self.sprites[self.fruit_name]
        else:
            sprites = self.sprites["Collected"]
            if self.animation_count // self.ANIMATION_DELAY >= len(sprites):
                return True  # Animation complete, remove fruit
                
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1
        self.mask = pygame.mask.from_surface(self.image)
        return False

    def collect(self):
        if not self.collected:
            self.collected = True
            self.animation_count = 0


class Spikes(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "spikes")
        self.spikes = load_sprite_sheets("Traps", "Spikes", width, height)
        self.image = self.spikes["idle"][0]  # Spikes use idle animation
        self.mask = pygame.mask.from_surface(self.image)


class SpikeHead(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "spikehead")
        self.spikehead = load_sprite_sheets("Traps", "Spike Head", width, height)
        self.image = self.spikehead["Blink"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "Blink"

    def loop(self):
        sprites = self.spikehead[self.animation_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1
        self.mask = pygame.mask.from_surface(self.image)


class Arrow(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "arrow")
        self.arrow = load_sprite_sheets("Traps", "Arrow", width, height)
        self.image = self.arrow["Idle"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "Idle"

    def loop(self):
        sprites = self.arrow[self.animation_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1
        self.mask = pygame.mask.from_surface(self.image)


class Fan(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fan")
        self.fan = load_sprite_sheets("Traps", "Fan", width, height)
        self.image = self.fan["On"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "On"

    def loop(self):
        sprites = self.fan[self.animation_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1
        self.mask = pygame.mask.from_surface(self.image)


class Saw(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "saw")
        self.saw = load_sprite_sheets("Traps", "Saw", width, height)
        self.image = self.saw["on"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "on"

    def loop(self):
        sprites = self.saw[self.animation_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1
        self.mask = pygame.mask.from_surface(self.image)


def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image


def draw(window, background, bg_image, player, objects, offset_x):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)

    # Draw score and health
    font = pygame.font.SysFont('comicsans', 30)
    score_text = font.render(f"Score: {player.score}", True, (255, 255, 255))
    window.blit(score_text, (10, 10))
    
    draw_health_bar(window, player)

    pygame.display.update()


def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)

    return collided_objects


def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break

    player.move(-dx, 0)
    player.update()
    return collided_object


def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    # Filter out fruits from collision objects
    non_fruit_objects = [obj for obj in objects if not isinstance(obj, Fruit)]

    if keys[pygame.K_LEFT] and not collide(player, non_fruit_objects, -PLAYER_VEL * 2):
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not collide(player, non_fruit_objects, PLAYER_VEL * 2):
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, non_fruit_objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]

    # Check for hazard collisions
    touching_hazard = False
    for obj in to_check:
        if obj and obj.name in ["fire", "saw", "spikes", "spikehead", "arrow", "fan"]:
            touching_hazard = True
            damage = {
                "fire": 20,
                "saw": 30,
                "spikes": 25,
                "spikehead": 35,
                "arrow": 15,
                "fan": 10
            }.get(obj.name, 20)
            player.take_damage(damage)
            hit_sound.play()
            break
    
    if not touching_hazard:
        player.reset_hit()
    
    # Check collisions with fruits separately
    fruits_to_remove = []
    player_rect = player.rect.inflate(-10, -10)  # Slightly smaller collision box for fruits
    for obj in objects:
        if isinstance(obj, Fruit) and not obj.collected:
            if player_rect.colliderect(obj.rect):
                obj.collect()
                player.score += 10
                collect_fruit_sound.play()

    # Remove completed fruit animations
    for obj in objects:
        if isinstance(obj, Fruit) and obj.collected:
            if obj.loop():
                fruits_to_remove.append(obj)
    
    for fruit in fruits_to_remove:
        objects.remove(fruit)
    
    return touching_hazard


class Button:
    def __init__(self, x, y, width, height, text, color=(73, 73, 73), hover_color=(189, 189, 189)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.current_color = color
        self.font = pygame.font.SysFont('comicsans', 30)
        
    def draw(self, win):
        pygame.draw.rect(win, self.current_color, self.rect)
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        win.blit(text_surface, (self.rect.x + (self.rect.width - text_surface.get_width()) // 2,
                               self.rect.y + (self.rect.height - text_surface.get_height()) // 2))
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                self.current_color = self.hover_color
            else:
                self.current_color = self.color
                
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False


def draw_menu_screen(window):
    background, bg_image = get_background("Blue.png")
    for tile in background:
        window.blit(bg_image, tile)
    font = pygame.font.Font(None, 74)
    title = font.render("Platformer Game", True, (255, 255, 255))
    title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 4))
    window.blit(title, title_rect)


def main(window):
    clock = pygame.time.Clock()
    
    # Create menu buttons
    play_button = Button(WIDTH//2 - 100, HEIGHT//2 - 60, 200, 50, "Play Game")
    level1_button = Button(WIDTH//2 - 100, HEIGHT//2, 200, 50, "Level 1")
    level2_button = Button(WIDTH//2 - 100, HEIGHT//2 + 60, 200, 50, "Level 2")
    level3_button = Button(WIDTH//2 - 100, HEIGHT//2 + 120, 200, 50, "Level 3")
    quit_button = Button(WIDTH//2 - 100, HEIGHT//2 + 180, 200, 50, "Quit")
    
    # Menu loop
    menu_screen = True
    current_level = 1
    
    while menu_screen:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
                
            if play_button.handle_event(event):
                menu_screen = False
            if level1_button.handle_event(event):
                current_level = 1
                menu_screen = False
            if level2_button.handle_event(event):
                current_level = 2
                menu_screen = False
            if level3_button.handle_event(event):
                current_level = 3
                menu_screen = False
            if quit_button.handle_event(event):
                pygame.quit()
        
        # Draw menu
        draw_menu_screen(window)
        play_button.draw(window)
        level1_button.draw(window)
        level2_button.draw(window)
        level3_button.draw(window)
        quit_button.draw(window)
        
        # Show selected level
        font = pygame.font.Font(None, 36)
        selected_text = font.render(f"Selected Level: {current_level}", True, (255, 255, 0))
        window.blit(selected_text, (WIDTH//2 - 100, HEIGHT//2 - 100))
        
        pygame.display.update()

    # Main game loop with level progression
    while current_level <= 3:
        background, bg_image = get_background(f"Blue.png")  # You can use different backgrounds per level
        block_size = 96
        player = Player(100, 100, 50, 50)
        
        # Create level-specific objects
        objects = create_level(current_level, block_size)
        
        offset_x = 0
        scroll_area_width = 200
        
        # Show level transition screen
        show_level_screen(window, current_level)
        
        # Level loop
        run = True
        while run:
            clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and player.jump_count < 2:
                        player.jump()

            player.loop(FPS)
            for obj in objects:
                if hasattr(obj, 'loop'):
                    obj.loop()
                    
            # Check for collision
            result = handle_move(player, objects)
            if player.rect.colliderect(objects[-1].rect):  # Check if player reaches the end flag
                result = "level_complete"
            if result == "level_complete":
                show_level_complete(window)
                current_level += 1
                if current_level <= 3:
                    show_level_screen(window, current_level)
                run = False
                break
                
            # Check for death (health or fire contact)
            if player.health <= 0 or (player.continuous_hit and player.death_timer >= 2) or player.rect.top > HEIGHT:
                if player.rect.top > HEIGHT and player.rect.right >= objects[-1].rect.left:
                    show_game_complete(window)
                else:
                    game_over_sound.play()  
                    show_death_screen(window)
                    
                run = False
                break

            # Update offset_x to move the screen with the player
            if player.rect.right - offset_x > WIDTH - scroll_area_width:
                offset_x += player.rect.right - offset_x - (WIDTH - scroll_area_width)
            elif player.rect.left - offset_x < scroll_area_width:
                offset_x -= scroll_area_width - (player.rect.left - offset_x)
            
            draw(window, background, bg_image, player, objects, offset_x)

    # Show game complete screen
    if current_level > 3:
        show_game_complete(window)

    pygame.quit()
    quit()

def create_level(level_num, block_size):
    objects = []
    platforms = []
    used_positions = set()
    
    # Create varied terrain
    prev_height = HEIGHT - block_size
    for i in range(-WIDTH // block_size, (WIDTH * (2 + level_num)) // block_size):
        # Random height variations
        if random.random() < 0.2:
            height_change = random.choice([-1, 1]) * block_size
            prev_height = max(min(prev_height + height_change, HEIGHT - block_size), HEIGHT - block_size * 4)
        
        # Create gaps based on level
        if level_num > 1 and random.random() < 0.1 * level_num:
            continue
            
        block = Block(i * block_size, prev_height, block_size)
        objects.append(block)
        platforms.append(block)
    
    # Add elevated platforms
    for i in range(-WIDTH // block_size, (WIDTH * (2 + level_num)) // block_size):
        if random.random() < 0.1:
            height = random.randint(2, 4)
            platform = Block(i * block_size, HEIGHT - block_size * height, block_size)
            objects.append(platform)
            platforms.append(platform)
    
    # Add hazards on platforms with spacing
    num_hazards = level_num * 3 + level_num  # Increase hazards with level
    for _ in range(num_hazards):
        attempts = 0
        while attempts < 10:  # Limit attempts to prevent infinite loop
            platform = random.choice(platforms)
            x = platform.rect.x
            y = platform.rect.y - 64  # Place on top of platform
            
            # Check if position is already used
            pos_key = (x // block_size, y // block_size)
            if pos_key not in used_positions:
                hazard_type = random.random()
                if hazard_type < 0.2:
                    fire = Fire(x, y, 16, 32)
                    fire.on()
                    objects.append(fire)
                elif hazard_type < 0.4:
                    objects.append(Saw(x, y, 38, 38))
                elif hazard_type < 0.6:
                    objects.append(SpikeHead(x, y, 54, 52))
                elif hazard_type < 0.8:
                    objects.append(Arrow(x, y, 32, 32))
                else:
                    objects.append(Fan(x, y, 24, 48))
                
                used_positions.add(pos_key)
                break
            attempts += 1
    
    # Add floating fruits with spacing and proper placement
    fruit_types = ["Apple", "Bananas", "Orange", "Cherries", "Kiwi", "Melon", "Strawberry", "Pineapple"]
    num_fruits = 5 + level_num * 2
    for _ in range(num_fruits):
        attempts = 0
        while attempts < 10:
            placement_type = random.random()
            
            if placement_type < 0.5:  # Place on platform
                platform = random.choice(platforms)
                x = platform.rect.x + block_size // 4
                y = platform.rect.y - 48  # Float slightly above platform
            else:  # Float in mid-air
                x = random.randint(block_size * 2, WIDTH * (2 + level_num) - block_size * 2)
                y = random.randint(HEIGHT - block_size * 6, HEIGHT - block_size * 3)
            
            # Check if position is already used or inside terrain
            pos_key = (x // block_size, y // block_size)
            collision = False
            
            # Check for collision with platforms
            fruit_rect = pygame.Rect(x, y, 32, 32)
            for platform in platforms:
                if fruit_rect.colliderect(platform.rect):
                    collision = True
                    break
            
            if pos_key not in used_positions and not collision:
                fruit_type = random.choice(fruit_types)
                objects.append(Fruit(x, y, 32, 32, fruit_type))
                used_positions.add(pos_key)
                break
            
            attempts += 1
    
    # Add end flag to complete the level
    end_flag = Block((WIDTH * (2 + level_num)) - block_size * 2, prev_height, block_size)
    end_flag.name = "end_flag"  # Add a name to the end flag for identification
    objects.append(end_flag)
    platforms.append(end_flag)
    
    return objects

def show_level_screen(window, level):
    background, bg_image = get_background("Blue.png")
    for tile in background:
        window.blit(bg_image, tile)
    font = pygame.font.Font(None, 74)
    text = font.render(f"Level {level}", True, (255, 255, 255))
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    window.blit(text, text_rect)
    pygame.display.update()
    pygame.time.delay(2000)

def show_level_complete(window):
    background, bg_image = get_background("Blue.png")
    for tile in background:
        window.blit(bg_image, tile)
    font = pygame.font.Font(None, 74)
    text = font.render("Level Complete!", True, (255, 255, 255))
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    window.blit(text, text_rect)
    pygame.display.update()
    next_level_sound.play()
    pygame.time.delay(2000)

def show_death_screen(window):
    background, bg_image = get_background("Blue.png")
    for tile in background:
        window.blit(bg_image, tile)
    font = pygame.font.Font(None, 74)
    text = font.render("You Died!", True, (255, 0, 0))
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    window.blit(text, text_rect)
    pygame.display.update()
    pygame.time.delay(2000)

def show_game_complete(window):
    background, bg_image = get_background("Blue.png")
    for tile in background:
        window.blit(bg_image, tile)
    font = pygame.font.Font(None, 74)
    text = font.render("Congratulations! Game Complete!", True, (255, 255, 0))
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    window.blit(text, text_rect)
    pygame.display.update()
    pygame.time.delay(3000)

def draw_health_bar(window, player):
    health_bar_width = 200
    health_bar_height = 20
    x = 10
    y = 60  # Increase gap between score and health bar
    
    # Draw background
    pygame.draw.rect(window, (255, 0, 0), (x, y, health_bar_width, health_bar_height))
    # Draw health
    current_health_width = (player.health / player.max_health) * health_bar_width
    pygame.draw.rect(window, (0, 255, 0), (x, y, current_health_width, health_bar_height))
    # Draw border
    pygame.draw.rect(window, (255, 255, 255), (x, y, health_bar_width, health_bar_height), 2)


if __name__ == "__main__":
    main(window)