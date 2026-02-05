"""
Tilemap system for retro 2D overworld
Loads CSV layers and tileset for proper depth layering
"""

import pygame
import os
import csv
import config

class Tilemap:
    def __init__(self):
        self.tile_size = 32  # Map tile size
        self.tileset_tile_size = 16  # Tileset tile size
        
        # Load tileset
        tileset_path = f'{config.IMAGE_PATH}/Sunnyside_World_ASSET_PACK_V2.1/Sunnyside_World_Assets/Tileset/spr_tileset_sunnysideworld_16px.png'
        if os.path.exists(tileset_path):
            self.tileset = pygame.image.load(tileset_path).convert_alpha()
            self.tileset_width = self.tileset.get_width() // self.tileset_tile_size  # 64
            self.tileset_height = self.tileset.get_height() // self.tileset_tile_size  # 64
            print(f"Loaded tileset: {tileset_path}")
        else:
            self.tileset = None
            print(f"Tileset not found: {tileset_path}")
        
        # Layer order (drawing order, bottom to top)
        self.layer_order = [
            'land', 'shadow_under', 'under', 'water', 'path', 'bridge', 'over', 
            'waterfall', 'items', 'sign', 'house', 'house1', 'front', 'trees', 
            'rocks', 'shadow'
        ]
        
        # Load layers
        self.layers = {}
        self.collision_map = []
        konekta_path = f'{config.RESOURCES_PATH}/konekta'
        
        for layer_name in self.layer_order + ['collision', 'gamedesignation']:
            csv_path = f'{konekta_path}/konekta._{layer_name}.csv'
            if os.path.exists(csv_path):
                self.layers[layer_name] = self.load_csv_layer(csv_path)
                # Debug: count non-empty tiles
                non_empty = sum(1 for row in self.layers[layer_name] for tile in row if tile > 0)
                print(f"Loaded layer: {layer_name} ({non_empty} non-empty tiles)")
            else:
                print(f"Layer not found: {layer_name}")
        
        # Set map dimensions from first layer
        if self.layers:
            first_layer = list(self.layers.values())[0]
            self.map_width = len(first_layer[0]) * self.tile_size
            self.map_height = len(first_layer) * self.tile_size
        else:
            self.map_width = 1024
            self.map_height = 768
        
        # Process collision layer
        if 'collision' in self.layers:
            self.collision_map = self.layers['collision']
        
        # Process gamedesignation for interaction zones
        self.interaction_zones = {}
        if 'gamedesignation' in self.layers:
            self.process_gamedesignation()
        
        # Find spawn position on land
        self.spawn_x, self.spawn_y = self.find_spawn_position()
        
        # Building labels (keep for now, could be moved to gamedesignation)
        self.labels = [
            {'text': 'Barangay Captain', 'x': 300, 'y': 180, 'color': config.BLUE},
            {'text': 'Recipe Game', 'x': 600, 'y': 280, 'color': config.RED},
            {'text': 'Word Match', 'x': 450, 'y': 430, 'color': config.PURPLE}
        ]
    
    def load_csv_layer(self, csv_path):
        """Load a CSV layer into a 2D list"""
        layer = []
        with open(csv_path, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                layer.append([int(cell) if cell and cell != '-1' else 0 for cell in row])
        return layer
    
    def process_gamedesignation(self):
        """Process gamedesignation layer for interaction zones"""
        # This would map special tile IDs to zone names
        # For now, keep hardcoded zones
        pass
    
    def find_spawn_position(self):
        """Find a suitable spawn position on land, not blocked"""
        # Try to find center of map with tiles
        for layer_name in ['land', 'path', 'water']:
            if layer_name in self.layers:
                layer = self.layers[layer_name]
                for y, row in enumerate(layer):
                    for x, tile_id in enumerate(row):
                        if tile_id > 0:
                            print(f"Found spawn on {layer_name} at ({x}, {y}), ID: {tile_id}")
                            return x, y
        
        # Fallback to center of map
        if self.layers:
            first_layer = list(self.layers.values())[0]
            center_x = len(first_layer[0]) // 2
            center_y = len(first_layer) // 2
            print(f"Using map center: ({center_x}, {center_y})")
            return center_x, center_y
        
        print("No suitable spawn found, using default (10, 8)")
        return 10, 8
    
    def draw(self, screen, camera_x, camera_y):
        """Draw all map layers with camera offset"""
        camera_x = int(camera_x)
        camera_y = int(camera_y)
        
        if not self.tileset:
            return
        
        # Draw layers in order
        for layer_name in self.layer_order:
            if layer_name in self.layers:
                self.draw_layer(screen, self.layers[layer_name], camera_x, camera_y)
    
    def draw_layer(self, screen, layer_data, camera_x, camera_y):
        """Draw a single layer"""
        tiles_drawn = 0
        
        # Tiled flip flags
        FLIPPED_HORIZONTALLY_FLAG = 0x80000000
        FLIPPED_VERTICALLY_FLAG = 0x40000000
        FLIPPED_DIAGONALLY_FLAG = 0x20000000
        FLAGS_MASK = ~(FLIPPED_HORIZONTALLY_FLAG | FLIPPED_VERTICALLY_FLAG | FLIPPED_DIAGONALLY_FLAG)
        
        for y, row in enumerate(layer_data):
            for x, tile_id in enumerate(row):
                if tile_id > 0:  # 0 = empty
                    # Extract flip flags
                    flipped_h = tile_id & FLIPPED_HORIZONTALLY_FLAG
                    flipped_v = tile_id & FLIPPED_VERTICALLY_FLAG
                    flipped_d = tile_id & FLIPPED_DIAGONALLY_FLAG
                    
                    # Remove flags to get actual tile ID
                    tile_id = tile_id & FLAGS_MASK
                    
                    # Tiled uses 0-based tile IDs (try without subtracting 1)
                    # tile_id -= 1
                    
                    if tile_id < 0:
                        continue
                    
                    # Convert tile_id to tileset coordinates
                    tile_x = (tile_id % self.tileset_width) * self.tileset_tile_size
                    tile_y = (tile_id // self.tileset_width) * self.tileset_tile_size
                    
                    # Skip if outside tileset bounds
                    if tile_x + self.tileset_tile_size > self.tileset.get_width() or tile_y + self.tileset_tile_size > self.tileset.get_height():
                        print(f"Tile {tile_id} out of bounds: pos ({tile_x},{tile_y}) size {self.tileset_tile_size}, tileset {self.tileset.get_width()}x{self.tileset.get_height()}")
                        continue
                    
                    # Get tile subsurface
                    try:
                        tile_surf = self.tileset.subsurface((tile_x, tile_y, self.tileset_tile_size, self.tileset_tile_size))
                        # Debug first few tiles
                        if tiles_drawn < 5:
                            print(f"Tile {tile_id} -> coords ({tile_x},{tile_y}) -> subsurface successful")
                    except ValueError as e:
                        print(f"Subsurface error for tile {tile_id} at ({tile_x},{tile_y}): {e}")
                        continue
                    
                    # Apply flips
                    if flipped_h:
                        tile_surf = pygame.transform.flip(tile_surf, True, False)
                    if flipped_v:
                        tile_surf = pygame.transform.flip(tile_surf, False, True)
                    if flipped_d:
                        tile_surf = pygame.transform.rotate(tile_surf, -90)
                        tile_surf = pygame.transform.flip(tile_surf, True, False)
                    
                    # Scale to map tile size
                    tile_surf = pygame.transform.scale(tile_surf, (self.tile_size, self.tile_size))
                    
                    # Screen position
                    screen_x = x * self.tile_size - camera_x
                    screen_y = y * self.tile_size - camera_y
                    
                    # Only draw if on screen
                    if -self.tile_size < screen_x < config.SCREEN_WIDTH and -self.tile_size < screen_y < config.SCREEN_HEIGHT:
                        screen.blit(tile_surf, (screen_x, screen_y))
                        tiles_drawn += 1
        
        return tiles_drawn
    
    def is_collision(self, tile_x, tile_y):
        """Check if tile is blocked"""
        if 0 <= tile_y < len(self.collision_map) and 0 <= tile_x < len(self.collision_map[tile_y]):
            return self.collision_map[tile_y][tile_x] > 0
        return False
    
    def check_interaction(self, tile_x, tile_y):
        """Check if player is near an interaction zone"""
        pixel_x = tile_x * 32
        pixel_y = tile_y * 32
        
        for zone_name, zone in self.interaction_zones.items():
            if (zone['x'] <= pixel_x < zone['x'] + zone['width'] and
                zone['y'] <= pixel_y < zone['y'] + zone['height']):
                return zone_name
        
        return None
    
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
        current_speed = 12 if running else 2
        
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