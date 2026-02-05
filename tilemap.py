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
        self.tile_cache = {}  # Cache pre-rendered tiles
        
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
            'water', 'under', 'shadow_under', 'land', 'path', 'bridge', 'over', 
            'waterfall', 'items', 'gamedesignation', 'sign', 'house1', 'house', 
            'front', 'trees', 'rocks', 'shadow'
        ]
        
        # Load layers
        self.layers = {}
        self.collision_map = []
        konekta_path = f'{config.RESOURCES_PATH}/konekta'
        
        for layer_name in self.layer_order + ['collision', 'gamedesignation']:
            csv_path = f'{konekta_path}/konekta_{layer_name}.csv'
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
        # Map tile IDs to game zone names
        tile_to_zone = {
            70: 'barangay_captain',  # Tile ID 70 = Barangay Captain game
            71: 'recipe_game',        # Tile ID 71 = Recipe game (if you add it later)
            72: 'word_match'          # Tile ID 72 = Word match (if you add it later)
        }
        
        layer = self.layers['gamedesignation']
        for y, row in enumerate(layer):
            for x, tile_id in enumerate(row):
                if tile_id in tile_to_zone:
                    zone_name = tile_to_zone[tile_id]
                    # Store tile position as interaction zone
                    if zone_name not in self.interaction_zones:
                        self.interaction_zones[zone_name] = {
                            'x': x * self.tile_size,
                            'y': y * self.tile_size,
                            'width': self.tile_size,
                            'height': self.tile_size
                        }
                        print(f"Found interaction zone '{zone_name}' at tile ({x}, {y})")
    
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
        """Draw a single layer with tile caching"""
        # Tiled flip flags
        FLIPPED_HORIZONTALLY_FLAG = 0x80000000
        FLIPPED_VERTICALLY_FLAG = 0x40000000
        FLIPPED_DIAGONALLY_FLAG = 0x20000000
        FLAGS_MASK = ~(FLIPPED_HORIZONTALLY_FLAG | FLIPPED_VERTICALLY_FLAG | FLIPPED_DIAGONALLY_FLAG)
        
        # Calculate visible tile range for culling
        start_x = max(0, camera_x // self.tile_size)
        start_y = max(0, camera_y // self.tile_size)
        end_x = min(len(layer_data[0]), (camera_x + config.SCREEN_WIDTH) // self.tile_size + 1)
        end_y = min(len(layer_data), (camera_y + config.SCREEN_HEIGHT) // self.tile_size + 1)
        
        for y in range(start_y, end_y):
            row = layer_data[y]
            for x in range(start_x, end_x):
                tile_id = row[x]
                if tile_id > 0:  # 0 = empty
                    # Create cache key with flip flags
                    cache_key = tile_id
                    
                    # Check cache first
                    if cache_key not in self.tile_cache:
                        # Extract flip flags
                        flipped_h = tile_id & FLIPPED_HORIZONTALLY_FLAG
                        flipped_v = tile_id & FLIPPED_VERTICALLY_FLAG
                        flipped_d = tile_id & FLIPPED_DIAGONALLY_FLAG
                        
                        # Remove flags to get actual tile ID
                        clean_tile_id = tile_id & FLAGS_MASK
                        
                        if clean_tile_id < 0:
                            self.tile_cache[cache_key] = None
                            continue
                        
                        # Convert tile_id to tileset coordinates
                        tile_x = (clean_tile_id % self.tileset_width) * self.tileset_tile_size
                        tile_y = (clean_tile_id // self.tileset_width) * self.tileset_tile_size
                        
                        # Skip if outside tileset bounds
                        if tile_x + self.tileset_tile_size > self.tileset.get_width() or tile_y + self.tileset_tile_size > self.tileset.get_height():
                            self.tile_cache[cache_key] = None
                            continue
                        
                        # Get tile subsurface
                        try:
                            tile_surf = self.tileset.subsurface((tile_x, tile_y, self.tileset_tile_size, self.tileset_tile_size)).copy()
                        except (ValueError, pygame.error):
                            self.tile_cache[cache_key] = None
                            continue
                        
                        # Apply flips
                        if flipped_h:
                            tile_surf = pygame.transform.flip(tile_surf, True, False)
                        if flipped_v:
                            tile_surf = pygame.transform.flip(tile_surf, False, True)
                        if flipped_d:
                            tile_surf = pygame.transform.rotate(tile_surf, -90)
                            tile_surf = pygame.transform.flip(tile_surf, True, False)
                        
                        # Scale to map tile size and cache
                        tile_surf = pygame.transform.scale(tile_surf, (self.tile_size, self.tile_size))
                        self.tile_cache[cache_key] = tile_surf
                    
                    # Draw cached tile (if not None)
                    if self.tile_cache[cache_key] is not None:
                        screen_x = x * self.tile_size - camera_x
                        screen_y = y * self.tile_size - camera_y
                        screen.blit(self.tile_cache[cache_key], (screen_x, screen_y))
    
    def is_collision(self, tile_x, tile_y):
        """Check if tile is blocked by collision map or boundaries"""
        # Check map boundaries first
        if tile_x < 0 or tile_y < 0:
            return True
        if tile_x >= len(self.collision_map[0]) if self.collision_map else tile_x * 32 >= self.map_width - 32:
            return True
        if tile_y >= len(self.collision_map) if self.collision_map else tile_y * 32 >= self.map_height - 32:
            return True
        
        # Check collision map
        if self.collision_map and 0 <= tile_y < len(self.collision_map) and 0 <= tile_x < len(self.collision_map[tile_y]):
            return self.collision_map[tile_y][tile_x] > 0
        
        return False
    
    def check_interaction(self, tile_x, tile_y):
        """Check if player is on or near an interaction zone"""
        # Check current tile and adjacent tiles (1 tile radius)
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                check_x = tile_x + dx
                check_y = tile_y + dy
                pixel_x = check_x * self.tile_size
                pixel_y = check_y * self.tile_size
                
                for zone_name, zone in self.interaction_zones.items():
                    if (zone['x'] == pixel_x and zone['y'] == pixel_y):
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
            # Animate idle when not moving
            self.idle_animation_frame = (self.idle_animation_frame + 0.05) % 8
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
        current_speed = 5 if running else 2
        
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
            # Animate idle when blocked
            self.idle_animation_frame = (self.idle_animation_frame + 0.05) % 8
    
    def draw(self, screen, camera_x, camera_y):
        """Draw player sprite with animation"""
        # Ensure integer screen positions (no sub-pixel rendering)
        # Center the larger sprite on the player position
        screen_x = int(self.pixel_x - camera_x - (self.size - 32) // 2)
        screen_y = int(self.pixel_y - camera_y - (self.size - 32))
        
        # Use loaded sprite frames if available
        if self.sprite_frames and self.direction in self.sprite_frames:
            current_frame = None
            
            # Get current frame based on direction and animation
            if self.moving:
                if self.running and self.sprite_frames_run and self.direction in self.sprite_frames_run:
                    frames = self.sprite_frames_run[self.direction]
                    frame_index = int(self.animation_frame) % len(frames)
                    current_frame = frames[frame_index]
                else:
                    frames = self.sprite_frames[self.direction]
                    frame_index = int(self.animation_frame) % len(frames)
                    current_frame = frames[frame_index]
            else:
                # When idle, just use the first frame of walk animation (static pose)
                current_frame = self.sprite_frames[self.direction][0]
            
            if current_frame:
                screen.blit(current_frame, (screen_x, screen_y))
            else:
                # Draw fallback if frame not found
                self._draw_fallback_character(screen, screen_x, screen_y)
        else:
            # Draw fallback character
            self._draw_fallback_character(screen, screen_x, screen_y)
    
    def _draw_fallback_character(self, screen, screen_x, screen_y):
        """Draw a simple fallback character"""
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