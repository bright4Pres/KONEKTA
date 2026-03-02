"""
Tilemap system for retro 2D overworld
Loads CSV layers and tileset for proper depth layering
"""

import pygame
import os
import csv
import random
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
        # Visual layers in drawing order (bottom to top)
        self.layer_order = [
            'water', 'under', 'shadow_under', 'ground',
            'object_back_low', 'object_back_high', 'decal_back',
            'shadow_mid', 'object_front_low', 'object_front_high', 'shadow'
        ]
        
        # All layers to load (visual + logic), in full map order
        all_layers = [
            'water', 'under', 'shadow_under', 'ground',
            'object_back_low', 'object_back_high', 'decal_back',
            'spawnpoint', 'bc_gamedesignation', 'recipe_gamedesignation', 'word_gamedesignation',
            'shadow_mid', 'object_front_low', 'object_front_high', 'shadow',
            'collision'
        ]
        
        # Load layers
        self.layers = {}
        self.collision_map = []
        konekta_path = f'{config.RESOURCES_PATH}/konekta'
        
        for layer_name in all_layers:
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
        
        # Process gamedesignation layers for interaction zones
        self.interaction_zones = {}
        self.process_gamedesignation()
        
        # Find spawn position on land (needed before randomizing games)
        self.spawn_x, self.spawn_y = self.find_spawn_position()
        
        # Randomize recipe and word game positions on land
        self.randomize_game_positions()
        
        # Update labels to match actual zone positions
        self.update_labels()
    
    def load_csv_layer(self, csv_path):
        """Load a CSV layer into a 2D list.
        
        Tiled uses -1 for empty and may write flipped tiles as large negative
        numbers (signed 32-bit overflow).  We convert every value to unsigned
        32-bit so the flip-flag bitmask logic works correctly.
        """
        layer = []
        with open(csv_path, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                parsed = []
                for cell in row:
                    cell = cell.strip()
                    if not cell or cell == '-1':
                        parsed.append(0)           # empty tile
                    else:
                        parsed.append(int(cell) & 0xFFFFFFFF)  # unsigned 32-bit
                layer.append(parsed)
        return layer
    
    def process_gamedesignation(self):
        """Process separate gamedesignation layers for interaction zones"""
        # Each CSV marks its dedicated zone; first non-empty tile sets the zone anchor
        layer_to_zone = {
            'bc_gamedesignation':     'barangay_captain',
            'recipe_gamedesignation': 'recipe_game',
            'word_gamedesignation':   'synonym_antonym',
        }
        
        for layer_name, zone_name in layer_to_zone.items():
            if layer_name not in self.layers:
                continue
            layer = self.layers[layer_name]
            for y, row in enumerate(layer):
                for x, tile_id in enumerate(row):
                    if tile_id > 0 and zone_name not in self.interaction_zones:
                        self.interaction_zones[zone_name] = {
                            'x': x * self.tile_size,
                            'y': y * self.tile_size,
                            'width': self.tile_size,
                            'height': self.tile_size
                        }
                        print(f"Found interaction zone '{zone_name}' at tile ({x}, {y})")
    
    def get_valid_land_tiles(self):
        """Get a list of all walkable land tiles (not collision, not water)"""
        valid_tiles = []
        
        if 'ground' not in self.layers or 'collision' not in self.layers:
            return valid_tiles
        
        land_layer = self.layers['ground']
        collision_layer = self.layers['collision']
        
        for y, row in enumerate(land_layer):
            for x, tile_id in enumerate(row):
                # Check if there's a land tile and no collision
                if tile_id > 0 and collision_layer[y][x] == 0:
                    valid_tiles.append((x, y))
        
        return valid_tiles
    
    def randomize_game_positions(self):
        """Place recipe_game and synonym_antonym from CSV data; fall back to random land tiles."""
        # If both zones were already loaded from their CSVs, nothing to do
        needs_recipe  = 'recipe_game'    not in self.interaction_zones
        needs_synonym = 'synonym_antonym' not in self.interaction_zones
        
        if not needs_recipe and not needs_synonym:
            print("Game positions loaded from CSV; no randomisation needed.")
            return
        
        valid_tiles = self.get_valid_land_tiles()
        
        zones_needed = [z for z, flag in [
            ('recipe_game', needs_recipe), ('synonym_antonym', needs_synonym)
        ] if flag]
        
        if len(valid_tiles) < len(zones_needed):
            print("Warning: Not enough valid tiles to place games")
            return
        
        # Remove tiles too close to spawn or existing zones
        filtered_tiles = []
        for x, y in valid_tiles:
            if abs(x - self.spawn_x) <= 3 and abs(y - self.spawn_y) <= 3:
                continue
            too_close = False
            for zone in self.interaction_zones.values():
                zone_tile_x = zone['x'] // self.tile_size
                zone_tile_y = zone['y'] // self.tile_size
                if abs(x - zone_tile_x) <= 5 and abs(y - zone_tile_y) <= 5:
                    too_close = True
                    break
            if not too_close:
                filtered_tiles.append((x, y))
        
        if len(filtered_tiles) < len(zones_needed):
            filtered_tiles = [
                (x, y) for x, y in valid_tiles
                if abs(x - self.spawn_x) > 2 or abs(y - self.spawn_y) > 2
            ]
        
        if len(filtered_tiles) >= len(zones_needed):
            selected_tiles = random.sample(filtered_tiles, len(zones_needed))
            for zone_name, (tx, ty) in zip(zones_needed, selected_tiles):
                self.interaction_zones[zone_name] = {
                    'x': tx * self.tile_size,
                    'y': ty * self.tile_size,
                    'width': self.tile_size,
                    'height': self.tile_size
                }
                print(f"Placed {zone_name} at tile ({tx}, {ty})")
        else:
            print("Warning: Could not find suitable positions for games")
    
    def update_labels(self):
        """Update label positions to match interaction zones"""
        self.labels = []
        
        zone_label_map = {
            'barangay_captain': {'text': 'Barangay Captain', 'color': config.BLUE},
            'recipe_game': {'text': 'Recipe Game', 'color': config.RED},
            'synonym_antonym': {'text': 'Word Match', 'color': config.PURPLE}
        }
        
        for zone_name, zone in self.interaction_zones.items():
            if zone_name in zone_label_map:
                label_info = zone_label_map[zone_name]
                self.labels.append({
                    'text': label_info['text'],
                    'x': zone['x'],
                    'y': zone['y'] - 10,  # Place label slightly above the zone
                    'color': label_info['color']
                })
    
    def find_spawn_position(self):
        """Find a suitable spawn position using spawnpoint layer, then ground, then fallback"""
        # Prefer explicit spawnpoint CSV
        if 'spawnpoint' in self.layers:
            for y, row in enumerate(self.layers['spawnpoint']):
                for x, tile_id in enumerate(row):
                    if tile_id > 0:
                        print(f"Found spawn on spawnpoint layer at ({x}, {y})")
                        return x, y
        
        # Fall back to first ground tile
        for layer_name in ['ground', 'water']:
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
        
        # Calculate visible tile range for culling (add extra tiles to prevent gaps)
        start_x = max(0, camera_x // self.tile_size - 1)
        start_y = max(0, camera_y // self.tile_size - 1)
        end_x = min(len(layer_data[0]), (camera_x + config.SCREEN_WIDTH) // self.tile_size + 2)
        end_y = min(len(layer_data), (camera_y + config.SCREEN_HEIGHT) // self.tile_size + 2)
        
        for y in range(start_y, end_y):
            row = layer_data[y]
            for x in range(start_x, end_x):
                tile_id = row[x]
                if tile_id != 0:  # 0 = empty
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
                        
                        # This tileset uses firstgid=0 (0-based GIDs directly)
                        idx = clean_tile_id
                        if idx < 0:
                            self.tile_cache[cache_key] = None
                            continue
                        
                        # Convert 0-based index to tileset coordinates
                        tile_x = (idx % self.tileset_width) * self.tileset_tile_size
                        tile_y = (idx // self.tileset_width) * self.tileset_tile_size
                        
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
                        screen_x = int(x * self.tile_size - camera_x)
                        screen_y = int(y * self.tile_size - camera_y)
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

        # Grid-movement state
        self.target_tile_x = start_x
        self.target_tile_y = start_y
        self.move_progress = 0.0   # 0.0 → 1.0 across one tile
        
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
        """Start a grid-aligned move. Ignored while a previous move is still animating."""
        if self.moving:
            return  # locked until current tile transition completes
        if dx == 0 and dy == 0:
            return

        # Only update direction once the previous move is done
        if dx < 0:   self.direction = 'left'
        elif dx > 0: self.direction = 'right'
        elif dy < 0: self.direction = 'up'
        elif dy > 0: self.direction = 'down'

        next_tile_x = self.tile_x + dx
        next_tile_y = self.tile_y + dy

        if tilemap.is_collision(next_tile_x, next_tile_y):
            return  # face the direction but stay put

        # Begin tile transition
        self.target_tile_x = next_tile_x
        self.target_tile_y = next_tile_y
        self.move_progress = 0.0
        self.moving = True
        self.running = running

    def update(self, dt):
        """Advance the tile-to-tile animation each frame."""
        if not self.moving:
            self.idle_animation_frame = (self.idle_animation_frame + 0.05) % 8
            self.animation_frame = 0  # reset walk frame when idle
            return

        # Running ~8 tiles/sec, walking ~4 tiles/sec
        tiles_per_sec = 8.0 if self.running else 4.0
        self.move_progress += tiles_per_sec * dt

        if self.move_progress >= 1.0:
            # Snap exactly to destination tile
            self.tile_x = self.target_tile_x
            self.tile_y = self.target_tile_y
            self.pixel_x = self.tile_x * 32
            self.pixel_y = self.tile_y * 32
            self.move_progress = 0.0
            self.moving = False
        else:
            # Smooth interpolation between origin and destination
            start_px = self.tile_x * 32
            start_py = self.tile_y * 32
            end_px   = self.target_tile_x * 32
            end_py   = self.target_tile_y * 32
            self.pixel_x = int(start_px + (end_px - start_px) * self.move_progress)
            self.pixel_y = int(start_py + (end_py - start_py) * self.move_progress)

        # Show 2 frames per tile step (Pokémon-style: left foot, right foot)
        # int() gives discrete frame switches rather than smooth float blending
        self.animation_frame = int(self.move_progress * 2) % 8
    
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