"""
Tilemap system for retro 2D overworld
Loads 32x32 tile sprites and arranges them in a grid
"""

import pygame
import os
import config

class Tilemap:
    def __init__(self):
        self.tile_size = 32
        
        # Load the full scene image
        scene_path = f'{config.IMAGE_PATH}/Sunnyside_World_ASSET_PACK_V2.1/Sunnyside_World_Assets/Sunnyside_World_ExampleScene.png'
        
        if os.path.exists(scene_path):
            self.map_image = pygame.image.load(scene_path).convert()
            print(f"Loaded map: {scene_path}")
        else:
            # Fallback: create a simple test map
            self.map_image = pygame.Surface((1024, 768))
            self.map_image.fill((0, 200, 0))
            print(f"Map not found at: {scene_path}")
        
        self.map_width = self.map_image.get_width()
        self.map_height = self.map_image.get_height()
        
        # Define interaction zones (x, y, width, height in pixels)
        self.interaction_zones = {
            'barangay_captain': {'x': 300, 'y': 200, 'width': 100, 'height': 100},
            'recipe_game': {'x': 600, 'y': 300, 'width': 100, 'height': 100},
            'synonym_antonym': {'x': 450, 'y': 450, 'width': 100, 'height': 100}
        }
        
        # Building labels
        self.labels = [
            {'text': 'Barangay Captain', 'x': 300, 'y': 180, 'color': config.BLUE},
            {'text': 'Recipe Game', 'x': 600, 'y': 280, 'color': config.RED},
            {'text': 'Word Match', 'x': 450, 'y': 430, 'color': config.PURPLE}
        ]
    
    def draw(self, screen, camera_x, camera_y):
        """Draw the full map image with camera offset"""
        camera_x = int(camera_x)
        camera_y = int(camera_y)
        
        # Draw the full scene
        screen.blit(self.map_image, (-camera_x, -camera_y))
    
    def draw_labels(self, screen, camera_x, camera_y, font):
        """Draw building labels"""
        for label in self.labels:
            x = label['x'] - camera_x
            y = label['y'] - camera_y
            
            text = font.render(label['text'], True, config.WHITE)
            text_shadow = font.render(label['text'], True, config.BLACK)
            
            # Shadow
            screen.blit(text_shadow, (x + 2, y + 2))
            # Text
            screen.blit(text, (x, y))
    
    def is_collision(self, tile_x, tile_y):
        """Check if position has collision - simple boundary check"""
        pixel_x = tile_x * 32
        pixel_y = tile_y * 32
        
        if pixel_x < 0 or pixel_x >= self.map_width - 32:
            return True
        if pixel_y < 0 or pixel_y >= self.map_height - 32:
            return True
        
        return False
    
    def check_interaction(self, tile_x, tile_y):
        """Check if player is in an interaction zone"""
        pixel_x = tile_x * 32
        pixel_y = tile_y * 32
        
        for zone_name, zone in self.interaction_zones.items():
            if (zone['x'] <= pixel_x < zone['x'] + zone['width'] and
                zone['y'] <= pixel_y < zone['y'] + zone['height']):
                return zone_name
        
        return None


class Player:
    def __init__(self, start_x, start_y):
        self.tile_x = start_x
        self.tile_y = start_y
        self.pixel_x = start_x * 32
        self.pixel_y = start_y * 32
        self.speed = 2
        self.animation_frame = 0
        self.idle_animation_frame = 0
        self.direction = 'down'
        self.moving = False
        self.running = False
        self.size = 100  # Character display size
        
        # Load character sprite
        self.load_sprite()
    
    def load_strip(self, filename, direction, num_frames=8):
        """Load animation frames from a specific row in the grid PNG"""
        path = f'{config.IMAGE_PATH}/lpc_male_animations_2026-02-05T00-35-56/standard/{filename}'
        if os.path.exists(path):
            grid = pygame.image.load(path).convert_alpha()
            frame_width = 64
            frame_height = 64
            row_index = {'down': 2, 'up': 0, 'right': 3, 'left': 1}[direction]
            frames = []
            for i in range(num_frames):
                x = i * frame_width
                y = row_index * frame_height
                frame = grid.subsurface((x, y, frame_width, frame_height)).copy()
                frame = pygame.transform.scale(frame, (self.size, self.size))
                frames.append(frame)
            return frames
        else:
            return None
    
    def load_sprite(self):
        """Load and extract animation frames from separate animation grids"""
        self.sprite_frames = {}
        self.sprite_frames_run = {}
        self.sprite_frames_idle = {}
        
        # Load walk animations (8 frames per direction)
        for direction in ['down', 'up', 'right', 'left']:
            frames = self.load_strip('walk.png', direction, 8)
            if frames:
                self.sprite_frames[direction] = frames
        
        if not self.sprite_frames:
            self.sprite_frames = None
        
        # Load run animations (8 frames per direction)
        for direction in ['down', 'up', 'right', 'left']:
            frames = self.load_strip('run.png', direction, 8)
            if frames:
                self.sprite_frames_run[direction] = frames
        
        if not self.sprite_frames_run:
            self.sprite_frames_run = None
        
        # Load idle animations (8 frames per direction)
        for direction in ['down', 'up', 'right', 'left']:
            frames = self.load_strip('idle.png', direction, 8)
            if frames:
                self.sprite_frames_idle[direction] = frames
        
        if not self.sprite_frames_idle:
            self.sprite_frames_idle = None
        
    def move(self, dx, dy, tilemap, running=False):
        """Move player with collision detection"""
        self.running = running
        if dx == 0 and dy == 0:
            self.moving = False
            return
            
        # Update direction
        if dx < 0:
            self.direction = 'left'
        elif dx > 0:
            self.direction = 'right'
        elif dy < 0:
            self.direction = 'up'
        elif dy > 0:
            self.direction = 'down'
        
        # Set speed based on running
        current_speed = 4 if running else 2
        
        # Calculate new position (ensure integers)
        new_pixel_x = int(self.pixel_x + dx * current_speed)
        new_pixel_y = int(self.pixel_y + dy * current_speed)
        
        # Convert to tile coordinates
        new_tile_x = new_pixel_x // 32
        new_tile_y = new_pixel_y // 32
        
        # Check collision
        if not tilemap.is_collision(new_tile_x, new_tile_y):
            self.pixel_x = new_pixel_x
            self.pixel_y = new_pixel_y
            self.tile_x = new_tile_x
            self.tile_y = new_tile_y
            self.moving = True
            # Animation speed based on running
            anim_speed = 0.3 if running else 0.15
            max_frames = 8
            self.animation_frame = (self.animation_frame + anim_speed) % max_frames
        else:
            self.moving = False
            # Animate idle when not moving
            self.idle_animation_frame = (self.idle_animation_frame + 0.05) % 8
    
    def draw(self, screen, camera_x, camera_y):
        """Draw player sprite with animation"""
        # Ensure integer screen positions (no sub-pixel rendering)
        # Center the larger sprite on the player position
        screen_x = int(self.pixel_x - camera_x - (self.size - 32) // 2)
        screen_y = int(self.pixel_y - camera_y - (self.size - 32))
        
        # Use loaded sprite frames if available
        if self.sprite_frames:
            # Get current frame based on direction and animation
            if self.moving:
                max_frames = 8
                frame_index = int(self.animation_frame) % max_frames
                if self.running and self.sprite_frames_run:
                    current_frame = self.sprite_frames_run[self.direction][frame_index]
                else:
                    current_frame = self.sprite_frames[self.direction][frame_index]
            else:
                # Idle animation
                frame_index = int(self.idle_animation_frame) % 8
                if self.sprite_frames_idle:
                    current_frame = self.sprite_frames_idle[self.direction][frame_index]
                else:
                    current_frame = self.sprite_frames[self.direction][0]  # Fallback to static walk frame
            screen.blit(current_frame, (screen_x, screen_y))
        else:
            # Fallback to procedural blocky character
            player_surf = pygame.Surface((32, 32))
            player_surf.fill((255, 0, 255))  # Transparent color
            player_surf.set_colorkey((255, 0, 255))
            
            # Body
            body_color = config.BLUE
            pygame.draw.rect(player_surf, body_color, (8, 12, 16, 16))
            
            # Head
            pygame.draw.rect(player_surf, (255, 220, 177), (10, 6, 12, 10))
            
            # Eyes
            pygame.draw.rect(player_surf, config.BLACK, (12, 9, 2, 2))
            pygame.draw.rect(player_surf, config.BLACK, (18, 9, 2, 2))
            
            # Legs (animate)
            leg_offset = int(self.animation_frame) if self.moving else 0
            if leg_offset % 2 == 0:
                pygame.draw.rect(player_surf, body_color, (10, 28, 4, 4))
                pygame.draw.rect(player_surf, body_color, (18, 28, 4, 4))
            else:
                pygame.draw.rect(player_surf, body_color, (8, 28, 4, 4))
                pygame.draw.rect(player_surf, body_color, (20, 28, 4, 4))
            
            # Border for blocky look
            pygame.draw.rect(player_surf, config.BLACK, (8, 6, 16, 26), 2)
            
            screen.blit(player_surf, (screen_x, screen_y))