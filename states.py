"""
Game states for Assistive Literacy Learning System
Contains all game state classes and logic
"""

import pygame
import random
import time
import math
import config
from database import Database
from tilemap import Tilemap, Player


# ---------------------------------------------------------------------------
# Base State with shared utilities
# ---------------------------------------------------------------------------

class State:
    """Base state class with shared utilities."""

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

    # --- Shared utility methods ---

    @staticmethod
    def wrap_text_pixel(text, max_width, font):
        """Wrap text to fit within *max_width* pixels."""
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
        """Pre-render a vertical gradient surface.

        *color_func(row_index)* must return an (r, g, b) tuple.
        """
        surface = pygame.Surface((width, height))
        for i in range(height):
            pygame.draw.line(surface, color_func(i), (0, i), (width - 1, i))
        return surface

    @staticmethod
    def draw_retro_box(screen, rect, bg_color, border_color=None,
                       shadow=True, border_width=3):
        """Draw a retro-styled box with optional shadow & border."""
        if shadow:
            pygame.draw.rect(screen, config.BLACK, rect.inflate(6, 6).move(2, 2))
        pygame.draw.rect(screen, bg_color, rect)
        if border_color:
            pygame.draw.rect(screen, border_color, rect, border_width)

    def draw_language_selection(self, screen, title_color):
        """Draw the shared language-selection overlay."""
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
        """Return 'english'/'tagalog'/'bisaya' if a language key was pressed,
        else *None*."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                return 'english'
            if event.key == pygame.K_2:
                return 'tagalog'
            if event.key == pygame.K_3:
                return 'bisaya'
        return None


# ---------------------------------------------------------------------------
# Menu / Hub (overworld)
# ---------------------------------------------------------------------------

class MenuState(State):
    """Top-down retro overworld hub."""

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
        self.student_id = config.DEFAULT_STUDENT_ID
        self.stats = {'total_gems': 0}
        self.saved_x = self.tilemap.spawn_x
        self.saved_y = self.tilemap.spawn_y
        # Initialize camera centered on player (critical for fullscreen)
        self.camera_x, self.camera_y = self._camera_target()
        self._clamp_camera()

    # --- helpers ---

    def _camera_target(self):
        """Return the ideal (x, y) the camera should look at."""
        sprite_oy = -(self.player.size - 32) + self.player.size // 2
        tx = int(self.player.pixel_x - config.SCREEN_WIDTH  // 2 + 16)
        ty = int(self.player.pixel_y - config.SCREEN_HEIGHT // 2 + sprite_oy)
        return tx, ty
    
    def _clamp_camera(self):
        """Clamp camera position to map boundaries."""
        max_cx = max(0, self.tilemap.map_width  - config.SCREEN_WIDTH)
        max_cy = max(0, self.tilemap.map_height - config.SCREEN_HEIGHT)
        self.camera_x = max(0, min(self.camera_x, max_cx))
        self.camera_y = max(0, min(self.camera_y, max_cy))

    # --- state callbacks ---

    def enter(self):
        self.stats = self.game.db.get_student_stats(self.student_id)
        self.player = Player(self.saved_x, self.saved_y)
        self.interaction_prompt = None
        # Immediately snap camera to player (no lerp) when entering/returning
        self.camera_x, self.camera_y = self._camera_target()
        self._clamp_camera()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.running = False
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
                    # Save tile position (not pixel) for proper restoration
                    self.saved_x = self.player.tile_x
                    self.saved_y = self.player.tile_y
                    zone_map = {
                        'barangay_captain': 'barangay',
                        'recipe_game':      'recipe',
                        'synonym_antonym':  'synonym_antonym',
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
        dx, dy = 0, 0
        if self.keys_held['up']:        dy = -1
        elif self.keys_held['down']:    dy = 1
        elif self.keys_held['left']:    dx = -1
        elif self.keys_held['right']:   dx = 1

        self.player.move(dx, dy, self.tilemap, self.shift_held)

        # Smooth camera
        target_x, target_y = self._camera_target()
        self.camera_x = int(self.camera_x + (target_x - self.camera_x) * 0.1)
        self.camera_y = int(self.camera_y + (target_y - self.camera_y) * 0.1)

        # Clamp to map boundaries
        self._clamp_camera()

        # Interaction zones
        new_prompt = self.tilemap.check_interaction(self.player.tile_x,
                                                    self.player.tile_y)
        if new_prompt != self.interaction_prompt:
            self.prompt_animation_start = time.time()
        self.interaction_prompt = new_prompt
        self.prompt_timer += dt

    def draw(self, screen):
        screen.fill((135, 206, 235))
        self.tilemap.draw(screen, self.camera_x, self.camera_y)
        self.player.draw(screen, self.camera_x, self.camera_y)
        self.tilemap.draw_labels(screen, self.camera_x, self.camera_y,
                                 self.game.font_small)

        # Interaction prompt
        if self.interaction_prompt:
            anim_t = time.time() - self.prompt_animation_start
            if anim_t < 0.3:
                scale = min(1.0, (0.5 + anim_t / 0.3 * 0.5) * 1.1)
            elif anim_t < 0.4:
                scale = 1.1 - (anim_t - 0.3) / 0.1 * 0.1
            else:
                scale = 1.0 + math.sin((anim_t - 0.4) * 2) * 0.03

            zone_names = {
                'barangay_captain': 'Barangay Captain Simulator',
                'recipe_game':      'Recipe Game',
                'synonym_antonym':  'Word Match Game',
            }
            prompt_str = f"Press SPACE to enter {zone_names.get(self.interaction_prompt, '')}"
            text = self.game.font_medium.render(prompt_str, True, config.WHITE)
            text_shadow = self.game.font_medium.render(prompt_str, True, config.BLACK)

            sw = int((text.get_width()  + 40) * scale)
            sh = int((text.get_height() + 20) * scale)
            cx = config.SCREEN_WIDTH  // 2
            cy = config.SCREEN_HEIGHT - 100
            bg_rect = pygame.Rect(cx - sw // 2, cy - sh // 2, sw, sh)

            pygame.draw.rect(screen, config.BLACK,  bg_rect.move(3, 3))
            pygame.draw.rect(screen, config.BLUE,   bg_rect)
            pygame.draw.rect(screen, config.YELLOW,  bg_rect, 4)

            tr = text.get_rect(center=bg_rect.center)
            screen.blit(text_shadow, tr.move(2, 2))
            screen.blit(text, tr)

        # Controls hint
        ctrl = self.game.font_small.render(
            "Arrow Keys / WASD: Move | SPACE: Interact | ESC: Quit",
            True, config.WHITE)
        ctrl_s = self.game.font_small.render(
            "Arrow Keys / WASD: Move | SPACE: Interact | ESC: Quit",
            True, config.BLACK)
        cr = ctrl.get_rect(center=(config.SCREEN_WIDTH // 2, 30))
        bg = cr.inflate(20, 10)
        pygame.draw.rect(screen, config.BLACK, bg.move(2, 2))
        pygame.draw.rect(screen, (50, 50, 50), bg)
        pygame.draw.rect(screen, config.WHITE, bg, 2)
        screen.blit(ctrl_s, cr.move(1, 1))
        screen.blit(ctrl, cr)

        # Gems
        stxt = self.game.font_medium.render(
            f"Total Gems: {self.stats['total_gems']}", True, config.YELLOW)
        sshd = self.game.font_medium.render(
            f"Total Gems: {self.stats['total_gems']}", True, config.BLACK)
        sr = stxt.get_rect(topright=(config.SCREEN_WIDTH - 20, 20))
        sbg = sr.inflate(20, 10)
        pygame.draw.rect(screen, config.BLACK,   sbg.move(2, 2))
        pygame.draw.rect(screen, (50, 50, 50),   sbg)
        pygame.draw.rect(screen, config.YELLOW,  sbg, 3)
        screen.blit(sshd, sr.move(1, 1))
        screen.blit(stxt, sr)


# ---------------------------------------------------------------------------
# Teacher Dashboard
# ---------------------------------------------------------------------------

class TeacherDashboardState(State):
    """Teacher dashboard for viewing student progress."""

    def __init__(self, game):
        super().__init__(game)
        self.font = pygame.font.Font(None, config.FONT_MEDIUM)
        self.small_font = pygame.font.Font(None, config.FONT_SMALL)
        self.report = None
        self.authenticated = False
        self.password_input = ''

    def enter(self):
        self.report = self.game.db.generate_report()
        self.authenticated = False
        self.password_input = ''

    def handle_event(self, event):
        if not self.authenticated:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if self.password_input == config.TEACHER_PASSWORD:
                        self.authenticated = True
                    else:
                        self.password_input = ''
                elif event.key == pygame.K_ESCAPE:
                    self.next_state = 'menu'
                elif event.key == pygame.K_BACKSPACE:
                    self.password_input = self.password_input[:-1]
                else:
                    self.password_input += event.unicode
        else:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.next_state = 'menu'

    def draw(self, screen):
        screen.fill(config.DARK_GRAY)

        if not self.authenticated:
            p = self.font.render('Teacher Password:', True, config.WHITE)
            screen.blit(p, p.get_rect(center=(config.SCREEN_WIDTH // 2, 300)))
            pw = self.font.render('*' * len(self.password_input), True,
                                  config.YELLOW)
            screen.blit(pw, pw.get_rect(center=(config.SCREEN_WIDTH // 2, 350)))
            h = self.small_font.render('Press ENTER to submit, ESC to cancel',
                                       True, config.LIGHT_GRAY)
            screen.blit(h, h.get_rect(center=(config.SCREEN_WIDTH // 2, 450)))
        else:
            title = self.font.render('Teacher Dashboard', True, config.WHITE)
            screen.blit(title, (50, 30))

            y = 100
            ts = self.font.render(
                f'Total Sessions: {self.report["total_sessions"]}',
                True, config.WHITE)
            screen.blit(ts, (50, y)); y += 50

            at = self.font.render(
                f'Avg Time per Module: {self.report["avg_time_per_module"]:.1f}s',
                True, config.WHITE)
            screen.blit(at, (50, y)); y += 80

            st = self.font.render('Student Progress:', True, config.YELLOW)
            screen.blit(st, (50, y)); y += 50

            for student in self.report['students']:
                sl = self.small_font.render(
                    f'{student[0]}: {student[1]} gems | '
                    f'P:{student[2]} S:{student[3]} St:{student[4]}',
                    True, config.WHITE)
                screen.blit(sl, (70, y)); y += 35

            esc = self.small_font.render('Press ESC to return', True,
                                         config.LIGHT_GRAY)
            screen.blit(esc, (50, config.SCREEN_HEIGHT - 50))


# ---------------------------------------------------------------------------
# Barangay Captain Simulator
# ---------------------------------------------------------------------------

class BarangayCaptainState(State):
    """Barangay Captain Simulator – decision-making game."""

    _gradient_bg = None  # class-level cached gradient

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
        self._cached_dimensions = None

    def enter(self):
        self.current_question = 0
        self.score = 0
        self.happiness = 50
        self.selected_choice = None
        self.show_result = False
        self.language = None
        self.game_started = False

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
        elif not self.show_result:
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                idx = event.key - pygame.K_1
                cd = config.BARANGAY_COMPLAINTS[self.current_question]
                complaint = cd.get(self.language, cd['english'])
                if idx < len(complaint['choices']):
                    self.selected_choice = idx
                    self.show_result = True
                    self.result_timer = time.time()
                    if idx == cd['correct']:
                        self.score += 1
                        self.feedback = "Correct! Good reading comprehension."
                    else:
                        self.feedback = "Try again. Re-read the passage carefully."
                    self.happiness = max(0, min(100,
                        self.happiness + cd['happiness_impact'][idx]))

    def update(self, dt):
        if self.show_result and time.time() - self.result_timer > 2:
            self.current_question += 1
            if self.current_question >= len(config.BARANGAY_COMPLAINTS):
                self.next_state = 'menu'
            else:
                self.show_result = False
                self.selected_choice = None

    def draw(self, screen):
        # Generate gradient if needed (handles dynamic screen size in fullscreen)
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

        complaints = config.BARANGAY_COMPLAINTS
        if self.current_question < len(complaints):
            self._draw_question(screen, complaints)
        else:
            self._draw_game_over(screen)

    # --- private draw helpers ---

    def _draw_question(self, screen, complaints):
        cd = complaints[self.current_question]
        complaint = cd.get(self.language, cd['english'])

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
            f'Question {self.current_question + 1}/{len(complaints)}',
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
        p_lines = self.wrap_text_pixel(complaint['passage'],
                                       config.SCREEN_WIDTH - 120, self.font)
        y = 210
        for line in p_lines:
            screen.blit(self.font.render(line, True, config.BLACK), (60, y))
            y += 35

        # Question
        q_lines = self.wrap_text_pixel(complaint['question'],
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
        for i, choice in enumerate(complaint['choices']):
            c_lines = self.wrap_text_pixel(choice, config.SCREEN_WIDTH - 190,
                                           self.small_font)
            ch = len(c_lines) * 28 + 20
            cbox = pygame.Rect(60, y, config.SCREEN_WIDTH - 120, ch)

            if self.show_result:
                if i == cd['correct']:
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
            correct = self.selected_choice == cd['correct']
            self.draw_retro_box(screen, rbox,
                                config.GREEN if correct else config.RED,
                                config.WHITE, border_width=4)
            msg = '✓ CORRECT!' if correct else '✗ INCORRECT!'
            rt = self.font.render(msg, True, config.WHITE)
            screen.blit(rt, rt.get_rect(center=rbox.center))

    def _draw_game_over(self, screen):
        gobox = pygame.Rect(config.SCREEN_WIDTH // 2 - 300, 150, 600, 400)
        self.draw_retro_box(screen, gobox, config.BLUE, config.YELLOW,
                            border_width=6)

        et = self.title_font.render('MISSION COMPLETE!', True, config.YELLOW)
        es = self.title_font.render('MISSION COMPLETE!', True, config.BLACK)
        er = et.get_rect(center=(config.SCREEN_WIDTH // 2, 220))
        screen.blit(es, er.move(3, 3)); screen.blit(et, er)

        total = len(config.BARANGAY_COMPLAINTS)
        sy = 320

        ssbox = pygame.Rect(config.SCREEN_WIDTH // 2 - 250, sy, 500, 60)
        sc = config.GREEN if self.score >= total * 0.7 else config.ORANGE
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

        hint = self.small_font.render('Press ESC to return to menu', True,
                                      config.WHITE)
        screen.blit(hint, hint.get_rect(center=(config.SCREEN_WIDTH // 2, 480)))


# ---------------------------------------------------------------------------
# Recipe Game
# ---------------------------------------------------------------------------

class RecipeGameState(State):
    """Recipe reading & comprehension game."""

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
        self._cached_dimensions = None

    def enter(self):
        self.current_recipe = 0
        self.current_question = 0
        self.score = 0
        self.selected_choice = None
        self.show_result = False
        self.recipe_shown = False
        self.language = None
        self.game_started = False

    def _questions(self):
        lang = self.language or 'english'
        qs = config.RECIPES[self.current_recipe]['questions']
        return qs.get(lang, qs['english'])

    def _recipe(self):
        """Resolve current recipe data for selected language."""
        rd = config.RECIPES[self.current_recipe]
        lang = self.language or 'english'
        return {
            'title':       rd['title'].get(lang, rd['title']['english']),
            'description': rd['description'].get(lang, rd['description']['english']),
            'ingredients': rd['ingredients'].get(lang, rd['ingredients']['english']),
            'directions':  rd['directions'].get(lang, rd['directions']['english']),
            'questions':   rd['questions'].get(lang, rd['questions']['english']),
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
        elif not self.recipe_shown:
            if event.key == pygame.K_SPACE:
                self.recipe_shown = True
        elif not self.show_result:
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
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
        if self.show_result and time.time() - self.result_timer > 2:
            self.current_question += 1
            if self.current_question >= len(self._questions()):
                self.next_state = 'menu'
            else:
                self.show_result = False
                self.selected_choice = None

    def draw(self, screen):
        # Generate gradient if needed (handles dynamic screen size in fullscreen)
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
        recipe = self._recipe()

        if not self.game_started:
            self.draw_language_selection(screen, config.ORANGE)
        elif not self.recipe_shown:
            self._draw_recipe_card(screen, recipe)
        elif self.current_question < len(recipe['questions']):
            self._draw_quiz(screen, recipe)
        else:
            self._draw_complete(screen, recipe)

    def _draw_recipe_card(self, screen, recipe):
        # Header
        hbox = pygame.Rect(30, 30, config.SCREEN_WIDTH - 60, 80)
        self.draw_retro_box(screen, hbox, config.ORANGE, config.YELLOW,
                            border_width=5)
        t = self.title_font.render(recipe['title'].upper(), True, config.WHITE)
        ts = self.title_font.render(recipe['title'].upper(), True, config.BLACK)
        tr = t.get_rect(center=(config.SCREEN_WIDTH // 2, 70))
        screen.blit(ts, tr.move(3, 3)); screen.blit(t, tr)

        # Ingredients
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

        # Directions
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

        # Prompt
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

        # Question box
        qbox = pygame.Rect(50, 190, config.SCREEN_WIDTH - 100, 100)
        self.draw_retro_box(screen, qbox, config.WHITE, config.ORANGE,
                            border_width=4)
        ql = self.wrap_text_pixel(q['q'], config.SCREEN_WIDTH - 160, self.font)
        qy = 210
        for line in ql:
            qt = self.font.render(line, True, config.BLACK)
            screen.blit(qt, qt.get_rect(center=(config.SCREEN_WIDTH // 2, qy)))
            qy += 35

        # Choices
        y = 320
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

        total = len(recipe['questions'])
        ssbox = pygame.Rect(config.SCREEN_WIDTH // 2 - 250, 350, 500, 80)
        sc = (config.GREEN if self.score == total
              else config.ORANGE if self.score >= total * 0.6
              else config.RED)
        self.draw_retro_box(screen, ssbox, sc, config.WHITE, border_width=4)
        st = self.font.render(f'Final Score: {self.score}/{total}', True,
                              config.WHITE)
        screen.blit(st, st.get_rect(center=ssbox.center))

        h = self.small_font.render('Press ESC to return to menu', True,
                                   config.WHITE)
        screen.blit(h, h.get_rect(center=(config.SCREEN_WIDTH // 2, 480)))


# ---------------------------------------------------------------------------
# Synonym / Antonym Word Match
# ---------------------------------------------------------------------------

class SynonymAntonymState(State):
    """Synonym/Antonym word-matching game."""

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
        self._cached_dimensions = None

    def enter(self):
        self.language = None
        self.game_started = False
        self.current_question = 0
        self.score = 0
        self.selected_choice = None
        self.show_result = False
        pool = config.SYNONYM_ANTONYM_WORDS
        self.questions = random.sample(pool, min(15, len(pool)))
        self.question_type = [random.choice(('synonym', 'antonym'))
                              for _ in self.questions]

    def _resolve(self, data_dict):
        """Resolve a per-language dict to the current language string."""
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
        elif not self.show_result and self.current_question < len(self.questions):
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                idx = event.key - pygame.K_1
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
            if self.current_question < len(self.questions):
                self.show_result = False
                self.selected_choice = None

    def draw(self, screen):
        # Generate gradient if needed (handles dynamic screen size in fullscreen)
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

        if self.current_question < len(self.questions):
            self._draw_question(screen)
        else:
            self._draw_game_over(screen)

    def _draw_question(self, screen):
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
            f'Question {self.current_question + 1}/15', True, config.WHITE),
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

        ssbox = pygame.Rect(config.SCREEN_WIDTH // 2 - 250, 350, 500, 80)
        sc = (config.GREEN if self.score >= 12
              else config.ORANGE if self.score >= 8
              else config.RED)
        self.draw_retro_box(screen, ssbox, sc, config.WHITE, border_width=4)
        st = self.font.render(f'Final Score: {self.score}/15', True,
                              config.WHITE)
        screen.blit(st, st.get_rect(center=ssbox.center))

        h = self.small_font.render('Press ESC to return to menu', True,
                                   config.WHITE)
        screen.blit(h, h.get_rect(center=(config.SCREEN_WIDTH // 2, 480)))
