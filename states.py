# states for each screen in the game
# all the game logic is in here too

import pygame
import random
import time
import math
import config
from database import Database
from tilemap import Tilemap, Player

# giant dev footnotes for this monster file:
# - yes this file is huge. splitting later would be nice but not today.
# - each state owns its own input/update/draw loop-ish behavior.
# - main.py just switches states; game logic mostly lives here.
# - teacher dashboard, forge, and all mini-games are in here rn.
# - if something "freezes", check score submit + db calls + state flags first.
# - language keys are normalized to english/tagalog/bisaya values.
# - db-only question flow means empty db => "no questions" screens by design.


LANGUAGE_LABELS = {
    'english': 'English',
    'tagalog': 'Tagalog',
    'bisaya': 'Cebuano',
}

QUESTION_GAME_KEYS = ['barangay', 'recipe', 'synonym_antonym']
QUESTION_GAME_LABELS = {
    'barangay': 'Barangay Captain Simulator',
    'recipe': 'Recipe Game',
    'synonym_antonym': 'Word Match Game',
}


def sanitize_student_id(raw_text):
    """clean student id so leaderboard names stay readable.

    tiny rule set:
    - allow letters/numbers/space/_/-
    - collapse wild spacing
    - fallback to default when blank
    """
    cleaned = ''.join(ch for ch in str(raw_text) if ch.isalnum() or ch in ('_', '-', ' '))
    cleaned = ' '.join(cleaned.strip().split())
    if not cleaned:
        cleaned = config.DEFAULT_STUDENT_ID
    return cleaned[:24]


# Base state (other states inherit from this)

class State:
    """base class that all states inherit from.

    Footnote:
    - super small on purpose, just the interface and a few shared ui helpers.
    """

    def __init__(self, game):
        self.game = game
        self.next_state = None

    def enter(self):
        pass

    def exit(self):
        pass

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, screen):
        pass

    # --- shared helper methods ---

    @staticmethod
    def wrap_text_pixel(text, max_width, font):
        """wrap text so it fits on screen"""
        words = text.split()
        lines = []
        current_line = ''
        for word in words:
            test_line = f'{current_line} {word}' if current_line else word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                if font.size(word)[0] > max_width:
                    lines.append(word)          # force-add oversized word
                    current_line = ''
                else:
                    current_line = word
        if current_line:
            lines.append(current_line)
        return lines

    @staticmethod
    def create_gradient(width, height, color_func):
        """make a gradient background surface"""
        surface = pygame.Surface((width, height))
        for i in range(height):
            pygame.draw.line(surface, color_func(i), (0, i), (width - 1, i))
        return surface

    @staticmethod
    def draw_retro_box(screen, rect, bg_color, border_color=None,
                       shadow=True, border_width=3):
        """draw a box with a shadow and border"""
        if shadow:
            pygame.draw.rect(screen, config.BLACK, rect.inflate(6, 6).move(2, 2))
        pygame.draw.rect(screen, bg_color, rect)
        if border_color:
            pygame.draw.rect(screen, border_color, rect, border_width)

    def draw_language_selection(self, screen, title_color):
        """show the pick a language screen"""
        title_box = pygame.Rect(config.SCREEN_WIDTH // 2 - 300, 100, 600, 80)
        self.draw_retro_box(screen, title_box, title_color, config.YELLOW,
                            border_width=5)

        title = self.title_font.render('SELECT LANGUAGE', True, config.YELLOW)
        title_shadow = self.title_font.render('SELECT LANGUAGE', True,
                                              config.BLACK)
        title_rect = title.get_rect(center=title_box.center)
        screen.blit(title_shadow, title_rect.move(3, 3))
        screen.blit(title, title_rect)

        languages = [
            ('1. ENGLISH',        config.GREEN),
            ('2. TAGALOG',        config.ORANGE),
            ('3. BISAYA/CEBUANO', config.PURPLE),
        ]

        y = 250
        for lang_text, color in languages:
            lang_box = pygame.Rect(config.SCREEN_WIDTH // 2 - 250, y, 500, 70)
            self.draw_retro_box(screen, lang_box, color, config.YELLOW,
                                border_width=4)
            text = self.font.render(lang_text, True, config.WHITE)
            text_shadow = self.font.render(lang_text, True, config.BLACK)
            text_rect = text.get_rect(center=lang_box.center)
            screen.blit(text_shadow, text_rect.move(2, 2))
            screen.blit(text, text_rect)
            y += 90

        hint = self.small_font.render('Press the number key to select', True,
                                      config.WHITE)
        screen.blit(hint, hint.get_rect(center=(config.SCREEN_WIDTH // 2, 580)))

    @staticmethod
    def handle_language_key(event):
        """check if 1 2 or 3 was pressed for language"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                return 'english'
            if event.key == pygame.K_2:
                return 'tagalog'
            if event.key == pygame.K_3:
                return 'bisaya'
        return None


class TitleScreenState(State):
    """animated title screen with blocky pixel vibe before map starts."""

    def __init__(self, game):
        super().__init__(game)
        self.anim_time = 0.0
        self.entered_at = 0.0
        self.input_unlock_at = 0.0

        self.title_raw = self._safe_load_image(config.TITLE_SCREEN_IMAGE_PATH)
        self.logo_raw = self._safe_load_image(config.LOGO_IMAGE_PATH)

        self.title_image = None
        self.logo_image = None
        self.bg_gradient = None
        self.scanlines = None
        self.layout_size = (0, 0)

        self.blocks = []
        self.sparkles = []
        self.block_colors = [
            (23, 44, 74),
            (29, 58, 94),
            (38, 72, 112),
            (52, 92, 138),
        ]

        self._refresh_layout()

    @staticmethod
    def _safe_load_image(path):
        """load image and keep alpha; return None if missing/corrupt."""
        try:
            return pygame.image.load(path).convert_alpha()
        except Exception:
            return None

    @staticmethod
    def _fit_image(surface, max_w, max_h):
        """scale image to fit a box while keeping aspect ratio."""
        if surface is None:
            return None
        sw, sh = surface.get_size()
        if sw <= 0 or sh <= 0:
            return None
        scale = min(max_w / sw, max_h / sh)
        width = max(1, int(sw * scale))
        height = max(1, int(sh * scale))
        return pygame.transform.scale(surface, (width, height))

    def _refresh_layout(self):
        """rebuild scaled assets + decorative layers for current resolution."""
        w, h = config.SCREEN_WIDTH, config.SCREEN_HEIGHT
        self.layout_size = (w, h)
        self.bg_gradient = self.create_gradient(
            w,
            h,
            lambda i: (10 + (i * 20) // max(1, h), 24 + (i * 28) // max(1, h), 46 + (i * 34) // max(1, h)),
        )

        self.scanlines = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(0, h, 4):
            pygame.draw.line(self.scanlines, (0, 0, 0, 25), (0, y), (w, y))

        self.title_image = self._fit_image(self.title_raw, int(w * 0.82), int(h * 0.52))
        self.logo_image = self._fit_image(self.logo_raw, int(w * 0.16), int(h * 0.14))

        self.blocks = []
        block_count = max(18, w // 90)
        for _ in range(block_count):
            bw = random.choice([24, 32, 40, 48, 56, 64])
            bh = random.choice([16, 20, 24, 28, 32])
            self.blocks.append({
                'x': random.randint(-80, w + 80),
                'y': random.randint(-h, h),
                'w': bw,
                'h': bh,
                'speed': random.uniform(28.0, 78.0),
                'drift': random.uniform(-16.0, 16.0),
                'phase': random.uniform(0.0, math.tau),
                'color': random.choice(self.block_colors),
            })

        self.sparkles = []
        sparkle_count = max(50, (w * h) // 35000)
        sparkle_palette = [config.YELLOW, config.WHITE, config.LIGHT_BLUE]
        for _ in range(sparkle_count):
            self.sparkles.append({
                'x': random.randint(0, w - 1),
                'y': random.randint(0, h - 1),
                'size': random.choice([2, 2, 3, 4]),
                'speed': random.uniform(12.0, 42.0),
                'phase': random.uniform(0.0, math.tau),
                'twinkle': random.uniform(2.0, 6.0),
                'color': random.choice(sparkle_palette),
            })

    def enter(self):
        self.next_state = None
        self.anim_time = 0.0
        self.entered_at = time.time()
        self.input_unlock_at = self.entered_at + 0.45
        if self.layout_size != (config.SCREEN_WIDTH, config.SCREEN_HEIGHT):
            self._refresh_layout()

    def handle_event(self, event):
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            if time.time() >= self.input_unlock_at:
                self.next_state = 'menu'

    def update(self, dt):
        self.anim_time += dt
        w, h = self.layout_size

        for block in self.blocks:
            block['y'] += block['speed'] * dt
            block['x'] += math.sin(self.anim_time * 0.8 + block['phase']) * block['drift'] * dt
            if block['y'] > h + 36:
                block['y'] = -block['h'] - random.randint(20, h // 2)
                block['x'] = random.randint(-80, w + 80)

        for spark in self.sparkles:
            spark['y'] += spark['speed'] * dt
            if spark['y'] > h + spark['size']:
                spark['y'] = -spark['size']
                spark['x'] = random.randint(0, max(1, w - 1))

    def draw(self, screen):
        if self.layout_size != (config.SCREEN_WIDTH, config.SCREEN_HEIGHT):
            self._refresh_layout()

        w, h = self.layout_size

        if self.bg_gradient:
            screen.blit(self.bg_gradient, (0, 0))
        else:
            screen.fill((14, 24, 46))

        for block in self.blocks:
            rect = pygame.Rect(int(block['x']), int(block['y']), block['w'], block['h'])
            pygame.draw.rect(screen, block['color'], rect)
            pygame.draw.rect(screen, (10, 18, 30), rect, 2)
            if rect.height > 5:
                shine = pygame.Rect(rect.x + 2, rect.y + 2, max(1, rect.w - 4), 2)
                pygame.draw.rect(screen, (130, 180, 230), shine)

        for spark in self.sparkles:
            glow = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(self.anim_time * spark['twinkle'] + spark['phase']))
            color = tuple(min(255, int(channel * glow)) for channel in spark['color'])
            pygame.draw.rect(
                screen,
                color,
                pygame.Rect(int(spark['x']), int(spark['y']), spark['size'], spark['size']),
            )

        frame = pygame.Rect(int(w * 0.08), int(h * 0.09), int(w * 0.84), int(h * 0.78))
        pygame.draw.rect(screen, config.BLACK, frame.move(6, 6))
        pygame.draw.rect(screen, (14, 26, 44), frame)
        pygame.draw.rect(screen, config.YELLOW, frame, 4)

        if self.logo_image:
            logo_bob = int(math.sin(self.anim_time * 2.8) * 3)
            logo_rect = self.logo_image.get_rect(midtop=(w // 2, frame.y + 16 + logo_bob))
            screen.blit(self.logo_image, logo_rect)

        if self.title_image:
            pulse = 1.0 + math.sin(self.anim_time * 2.2) * 0.02
            tw, th = self.title_image.get_size()
            live_w = max(1, int(tw * pulse))
            live_h = max(1, int(th * pulse))
            animated_title = pygame.transform.scale(self.title_image, (live_w, live_h))
            title_y = int(h * 0.42) + int(math.sin(self.anim_time * 1.7) * 8)
            title_rect = animated_title.get_rect(center=(w // 2, title_y))
            screen.blit(animated_title, title_rect.move(4, 4))
            screen.blit(animated_title, title_rect)
        else:
            fallback = self.game.font_title.render('KONEKTA', True, config.YELLOW)
            fallback_shadow = self.game.font_title.render('KONEKTA', True, config.BLACK)
            fallback_rect = fallback.get_rect(center=(w // 2, int(h * 0.42)))
            screen.blit(fallback_shadow, fallback_rect.move(3, 3))
            screen.blit(fallback, fallback_rect)

        subtitle = self.game.font_medium.render('Classroom Literacy Arcade', True, config.WHITE)
        subtitle_rect = subtitle.get_rect(center=(w // 2, int(h * 0.64)))
        pygame.draw.rect(screen, config.BLACK, subtitle_rect.inflate(24, 14).move(2, 2))
        pygame.draw.rect(screen, (30, 45, 68), subtitle_rect.inflate(24, 14))
        pygame.draw.rect(screen, config.BLUE, subtitle_rect.inflate(24, 14), 3)
        screen.blit(subtitle, subtitle_rect)

        blink_on = int((time.time() - self.entered_at) * 2.3) % 2 == 0
        prompt_color = config.YELLOW if blink_on else config.WHITE
        prompt = self.game.font_large.render('PRESS ANY KEY TO START', True, prompt_color)
        prompt_shadow = self.game.font_large.render('PRESS ANY KEY TO START', True, config.BLACK)
        prompt_rect = prompt.get_rect(center=(w // 2, int(h * 0.77)))
        screen.blit(prompt_shadow, prompt_rect.move(2, 2))
        screen.blit(prompt, prompt_rect)

        tip = self.game.font_small.render('CTRL+T: Teacher Mode  |  ESC on map: Exit game', True, config.LIGHT_GRAY)
        tip_rect = tip.get_rect(center=(w // 2, int(h * 0.86)))
        screen.blit(tip, tip_rect)

        if self.scanlines:
            screen.blit(self.scanlines, (0, 0))


# Menu (the overworld map)

class MenuState(State):
    """the overworld map where you walk around.

    notes to self:
    - player id editing starts here (tab modal).
    - this state is the launcher for the 3 mini-games.
    - camera smoothing/clamp is tuned here, dont duplicate in other states.
    """

    def __init__(self, game):
        super().__init__(game)
        self.tilemap = Tilemap()
        self.player = Player(self.tilemap.spawn_x, self.tilemap.spawn_y)
        self.keys_held = {'up': False, 'down': False,
                          'left': False, 'right': False}
        self.shift_held = False
        self.interaction_prompt = None
        self.prompt_timer = 0
        self.prompt_animation_start = 0
        self.student_id = sanitize_student_id(
            getattr(self.game, 'current_student_id', config.DEFAULT_STUDENT_ID)
        )
        self.student_input = self.student_id
        self.editing_student = False
        self.creating_profile = False
        self.profile_list = []
        self.profile_cursor = 0
        self.flash_message = ''
        self.flash_until = 0
        self.stats = {'total_gems': 0}
        self.saved_x = self.tilemap.spawn_x
        self.saved_y = self.tilemap.spawn_y
        # start camera on player
        self.camera_x, self.camera_y = self._camera_target()
        self._clamp_camera()

    # --- camera stuff ---

    def _camera_target(self):
        """calculate where the camera should be"""
        sprite_oy = -(self.player.size - 32) + self.player.size // 2
        tx = int(self.player.pixel_x - config.SCREEN_WIDTH // 2 + 16)
        ty = int(self.player.pixel_y - config.SCREEN_HEIGHT // 2 + sprite_oy)
        return tx, ty

    def _clamp_camera(self):
        """dont let camera go outside the map"""
        max_cx = max(0, self.tilemap.map_width - config.SCREEN_WIDTH)
        max_cy = max(0, self.tilemap.map_height - config.SCREEN_HEIGHT)
        self.camera_x = max(0, min(self.camera_x, max_cx))
        self.camera_y = max(0, min(self.camera_y, max_cy))

    # --- lifecycle ---

    def _set_active_student_profile(self, student_id):
        """set current profile + rotate active session when profile changes"""
        clean_id = sanitize_student_id(student_id)
        if hasattr(self.game, 'set_current_student'):
            self.game.set_current_student(clean_id)
        else:
            self.game.current_student_id = clean_id
        self.student_id = clean_id
        self.stats = self.game.db.get_student_stats(clean_id)

    def _refresh_profiles(self):
        self.profile_list = self.game.db.get_profiles()
        if not self.profile_list:
            self.game.db.create_profile(config.DEFAULT_STUDENT_ID)
            self.profile_list = self.game.db.get_profiles()

        idx = 0
        for i, row in enumerate(self.profile_list):
            if row['student_id'] == self.student_id:
                idx = i
                break
        self.profile_cursor = idx

    def enter(self):
        self.student_id = sanitize_student_id(
            getattr(self.game, 'current_student_id', config.DEFAULT_STUDENT_ID)
        )
        self._set_active_student_profile(self.student_id)
        self._refresh_profiles()
        self.stats = self.game.db.get_student_stats(self.student_id)
        self.player = Player(self.saved_x, self.saved_y)
        self.interaction_prompt = None
        self.editing_student = False
        self.creating_profile = False
        # snap camera to player immediately when entering
        self.camera_x, self.camera_y = self._camera_target()
        self._clamp_camera()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and self.editing_student:
            if self.creating_profile:
                if event.key == pygame.K_RETURN:
                    candidate = sanitize_student_id(self.student_input)
                    self.game.db.create_profile(candidate)
                    self._set_active_student_profile(candidate)
                    self._refresh_profiles()
                    self.flash_message = f'Profile created: {candidate}'
                    self.flash_until = time.time() + 2.0
                    self.editing_student = False
                    self.creating_profile = False
                elif event.key == pygame.K_ESCAPE:
                    self.creating_profile = False
                    self.student_input = ''
                elif event.key == pygame.K_BACKSPACE:
                    self.student_input = self.student_input[:-1]
                elif event.unicode and event.unicode.isprintable() and len(self.student_input) < 24:
                    self.student_input += event.unicode
            else:
                if event.key == pygame.K_RETURN and self.profile_list:
                    selected = self.profile_list[self.profile_cursor]['student_id']
                    self._set_active_student_profile(selected)
                    self.flash_message = f'Profile selected: {selected}'
                    self.flash_until = time.time() + 1.8
                    self.editing_student = False
                elif event.key == pygame.K_ESCAPE:
                    self.editing_student = False
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self.profile_cursor = max(0, self.profile_cursor - 1)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.profile_cursor = min(max(0, len(self.profile_list) - 1), self.profile_cursor + 1)
                elif event.key == pygame.K_n:
                    self.creating_profile = True
                    self.student_input = ''
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                self.editing_student = True
                self.creating_profile = False
                self._refresh_profiles()
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.keys_held['up'] = True
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.keys_held['down'] = True
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.keys_held['left'] = True
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.keys_held['right'] = True
            elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                self.shift_held = True
            elif event.key in (pygame.K_e, pygame.K_SPACE):
                if self.interaction_prompt:
                    # save where we are before switching screens
                    self.saved_x = self.player.tile_x
                    self.saved_y = self.player.tile_y
                    self._set_active_student_profile(self.student_id)
                    zone_map = {
                        'barangay_captain': 'barangay',
                        'recipe_game': 'recipe',
                        'synonym_antonym': 'synonym_antonym',
                    }
                    target = zone_map.get(self.interaction_prompt)
                    if target:
                        self.next_state = target

        elif event.type == pygame.KEYUP:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.keys_held['up'] = False
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.keys_held['down'] = False
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.keys_held['left'] = False
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.keys_held['right'] = False
            elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                self.shift_held = False

    def update(self, dt):
        if self.editing_student:
            return

        dx, dy = 0, 0
        if self.keys_held['up']:
            dy = -1
        elif self.keys_held['down']:
            dy = 1
        elif self.keys_held['left']:
            dx = -1
        elif self.keys_held['right']:
            dx = 1

        self.player.move(dx, dy, self.tilemap, self.shift_held)
        self.player.update(dt)  # advance tile-to-tile animation

        # move camera towards player smoothly
        target_x, target_y = self._camera_target()
        self.camera_x = int(self.camera_x + (target_x - self.camera_x) * 0.1)
        self.camera_y = int(self.camera_y + (target_y - self.camera_y) * 0.1)

        # keep camera inside map
        self._clamp_camera()

        # check if player is near a game zone
        new_prompt = self.tilemap.check_interaction(self.player.tile_x,
                                                    self.player.tile_y)
        if new_prompt != self.interaction_prompt:
            self.prompt_animation_start = time.time()
        self.interaction_prompt = new_prompt
        self.prompt_timer += dt

    def _draw_student_box(self, screen):
        tag = self.game.font_small.render(
            f'PLAYER ID: {self.student_id}  |  TAB: PROFILES', True, config.WHITE)
        sh = self.game.font_small.render(
            f'PLAYER ID: {self.student_id}  |  TAB: PROFILES', True, config.BLACK)
        rect = tag.get_rect(topleft=(20, 55))
        box = rect.inflate(22, 14)
        pygame.draw.rect(screen, config.BLACK, box.move(2, 2))
        pygame.draw.rect(screen, (35, 35, 50), box)
        pygame.draw.rect(screen, config.GREEN, box, 3)
        screen.blit(sh, rect.move(1, 1))
        screen.blit(tag, rect)

        if self.flash_message and time.time() < self.flash_until:
            f = self.game.font_small.render(self.flash_message, True, config.YELLOW)
            screen.blit(f, (22, 95))

    def _draw_student_modal(self, screen):
        overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        modal = pygame.Rect(config.SCREEN_WIDTH // 2 - 420, config.SCREEN_HEIGHT // 2 - 220, 840, 440)
        self.draw_retro_box(screen, modal, (25, 35, 60), config.YELLOW, border_width=5)

        if self.creating_profile:
            title = self.game.font_large.render('CREATE NEW PROFILE', True, config.YELLOW)
            screen.blit(title, title.get_rect(center=(config.SCREEN_WIDTH // 2, modal.y + 60)))

            input_rect = pygame.Rect(modal.x + 70, modal.y + 130, modal.width - 140, 68)
            self.draw_retro_box(screen, input_rect, config.WHITE, config.BLUE, border_width=4, shadow=False)
            cursor = '|' if int(time.time() * 2) % 2 == 0 else ''
            text = self.game.font_medium.render(self.student_input + cursor, True, config.BLACK)
            screen.blit(text, text.get_rect(midleft=(input_rect.x + 12, input_rect.centery)))

            note = self.game.font_small.render('Type profile name, ENTER to create, ESC to go back', True, config.WHITE)
            screen.blit(note, note.get_rect(center=(config.SCREEN_WIDTH // 2, modal.y + 220)))
            return

        title = self.game.font_large.render('SELECT PROFILE', True, config.YELLOW)
        screen.blit(title, title.get_rect(center=(config.SCREEN_WIDTH // 2, modal.y + 52)))

        list_box = pygame.Rect(modal.x + 55, modal.y + 95, modal.width - 110, 275)
        self.draw_retro_box(screen, list_box, (15, 20, 35), config.BLUE, border_width=4, shadow=False)

        if not self.profile_list:
            empty = self.game.font_medium.render('No profiles yet. Press N to create one.', True, config.WHITE)
            screen.blit(empty, empty.get_rect(center=list_box.center))
        else:
            max_rows = 8
            start_idx = max(0, min(self.profile_cursor - max_rows // 2, max(0, len(self.profile_list) - max_rows)))
            end_idx = min(len(self.profile_list), start_idx + max_rows)
            y = list_box.y + 20
            for idx in range(start_idx, end_idx):
                row = self.profile_list[idx]
                active = idx == self.profile_cursor
                row_rect = pygame.Rect(list_box.x + 14, y, list_box.width - 28, 30)
                fill = config.BLUE if active else (35, 35, 55)
                border = config.YELLOW if active else config.DARK_GRAY
                self.draw_retro_box(screen, row_rect, fill, border, border_width=2, shadow=False)
                label = self.game.font_small.render(row['student_id'], True, config.WHITE)
                screen.blit(label, (row_rect.x + 10, row_rect.y + 6))
                y += 34

        hint = self.game.font_small.render(
            'UP/DOWN: Choose  |  ENTER: Select  |  N: New Profile  |  ESC: Close',
            True,
            config.WHITE,
        )
        screen.blit(hint, hint.get_rect(center=(config.SCREEN_WIDTH // 2, modal.y + 400)))

    def draw(self, screen):
        screen.fill((135, 206, 235))
        self.tilemap.draw_back(screen, self.camera_x, self.camera_y)
        self.player.draw(screen, self.camera_x, self.camera_y)
        self.tilemap.draw_front(screen, self.camera_x, self.camera_y)
        self.tilemap.draw_labels(screen, self.camera_x, self.camera_y,
                                 self.game.font_small)

        # show the press space prompt
        if self.interaction_prompt and not self.editing_student:
            anim_t = time.time() - self.prompt_animation_start
            if anim_t < 0.3:
                scale = min(1.0, (0.5 + anim_t / 0.3 * 0.5) * 1.1)
            elif anim_t < 0.4:
                scale = 1.1 - (anim_t - 0.3) / 0.1 * 0.1
            else:
                scale = 1.0 + math.sin((anim_t - 0.4) * 2) * 0.03

            zone_names = {
                'barangay_captain': 'Barangay Captain Simulator',
                'recipe_game': 'Recipe Game',
                'synonym_antonym': 'Word Match Game',
            }
            prompt_str = f"Press SPACE to enter {zone_names.get(self.interaction_prompt, '')}"
            text = self.game.font_medium.render(prompt_str, True, config.WHITE)
            text_shadow = self.game.font_medium.render(prompt_str, True, config.BLACK)

            sw = int((text.get_width() + 40) * scale)
            sh = int((text.get_height() + 20) * scale)
            cx = config.SCREEN_WIDTH // 2
            cy = config.SCREEN_HEIGHT - 100
            bg_rect = pygame.Rect(cx - sw // 2, cy - sh // 2, sw, sh)

            pygame.draw.rect(screen, config.BLACK, bg_rect.move(3, 3))
            pygame.draw.rect(screen, config.BLUE, bg_rect)
            pygame.draw.rect(screen, config.YELLOW, bg_rect, 4)

            tr = text.get_rect(center=bg_rect.center)
            screen.blit(text_shadow, tr.move(2, 2))
            screen.blit(text, tr)

        # controls hint at the top
        ctrl = self.game.font_small.render(
            'Arrow Keys / WASD: Move | SPACE: Interact | TAB: Profiles',
            True, config.WHITE)
        ctrl_s = self.game.font_small.render(
            'Arrow Keys / WASD: Move | SPACE: Interact | TAB: Profiles',
            True, config.BLACK)
        cr = ctrl.get_rect(center=(config.SCREEN_WIDTH // 2, 30))
        bg = cr.inflate(20, 10)
        pygame.draw.rect(screen, config.BLACK, bg.move(2, 2))
        pygame.draw.rect(screen, (50, 50, 50), bg)
        pygame.draw.rect(screen, config.WHITE, bg, 2)
        screen.blit(ctrl_s, cr.move(1, 1))
        screen.blit(ctrl, cr)

        self._draw_student_box(screen)

        # gems counter
        stxt = self.game.font_medium.render(
            f"Total Gems: {self.stats['total_gems']}", True, config.YELLOW)
        sshd = self.game.font_medium.render(
            f"Total Gems: {self.stats['total_gems']}", True, config.BLACK)
        sr = stxt.get_rect(topright=(config.SCREEN_WIDTH - 20, 20))
        sbg = sr.inflate(20, 10)
        pygame.draw.rect(screen, config.BLACK, sbg.move(2, 2))
        pygame.draw.rect(screen, (50, 50, 50), sbg)
        pygame.draw.rect(screen, config.YELLOW, sbg, 3)
        screen.blit(sshd, sr.move(1, 1))
        screen.blit(stxt, sr)

        if self.editing_student:
            self._draw_student_modal(screen)


# Teacher Screen

class TeacherDashboardState(State):
    """password protected teacher control room.

    messy notes:
    - has 3 tabs: overview, leaderboard, question forge.
    - forge supports both keyboard + mouse interactions.
    - data refresh is centralized in refresh_data().
    """

    def __init__(self, game):
        super().__init__(game)
        self.font = pygame.font.Font(None, config.FONT_MEDIUM)
        self.small_font = pygame.font.Font(None, config.FONT_SMALL)
        self.title_font = pygame.font.Font(None, config.FONT_LARGE)
        self.report = None
        self.authenticated = False
        self.password_input = ''

        self.tab = 'overview'
        self.analytics = {}
        self.leaderboard = []
        self.question_counts = []
        self.recent_questions = []
        self.profile_rows = []
        self.selected_profile_idx = 0
        self.selected_profile_modules = []
        self.selected_profile_runs = []
        self.account_editor = None

        self.status_message = ''
        self.status_color = config.WHITE
        self.status_until = 0

        self.forge_game_index = 0
        self.forge_lang_index = 0
        self.forge_mode_index = 0
        self.difficulty_modes = []
        self.forge_mode_editor = None
        self.forge_fields = [
            ('prompt_text', 'Context / Passage (optional)'),
            ('question_text', 'Question Text'),
            ('choice_1', 'Choice 1'),
            ('choice_2', 'Choice 2'),
            ('choice_3', 'Choice 3'),
            ('choice_4', 'Choice 4 (optional)'),
            ('correct_answer', 'Correct Answer Number (1-4)'),
        ]
        self.forge_active_field = 0
        self.forge_form = {}
        self.tab_rects = {}
        self.forge_field_rects = []
        self.forge_game_prev_rect = None
        self.forge_game_next_rect = None
        self.forge_lang_prev_rect = None
        self.forge_lang_next_rect = None
        self.forge_mode_prev_rect = None
        self.forge_mode_next_rect = None
        self.forge_mode_create_rect = None
        self.forge_mode_rename_rect = None
        self.forge_save_rect = None
        self.leaderboard_profile_rects = []
        self.leaderboard_btn_create = None
        self.leaderboard_btn_rename = None
        self.leaderboard_btn_delete = None
        self._reset_forge_form()

    def _reset_forge_form(self):
        self.forge_form = {
            'prompt_text': '',
            'question_text': '',
            'choice_1': '',
            'choice_2': '',
            'choice_3': '',
            'choice_4': '',
            'correct_answer': '1',
        }
        self.forge_active_field = 0

    def _current_game_key(self):
        return QUESTION_GAME_KEYS[self.forge_game_index]

    def _current_language(self):
        return ['english', 'tagalog', 'bisaya'][self.forge_lang_index]

    def _current_difficulty_mode(self):
        if not self.difficulty_modes:
            self._refresh_difficulty_slot()
        if not self.difficulty_modes:
            return 'General'
        self.forge_mode_index = max(0, min(self.forge_mode_index, len(self.difficulty_modes) - 1))
        return self.difficulty_modes[self.forge_mode_index]

    def _refresh_difficulty_slot(self):
        self.difficulty_modes = self.game.db.get_difficulty_modes()
        if not self.difficulty_modes:
            self.difficulty_modes = ['General']

        slot_mode = self.game.db.get_selected_difficulty_mode(
            self._current_game_key(),
            self._current_language(),
        )

        if slot_mode in self.difficulty_modes:
            self.forge_mode_index = self.difficulty_modes.index(slot_mode)
            return

        self.forge_mode_index = 0
        fallback = self.difficulty_modes[0]
        self.game.db.set_selected_difficulty_mode(
            self._current_game_key(),
            self._current_language(),
            fallback,
        )

    def _cycle_difficulty_mode(self, direction):
        if not self.difficulty_modes:
            self._refresh_difficulty_slot()
        if not self.difficulty_modes:
            return

        self.forge_mode_index = (self.forge_mode_index + direction) % len(self.difficulty_modes)
        self.game.db.set_selected_difficulty_mode(
            self._current_game_key(),
            self._current_language(),
            self._current_difficulty_mode(),
        )
        self._refresh_recent_questions()

    def _start_mode_editor(self, mode):
        if mode == 'create':
            self.forge_mode_editor = {
                'mode': 'create',
                'target': None,
                'value': '',
            }
            return

        current_mode = self._current_difficulty_mode()
        self.forge_mode_editor = {
            'mode': 'rename',
            'target': current_mode,
            'value': current_mode,
        }

    def _commit_mode_editor(self):
        if not self.forge_mode_editor:
            return

        try:
            if self.forge_mode_editor['mode'] == 'create':
                created = self.game.db.create_difficulty_mode(self.forge_mode_editor['value'])
                self.game.db.set_selected_difficulty_mode(
                    self._current_game_key(),
                    self._current_language(),
                    created,
                )
                self._set_status(f'Difficulty mode created: {created}', config.GREEN)
            else:
                old_mode = self.forge_mode_editor['target']
                renamed = self.game.db.rename_difficulty_mode(old_mode, self.forge_mode_editor['value'])
                self._set_status(f'Difficulty mode renamed: {old_mode} -> {renamed}', config.GREEN)

            self.refresh_data()
        except Exception as exc:
            self._set_status(f'Mode update failed: {exc}', config.RED)

        self.forge_mode_editor = None

    def _refresh_recent_questions(self):
        self.recent_questions = self.game.db.get_custom_questions(
            game_key=self._current_game_key(),
            language=self._current_language(),
            difficulty_mode=self._current_difficulty_mode(),
        )[:5]

    def refresh_data(self):
        self.report = self.game.db.generate_report()
        self.analytics = self.report.get('analytics', self.game.db.get_teacher_metrics())
        self.leaderboard = self.report.get('leaderboard', self.game.db.get_leaderboard(limit=20))
        self.question_counts = self.game.db.get_custom_question_counts(include_difficulty=True)
        self._refresh_difficulty_slot()
        self._refresh_recent_questions()
        self._refresh_profile_tracking()

    def _refresh_profile_tracking(self):
        self.profile_rows = self.game.db.get_student_profiles_with_metrics()
        if not self.profile_rows:
            self.selected_profile_idx = 0
            self.selected_profile_modules = []
            self.selected_profile_runs = []
            return

        self.selected_profile_idx = max(0, min(self.selected_profile_idx, len(self.profile_rows) - 1))
        self._refresh_selected_profile_details()

    def _selected_profile_id(self):
        if not self.profile_rows:
            return None
        return self.profile_rows[self.selected_profile_idx]['student_id']

    def _refresh_selected_profile_details(self):
        sid = self._selected_profile_id()
        if not sid:
            self.selected_profile_modules = []
            self.selected_profile_runs = []
            return
        self.selected_profile_modules = self.game.db.get_student_module_performance(sid)
        self.selected_profile_runs = self.game.db.get_student_recent_runs(sid, limit=12)

    def _start_account_editor(self, mode):
        if mode == 'create':
            self.account_editor = {
                'mode': 'create',
                'target': None,
                'value': '',
            }
            return

        sid = self._selected_profile_id()
        if not sid:
            return
        self.account_editor = {
            'mode': 'rename',
            'target': sid,
            'value': sid,
        }

    def _commit_account_editor(self):
        if not self.account_editor:
            return

        mode = self.account_editor['mode']
        new_value = sanitize_student_id(self.account_editor['value'])

        try:
            if mode == 'create':
                created = self.game.db.create_profile(new_value)
                self._set_status(f'Profile created: {created}', config.GREEN)
                self.refresh_data()
                for i, row in enumerate(self.profile_rows):
                    if row['student_id'] == created:
                        self.selected_profile_idx = i
                        break
                self._refresh_selected_profile_details()
            else:
                old_id = self.account_editor['target']
                renamed = self.game.db.rename_profile(old_id, new_value)
                if getattr(self.game, 'current_student_id', '') == old_id:
                    if hasattr(self.game, 'set_current_student'):
                        self.game.set_current_student(renamed)
                    else:
                        self.game.current_student_id = renamed
                self._set_status(f'Profile renamed: {old_id} -> {renamed}', config.GREEN)
                self.refresh_data()
                for i, row in enumerate(self.profile_rows):
                    if row['student_id'] == renamed:
                        self.selected_profile_idx = i
                        break
                self._refresh_selected_profile_details()
        except Exception as exc:
            self._set_status(f'Account update failed: {exc}', config.RED)

        self.account_editor = None

    def _handle_leaderboard_event(self, event):
        if self.account_editor:
            if event.key == pygame.K_RETURN:
                self._commit_account_editor()
            elif event.key == pygame.K_ESCAPE:
                self.account_editor = None
            elif event.key == pygame.K_BACKSPACE:
                self.account_editor['value'] = self.account_editor['value'][:-1]
            elif event.unicode and event.unicode.isprintable() and len(self.account_editor['value']) < 24:
                self.account_editor['value'] += event.unicode
            return

        if event.key in (pygame.K_UP, pygame.K_w):
            self.selected_profile_idx = max(0, self.selected_profile_idx - 1)
            self._refresh_selected_profile_details()
            return
        if event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected_profile_idx = min(max(0, len(self.profile_rows) - 1), self.selected_profile_idx + 1)
            self._refresh_selected_profile_details()
            return
        if event.key == pygame.K_n:
            self._start_account_editor('create')
            return
        if event.key == pygame.K_r:
            self._start_account_editor('rename')
            return
        if event.key == pygame.K_DELETE:
            self._delete_selected_profile()
            return

    def _delete_selected_profile(self):
        sid = self._selected_profile_id()
        if not sid:
            return
        try:
            self.game.db.delete_profile(sid)
            if getattr(self.game, 'current_student_id', '') == sid:
                fallback = config.DEFAULT_STUDENT_ID
                self.game.db.create_profile(fallback)
                if hasattr(self.game, 'set_current_student'):
                    self.game.set_current_student(fallback)
                else:
                    self.game.current_student_id = fallback
            self._set_status(f'Profile deleted: {sid}', config.ORANGE)
            self.refresh_data()
        except Exception as exc:
            self._set_status(f'Cannot delete profile: {exc}', config.RED)

    def _set_status(self, message, color=config.WHITE):
        self.status_message = message
        self.status_color = color
        self.status_until = time.time() + 2.5

    def _handle_mouse_click(self, pos):
        """handle clickable UI in teacher mode"""
        for tab_name, rect in self.tab_rects.items():
            if rect and rect.collidepoint(pos):
                self.tab = tab_name
                return

        if self.tab == 'leaderboard':
            if self.account_editor:
                return

            if self.leaderboard_btn_create and self.leaderboard_btn_create.collidepoint(pos):
                self._start_account_editor('create')
                return
            if self.leaderboard_btn_rename and self.leaderboard_btn_rename.collidepoint(pos):
                self._start_account_editor('rename')
                return
            if self.leaderboard_btn_delete and self.leaderboard_btn_delete.collidepoint(pos):
                self._delete_selected_profile()
                return

            for idx, rect in self.leaderboard_profile_rects:
                if rect.collidepoint(pos):
                    self.selected_profile_idx = idx
                    self._refresh_selected_profile_details()
                    return

            return

        if self.tab != 'forge':
            return

        if self.forge_mode_editor:
            return

        if self.forge_game_prev_rect and self.forge_game_prev_rect.collidepoint(pos):
            self._cycle_game(-1)
            return
        if self.forge_game_next_rect and self.forge_game_next_rect.collidepoint(pos):
            self._cycle_game(1)
            return
        if self.forge_lang_prev_rect and self.forge_lang_prev_rect.collidepoint(pos):
            self._cycle_language(-1)
            return
        if self.forge_lang_next_rect and self.forge_lang_next_rect.collidepoint(pos):
            self._cycle_language(1)
            return
        if self.forge_mode_prev_rect and self.forge_mode_prev_rect.collidepoint(pos):
            self._cycle_difficulty_mode(-1)
            return
        if self.forge_mode_next_rect and self.forge_mode_next_rect.collidepoint(pos):
            self._cycle_difficulty_mode(1)
            return
        if self.forge_mode_create_rect and self.forge_mode_create_rect.collidepoint(pos):
            self._start_mode_editor('create')
            return
        if self.forge_mode_rename_rect and self.forge_mode_rename_rect.collidepoint(pos):
            self._start_mode_editor('rename')
            return
        if self.forge_save_rect and self.forge_save_rect.collidepoint(pos):
            self._save_forge_question()
            return

        for idx, rect in enumerate(self.forge_field_rects):
            if rect.collidepoint(pos):
                self.forge_active_field = idx
                return

    def enter(self):
        self.authenticated = False
        self.password_input = ''
        self.tab = 'overview'
        self.account_editor = None
        self.forge_mode_editor = None
        self.refresh_data()
        self._reset_forge_form()

    def _handle_auth_event(self, event):
        if event.key == pygame.K_RETURN:
            if self.password_input == config.TEACHER_PASSWORD:
                self.authenticated = True
                self.refresh_data()
            else:
                self.password_input = ''
                self._set_status('Wrong password.', config.RED)
        elif event.key == pygame.K_ESCAPE:
            self.next_state = 'menu'
        elif event.key == pygame.K_BACKSPACE:
            self.password_input = self.password_input[:-1]
        elif event.unicode and event.unicode.isprintable() and len(self.password_input) < 40:
            self.password_input += event.unicode

    def _cycle_game(self, direction):
        self.forge_game_index = (self.forge_game_index + direction) % len(QUESTION_GAME_KEYS)
        self._refresh_difficulty_slot()
        self._refresh_recent_questions()

    def _cycle_language(self, direction):
        self.forge_lang_index = (self.forge_lang_index + direction) % 3
        self._refresh_difficulty_slot()
        self._refresh_recent_questions()

    def _save_forge_question(self):
        try:
            question_text = self.forge_form['question_text'].strip()
            if not question_text:
                raise ValueError('Question text is required.')

            choices = [
                self.forge_form['choice_1'],
                self.forge_form['choice_2'],
                self.forge_form['choice_3'],
                self.forge_form['choice_4'],
            ]
            correct_idx = int(self.forge_form['correct_answer'].strip() or '1') - 1

            self.game.db.add_custom_question(
                game_key=self._current_game_key(),
                language=self._current_language(),
                difficulty_mode=self._current_difficulty_mode(),
                prompt_text=self.forge_form['prompt_text'],
                question_text=question_text,
                choices=choices,
                correct_index=correct_idx,
            )
            self._set_status(
                f'Question saved to "{self._current_difficulty_mode()}" mode.',
                config.GREEN,
            )
            self._reset_forge_form()
            self.refresh_data()
        except Exception as exc:
            self._set_status(f'Cannot save: {exc}', config.RED)

    def _handle_forge_event(self, event):
        if self.forge_mode_editor:
            if event.key == pygame.K_RETURN:
                self._commit_mode_editor()
            elif event.key == pygame.K_ESCAPE:
                self.forge_mode_editor = None
            elif event.key == pygame.K_BACKSPACE:
                self.forge_mode_editor['value'] = self.forge_mode_editor['value'][:-1]
            elif event.unicode and event.unicode.isprintable() and len(self.forge_mode_editor['value']) < 40:
                self.forge_mode_editor['value'] += event.unicode
            return

        if event.key == pygame.K_LEFT:
            self._cycle_game(-1)
            return
        if event.key == pygame.K_RIGHT:
            self._cycle_game(1)
            return
        if event.key == pygame.K_PAGEUP:
            self._cycle_language(-1)
            return
        if event.key == pygame.K_PAGEDOWN:
            self._cycle_language(1)
            return
        if event.key == pygame.K_LEFTBRACKET:
            self._cycle_difficulty_mode(-1)
            return
        if event.key == pygame.K_RIGHTBRACKET:
            self._cycle_difficulty_mode(1)
            return
        if event.key == pygame.K_F7:
            self._start_mode_editor('create')
            return
        if event.key == pygame.K_F8:
            self._start_mode_editor('rename')
            return
        if event.key == pygame.K_UP:
            self.forge_active_field = (self.forge_active_field - 1) % len(self.forge_fields)
            return
        if event.key == pygame.K_DOWN:
            self.forge_active_field = (self.forge_active_field + 1) % len(self.forge_fields)
            return
        if event.key == pygame.K_TAB:
            self.forge_active_field = (self.forge_active_field + 1) % len(self.forge_fields)
            return
        if event.key == pygame.K_F6:
            self._save_forge_question()
            return

        key_name = self.forge_fields[self.forge_active_field][0]
        if event.key == pygame.K_RETURN:
            if self.forge_active_field == len(self.forge_fields) - 1:
                self._save_forge_question()
            else:
                self.forge_active_field += 1
            return
        if event.key == pygame.K_BACKSPACE:
            self.forge_form[key_name] = self.forge_form[key_name][:-1]
            return
        if key_name == 'correct_answer' and event.unicode in ('1', '2', '3', '4'):
            self.forge_form[key_name] = event.unicode
            return
        if key_name == 'correct_answer' and event.unicode and event.unicode.isdigit():
            return
        if event.unicode and event.unicode.isprintable() and len(self.forge_form[key_name]) < 220:
            self.forge_form[key_name] += event.unicode

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.authenticated:
                self._handle_mouse_click(event.pos)
            return

        if event.type != pygame.KEYDOWN:
            return

        if not self.authenticated:
            self._handle_auth_event(event)
            return

        if event.key == pygame.K_ESCAPE:
            self.next_state = 'menu'
            return
        if event.key == pygame.K_F5:
            self.refresh_data()
            self._set_status('Dashboard refreshed.', config.YELLOW)
            return

        # function key shortcuts stay safe even while typing numbers in forms.
        if event.key == pygame.K_F1:
            self.tab = 'overview'
            return
        if event.key == pygame.K_F2:
            self.tab = 'leaderboard'
            return
        if event.key == pygame.K_F3:
            self.tab = 'forge'
            return

        # handle form/editing states first so number keys (ex: correct answer = 2)
        # do not accidentally switch tabs.
        if self.tab == 'forge':
            self._handle_forge_event(event)
            return

        if self.tab == 'leaderboard':
            self._handle_leaderboard_event(event)
            if self.account_editor:
                return

        if event.key == pygame.K_1:
            self.tab = 'overview'
            return
        if event.key == pygame.K_2:
            self.tab = 'leaderboard'
            return
        if event.key == pygame.K_3:
            self.tab = 'forge'
            return

    def _draw_tab_button(self, screen, rect, text, active, base_color, tab_name):
        fill = base_color if active else (45, 45, 60)
        border = config.YELLOW if active else config.LIGHT_GRAY
        self.draw_retro_box(screen, rect, fill, border, border_width=3)
        txt = self.small_font.render(text, True, config.WHITE)
        screen.blit(txt, txt.get_rect(center=rect.center))
        self.tab_rects[tab_name] = rect

    def _draw_overview(self, screen):
        cards = [
            ('Sessions', str(self.analytics.get('total_sessions', 0))),
            ('Active Students', str(self.analytics.get('active_students', 0))),
            ('Games Logged', str(self.analytics.get('total_logged_games', 0))),
            ('Avg Accuracy', f"{self.analytics.get('avg_accuracy', 0):.1f}%"),
        ]

        x = 40
        for label, value in cards:
            card = pygame.Rect(x, 120, 260, 90)
            self.draw_retro_box(screen, card, (28, 52, 82), config.YELLOW, border_width=3)
            lt = self.small_font.render(label, True, config.LIGHT_BLUE)
            vt = self.font.render(value, True, config.WHITE)
            screen.blit(lt, (card.x + 12, card.y + 8))
            screen.blit(vt, (card.x + 12, card.y + 38))
            x += 280

        left = pygame.Rect(40, 240, 560, 420)
        right = pygame.Rect(640, 240, 560, 420)
        self.draw_retro_box(screen, left, (22, 32, 56), config.BLUE, border_width=3)
        self.draw_retro_box(screen, right, (22, 32, 56), config.ORANGE, border_width=3)

        lt = self.font.render('Module Performance', True, config.YELLOW)
        rt = self.font.render('Student Performance', True, config.YELLOW)
        screen.blit(lt, (left.x + 14, left.y + 12))
        screen.blit(rt, (right.x + 14, right.y + 12))

        y = left.y + 58
        for row in self.analytics.get('module_breakdown', [])[:8]:
            line = (
                f"{row['module']}: plays {row['plays']} | "
                f"avg {row['avg_accuracy']:.1f}% | best {row['best_accuracy']:.1f}%"
            )
            txt = self.small_font.render(line, True, config.WHITE)
            screen.blit(txt, (left.x + 14, y))
            y += 34

        y = right.y + 58
        for row in self.analytics.get('student_breakdown', [])[:10]:
            line = (
                f"{row['student_id']}: {row['games_played']} games | "
                f"avg {row['avg_accuracy']:.1f}% | pts {row['total_points']}"
            )
            txt = self.small_font.render(line, True, config.WHITE)
            screen.blit(txt, (right.x + 14, y))
            y += 32

    def _draw_leaderboard(self, screen):
        left = pygame.Rect(40, 120, 780, config.SCREEN_HEIGHT - 180)
        right = pygame.Rect(840, 120, config.SCREEN_WIDTH - 880, config.SCREEN_HEIGHT - 180)
        self.draw_retro_box(screen, left, (28, 28, 44), config.PURPLE, border_width=4)
        self.draw_retro_box(screen, right, (24, 36, 58), config.YELLOW, border_width=4)

        self.leaderboard_profile_rects = []
        self.leaderboard_btn_create = None
        self.leaderboard_btn_rename = None
        self.leaderboard_btn_delete = None

        title = self.font.render('STUDENT TRACKER + LEADERBOARD', True, config.YELLOW)
        screen.blit(title, (left.x + 14, left.y + 14))

        header = self.small_font.render('PROFILE                 GAMES   AVG%   BEST%   GEMS', True, config.LIGHT_BLUE)
        screen.blit(header, (left.x + 16, left.y + 56))

        visible = 12
        if self.profile_rows:
            start_idx = max(0, min(self.selected_profile_idx - visible // 2, max(0, len(self.profile_rows) - visible)))
            end_idx = min(len(self.profile_rows), start_idx + visible)
            y = left.y + 88
            for idx in range(start_idx, end_idx):
                row = self.profile_rows[idx]
                active = idx == self.selected_profile_idx
                row_rect = pygame.Rect(left.x + 12, y - 2, left.width - 24, 31)
                fill = (70, 45, 105) if active else (38, 38, 56)
                border = config.YELLOW if active else config.DARK_GRAY
                self.draw_retro_box(screen, row_rect, fill, border, border_width=2, shadow=False)

                line = (
                    f"{row['student_id'][:22]:<22}   "
                    f"{row['games_played']:>3}   "
                    f"{row['avg_accuracy']:>5.1f}   "
                    f"{row['best_accuracy']:>5.1f}   "
                    f"{row['total_gems']:>4}"
                )
                color = config.WHITE if active else config.LIGHT_GRAY
                txt = self.small_font.render(line, True, color)
                screen.blit(txt, (left.x + 20, y + 3))
                self.leaderboard_profile_rects.append((idx, row_rect))
                y += 34

        btn_y = left.bottom - 84
        self.leaderboard_btn_create = pygame.Rect(left.x + 16, btn_y, 120, 34)
        self.leaderboard_btn_rename = pygame.Rect(left.x + 146, btn_y, 120, 34)
        self.leaderboard_btn_delete = pygame.Rect(left.x + 276, btn_y, 120, 34)

        self.draw_retro_box(screen, self.leaderboard_btn_create, config.GREEN, config.YELLOW, border_width=3, shadow=False)
        self.draw_retro_box(screen, self.leaderboard_btn_rename, config.BLUE, config.YELLOW, border_width=3, shadow=False)
        self.draw_retro_box(screen, self.leaderboard_btn_delete, config.RED, config.YELLOW, border_width=3, shadow=False)

        c_text = self.small_font.render('CREATE', True, config.WHITE)
        r_text = self.small_font.render('RENAME', True, config.WHITE)
        d_text = self.small_font.render('DELETE', True, config.WHITE)
        screen.blit(c_text, c_text.get_rect(center=self.leaderboard_btn_create.center))
        screen.blit(r_text, r_text.get_rect(center=self.leaderboard_btn_rename.center))
        screen.blit(d_text, d_text.get_rect(center=self.leaderboard_btn_delete.center))

        controls = self.small_font.render(
            'Click row to select  |  Buttons or N/R/DEL keys for account actions',
            True,
            config.LIGHT_GRAY,
        )
        screen.blit(controls, (left.x + 16, left.bottom - 40))

        sid = self._selected_profile_id()
        right_title = self.font.render('INDIVIDUAL PERFORMANCE', True, config.YELLOW)
        screen.blit(right_title, (right.x + 14, right.y + 14))

        if sid:
            summary = next((r for r in self.profile_rows if r['student_id'] == sid), None)
            if summary:
                top = self.small_font.render(
                    f"Profile: {sid}  |  Games: {summary['games_played']}  |  Avg: {summary['avg_accuracy']:.1f}%",
                    True,
                    config.WHITE,
                )
                screen.blit(top, (right.x + 14, right.y + 56))
                top2 = self.small_font.render(
                    f"Best: {summary['best_accuracy']:.1f}%  |  Points: {summary['total_points']}  |  Last: {summary['last_played']}",
                    True,
                    config.LIGHT_BLUE,
                )
                screen.blit(top2, (right.x + 14, right.y + 84))

            mod_title = self.small_font.render('By Module', True, config.ORANGE)
            screen.blit(mod_title, (right.x + 14, right.y + 118))
            y = right.y + 146
            for row in self.selected_profile_modules[:5]:
                line = (
                    f"{row['module'][:22]:<22}  plays {row['plays']:>2}  "
                    f"avg {row['avg_accuracy']:>5.1f}%"
                )
                txt = self.small_font.render(line, True, config.WHITE)
                screen.blit(txt, (right.x + 14, y))
                y += 26

            recent_title = self.small_font.render('Recent Attempts', True, config.ORANGE)
            screen.blit(recent_title, (right.x + 14, y + 8))
            y += 36
            for row in self.selected_profile_runs[:8]:
                line = (
                    f"{row['module'][:16]:<16}  {row['score']:>2}/{row['max_score']:<2}  "
                    f"{(row['accuracy'] or 0):>5.1f}%  {LANGUAGE_LABELS.get(row.get('language', ''), '-')[:3]}"
                )
                txt = self.small_font.render(line, True, config.LIGHT_GRAY)
                screen.blit(txt, (right.x + 14, y))
                y += 24
        else:
            empty = self.small_font.render('No profile selected yet.', True, config.LIGHT_GRAY)
            screen.blit(empty, (right.x + 14, right.y + 70))

        if self.account_editor:
            overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 165))
            screen.blit(overlay, (0, 0))

            panel = pygame.Rect(config.SCREEN_WIDTH // 2 - 320, config.SCREEN_HEIGHT // 2 - 120, 640, 240)
            self.draw_retro_box(screen, panel, (16, 24, 42), config.YELLOW, border_width=5)
            mode_label = 'CREATE PROFILE' if self.account_editor['mode'] == 'create' else 'RENAME PROFILE'
            title = self.font.render(mode_label, True, config.YELLOW)
            screen.blit(title, title.get_rect(center=(config.SCREEN_WIDTH // 2, panel.y + 46)))

            input_box = pygame.Rect(panel.x + 36, panel.y + 92, panel.width - 72, 58)
            self.draw_retro_box(screen, input_box, config.WHITE, config.BLUE, border_width=4, shadow=False)
            cursor = '|' if int(time.time() * 2) % 2 == 0 else ''
            value = self.account_editor['value'] + cursor
            text = self.font.render(value, True, config.BLACK)
            screen.blit(text, text.get_rect(midleft=(input_box.x + 10, input_box.centery)))

            hint = self.small_font.render('ENTER: Save  |  ESC: Cancel', True, config.WHITE)
            screen.blit(hint, hint.get_rect(center=(config.SCREEN_WIDTH // 2, panel.y + 192)))

    def _draw_forge(self, screen):
        left = pygame.Rect(40, 120, 720, config.SCREEN_HEIGHT - 180)
        right = pygame.Rect(800, 120, config.SCREEN_WIDTH - 840, config.SCREEN_HEIGHT - 180)

        self.draw_retro_box(screen, left, (26, 24, 40), config.GREEN, border_width=4)
        self.draw_retro_box(screen, right, (22, 32, 56), config.YELLOW, border_width=4)

        self.forge_field_rects = []
        self.forge_game_prev_rect = None
        self.forge_game_next_rect = None
        self.forge_lang_prev_rect = None
        self.forge_lang_next_rect = None
        self.forge_mode_prev_rect = None
        self.forge_mode_next_rect = None
        self.forge_mode_create_rect = None
        self.forge_mode_rename_rect = None
        self.forge_save_rect = None

        gk = self._current_game_key()
        lang = self._current_language()
        title = self.font.render('QUESTION FORGE', True, config.YELLOW)
        screen.blit(title, (left.x + 16, left.y + 14))

        # clickable selector: game
        game_y = left.y + 52
        self.forge_game_prev_rect = pygame.Rect(left.x + 16, game_y, 44, 34)
        game_label_rect = pygame.Rect(left.x + 68, game_y, left.width - 136, 34)
        self.forge_game_next_rect = pygame.Rect(left.x + left.width - 60, game_y, 44, 34)

        self.draw_retro_box(screen, self.forge_game_prev_rect, config.BLUE, config.YELLOW,
                            border_width=3, shadow=False)
        self.draw_retro_box(screen, game_label_rect, (32, 56, 88), config.YELLOW,
                            border_width=3, shadow=False)
        self.draw_retro_box(screen, self.forge_game_next_rect, config.BLUE, config.YELLOW,
                            border_width=3, shadow=False)

        gp = self.small_font.render('<', True, config.WHITE)
        gn = self.small_font.render('>', True, config.WHITE)
        gl = self.small_font.render(f'Game: {QUESTION_GAME_LABELS[gk]}', True, config.WHITE)
        screen.blit(gp, gp.get_rect(center=self.forge_game_prev_rect.center))
        screen.blit(gn, gn.get_rect(center=self.forge_game_next_rect.center))
        screen.blit(gl, gl.get_rect(center=game_label_rect.center))

        # clickable selector: language
        lang_y = left.y + 92
        self.forge_lang_prev_rect = pygame.Rect(left.x + 16, lang_y, 44, 34)
        lang_label_rect = pygame.Rect(left.x + 68, lang_y, left.width - 136, 34)
        self.forge_lang_next_rect = pygame.Rect(left.x + left.width - 60, lang_y, 44, 34)

        self.draw_retro_box(screen, self.forge_lang_prev_rect, config.PURPLE, config.YELLOW,
                            border_width=3, shadow=False)
        self.draw_retro_box(screen, lang_label_rect, (54, 34, 74), config.YELLOW,
                            border_width=3, shadow=False)
        self.draw_retro_box(screen, self.forge_lang_next_rect, config.PURPLE, config.YELLOW,
                            border_width=3, shadow=False)

        lp = self.small_font.render('<', True, config.WHITE)
        ln = self.small_font.render('>', True, config.WHITE)
        ll = self.small_font.render(f'Language: {LANGUAGE_LABELS[lang]}', True, config.WHITE)
        screen.blit(lp, lp.get_rect(center=self.forge_lang_prev_rect.center))
        screen.blit(ln, ln.get_rect(center=self.forge_lang_next_rect.center))
        screen.blit(ll, ll.get_rect(center=lang_label_rect.center))

        # clickable selector: difficulty mode + mode manager tools
        mode_y = left.y + 132
        self.forge_mode_prev_rect = pygame.Rect(left.x + 16, mode_y, 44, 34)
        self.forge_mode_rename_rect = pygame.Rect(left.x + left.width - 112, mode_y, 96, 34)
        self.forge_mode_create_rect = pygame.Rect(self.forge_mode_rename_rect.x - 104, mode_y, 96, 34)
        self.forge_mode_next_rect = pygame.Rect(self.forge_mode_create_rect.x - 52, mode_y, 44, 34)
        mode_label_rect = pygame.Rect(
            left.x + 68,
            mode_y,
            self.forge_mode_next_rect.x - (left.x + 68) - 8,
            34,
        )

        self.draw_retro_box(screen, self.forge_mode_prev_rect, config.GREEN, config.YELLOW,
                            border_width=3, shadow=False)
        self.draw_retro_box(screen, mode_label_rect, (42, 72, 44), config.YELLOW,
                            border_width=3, shadow=False)
        self.draw_retro_box(screen, self.forge_mode_next_rect, config.GREEN, config.YELLOW,
                            border_width=3, shadow=False)
        self.draw_retro_box(screen, self.forge_mode_create_rect, config.BLUE, config.YELLOW,
                            border_width=3, shadow=False)
        self.draw_retro_box(screen, self.forge_mode_rename_rect, config.PURPLE, config.YELLOW,
                            border_width=3, shadow=False)

        mp = self.small_font.render('<', True, config.WHITE)
        mn = self.small_font.render('>', True, config.WHITE)
        mode_label = self._current_difficulty_mode()
        if len(mode_label) > 20:
            mode_label = mode_label[:17] + '...'
        ml = self.small_font.render(f'Difficulty: {mode_label}', True, config.WHITE)
        mc = self.small_font.render('NEW', True, config.WHITE)
        mr = self.small_font.render('RENAME', True, config.WHITE)
        screen.blit(mp, mp.get_rect(center=self.forge_mode_prev_rect.center))
        screen.blit(mn, mn.get_rect(center=self.forge_mode_next_rect.center))
        screen.blit(ml, ml.get_rect(center=mode_label_rect.center))
        screen.blit(mc, mc.get_rect(center=self.forge_mode_create_rect.center))
        screen.blit(mr, mr.get_rect(center=self.forge_mode_rename_rect.center))

        controls = self.small_font.render(
            'Click fields to edit | F6 save | [ ] switch difficulty | F7/F8 mode tools',
            True,
            config.LIGHT_GRAY,
        )
        screen.blit(controls, (left.x + 16, left.y + 176))

        self.forge_save_rect = pygame.Rect(left.x + left.width - 180, left.y + 170, 160, 40)
        self.draw_retro_box(screen, self.forge_save_rect, config.GREEN, config.YELLOW,
                            border_width=3, shadow=False)
        save_text = self.small_font.render('SAVE', True, config.WHITE)
        screen.blit(save_text, save_text.get_rect(center=self.forge_save_rect.center))

        y = left.y + 226
        for i, (field_name, field_label) in enumerate(self.forge_fields):
            field_rect = pygame.Rect(left.x + 16, y, left.width - 32, 60)
            active = i == self.forge_active_field
            fill = (255, 255, 255) if active else (230, 230, 230)
            border = config.ORANGE if active else config.DARK_GRAY
            self.draw_retro_box(screen, field_rect, fill, border, border_width=3, shadow=False)
            self.forge_field_rects.append(field_rect)

            label = self.small_font.render(field_label, True, config.DARK_GRAY)
            value_text = self.forge_form[field_name]
            if active and int(time.time() * 2) % 2 == 0:
                value_text += '|'
            value = self.small_font.render(value_text, True, config.BLACK)
            screen.blit(label, (field_rect.x + 10, field_rect.y + 6))
            screen.blit(value, (field_rect.x + 10, field_rect.y + 30))
            y += 68

        active_mode = self._current_difficulty_mode()
        counts_map = {(g, l, m): c for g, l, m, c in self.question_counts}
        title2 = self.font.render('Bank Counts (Active Mode)', True, config.YELLOW)
        screen.blit(title2, (right.x + 14, right.y + 14))
        active_text = self.small_font.render(f'Mode: {active_mode}', True, config.LIGHT_BLUE)
        screen.blit(active_text, (right.x + 14, right.y + 52))

        y = right.y + 82
        for game_key in QUESTION_GAME_KEYS:
            line = f"{QUESTION_GAME_LABELS[game_key]}"
            txt = self.small_font.render(line, True, config.WHITE)
            screen.blit(txt, (right.x + 14, y))
            y += 24
            for language in ('english', 'tagalog', 'bisaya'):
                count = counts_map.get((game_key, language, active_mode), 0)
                row = self.small_font.render(
                    f"  {LANGUAGE_LABELS[language]}: {count}",
                    True,
                    config.LIGHT_GRAY,
                )
                screen.blit(row, (right.x + 20, y))
                y += 22
            y += 8

        y += 8
        recent_title = self.font.render('Recent In This Slot', True, config.ORANGE)
        screen.blit(recent_title, (right.x + 14, y))
        y += 36
        for row in self.recent_questions:
            q = row['question_text']
            if len(q) > 38:
                q = q[:35] + '...'
            line = self.small_font.render(f"#{row['id']} {q}", True, config.WHITE)
            screen.blit(line, (right.x + 14, y))
            y += 24

        if self.forge_mode_editor:
            overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 165))
            screen.blit(overlay, (0, 0))

            panel = pygame.Rect(config.SCREEN_WIDTH // 2 - 320, config.SCREEN_HEIGHT // 2 - 120, 640, 240)
            self.draw_retro_box(screen, panel, (16, 24, 42), config.YELLOW, border_width=5)
            editor_mode = self.forge_mode_editor['mode']
            mode_title = 'CREATE DIFFICULTY MODE' if editor_mode == 'create' else 'RENAME DIFFICULTY MODE'
            title = self.font.render(mode_title, True, config.YELLOW)
            screen.blit(title, title.get_rect(center=(config.SCREEN_WIDTH // 2, panel.y + 46)))

            input_box = pygame.Rect(panel.x + 36, panel.y + 92, panel.width - 72, 58)
            self.draw_retro_box(screen, input_box, config.WHITE, config.BLUE, border_width=4, shadow=False)
            cursor = '|' if int(time.time() * 2) % 2 == 0 else ''
            value = self.forge_mode_editor['value'] + cursor
            text = self.font.render(value, True, config.BLACK)
            screen.blit(text, text.get_rect(midleft=(input_box.x + 10, input_box.centery)))

            hint = self.small_font.render('ENTER: Save  |  ESC: Cancel', True, config.WHITE)
            screen.blit(hint, hint.get_rect(center=(config.SCREEN_WIDTH // 2, panel.y + 192)))

    def draw(self, screen):
        # dark arcade room base
        screen.fill((12, 10, 28))
        for y in range(0, config.SCREEN_HEIGHT, 6):
            shade = 18 + (y % 24)
            pygame.draw.line(screen, (shade, shade, shade + 12), (0, y), (config.SCREEN_WIDTH, y))

        # reset clickable map each frame and repopulate while drawing
        self.tab_rects = {}

        if not self.authenticated:
            panel = pygame.Rect(config.SCREEN_WIDTH // 2 - 320, 180, 640, 360)
            self.draw_retro_box(screen, panel, (20, 26, 50), config.YELLOW, border_width=6)

            title = self.title_font.render('TEACHER MODE', True, config.YELLOW)
            screen.blit(title, title.get_rect(center=(config.SCREEN_WIDTH // 2, 250)))

            sub = self.small_font.render('Arcade admin access required', True, config.LIGHT_BLUE)
            screen.blit(sub, sub.get_rect(center=(config.SCREEN_WIDTH // 2, 285)))

            pw_box = pygame.Rect(panel.x + 80, panel.y + 150, panel.width - 160, 60)
            self.draw_retro_box(screen, pw_box, config.WHITE, config.BLUE, border_width=4, shadow=False)
            pw = self.font.render('*' * len(self.password_input), True, config.BLACK)
            screen.blit(pw, pw.get_rect(midleft=(pw_box.x + 15, pw_box.centery)))

            h = self.small_font.render('ENTER: Submit  |  ESC: Cancel', True, config.WHITE)
            screen.blit(h, h.get_rect(center=(config.SCREEN_WIDTH // 2, panel.y + 260)))
        else:
            title = self.title_font.render('TEACHER ARCADE CONTROL ROOM', True, config.YELLOW)
            shadow = self.title_font.render('TEACHER ARCADE CONTROL ROOM', True, config.BLACK)
            tr = title.get_rect(center=(config.SCREEN_WIDTH // 2, 42))
            screen.blit(shadow, tr.move(2, 2))
            screen.blit(title, tr)

            tab_y = 72
            self._draw_tab_button(screen, pygame.Rect(40, tab_y, 190, 38), '1 OVERVIEW', self.tab == 'overview', config.BLUE, 'overview')
            self._draw_tab_button(screen, pygame.Rect(245, tab_y, 220, 38), '2 LEADERBOARD', self.tab == 'leaderboard', config.PURPLE, 'leaderboard')
            self._draw_tab_button(screen, pygame.Rect(480, tab_y, 220, 38), '3 QUESTION FORGE', self.tab == 'forge', config.GREEN, 'forge')

            if self.tab == 'overview':
                self._draw_overview(screen)
            elif self.tab == 'leaderboard':
                self._draw_leaderboard(screen)
            else:
                self._draw_forge(screen)

            hint = self.small_font.render(
                'F1/F2/F3 Tabs  |  F5 Refresh  |  Forge: [ ] Difficulty + F7/F8 Mode Edit  |  ESC Return To Map',
                True,
                config.LIGHT_GRAY,
            )
            screen.blit(hint, (40, config.SCREEN_HEIGHT - 36))

        if self.status_message and time.time() < self.status_until:
            msg = self.small_font.render(self.status_message, True, self.status_color)
            screen.blit(msg, msg.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT - 20)))


# Barangay Captain Game

class BarangayCaptainState(State):
    """the barangay captain reading game.

    flow notes:
    - choose language -> load db questions -> answer rounds -> submit score.
    - submit uses record_game_result so leaderboard + progress stay in sync.
    """

    _gradient_bg = None  # cached background so we dont redraw it every frame

    def __init__(self, game):
        super().__init__(game)
        self.font       = pygame.font.Font(config.FONT_PATH, 24)
        self.title_font = pygame.font.Font(config.FONT_PATH, 36)
        self.small_font = pygame.font.Font(config.FONT_PATH, 18)
        self.current_question = 0
        self.score = 0
        self.happiness = 50
        self.selected_choice = None
        self.show_result = False
        self.result_timer = 0
        self.feedback = ''
        self.language = None
        self.game_started = False
        self.game_finished = False
        self.score_submitted = False
        self.submit_message = ''
        self.round_start_time = 0
        self.questions = []
        self.use_custom_questions = False
        self.active_difficulty_mode = 'General'
        self._cached_dimensions = None

    def enter(self):
        self.current_question = 0
        self.score = 0
        self.happiness = 50
        self.selected_choice = None
        self.show_result = False
        self.language = None
        self.game_started = False
        self.game_finished = False
        self.score_submitted = False
        self.submit_message = ''
        self.round_start_time = time.time()
        self.questions = []
        self.use_custom_questions = False
        self.active_difficulty_mode = 'General'

    def _load_questions(self):
        self.active_difficulty_mode = self.game.db.get_selected_difficulty_mode(
            'barangay',
            self.language,
        )
        custom_rows = self.game.db.get_custom_questions(
            game_key='barangay',
            language=self.language,
            difficulty_mode=self.active_difficulty_mode,
        )

        cooked = []
        for row in custom_rows:
            choices = [c for c in row['choices'] if str(c).strip()]
            if len(choices) < 2:
                continue
            correct = row['correct_index']
            if correct < 0 or correct >= len(choices):
                continue

            impact = [10 if i == correct else -5 for i in range(len(choices))]
            cooked.append({
                'passage': row['prompt_text'] or 'Read the scenario and answer carefully.',
                'question': row['question_text'],
                'choices': choices,
                'correct': correct,
                'happiness_impact': impact,
            })

        if cooked:
            random.shuffle(cooked)
            self.questions = cooked
            self.use_custom_questions = True
        else:
            self.questions = []
            self.use_custom_questions = True

    def _active_question(self):
        return self.questions[self.current_question]

    def _submit_score(self):
        if self.score_submitted:
            return

        if not self.questions:
            self.submit_message = 'No score to save. Add questions in Teacher Mode first.'
            return

        try:
            student_id = sanitize_student_id(
                getattr(self.game, 'current_student_id', config.DEFAULT_STUDENT_ID)
            )
            duration = max(0.1, time.time() - self.round_start_time)
            self.game.db.record_game_result(
                student_id=student_id,
                module='Barangay Captain Simulator',
                score=self.score,
                max_score=len(self.questions),
                language=self.language or 'english',
                time_spent=duration,
            )
            self.score_submitted = True
            self.submit_message = f'Score saved for {student_id}!'
        except Exception as exc:
            self.submit_message = f'Could not save score: {exc}'

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.next_state = 'menu'
            return

        if not self.game_started:
            lang = self.handle_language_key(event)
            if lang:
                self.language = lang
                self.game_started = True
                self._load_questions()
                self.round_start_time = time.time()
        elif self.game_finished:
            if event.key == pygame.K_RETURN:
                self._submit_score()
        elif not self.show_result:
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                idx = event.key - pygame.K_1
                q = self._active_question()
                if idx < len(q['choices']):
                    self.selected_choice = idx
                    self.show_result = True
                    self.result_timer = time.time()
                    if idx == q['correct']:
                        self.score += 1
                        self.feedback = "Correct! Good reading comprehension."
                    else:
                        self.feedback = "Try again. Re-read the passage carefully."

                    impact = q['happiness_impact']
                    delta = impact[idx] if idx < len(impact) else (10 if idx == q['correct'] else -5)
                    self.happiness = max(0, min(100,
                        self.happiness + delta))

    def update(self, dt):
        if not self.questions:
            return

        if self.show_result and time.time() - self.result_timer > 2:
            self.current_question += 1
            if self.current_question >= len(self.questions):
                self.game_finished = True
                self.show_result = False
            else:
                self.show_result = False
                self.selected_choice = None

    def draw(self, screen):
        # make background gradient (only redo if screen size changed)
        current_dims = (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        if BarangayCaptainState._gradient_bg is None or self._cached_dimensions != current_dims:
            h = config.SCREEN_HEIGHT
            BarangayCaptainState._gradient_bg = self.create_gradient(
                config.SCREEN_WIDTH, h,
                lambda i: (int(30 + i / h * 40),
                           int(30 + i / h * 40),
                           int(30 + i / h * 40) + 80))
            self._cached_dimensions = current_dims
        
        screen.blit(self._gradient_bg, (0, 0))

        if not self.game_started:
            self.draw_language_selection(screen, config.BLUE)
            return

        if not self.questions:
            self._draw_no_questions(screen)
            return

        if self.game_finished:
            self._draw_game_over(screen)
        else:
            self._draw_question(screen)

    # --- private draw helpers ---

    def _draw_question(self, screen):
        q = self._active_question()

        # Title
        title_box = pygame.Rect(20, 20, config.SCREEN_WIDTH - 40, 70)
        self.draw_retro_box(screen, title_box, config.BLUE, config.YELLOW,
                            border_width=4)
        t = self.title_font.render('BARANGAY CAPTAIN', True, config.YELLOW)
        ts = self.title_font.render('BARANGAY CAPTAIN', True, config.BLACK)
        tr = t.get_rect(center=(config.SCREEN_WIDTH // 2, 55))
        screen.blit(ts, tr.move(3, 3)); screen.blit(t, tr)

        info_y = 110

        # Progress
        self.draw_retro_box(screen, pygame.Rect(30, info_y, 200, 50),
                            config.DARK_GRAY, config.WHITE)
        pt = self.small_font.render(
            f'Question {self.current_question + 1}/{len(self.questions)}',
            True, config.WHITE)
        screen.blit(pt, (40, info_y + 15))

        # Happiness bar
        hbox = pygame.Rect(250, info_y, 400, 50)
        self.draw_retro_box(screen, hbox, config.DARK_GRAY, config.WHITE)
        bw = int(self.happiness / 100 * 360)
        bc = (config.GREEN if self.happiness >= 70
              else config.YELLOW if self.happiness >= 40
              else config.RED)
        pygame.draw.rect(screen, bc, (270, info_y + 15, bw, 20))
        pygame.draw.rect(screen, config.WHITE, (270, info_y + 15, 360, 20), 2)
        ht = self.small_font.render(f'Happiness: {self.happiness}/100', True,
                                    config.WHITE)
        screen.blit(ht, (270, info_y + 15))

        # Score
        sbox = pygame.Rect(670, info_y, 320, 50)
        self.draw_retro_box(screen, sbox, config.DARK_GRAY, config.WHITE)
        st = self.small_font.render(f'Correct: {self.score}', True,
                                    config.YELLOW)
        screen.blit(st, (690, info_y + 15))

        # Passage
        pbox = pygame.Rect(40, 190, config.SCREEN_WIDTH - 80, 180)
        self.draw_retro_box(screen, pbox, config.WHITE, config.BLACK,
                            border_width=4)
        p_lines = self.wrap_text_pixel(q['passage'],
                                       config.SCREEN_WIDTH - 120, self.font)
        y = 210
        for line in p_lines:
            screen.blit(self.font.render(line, True, config.BLACK), (60, y))
            y += 35

        # Question
        q_lines = self.wrap_text_pixel(q['question'],
                                       config.SCREEN_WIDTH - 120, self.font)
        qh = max(60, len(q_lines) * 35 + 30)
        qbox = pygame.Rect(40, y + 10, config.SCREEN_WIDTH - 80, qh)
        self.draw_retro_box(screen, qbox, config.LIGHT_BLUE, config.BLACK,
                            border_width=4)
        y = qbox.y + 15
        for line in q_lines:
            screen.blit(self.font.render(line, True, config.BLACK), (60, y))
            y += 35

        # Choices
        y = qbox.y + qbox.height + 20
        for i, choice in enumerate(q['choices']):
            c_lines = self.wrap_text_pixel(choice, config.SCREEN_WIDTH - 190,
                                           self.small_font)
            ch = len(c_lines) * 28 + 20
            cbox = pygame.Rect(60, y, config.SCREEN_WIDTH - 120, ch)

            if self.show_result:
                if i == q['correct']:
                    bg, brd, tc = config.GREEN, config.WHITE, config.WHITE
                elif i == self.selected_choice:
                    bg, brd, tc = config.RED, config.YELLOW, config.WHITE
                else:
                    bg, brd, tc = config.DARK_GRAY, config.LIGHT_GRAY, config.LIGHT_GRAY
            else:
                bg, brd, tc = config.BLUE, config.YELLOW, config.WHITE

            self.draw_retro_box(screen, cbox, bg, brd)

            # Number badge
            bs = 30
            br = pygame.Rect(70, y + (ch - bs) // 2, bs, bs)
            self.draw_retro_box(screen, br, config.YELLOW, config.BLACK,
                                shadow=False, border_width=2)
            nt = self.font.render(str(i + 1), True, config.BLACK)
            screen.blit(nt, nt.get_rect(center=br.center))

            # Text
            ty = y + 10
            for line in c_lines:
                screen.blit(self.small_font.render(line, True, tc), (115, ty))
                ty += 28
            y += ch + 10

        # Result
        if self.show_result:
            rbox = pygame.Rect(config.SCREEN_WIDTH // 2 - 150, y + 10, 300, 50)
            correct = self.selected_choice == q['correct']
            self.draw_retro_box(screen, rbox,
                                config.GREEN if correct else config.RED,
                                config.WHITE, border_width=4)
            msg = '✓ CORRECT!' if correct else '✗ INCORRECT!'
            rt = self.font.render(msg, True, config.WHITE)
            screen.blit(rt, rt.get_rect(center=rbox.center))

    def _draw_no_questions(self, screen):
        box = pygame.Rect(config.SCREEN_WIDTH // 2 - 360, 220, 720, 280)
        self.draw_retro_box(screen, box, config.BLUE, config.YELLOW,
                            border_width=6)
        title = self.title_font.render('NO QUESTIONS FOUND', True, config.YELLOW)
        screen.blit(title, title.get_rect(center=(config.SCREEN_WIDTH // 2, 280)))

        line1 = self.small_font.render('Teacher Mode > Question Forge', True, config.WHITE)
        line2 = self.small_font.render(
            f'Add Barangay questions in "{self.active_difficulty_mode}" for this language first.',
            True,
            config.WHITE,
        )
        line3 = self.small_font.render('Press ESC to return to menu.', True, config.LIGHT_BLUE)
        screen.blit(line1, line1.get_rect(center=(config.SCREEN_WIDTH // 2, 350)))
        screen.blit(line2, line2.get_rect(center=(config.SCREEN_WIDTH // 2, 386)))
        screen.blit(line3, line3.get_rect(center=(config.SCREEN_WIDTH // 2, 432)))

    def _draw_game_over(self, screen):
        gobox = pygame.Rect(config.SCREEN_WIDTH // 2 - 300, 150, 600, 400)
        self.draw_retro_box(screen, gobox, config.BLUE, config.YELLOW,
                            border_width=6)

        et = self.title_font.render('MISSION COMPLETE!', True, config.YELLOW)
        es = self.title_font.render('MISSION COMPLETE!', True, config.BLACK)
        er = et.get_rect(center=(config.SCREEN_WIDTH // 2, 220))
        screen.blit(es, er.move(3, 3)); screen.blit(et, er)

        total = max(1, len(self.questions))
        ratio = self.score / total
        sy = 320

        ssbox = pygame.Rect(config.SCREEN_WIDTH // 2 - 250, sy, 500, 60)
        sc = config.GREEN if ratio >= 0.7 else config.ORANGE
        self.draw_retro_box(screen, ssbox, sc, config.WHITE)
        st = self.font.render(f'Correct Answers: {self.score}/{total}', True,
                              config.WHITE)
        screen.blit(st, st.get_rect(center=ssbox.center))

        hsbox = pygame.Rect(config.SCREEN_WIDTH // 2 - 250, sy + 80, 500, 60)
        hc = (config.GREEN if self.happiness >= 70
              else config.YELLOW if self.happiness >= 40
              else config.RED)
        self.draw_retro_box(screen, hsbox, hc, config.WHITE)
        ht = self.font.render(f'Final Happiness: {self.happiness}/100', True,
                              config.WHITE)
        screen.blit(ht, ht.get_rect(center=hsbox.center))

        hint_text = (
            self.submit_message if self.score_submitted
            else 'Press ENTER to log score to leaderboard'
        )
        hint_color = config.GREEN if self.score_submitted else config.YELLOW
        hint = self.small_font.render(hint_text, True, hint_color)
        screen.blit(hint, hint.get_rect(center=(config.SCREEN_WIDTH // 2, 480)))

        esc = self.small_font.render('Press ESC to return to menu', True,
                                     config.WHITE)
        screen.blit(esc, esc.get_rect(center=(config.SCREEN_WIDTH // 2, 510)))


# Recipe Game
class RecipeGameState(State):
    """recipe reading game.

    footnotes:
    - now db-question driven, wrapper recipe object is mostly ui convenience.
    - score submit mirrors other games for consistency.
    """

    _gradient_bg = None

    def __init__(self, game):
        super().__init__(game)
        self.font       = pygame.font.Font(config.FONT_PATH, 24)
        self.title_font = pygame.font.Font(config.FONT_PATH, 36)
        self.small_font = pygame.font.Font(config.FONT_PATH, 18)
        self.current_recipe = 0
        self.current_question = 0
        self.score = 0
        self.selected_choice = None
        self.show_result = False
        self.result_timer = 0
        self.recipe_shown = False
        self.language = None
        self.game_started = False
        self.game_finished = False
        self.score_submitted = False
        self.submit_message = ''
        self.round_start_time = 0
        self.custom_questions = []
        self.use_custom_questions = False
        self.active_difficulty_mode = 'General'
        self._cached_dimensions = None

    def enter(self):
        self.current_recipe = 0
        self.current_question = 0
        self.score = 0
        self.selected_choice = None
        self.show_result = False
        self.recipe_shown = True
        self.language = None
        self.game_started = False
        self.game_finished = False
        self.score_submitted = False
        self.submit_message = ''
        self.round_start_time = time.time()
        self.custom_questions = []
        self.use_custom_questions = True
        self.active_difficulty_mode = 'General'

    def _load_custom_questions(self):
        self.active_difficulty_mode = self.game.db.get_selected_difficulty_mode(
            'recipe',
            self.language,
        )
        custom_rows = self.game.db.get_custom_questions(
            game_key='recipe',
            language=self.language,
            difficulty_mode=self.active_difficulty_mode,
        )

        cooked = []
        for row in custom_rows:
            choices = [c for c in row['choices'] if str(c).strip()]
            if len(choices) < 2:
                continue
            answer = row['correct_index']
            if answer < 0 or answer >= len(choices):
                continue

            cooked.append({
                'prompt': row['prompt_text'],
                'q': row['question_text'],
                'choices': choices,
                'answer': answer,
                'skill': 'teacher_custom',
            })

        if cooked:
            random.shuffle(cooked)
            self.custom_questions = cooked
            self.use_custom_questions = True
        else:
            self.custom_questions = []
            self.use_custom_questions = True

    def _submit_score(self):
        if self.score_submitted:
            return

        if not self._questions():
            self.submit_message = 'No score to save. Add questions in Teacher Mode first.'
            return

        try:
            student_id = sanitize_student_id(
                getattr(self.game, 'current_student_id', config.DEFAULT_STUDENT_ID)
            )
            duration = max(0.1, time.time() - self.round_start_time)
            self.game.db.record_game_result(
                student_id=student_id,
                module='Recipe Game',
                score=self.score,
                max_score=len(self._questions()),
                language=self.language or 'english',
                time_spent=duration,
            )
            self.score_submitted = True
            self.submit_message = f'Score saved for {student_id}!'
        except Exception as exc:
            self.submit_message = f'Could not save score: {exc}'

    def _questions(self):
        return self.custom_questions

    def _recipe(self):
        """db-backed recipe quiz container"""
        return {
            'title': 'Teacher Recipe Challenge',
            'description': '',
            'ingredients': [],
            'directions': [],
            'questions': self.custom_questions,
        }

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.next_state = 'menu'; return

        if not self.game_started:
            lang = self.handle_language_key(event)
            if lang:
                self.language = lang
                self.game_started = True
                self._load_custom_questions()
                self.round_start_time = time.time()
        elif self.game_finished:
            if event.key == pygame.K_RETURN:
                self._submit_score()
        elif not self.show_result:
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                idx = event.key - pygame.K_1
                qs = self._questions()
                if self.current_question < len(qs):
                    q = qs[self.current_question]
                    if idx < len(q['choices']):
                        self.selected_choice = idx
                        self.show_result = True
                        self.result_timer = time.time()
                        if idx == q['answer']:
                            self.score += 1

    def update(self, dt):
        if not self._questions():
            return

        if self.show_result and time.time() - self.result_timer > 2:
            self.current_question += 1
            if self.current_question >= len(self._questions()):
                self.game_finished = True
                self.show_result = False
            else:
                self.show_result = False
                self.selected_choice = None

    def draw(self, screen):
        # make background gradient (only redo if screen size changed)
        current_dims = (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        if RecipeGameState._gradient_bg is None or self._cached_dimensions != current_dims:
            h = config.SCREEN_HEIGHT
            RecipeGameState._gradient_bg = self.create_gradient(
                config.SCREEN_WIDTH, h,
                lambda i: (min(255, int(220 + i / h * 35)),
                           max(0, min(255, int(220 + i / h * 35) - 30)),
                           max(0, min(255, int(220 + i / h * 35) - 80))))
            self._cached_dimensions = current_dims
        
        screen.blit(self._gradient_bg, (0, 0))

        if not self.game_started:
            self.draw_language_selection(screen, config.ORANGE)
            return

        if not self.custom_questions:
            self._draw_no_questions(screen)
            return

        recipe = self._recipe()
        if self.game_finished:
            self._draw_complete(screen, recipe)
        elif self.current_question < len(self.custom_questions):
            self._draw_quiz(screen, recipe)
        else:
            self._draw_complete(screen, recipe)

    def _draw_no_questions(self, screen):
        box = pygame.Rect(config.SCREEN_WIDTH // 2 - 360, 220, 720, 280)
        self.draw_retro_box(screen, box, config.ORANGE, config.YELLOW,
                            border_width=6)
        title = self.title_font.render('NO QUESTIONS FOUND', True, config.WHITE)
        screen.blit(title, title.get_rect(center=(config.SCREEN_WIDTH // 2, 280)))

        line1 = self.small_font.render('Teacher Mode > Question Forge', True, config.WHITE)
        line2 = self.small_font.render(
            f'Add Recipe questions in "{self.active_difficulty_mode}" for this language first.',
            True,
            config.WHITE,
        )
        line3 = self.small_font.render('Press ESC to return to menu.', True, config.LIGHT_BLUE)
        screen.blit(line1, line1.get_rect(center=(config.SCREEN_WIDTH // 2, 350)))
        screen.blit(line2, line2.get_rect(center=(config.SCREEN_WIDTH // 2, 386)))
        screen.blit(line3, line3.get_rect(center=(config.SCREEN_WIDTH // 2, 432)))

    def _draw_recipe_card(self, screen, recipe):
        # title header
        hbox = pygame.Rect(30, 30, config.SCREEN_WIDTH - 60, 80)
        self.draw_retro_box(screen, hbox, config.ORANGE, config.YELLOW,
                            border_width=5)
        t = self.title_font.render(recipe['title'].upper(), True, config.WHITE)
        ts = self.title_font.render(recipe['title'].upper(), True, config.BLACK)
        tr = t.get_rect(center=(config.SCREEN_WIDTH // 2, 70))
        screen.blit(ts, tr.move(3, 3)); screen.blit(t, tr)

        # ingredients list
        ibox = pygame.Rect(40, 130, 450, 560)
        self.draw_retro_box(screen, ibox, (255, 250, 230), config.ORANGE,
                            border_width=4)
        ihbox = pygame.Rect(50, 140, 430, 40)
        self.draw_retro_box(screen, ihbox, config.ORANGE, config.YELLOW,
                            shadow=False, border_width=3)
        it = self.font.render('INGREDIENTS', True, config.WHITE)
        screen.blit(it, it.get_rect(center=ihbox.center))
        y = 195
        for ing in recipe['ingredients']:
            pygame.draw.circle(screen, config.ORANGE, (65, y + 10), 5)
            screen.blit(self.small_font.render(ing, True, config.BLACK),
                        (80, y))
            y += 28

        # steps/directions
        dbox = pygame.Rect(510, 130, 475, 560)
        self.draw_retro_box(screen, dbox, (255, 250, 230), config.ORANGE,
                            border_width=4)
        dhbox = pygame.Rect(520, 140, 455, 40)
        self.draw_retro_box(screen, dhbox, config.ORANGE, config.YELLOW,
                            shadow=False, border_width=3)
        dt_ = self.font.render('DIRECTIONS', True, config.WHITE)
        screen.blit(dt_, dt_.get_rect(center=dhbox.center))
        y = 195
        for i, d in enumerate(recipe['directions'], 1):
            br = pygame.Rect(525, y, 25, 25)
            self.draw_retro_box(screen, br, config.ORANGE, config.YELLOW,
                                shadow=False, border_width=2)
            nt = self.small_font.render(str(i), True, config.WHITE)
            screen.blit(nt, nt.get_rect(center=br.center))
            d_lines = self.wrap_text_pixel(d, 300, self.small_font)
            ty = y
            for line in d_lines:
                screen.blit(self.small_font.render(line, True, config.BLACK),
                            (560, ty))
                ty += 24
            y += max(28, len(d_lines) * 24 + 4)

        # spacebar prompt
        pbox = pygame.Rect(config.SCREEN_WIDTH // 2 - 250,
                           config.SCREEN_HEIGHT - 70, 500, 50)
        self.draw_retro_box(screen, pbox, config.BLUE, config.YELLOW,
                            border_width=4)
        sp = self.font.render('Press SPACE to start quiz', True, config.WHITE)
        screen.blit(sp, sp.get_rect(center=pbox.center))

    def _draw_quiz(self, screen, recipe):
        q = recipe['questions'][self.current_question]

        # Title
        tbox = pygame.Rect(30, 30, config.SCREEN_WIDTH - 60, 70)
        self.draw_retro_box(screen, tbox, config.ORANGE, config.YELLOW,
                            border_width=4)
        t = self.title_font.render(recipe['title'].upper(), True, config.WHITE)
        screen.blit(t, t.get_rect(center=(config.SCREEN_WIDTH // 2, 65)))

        # Progress
        pbox = pygame.Rect(30, 120, 200, 45)
        self.draw_retro_box(screen, pbox, config.DARK_GRAY, config.WHITE)
        pt = self.small_font.render(
            f'Question {self.current_question + 1}/{len(recipe["questions"])}',
            True, config.WHITE)
        screen.blit(pt, (40, 132))

        # Score
        sbox = pygame.Rect(config.SCREEN_WIDTH - 230, 120, 200, 45)
        self.draw_retro_box(screen, sbox, config.DARK_GRAY, config.WHITE)
        screen.blit(self.small_font.render(f'Score: {self.score}', True,
                                           config.YELLOW),
                    (config.SCREEN_WIDTH - 210, 132))

        prompt_text = q.get('prompt', '').strip()
        question_y = 190
        if prompt_text:
            pbox = pygame.Rect(50, 190, config.SCREEN_WIDTH - 100, 90)
            self.draw_retro_box(screen, pbox, config.LIGHT_BLUE, config.ORANGE,
                                border_width=4)
            pl = self.wrap_text_pixel(prompt_text, config.SCREEN_WIDTH - 160,
                                      self.small_font)
            py = 205
            for line in pl[:3]:
                pt = self.small_font.render(line, True, config.BLACK)
                screen.blit(pt, pt.get_rect(center=(config.SCREEN_WIDTH // 2, py)))
                py += 24
            question_y = 295

        # Question box
        qbox = pygame.Rect(50, question_y, config.SCREEN_WIDTH - 100, 100)
        self.draw_retro_box(screen, qbox, config.WHITE, config.ORANGE,
                            border_width=4)
        ql = self.wrap_text_pixel(q['q'], config.SCREEN_WIDTH - 160, self.font)
        qy = question_y + 20
        for line in ql:
            qt = self.font.render(line, True, config.BLACK)
            screen.blit(qt, qt.get_rect(center=(config.SCREEN_WIDTH // 2, qy)))
            qy += 35

        # Choices
        y = question_y + 130
        for i, choice in enumerate(q['choices']):
            cl = self.wrap_text_pixel(choice, config.SCREEN_WIDTH - 220,
                                      self.small_font)
            ch = len(cl) * 28 + 20
            cbox = pygame.Rect(80, y, config.SCREEN_WIDTH - 160, ch)

            if self.show_result:
                if i == q['answer']:
                    bg, brd, tc = config.GREEN, config.WHITE, config.WHITE
                elif i == self.selected_choice:
                    bg, brd, tc = config.RED, config.YELLOW, config.WHITE
                else:
                    bg, brd, tc = config.DARK_GRAY, config.LIGHT_GRAY, config.LIGHT_GRAY
            else:
                bg, brd, tc = config.ORANGE, config.YELLOW, config.WHITE

            self.draw_retro_box(screen, cbox, bg, brd)

            bs = 30
            br = pygame.Rect(90, y + (ch - bs) // 2, bs, bs)
            self.draw_retro_box(screen, br, config.YELLOW, config.BLACK,
                                shadow=False, border_width=2)
            nt = self.font.render(str(i + 1), True, config.BLACK)
            screen.blit(nt, nt.get_rect(center=br.center))

            ty = y + 10
            for line in cl:
                screen.blit(self.small_font.render(line, True, tc), (135, ty))
                ty += 28
            y += ch + 12

        if self.show_result:
            rbox = pygame.Rect(config.SCREEN_WIDTH // 2 - 150, y + 10, 300, 50)
            correct = self.selected_choice == q['answer']
            self.draw_retro_box(screen, rbox,
                                config.GREEN if correct else config.RED,
                                config.WHITE, border_width=4)
            msg = '✓ CORRECT!' if correct else '✗ WRONG!'
            rt = self.font.render(msg, True, config.WHITE)
            screen.blit(rt, rt.get_rect(center=rbox.center))

    def _draw_complete(self, screen, recipe):
        cbox = pygame.Rect(config.SCREEN_WIDTH // 2 - 300, 200, 600, 350)
        self.draw_retro_box(screen, cbox, config.ORANGE, config.YELLOW,
                            border_width=6)
        ct = self.title_font.render('RECIPE MASTERED!', True, config.WHITE)
        cs = self.title_font.render('RECIPE MASTERED!', True, config.BLACK)
        cr = ct.get_rect(center=(config.SCREEN_WIDTH // 2, 270))
        screen.blit(cs, cr.move(3, 3)); screen.blit(ct, cr)

        total = max(1, len(recipe['questions']))
        ratio = self.score / total
        ssbox = pygame.Rect(config.SCREEN_WIDTH // 2 - 250, 350, 500, 80)
        sc = (config.GREEN if ratio >= 0.9
                  else config.ORANGE if ratio >= 0.6
                  else config.RED)
        self.draw_retro_box(screen, ssbox, sc, config.WHITE, border_width=4)
        st = self.font.render(f'Final Score: {self.score}/{total}', True,
                              config.WHITE)
        screen.blit(st, st.get_rect(center=ssbox.center))

        hint_text = (
            self.submit_message if self.score_submitted
            else 'Press ENTER to log score to leaderboard'
        )
        hint_color = config.GREEN if self.score_submitted else config.YELLOW
        h = self.small_font.render(hint_text, True, hint_color)
        screen.blit(h, h.get_rect(center=(config.SCREEN_WIDTH // 2, 480)))

        esc = self.small_font.render('Press ESC to return to menu', True,
                                     config.WHITE)
        screen.blit(esc, esc.get_rect(center=(config.SCREEN_WIDTH // 2, 508)))


# Synonym / Antonym Game

class SynonymAntonymState(State):
    """the synonym and antonym word game.

    reminder:
    - despite old name, this now reads teacher-made items from custom_questions.
    - keep question payload shape simple: prompt/question/choices/correct_index.
    """

    _gradient_bg = None

    def __init__(self, game):
        super().__init__(game)
        self.font       = pygame.font.Font(config.FONT_PATH, 28)
        self.title_font = pygame.font.Font(config.FONT_PATH, 42)
        self.small_font = pygame.font.Font(config.FONT_PATH, 20)
        self.language = None
        self.game_started = False
        self.current_question = 0
        self.score = 0
        self.selected_choice = None
        self.show_result = False
        self.result_timer = 0
        self.questions = []
        self.question_type = []
        self.use_custom_questions = False
        self.active_difficulty_mode = 'General'
        self.game_finished = False
        self.score_submitted = False
        self.submit_message = ''
        self.round_start_time = 0
        self._cached_dimensions = None

    def enter(self):
        self.language = None
        self.game_started = False
        self.current_question = 0
        self.score = 0
        self.selected_choice = None
        self.show_result = False
        self.questions = []
        self.question_type = []
        self.use_custom_questions = True
        self.active_difficulty_mode = 'General'
        self.game_finished = False
        self.score_submitted = False
        self.submit_message = ''
        self.round_start_time = time.time()

    def _load_questions(self):
        self.active_difficulty_mode = self.game.db.get_selected_difficulty_mode(
            'synonym_antonym',
            self.language,
        )
        custom_rows = self.game.db.get_custom_questions(
            game_key='synonym_antonym',
            language=self.language,
            difficulty_mode=self.active_difficulty_mode,
        )

        cooked = []
        for row in custom_rows:
            choices = [c for c in row['choices'] if str(c).strip()]
            if len(choices) < 2:
                continue
            correct = row['correct_index']
            if correct < 0 or correct >= len(choices):
                continue

            cooked.append({
                'prompt': row['prompt_text'] or 'Read and pick the best answer.',
                'question': row['question_text'],
                'choices': choices,
                'correct_index': correct,
            })

        if cooked:
            random.shuffle(cooked)
            self.questions = cooked
            self.question_type = []
            self.use_custom_questions = True
            return

        self.questions = []
        self.question_type = []
        self.use_custom_questions = True

    def _submit_score(self):
        if self.score_submitted:
            return

        if not self.questions:
            self.submit_message = 'No score to save. Add questions in Teacher Mode first.'
            return

        try:
            student_id = sanitize_student_id(
                getattr(self.game, 'current_student_id', config.DEFAULT_STUDENT_ID)
            )
            duration = max(0.1, time.time() - self.round_start_time)
            self.game.db.record_game_result(
                student_id=student_id,
                module='Word Match Game',
                score=self.score,
                max_score=len(self.questions),
                language=self.language or 'english',
                time_spent=duration,
            )
            self.score_submitted = True
            self.submit_message = f'Score saved for {student_id}!'
        except Exception as exc:
            self.submit_message = f'Could not save score: {exc}'

    def _resolve(self, data_dict):
        """get text in the right language"""
        lang = self.language or 'english'
        return data_dict.get(lang, data_dict['english'])

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.next_state = 'menu'; return

        if not self.game_started:
            lang = self.handle_language_key(event)
            if lang:
                self.language = lang
                self.game_started = True
                self._load_questions()
                self.round_start_time = time.time()
        elif self.game_finished:
            if event.key == pygame.K_RETURN:
                self._submit_score()
        elif not self.show_result and self.current_question < len(self.questions):
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                idx = event.key - pygame.K_1
                if self.use_custom_questions:
                    qd = self.questions[self.current_question]
                    choices = qd['choices']
                    if idx < len(choices):
                        self.selected_choice = idx
                        self.show_result = True
                        self.result_timer = time.time()
                        if idx == qd['correct_index']:
                            self.score += 1
                else:
                    qd = self.questions[self.current_question]
                    qt = self.question_type[self.current_question]
                    correct = self._resolve(
                        qd['synonym'] if qt == 'synonym' else qd['antonym'])
                    choices = self._resolve(qd['choices'])
                    if idx < len(choices):
                        self.selected_choice = idx
                        self.show_result = True
                        self.result_timer = time.time()
                        if choices[idx] == correct:
                            self.score += 1

    def update(self, dt):
        if self.show_result and time.time() - self.result_timer > 2:
            self.current_question += 1
            if self.current_question >= len(self.questions):
                self.game_finished = True
                self.show_result = False
            else:
                self.show_result = False
                self.selected_choice = None

    def draw(self, screen):
        # make background gradient (only redo if screen size changed)
        current_dims = (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        if SynonymAntonymState._gradient_bg is None or self._cached_dimensions != current_dims:
            h = config.SCREEN_HEIGHT
            SynonymAntonymState._gradient_bg = self.create_gradient(
                config.SCREEN_WIDTH, h,
                lambda i: (int(80 + i / h * 40),
                           max(0, int(80 + i / h * 40) - 30),
                           int(80 + i / h * 40) + 60))
            self._cached_dimensions = current_dims
        
        screen.blit(self._gradient_bg, (0, 0))

        if not self.game_started:
            self.draw_language_selection(screen, config.PURPLE)
            return

        if not self.questions:
            self._draw_no_questions(screen)
            return

        if self.game_finished:
            self._draw_game_over(screen)
        elif self.current_question < len(self.questions):
            self._draw_question(screen)
        else:
            self._draw_game_over(screen)

    def _draw_no_questions(self, screen):
        box = pygame.Rect(config.SCREEN_WIDTH // 2 - 360, 220, 720, 280)
        self.draw_retro_box(screen, box, config.PURPLE, config.YELLOW,
                            border_width=6)
        title = self.title_font.render('NO QUESTIONS FOUND', True, config.YELLOW)
        screen.blit(title, title.get_rect(center=(config.SCREEN_WIDTH // 2, 280)))

        line1 = self.small_font.render('Teacher Mode > Question Forge', True, config.WHITE)
        line2 = self.small_font.render(
            f'Add Word Match questions in "{self.active_difficulty_mode}" for this language first.',
            True,
            config.WHITE,
        )
        line3 = self.small_font.render('Press ESC to return to menu.', True, config.LIGHT_BLUE)
        screen.blit(line1, line1.get_rect(center=(config.SCREEN_WIDTH // 2, 350)))
        screen.blit(line2, line2.get_rect(center=(config.SCREEN_WIDTH // 2, 386)))
        screen.blit(line3, line3.get_rect(center=(config.SCREEN_WIDTH // 2, 432)))

    def _draw_question(self, screen):
        if self.use_custom_questions:
            qd = self.questions[self.current_question]

            # Title
            tbox = pygame.Rect(30, 30, config.SCREEN_WIDTH - 60, 70)
            self.draw_retro_box(screen, tbox, config.PURPLE, config.YELLOW,
                                border_width=5)
            t = self.title_font.render('WORD MATCH GAME', True, config.WHITE)
            screen.blit(t, t.get_rect(center=tbox.center))

            # Progress
            pbox = pygame.Rect(30, 120, 260, 45)
            self.draw_retro_box(screen, pbox, config.DARK_GRAY, config.WHITE)
            screen.blit(self.small_font.render(
                f'Question {self.current_question + 1}/{len(self.questions)}', True, config.WHITE),
                (40, 132))

            # Score
            sbox = pygame.Rect(config.SCREEN_WIDTH - 230, 120, 200, 45)
            self.draw_retro_box(screen, sbox, config.DARK_GRAY, config.WHITE)
            screen.blit(self.small_font.render(f'Score: {self.score}', True,
                                               config.YELLOW),
                        (config.SCREEN_WIDTH - 210, 132))

            # Prompt/context
            cbox = pygame.Rect(100, 180, config.SCREEN_WIDTH - 200, 90)
            self.draw_retro_box(screen, cbox, config.LIGHT_BLUE, config.PURPLE)
            cl = self.wrap_text_pixel(qd['prompt'], config.SCREEN_WIDTH - 240,
                                      self.small_font)
            cy = 193
            for line in cl[:3]:
                screen.blit(self.small_font.render(line, True, config.BLACK),
                            (120, cy))
                cy += 22

            # Question text
            qbox = pygame.Rect(100, 290, config.SCREEN_WIDTH - 200, 75)
            self.draw_retro_box(screen, qbox, config.WHITE, config.PURPLE,
                                border_width=5)
            q_lines = self.wrap_text_pixel(qd['question'], config.SCREEN_WIDTH - 250,
                                           self.small_font)
            qy = 305
            for line in q_lines[:2]:
                screen.blit(self.small_font.render(line, True, config.BLACK),
                            (120, qy))
                qy += 24

            # Choices
            y = 385
            for i, choice in enumerate(qd['choices']):
                chbox = pygame.Rect(100, y, config.SCREEN_WIDTH - 200, 60)
                if self.show_result:
                    if i == qd['correct_index']:
                        bg, brd, tc = config.GREEN, config.WHITE, config.WHITE
                    elif i == self.selected_choice:
                        bg, brd, tc = config.RED, config.YELLOW, config.WHITE
                    else:
                        bg, brd, tc = config.DARK_GRAY, config.LIGHT_GRAY, config.LIGHT_GRAY
                else:
                    bg, brd, tc = config.PURPLE, config.YELLOW, config.WHITE

                self.draw_retro_box(screen, chbox, bg, brd, border_width=4)

                bs = 35
                br = pygame.Rect(115, y + 12, bs, bs)
                self.draw_retro_box(screen, br, config.YELLOW, config.BLACK,
                                    shadow=False, border_width=2)
                nt = self.font.render(str(i + 1), True, config.BLACK)
                screen.blit(nt, nt.get_rect(center=br.center))

                ct = self.font.render(choice, True, tc)
                screen.blit(ct, ct.get_rect(left=165, centery=y + 30))
                y += 75

            if self.show_result:
                rbox = pygame.Rect(config.SCREEN_WIDTH // 2 - 150, y + 10, 300, 50)
                correct = self.selected_choice == qd['correct_index']
                self.draw_retro_box(screen, rbox,
                                    config.GREEN if correct else config.RED,
                                    config.WHITE, border_width=4)
                msg = '✓ CORRECT!' if correct else '✗ WRONG!'
                rt = self.font.render(msg, True, config.WHITE)
                screen.blit(rt, rt.get_rect(center=rbox.center))
            return

        qd = self.questions[self.current_question]
        qt = self.question_type[self.current_question]
        q = {
            'context': self._resolve(qd['context']),
            'word':    self._resolve(qd['word']),
            'synonym': self._resolve(qd['synonym']),
            'antonym': self._resolve(qd['antonym']),
            'choices': self._resolve(qd['choices']),
        }

        # Title
        tbox = pygame.Rect(30, 30, config.SCREEN_WIDTH - 60, 70)
        self.draw_retro_box(screen, tbox, config.PURPLE, config.YELLOW,
                            border_width=5)
        t = self.title_font.render('WORD MATCH GAME', True, config.WHITE)
        screen.blit(t, t.get_rect(center=tbox.center))

        # Progress
        pbox = pygame.Rect(30, 120, 200, 45)
        self.draw_retro_box(screen, pbox, config.DARK_GRAY, config.WHITE)
        screen.blit(self.small_font.render(
            f'Question {self.current_question + 1}/{len(self.questions)}', True, config.WHITE),
            (40, 132))

        # Score
        sbox = pygame.Rect(config.SCREEN_WIDTH - 230, 120, 200, 45)
        self.draw_retro_box(screen, sbox, config.DARK_GRAY, config.WHITE)
        screen.blit(self.small_font.render(f'Score: {self.score}', True,
                                           config.YELLOW),
                    (config.SCREEN_WIDTH - 210, 132))

        # Context
        cbox = pygame.Rect(100, 180, config.SCREEN_WIDTH - 200, 80)
        self.draw_retro_box(screen, cbox, config.LIGHT_BLUE, config.PURPLE)
        cl = self.wrap_text_pixel(q['context'], config.SCREEN_WIDTH - 240,
                                  self.small_font)
        cy = 190
        for line in cl:
            screen.blit(self.small_font.render(line, True, config.BLACK),
                        (120, cy))
            cy += 20

        # Word
        wbox = pygame.Rect(100, 280, config.SCREEN_WIDTH - 200, 60)
        self.draw_retro_box(screen, wbox, config.WHITE, config.PURPLE,
                            border_width=5)
        wt = self.title_font.render(q['word'].upper(), True, config.PURPLE)
        screen.blit(wt, wt.get_rect(center=(config.SCREEN_WIDTH // 2, 310)))
        pr = self.font.render(f"Select the {qt.upper()}", True, config.BLACK)
        screen.blit(pr, pr.get_rect(center=(config.SCREEN_WIDTH // 2, 335)))

        # Choices
        correct_ans = q['synonym'] if qt == 'synonym' else q['antonym']
        y = 350
        for i, choice in enumerate(q['choices']):
            chbox = pygame.Rect(100, y, config.SCREEN_WIDTH - 200, 60)
            if self.show_result:
                if choice == correct_ans:
                    bg, brd, tc = config.GREEN, config.WHITE, config.WHITE
                elif i == self.selected_choice:
                    bg, brd, tc = config.RED, config.YELLOW, config.WHITE
                else:
                    bg, brd, tc = config.DARK_GRAY, config.LIGHT_GRAY, config.LIGHT_GRAY
            else:
                bg, brd, tc = config.PURPLE, config.YELLOW, config.WHITE

            self.draw_retro_box(screen, chbox, bg, brd, border_width=4)

            bs = 35
            br = pygame.Rect(115, y + 12, bs, bs)
            self.draw_retro_box(screen, br, config.YELLOW, config.BLACK,
                                shadow=False, border_width=2)
            nt = self.font.render(str(i + 1), True, config.BLACK)
            screen.blit(nt, nt.get_rect(center=br.center))

            ct = self.font.render(choice, True, tc)
            screen.blit(ct, ct.get_rect(left=165, centery=y + 30))
            y += 75

        if self.show_result:
            rbox = pygame.Rect(config.SCREEN_WIDTH // 2 - 150, y + 10, 300, 50)
            sel = q['choices'][self.selected_choice]
            correct = (sel == correct_ans)
            self.draw_retro_box(screen, rbox,
                                config.GREEN if correct else config.RED,
                                config.WHITE, border_width=4)
            msg = '✓ CORRECT!' if correct else '✗ WRONG!'
            rt = self.font.render(msg, True, config.WHITE)
            screen.blit(rt, rt.get_rect(center=rbox.center))

    def _draw_game_over(self, screen):
        gobox = pygame.Rect(config.SCREEN_WIDTH // 2 - 300, 200, 600, 350)
        self.draw_retro_box(screen, gobox, config.PURPLE, config.YELLOW,
                            border_width=6)

        t = self.title_font.render('GAME COMPLETE!', True, config.YELLOW)
        ts = self.title_font.render('GAME COMPLETE!', True, config.BLACK)
        tr = t.get_rect(center=(config.SCREEN_WIDTH // 2, 270))
        screen.blit(ts, tr.move(3, 3)); screen.blit(t, tr)

        total = max(1, len(self.questions))
        ratio = self.score / total

        ssbox = pygame.Rect(config.SCREEN_WIDTH // 2 - 250, 350, 500, 80)
        sc = (config.GREEN if ratio >= 0.8
              else config.ORANGE if ratio >= 0.55
              else config.RED)
        self.draw_retro_box(screen, ssbox, sc, config.WHITE, border_width=4)
        st = self.font.render(f'Final Score: {self.score}/{total}', True,
                              config.WHITE)
        screen.blit(st, st.get_rect(center=ssbox.center))

        hint_text = (
            self.submit_message if self.score_submitted
            else 'Press ENTER to log score to leaderboard'
        )
        hint_color = config.GREEN if self.score_submitted else config.YELLOW
        h = self.small_font.render(hint_text, True, hint_color)
        screen.blit(h, h.get_rect(center=(config.SCREEN_WIDTH // 2, 480)))

        esc = self.small_font.render('Press ESC to return to menu', True,
                                     config.WHITE)
        screen.blit(esc, esc.get_rect(center=(config.SCREEN_WIDTH // 2, 510)))
