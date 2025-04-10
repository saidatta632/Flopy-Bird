import pygame
import random
import os
import json
import sys
import traceback

# Initialize pygame with optimized flags
pygame.init()
pygame.mixer.init()
pygame.display.set_caption("Flappy Bird")

# Performance optimization flags
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION])

# Screen dimensions
WIDTH, HEIGHT = 800, 600
try:
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.HWSURFACE|pygame.DOUBLEBUF)
except pygame.error as e:
    print(f"Could not create display: {e}")
    sys.exit(1)

clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (135, 206, 235)
GOLD = (255, 215, 0)
TRANSPARENT_BLACK = (0, 0, 0, 180)

# Fonts
try:
    title_font = pygame.font.Font(None, 74)  # Larger font for titles
    main_font = pygame.font.SysFont('Arial', 36, bold=True)
    score_font = pygame.font.SysFont('Arial', 48, bold=True)
except:
    print("Font loading failed, using default font")
    title_font = pygame.font.Font(None, 74)
    main_font = pygame.font.Font(None, 36)
    score_font = pygame.font.Font(None, 48)

# Game data management
def load_game_data():
    try:
        with open('game_data.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Default data if file doesn't exist or is invalid
        default_data = {
            "players": [
                {"name": "Player 1", "high_score": 0, "color": [255, 0, 0]},
                {"name": "Player 2", "high_score": 0, "color": [0, 0, 255]}
            ],
            "settings": {
                "difficulty_levels": [
                    {"name": "Very Easy", "jump_power": 7, "pipe_speed": 2, "pipe_gap": 200},
                    {"name": "Easy", "jump_power": 8, "pipe_speed": 3, "pipe_gap": 180},
                    {"name": "Medium", "jump_power": 9, "pipe_speed": 4, "pipe_gap": 160},
                    {"name": "Hard", "jump_power": 10, "pipe_speed": 5, "pipe_gap": 140},
                    {"name": "Extreme", "jump_power": 12, "pipe_speed": 6, "pipe_gap": 120}
                ],
                "last_player": "Player 1",
                "last_difficulty": "Easy",
                "sound_enabled": True,
                "music_enabled": True
            }
        }
        save_game_data(default_data)
        return default_data

def save_game_data(data):
    with open('game_data.json', 'w') as f:
        json.dump(data, f, indent=2)

# Load game data
game_data = load_game_data()
current_player = next((p for p in game_data["players"] if p["name"] == game_data["settings"]["last_player"]), game_data["players"][0])
current_difficulty = game_data["settings"]["last_difficulty"]
difficulty_settings = {d["name"]: d for d in game_data["settings"]["difficulty_levels"]}

# Game constants
GRAVITY = 0.5
PIPE_GAP = difficulty_settings[current_difficulty]["pipe_gap"]

# Load assets from assets folder
try:
    # Create paths to asset files
    assets_dir = os.path.join(os.getcwd(), 'assets')
    bird_path = os.path.join(assets_dir, 'bird.png')
    pipe_path = os.path.join(assets_dir, 'pipe.png')
    bg_path = os.path.join(assets_dir, 'background.png')
    
    # Load images
    bird_img = pygame.image.load(bird_path)
    pipe_img = pygame.image.load(pipe_path)
    bg_img = pygame.image.load(bg_path)
    
    # Resize images if needed
    bird_img = pygame.transform.scale(bird_img, (40, 30))
    bg_img = pygame.transform.scale(bg_img, (WIDTH, HEIGHT))
    
    print("Successfully loaded images from assets folder")
except Exception as e:
    print(f"Error loading images: {e}")
    # Fallback to placeholder images
    def create_bird_image():
        surface = pygame.Surface((40, 30), pygame.SRCALPHA)
        pygame.draw.ellipse(surface, (255, 165, 0), (0, 0, 40, 30))
        pygame.draw.circle(surface, BLACK, (30, 15), 4)
        pygame.draw.ellipse(surface, (255, 140, 0), (5, 10, 15, 10))
        return surface

    def create_pipe_image():
        surface = pygame.Surface((70, HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(surface, GREEN, (0, 0, 70, HEIGHT))
        pygame.draw.rect(surface, (0, 200, 0), (0, 0, 70, HEIGHT), 2)
        pygame.draw.rect(surface, (0, 180, 0), (0, 0, 70, 30))
        return surface

    def create_background():
        surface = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            color = (
                int(135 + (y/HEIGHT) * 20),
                int(206 + (y/HEIGHT) * 20),
                int(235 + (y/HEIGHT) * 20)
            )
            pygame.draw.line(surface, color, (0, y), (WIDTH, y))
        return surface

    bird_img = create_bird_image()
    pipe_img = create_pipe_image()
    bg_img = create_background()
    print("Using placeholder images")

# Bird class
class Bird:
    def __init__(self, player_data=None):
        self.x, self.y = 50, HEIGHT // 2
        self.velocity = 0
        self.rect = pygame.Rect(self.x, self.y, bird_img.get_width(), bird_img.get_height())
        self.rotation = 0
        self.original_image = bird_img.copy()
        
        # Apply player color if provided
        if player_data and "color" in player_data:
            self.apply_color(player_data["color"])
        else:
            self.image = self.original_image
            
    def apply_color(self, color):
        # Create a colored version of the bird
        colored_img = self.original_image.copy()
        color_surface = pygame.Surface(colored_img.get_size(), pygame.SRCALPHA)
        color_surface.fill((color[0], color[1], color[2], 100))  # Semi-transparent color
        colored_img.blit(color_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.original_image = colored_img
        self.image = self.original_image

    def jump(self, power):
        self.velocity = -power
        self.rotation = 30  # Rotate up when jumping

    def update(self):
        self.velocity += GRAVITY
        self.y += self.velocity
        self.rect.y = self.y
        
        # Update rotation based on velocity
        self.rotation = max(-90, min(30, -self.velocity * 2))
        self.image = pygame.transform.rotate(self.original_image, self.rotation)
        self.rect = self.image.get_rect(center=(self.x + bird_img.get_width()//2, self.y + bird_img.get_height()//2))

    def draw(self):
        screen.blit(self.image, self.rect)

# Pipe class
class Pipe:
    def __init__(self, x, speed, gap):
        self.x = x
        self.height = random.randint(150, 400)
        self.gap = gap
        self.speed = speed
        self.width = pipe_img.get_width()
        
        # Create rectangles for collision detection
        self.top_rect = pygame.Rect(self.x, 0, self.width, self.height)
        self.bottom_rect = pygame.Rect(self.x, self.height + self.gap, self.width, HEIGHT)

    def update(self):
        self.x -= self.speed
        self.top_rect.x = self.x
        self.bottom_rect.x = self.x

    def draw(self):
        # Top pipe (upside down)
        top_pipe = pygame.transform.flip(pipe_img, False, True)
        screen.blit(top_pipe, (self.x, self.height - pipe_img.get_height()))
        
        # Bottom pipe
        screen.blit(pipe_img, (self.x, self.height + self.gap))

    def check_collision(self, bird):
        return bird.rect.colliderect(self.top_rect) or bird.rect.colliderect(self.bottom_rect)

# UI Enhancement: Add animation effects
class AnimatedValue:
    def __init__(self, start_value, target_value, speed=0.1):
        self.current = float(start_value)
        self.target = float(target_value)
        self.speed = speed

    def update(self):
        if self.current != self.target:
            diff = self.target - self.current
            self.current += diff * self.speed
        return int(self.current)

# Enhanced Button class with animations
class Button:
    def __init__(self, x, y, width, height, text, color=(100, 100, 100), hover_color=(150, 150, 150), text_color=WHITE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.base_color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.hovered = False
        self.scale = AnimatedValue(1.0, 1.0)
        self.alpha = AnimatedValue(255, 255)
        
    def draw(self, surface, font):
        # Update animations
        scale = self.scale.update()
        alpha = self.alpha.update()
        
        # Calculate scaled rect
        scaled_rect = pygame.Rect(
            self.rect.centerx - (self.rect.width * scale) // 2,
            self.rect.centery - (self.rect.height * scale) // 2,
            self.rect.width * scale,
            self.rect.height * scale
        )
        
        # Draw button with current color and scale
        color = self.hover_color if self.hovered else self.base_color
        pygame.draw.rect(surface, color, scaled_rect, border_radius=15)
        pygame.draw.rect(surface, WHITE, scaled_rect, 3, border_radius=15)
        
        # Draw text
        text_surf = font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=scaled_rect.center)
        surface.blit(text_surf, text_rect)
        
    def is_hovered(self, pos):
        was_hovered = self.hovered
        self.hovered = self.rect.collidepoint(pos)
        if self.hovered != was_hovered:
            self.scale.target = 1.1 if self.hovered else 1.0
        return self.hovered
        
    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False

def create_menu_background():
    # Create a gradient background
    background = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        color = (
            int(135 + (y/HEIGHT) * 20),
            int(206 + (y/HEIGHT) * 20),
            int(235 + (y/HEIGHT) * 20)
        )
        pygame.draw.line(background, color, (0, y), (WIDTH, y))
    return background

# Create a static menu background
menu_background = create_menu_background()

def draw_fancy_text(surface, text, font, color, y_pos, glow=True):
    if glow:
        # Draw glow effect
        glow_surf = font.render(text, True, (*color[:3], 100))
        for offset in range(1, 4, 2):
            surface.blit(glow_surf, (WIDTH//2 - glow_surf.get_width()//2 + offset, y_pos))
            surface.blit(glow_surf, (WIDTH//2 - glow_surf.get_width()//2 - offset, y_pos))
    
    # Draw main text
    text_surf = font.render(text, True, color)
    surface.blit(text_surf, (WIDTH//2 - text_surf.get_width()//2, y_pos))

def draw_player_selection(screen, font):
    screen.blit(menu_background, (0, 0))
    
    # Create semi-transparent overlay
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(overlay, (0, 0, 0, 100), overlay.get_rect())
    screen.blit(overlay, (0, 0))
    
    # Draw fancy title
    draw_fancy_text(screen, "Select Player", title_font, GOLD, 50, True)
    
    buttons = []
    y_pos = 150
    button_width = WIDTH - 200  # Wider buttons
    
    # Create buttons for existing players
    for player in game_data["players"]:
        color = tuple(player["color"])
        hover_color = tuple(min(c+50, 255) for c in color)
        btn = Button(100, y_pos, button_width, 60, 
                    f"{player['name']} (Best: {player['high_score']})",
                    color=color, hover_color=hover_color)
        buttons.append(btn)
        y_pos += 80
    
    # Add New Player button
    new_player_btn = Button(100, HEIGHT-100, button_width, 60, 
                           "➕ Add New Player",
                           color=(0, 150, 0), hover_color=(0, 200, 0))
    buttons.append(new_player_btn)
    
    return buttons

def draw_difficulty_selection(screen, font):
    screen.blit(bg_img, (0, 0))
    
    # Create semi-transparent background
    menu_bg = pygame.Surface((WIDTH-40, HEIGHT-100), pygame.SRCALPHA)
    pygame.draw.rect(menu_bg, (0, 0, 0, 180), (0, 0, WIDTH-40, HEIGHT-100), border_radius=15)
    screen.blit(menu_bg, (20, 50))
    
    title = font.render("Select Difficulty", True, GOLD)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 70))
    
    buttons = []
    y_pos = 150
    
    # Create buttons for difficulty levels
    for diff in game_data["settings"]["difficulty_levels"]:
        color = (0, 150, 0) if diff["name"] == "Very Easy" else \
                (150, 150, 0) if diff["name"] == "Easy" else \
                (150, 100, 0) if diff["name"] == "Medium" else \
                (150, 50, 0) if diff["name"] == "Hard" else \
                (150, 0, 0)
        
        hover_color = tuple(min(c+50, 255) for c in color)
        btn = Button(50, y_pos, WIDTH-100, 50, diff["name"], color=color, hover_color=hover_color)
        buttons.append(btn)
        y_pos += 70
    
    return buttons

def add_new_player(screen, font):
    input_text = ""
    color = [random.randint(50, 200) for _ in range(3)]
    input_active = True
    
    while True:
        screen.blit(bg_img, (0, 0))
        
        # Create semi-transparent background
        menu_bg = pygame.Surface((WIDTH-40, HEIGHT-100), pygame.SRCALPHA)
        pygame.draw.rect(menu_bg, (0, 0, 0, 180), (0, 0, WIDTH-40, HEIGHT-100), border_radius=15)
        screen.blit(menu_bg, (20, 50))
        
        title = font.render("New Player", True, GOLD)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 70))
        
        # Draw input box with active state
        input_box = pygame.Rect(50, 150, WIDTH-100, 50)
        pygame.draw.rect(screen, WHITE, input_box, border_radius=10)
        if input_active:
            pygame.draw.rect(screen, GOLD, input_box, 3, border_radius=10)
        
        # Draw input text
        text_surface = font.render(input_text, True, BLACK)
        screen.blit(text_surface, (input_box.x + 10, input_box.y + 10))
        
        # Draw color preview
        color_box = pygame.Rect(50, 250, WIDTH-100, 50)
        pygame.draw.rect(screen, color, color_box, border_radius=10)
        
        # Draw buttons
        save_btn = Button(50, HEIGHT-180, WIDTH-100, 50, "Save Player", color=(0, 150, 0))
        random_color_btn = Button(50, HEIGHT-120, WIDTH-100, 50, "Random Color")
        cancel_btn = Button(50, HEIGHT-60, WIDTH-100, 50, "Cancel", color=(150, 0, 0))
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Update button hover states
        save_btn.is_hovered(mouse_pos)
        random_color_btn.is_hovered(mouse_pos)
        cancel_btn.is_hovered(mouse_pos)
        
        # Draw all buttons
        save_btn.draw(screen, font)
        random_color_btn.draw(screen, font)
        cancel_btn.draw(screen, font)
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if save_btn.is_clicked(mouse_pos, event) and input_text.strip():
                    new_player = {
                        "name": input_text.strip(),
                        "high_score": 0,
                        "color": color
                    }
                    return new_player
                elif random_color_btn.is_clicked(mouse_pos, event):
                    color = [random.randint(50, 200) for _ in range(3)]
                elif cancel_btn.is_clicked(mouse_pos, event):
                    return None
                
                # Toggle input box active state
                if input_box.collidepoint(mouse_pos):
                    input_active = True
                else:
                    input_active = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and input_text.strip():
                    new_player = {
                        "name": input_text.strip(),
                        "high_score": 0,
                        "color": color
                    }
                    return new_player
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    return None
                else:
                    if len(input_text) < 20:  # Limit name length
                        input_text += event.unicode
        
        clock.tick(60)

def update_main():
    global game_data, current_player, current_difficulty
    
    try:
        font = pygame.font.SysFont('Arial', 36, bold=True)
        running = True
        
        while running:
            try:
                # Player Selection
                buttons = draw_player_selection(screen, font)
                pygame.display.flip()
                
                selecting_player = True
                while selecting_player and running:
                    try:
                        mouse_pos = pygame.mouse.get_pos()
                        
                        # Update button hover states
                        for btn in buttons:
                            btn.is_hovered(mouse_pos)
                        
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()
                            
                            if event.type == pygame.MOUSEBUTTONDOWN:
                                for i, btn in enumerate(buttons):
                                    if btn.is_clicked(mouse_pos, event):
                                        if i == len(buttons) - 1:  # New Player button
                                            new_player = add_new_player(screen, font)
                                            if new_player:
                                                game_data["players"].append(new_player)
                                                save_game_data(game_data)
                                                return True  # Restart the menu to show new player
                                        else:
                                            current_player = game_data["players"][i]
                                            selecting_player = False
                                            
                            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                                running = False
                                break
                        
                        # Redraw buttons
                        screen.blit(menu_background, (0, 0))
                        for btn in buttons:
                            btn.draw(screen, font)
                        pygame.display.flip()
                        clock.tick(60)
                    except Exception as e:
                        print(f"Error in player selection loop: {e}")
                        traceback.print_exc()
                
                if not running:
                    break
                
                # Difficulty Selection
                buttons = draw_difficulty_selection(screen, font)
                pygame.display.flip()
                
                selecting_difficulty = True
                while selecting_difficulty and running:
                    try:
                        mouse_pos = pygame.mouse.get_pos()
                        
                        # Update button hover states
                        for btn in buttons:
                            btn.is_hovered(mouse_pos)
                        
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()
                            
                            if event.type == pygame.MOUSEBUTTONDOWN:
                                for i, btn in enumerate(buttons):
                                    if btn.is_clicked(mouse_pos, event):
                                        current_difficulty = game_data["settings"]["difficulty_levels"][i]["name"]
                                        game_data["settings"]["last_player"] = current_player["name"]
                                        game_data["settings"]["last_difficulty"] = current_difficulty
                                        save_game_data(game_data)
                                        selecting_difficulty = False
                                        
                            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                                selecting_difficulty = False
                                selecting_player = True
                                break
                        
                        # Redraw buttons
                        screen.blit(bg_img, (0, 0))
                        for btn in buttons:
                            btn.draw(screen, font)
                        pygame.display.flip()
                        clock.tick(60)
                    except Exception as e:
                        print(f"Error in difficulty selection loop: {e}")
                        traceback.print_exc()
                
                if selecting_player:
                    continue
                
                # Start the game
                if game(current_difficulty) == False:
                    running = False
            except Exception as e:
                print(f"Error in main game loop: {e}")
                traceback.print_exc()
                pygame.time.wait(1000)  # Wait a second before continuing
        
        return False
    except Exception as e:
        print(f"Critical error in update_main: {e}")
        traceback.print_exc()
        return False

def draw_menu(screen, font):
    screen.blit(bg_img, (0, 0))
    title = font.render("Flappy Bird", True, GOLD)
    start = font.render("Press SPACE to Start", True, WHITE)
    difficulty = font.render("Press 1-3 for Difficulty", True, WHITE)
    
    # Create semi-transparent background for menu text
    menu_bg = pygame.Surface((300, 200), pygame.SRCALPHA)
    pygame.draw.rect(menu_bg, (0, 0, 0, 128), (0, 0, 300, 200), border_radius=10)
    screen.blit(menu_bg, (WIDTH//2 - 150, HEIGHT//3 - 30))
    
    screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//3))
    screen.blit(start, (WIDTH//2 - start.get_width()//2, HEIGHT//2))
    screen.blit(difficulty, (WIDTH//2 - difficulty.get_width()//2, 2*HEIGHT//3))

def game(difficulty):
    global current_player, game_data
    
    try:
        bird = Bird(current_player)
        pipes = [Pipe(WIDTH + i * 200, difficulty_settings[difficulty]["pipe_speed"], 
                     difficulty_settings[difficulty]["pipe_gap"]) for i in range(3)]
        running = True
        score = 0
        high_score = current_player["high_score"]
        animated_score = AnimatedValue(0, 0)
        
        # Get difficulty settings
        diff_settings = difficulty_settings[difficulty]
        jump_power = diff_settings["jump_power"]
        
        # Game state
        game_started = False
        game_over = False
        
        while running:
            try:
                screen.fill(WHITE)
                screen.blit(bg_img, (0, 0))
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            if game_over:
                                return True
                            else:
                                game_started = True
                                bird.jump(jump_power)
                        elif event.key == pygame.K_ESCAPE:
                            return True
                
                if not game_started:
                    draw_fancy_text(screen, "Press SPACE to Start", main_font, WHITE, HEIGHT//2 - 50)
                    draw_fancy_text(screen, f"Difficulty: {difficulty}", main_font, GOLD, HEIGHT//2 + 50)
                    bird.draw()
                    pygame.display.flip()
                    clock.tick(60)
                    continue
                
                # Game logic
                if not game_over:
                    bird.update()
                    
                    if bird.y < 0 or bird.y > HEIGHT:
                        game_over = True
                    
                    for pipe in pipes:
                        pipe.update()
                        if pipe.check_collision(bird):
                            game_over = True
                        elif pipe.x < -pipe.width:
                            pipes.remove(pipe)
                            pipes.append(Pipe(WIDTH, diff_settings["pipe_speed"], diff_settings["pipe_gap"]))
                            score += 1
                            animated_score.target = score
                            if score > high_score:
                                high_score = score
                                current_player["high_score"] = high_score
                                game_data["players"] = [p if p["name"] != current_player["name"] else current_player 
                                                      for p in game_data["players"]]
                                save_game_data(game_data)
                        pipe.draw()
                    
                    bird.draw()
                    
                    # Display score
                    current_score = animated_score.update()
                    score_bg = pygame.Surface((300, 120), pygame.SRCALPHA)
                    pygame.draw.rect(score_bg, (0, 0, 0, 128), (0, 0, 300, 120), border_radius=15)
                    screen.blit(score_bg, (10, 10))
                    draw_fancy_text(screen, f"Score: {current_score}", score_font, WHITE, 20, glow=True)
                    draw_fancy_text(screen, f"Best: {high_score}", main_font, GOLD, 80, glow=True)
                
                else:  # Game Over state
                    for pipe in pipes:
                        pipe.draw()
                    bird.draw()
                    
                    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    pygame.draw.rect(overlay, (0, 0, 0, 150), overlay.get_rect())
                    screen.blit(overlay, (0, 0))
                    
                    y_pos = HEIGHT//2 - 150
                    draw_fancy_text(screen, "Game Over!", title_font, GOLD, y_pos)
                    y_pos += 80
                    draw_fancy_text(screen, f"Score: {score}", score_font, WHITE, y_pos)
                    y_pos += 60
                    draw_fancy_text(screen, f"Best: {high_score}", main_font, WHITE, y_pos)
                    y_pos += 60
                    draw_fancy_text(screen, "Press SPACE to Restart", main_font, WHITE, y_pos)
                    y_pos += 40
                    draw_fancy_text(screen, "Press ESC for Menu", main_font, WHITE, y_pos)
                
                pygame.display.flip()
                clock.tick(60)
            
            except Exception as e:
                print(f"Error in game loop: {e}")
                traceback.print_exc()
                pygame.time.wait(1000)  # Wait a second before continuing
        
        return True
    
    except Exception as e:
        print(f"Critical error in game: {e}")
        traceback.print_exc()
        return True

def main():
    try:
        while True:
            try:
                if not update_main():
                    break
                game_data = load_game_data()
            except Exception as e:
                print(f"Error in main loop: {e}")
                traceback.print_exc()
                pygame.time.wait(1000)  # Wait a second before continuing
    except Exception as e:
        print(f"Critical error: {e}")
        traceback.print_exc()
    finally:
        try:
            pygame.quit()
        except:
            pass
        sys.exit()

if __name__ == "__main__":
    main()
