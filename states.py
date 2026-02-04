"""
Game states for Assistive Literacy Learning System
Contains all game state classes and logic
"""

import pygame
import random
import time
import config
from database import Database
from tilemap import Tilemap, Player

class State:
    """Base state class"""
    def __init__(self, game):
        self.game = game
        self.next_state = None
    
    def enter(self):
        """Called when entering this state"""
        pass
    
    def exit(self):
        """Called when exiting this state"""
        pass
    
    def handle_event(self, event):
        """Handle pygame events"""
        pass
    
    def update(self, dt):
        """Update state logic"""
        pass
    
    def draw(self, screen):
        """Draw state to screen"""
        pass


class MenuState(State):
    """Main menu / Hub state - Top-down retro overworld"""
    def __init__(self, game):
        super().__init__(game)
        self.tilemap = Tilemap()
        self.player = Player(10, 8)  # Start in center
        self.camera_x = 0
        self.camera_y = 0
        self.keys_held = {'up': False, 'down': False, 'left': False, 'right': False}
        self.interaction_prompt = None
        self.prompt_timer = 0
        self.student_id = config.DEFAULT_STUDENT_ID
        self.stats = {'total_gems': 0}
    
    def enter(self):
        """Load student stats and reset player"""
        self.stats = self.game.db.get_student_stats(self.student_id)
        self.player = Player(10, 8)
        self.interaction_prompt = None
        
        # Center camera on player immediately
        self.camera_x = self.player.pixel_x - config.SCREEN_WIDTH // 2 + 16
        self.camera_y = self.player.pixel_y - config.SCREEN_HEIGHT // 2 + 16
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.running = False
            elif event.key == pygame.K_UP or event.key == pygame.K_w:
                self.keys_held['up'] = True
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self.keys_held['down'] = True
            elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                self.keys_held['left'] = True
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                self.keys_held['right'] = True
            elif event.key == pygame.K_SPACE:
                # Check if player is near an interaction zone
                if self.interaction_prompt:
                    if self.interaction_prompt == 'barangay_captain':
                        self.next_state = 'barangay'
                    elif self.interaction_prompt == 'recipe_game':
                        self.next_state = 'recipe'
        
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                self.keys_held['up'] = False
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self.keys_held['down'] = False
            elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                self.keys_held['left'] = False
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                self.keys_held['right'] = False
    
    def update(self, dt):
        """Update player movement and camera"""
        # Move player based on keys (no diagonal movement)
        dx, dy = 0, 0
        
        # Prioritize vertical movement over horizontal
        if self.keys_held['up']:
            dy = -1
        elif self.keys_held['down']:
            dy = 1
        elif self.keys_held['left']:
            dx = -1
        elif self.keys_held['right']:
            dx = 1
        
        self.player.move(dx, dy, self.tilemap)
        
        # Update camera to follow player (smooth centering) - ensure integers
        target_x = self.player.pixel_x - config.SCREEN_WIDTH // 2 + 16
        target_y = self.player.pixel_y - config.SCREEN_HEIGHT // 2 + 16
        
        self.camera_x = int(self.camera_x + (target_x - self.camera_x) * 0.1)
        self.camera_y = int(self.camera_y + (target_y - self.camera_y) * 0.1)
        
        # Clamp camera to map boundaries
        self.camera_x = max(0, min(self.camera_x, self.tilemap.map_width - config.SCREEN_WIDTH))
        self.camera_y = max(0, min(self.camera_y, self.tilemap.map_height - config.SCREEN_HEIGHT))
        
        # Check if player is near an interaction zone
        self.interaction_prompt = self.tilemap.check_interaction(self.player.tile_x, self.player.tile_y)
        
        # Update prompt animation timer
        self.prompt_timer += dt
    
    def draw(self, screen):
        """Draw the overworld"""
        # Sky background
        screen.fill((135, 206, 235))
        
        # Draw tilemap
        self.tilemap.draw(screen, self.camera_x, self.camera_y)
        
        # Draw player
        self.player.draw(screen, self.camera_x, self.camera_y)
        
        # Draw labels
        self.tilemap.draw_labels(screen, self.camera_x, self.camera_y, self.game.font_small)
        
        # Draw interaction prompt
        if self.interaction_prompt:
            # Pulsing animation
            pulse = abs((self.prompt_timer * 3) % 2 - 1)
            
            zone_names = {
                'barangay_captain': 'Barangay Captain Simulator',
                'recipe_game': 'Recipe Game'
            }
            
            prompt_text = f"Press SPACE to enter {zone_names.get(self.interaction_prompt, '')}"
            text = self.game.font_medium.render(prompt_text, True, config.WHITE)
            text_shadow = self.game.font_medium.render(prompt_text, True, config.BLACK)
            
            # Blocky prompt box
            prompt_rect = text.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT - 100 - int(pulse * 10)))
            bg_rect = prompt_rect.inflate(40, 20)
            
            # Shadow
            pygame.draw.rect(screen, config.BLACK, bg_rect.move(3, 3))
            # Background
            pygame.draw.rect(screen, config.BLUE, bg_rect)
            # Border
            pygame.draw.rect(screen, config.YELLOW, bg_rect, 4)
            
            # Text
            screen.blit(text_shadow, prompt_rect.move(2, 2))
            screen.blit(text, prompt_rect)
        
        # Draw controls hint at top
        controls = self.game.font_small.render("Arrow Keys / WASD: Move | SPACE: Interact | ESC: Quit", True, config.WHITE)
        controls_shadow = self.game.font_small.render("Arrow Keys / WASD: Move | SPACE: Interact | ESC: Quit", True, config.BLACK)
        controls_rect = controls.get_rect(center=(config.SCREEN_WIDTH // 2, 30))
        
        # Background box
        bg_rect = controls_rect.inflate(20, 10)
        pygame.draw.rect(screen, config.BLACK, bg_rect.move(2, 2))
        pygame.draw.rect(screen, (50, 50, 50), bg_rect)
        pygame.draw.rect(screen, config.WHITE, bg_rect, 2)
        
        screen.blit(controls_shadow, controls_rect.move(1, 1))
        screen.blit(controls, controls_rect)
        
        # Score display
        score_text = self.game.font_medium.render(f"Total Gems: {self.stats['total_gems']}", True, config.YELLOW)
        score_shadow = self.game.font_medium.render(f"Total Gems: {self.stats['total_gems']}", True, config.BLACK)
        score_rect = score_text.get_rect(topright=(config.SCREEN_WIDTH - 20, 20))
        score_bg = score_rect.inflate(20, 10)
        
        pygame.draw.rect(screen, config.BLACK, score_bg.move(2, 2))
        pygame.draw.rect(screen, (50, 50, 50), score_bg)
        pygame.draw.rect(screen, config.YELLOW, score_bg, 3)
        
        screen.blit(score_shadow, score_rect.move(1, 1))
        screen.blit(score_text, score_rect)


class PhonicsForestState(State):
    """Word Recognition - Phil IRI Sight Word Assessment"""
    def __init__(self, game):
        super().__init__(game)
        self.font = pygame.font.Font(None, config.FONT_LARGE)
        self.word_font = pygame.font.Font(None, 56)
        
        self.current_word = None
        self.word_choices = []
        self.choice_buttons = []
        self.score = 0
        self.words_attempted = 0
        self.correct_count = 0
        self.start_time = 0
        self.last_input_time = 0
        self.hint_shown = False
        self.feedback_text = ''
        self.show_feedback = False
        self.feedback_timer = 0
    
    def enter(self):
        """Initialize word recognition test"""
        self.score = 0
        self.words_attempted = 0
        self.correct_count = 0
        self.start_time = time.time()
        self.last_input_time = time.time()
        self.show_next_word()
    
    def exit(self):
        """Save progress"""
        time_spent = time.time() - self.start_time
        accuracy = (self.correct_count / self.words_attempted * 100) if self.words_attempted > 0 else 0
        self.game.db.log_progress(
            config.DEFAULT_STUDENT_ID,
            'Word Recognition',
            int(accuracy),
            self.score,
            time_spent
        )
    
    def show_next_word(self):
        """Display next word with distractors"""
        if self.words_attempted >= 20:  # 20 word assessment for Grade 6
            self.next_state = 'menu'
            return
            
        self.current_word = random.choice(config.ALL_SIGHT_WORDS)
        
        # Create distractors (similar words)
        distractors = [w for w in config.ALL_SIGHT_WORDS if w != self.current_word]
        self.word_choices = [self.current_word] + random.sample(distractors, 2)
        random.shuffle(self.word_choices)
        
        # Create choice buttons
        self.choice_buttons = []
        button_width = 250
        button_height = 80
        spacing = 100
        start_x = (config.SCREEN_WIDTH - (button_width * 3 + spacing * 2)) // 2
        
        for i, word in enumerate(self.word_choices):
            button = pygame.Rect(start_x + i * (button_width + spacing), 450, button_width, button_height)
            self.choice_buttons.append({'rect': button, 'word': word})
        
        self.hint_shown = False
        self.show_feedback = False
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.next_state = 'menu'
            self.last_input_time = time.time()
        
        if event.type == pygame.MOUSEBUTTONDOWN and not self.show_feedback:
            mouse_pos = event.pos
            for button in self.choice_buttons:
                if button['rect'].collidepoint(mouse_pos):
                    self.words_attempted += 1
                    if button['word'] == self.current_word:
                        self.score += config.POINTS_PER_CORRECT_ANSWER
                        self.correct_count += 1
                        self.feedback_text = 'Tama! ✓'
                        # Score popup
                        self.score_popup = f'+{config.POINTS_PER_CORRECT_ANSWER}'
                        self.score_popup_timer = time.time()
                        # Create particles
                        for _ in range(10):
                            self.particles.append({
                                'x': mouse_pos[0],
                                'y': mouse_pos[1],
                                'vx': random.uniform(-3, 3),
                                'vy': random.uniform(-5, -1),
                                'life': 1.0
                            })
                    else:
                        self.feedback_text = f'Hindi tama. Ang tamang sagot: {self.current_word}'
                    self.show_feedback = True
                    self.feedback_timer = time.time()
                    self.last_input_time = time.time()
    
    def update(self, dt):
        # Check for hint trigger
        if time.time() - self.last_input_time > config.HINT_DELAY_MS / 1000:
            self.hint_shown = True
        
        # Update particles
        for particle in self.particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vy'] += 0.2  # Gravity
            particle['life'] -= 0.02
            if particle['life'] <= 0:
                self.particles.remove(particle)
        
        # Auto-advance after feedback
        if self.show_feedback and time.time() - self.feedback_timer > 2:
            self.show_next_word()
    
    def draw(self, screen):
        screen.fill(config.GREEN)
        
        # Retro pixel grid background
        for x in range(0, config.SCREEN_WIDTH, 40):
            for y in range(0, config.SCREEN_HEIGHT, 40):
                if (x + y) % 80 == 0:
                    pygame.draw.rect(screen, (0, 180, 0), (x, y, 40, 40), 1)
        
        # Title with shadow
        title = self.font.render('Word Recognition', True, config.BLACK)
        screen.blit(title, (22, 22))
        title = self.font.render('Word Recognition', True, config.WHITE)
        screen.blit(title, (20, 20))
        
        # Progress with blocky bar
        progress_text = self.font.render(f'Word {self.words_attempted + 1}/20', True, config.WHITE)
        screen.blit(progress_text, (20, 70))
        
        # Progress bar
        bar_width = 200
        bar_height = 20
        progress_pct = self.words_attempted / 20
        pygame.draw.rect(screen, config.BLACK, (22, 122, bar_width, bar_height))
        pygame.draw.rect(screen, config.DARK_GRAY, (20, 120, bar_width, bar_height))
        pygame.draw.rect(screen, config.YELLOW, (20, 120, int(bar_width * progress_pct), bar_height))
        pygame.draw.rect(screen, config.WHITE, (20, 120, bar_width, bar_height), 3)
        
        # Score with 3D box
        score_box = pygame.Rect(config.SCREEN_WIDTH - 280, 10, 260, 70)
        pygame.draw.rect(screen, config.BLACK, score_box.move(4, 4))
        pygame.draw.rect(screen, config.DARK_GRAY, score_box)
        pygame.draw.rect(screen, config.YELLOW, score_box, 4)
        score_text = self.font.render(f'Score: {self.score}', True, config.YELLOW)
        score_rect = score_text.get_rect(center=score_box.center)
        screen.blit(score_text, score_rect)
        
        if not self.show_feedback:
            # Instruction
            inst_text = self.font.render('Basahin at piliin ang tamang salita:', True, config.WHITE)
            inst_rect = inst_text.get_rect(center=(config.SCREEN_WIDTH // 2, 200))
            screen.blit(inst_text, inst_rect)
            
            # Target word in blocky display box
            word_box = pygame.Rect(config.SCREEN_WIDTH // 2 - 150, 270, 300, 80)
            pygame.draw.rect(screen, config.BLACK, word_box.move(5, 5))
            pygame.draw.rect(screen, config.WHITE, word_box)
            pygame.draw.rect(screen, config.YELLOW, word_box, 5)
            word_text = self.word_font.render(self.current_word, True, config.BLACK)
            word_rect = word_text.get_rect(center=word_box.center)
            screen.blit(word_text, word_rect)
            
            # Hint
            if self.hint_shown:
                hint_text = self.font.render('Tingnan mabuti ang mga titik', True, config.YELLOW)
                hint_rect = hint_text.get_rect(center=(config.SCREEN_WIDTH // 2, 370))
                screen.blit(hint_text, hint_rect)
            
            # Choice buttons with hover effect
            mouse_pos = pygame.mouse.get_pos()
            for button in self.choice_buttons:
                is_hover = button['rect'].collidepoint(mouse_pos)
                offset = 3 if is_hover else 0
                
                btn_rect = button['rect'].inflate(offset, offset)
                
                # Shadow
                pygame.draw.rect(screen, config.BLACK, btn_rect.move(5, 5))
                # Base
                pygame.draw.rect(screen, config.WHITE if is_hover else config.LIGHT_GRAY, btn_rect)
                # Border
                pygame.draw.rect(screen, config.BLACK, btn_rect, 4)
                
                choice_text = self.word_font.render(button['word'], True, config.BLACK)
                choice_rect = choice_text.get_rect(center=btn_rect.center)
                screen.blit(choice_text, choice_rect)
        else:
            # Feedback with bounce
            feedback_surf = self.font.render(self.feedback_text, True, config.YELLOW)
            feedback_rect = feedback_surf.get_rect(center=(config.SCREEN_WIDTH // 2, 350))
            # Blocky background
            bg_rect = feedback_rect.inflate(40, 20)
            pygame.draw.rect(screen, config.BLACK, bg_rect.move(4, 4))
            pygame.draw.rect(screen, config.DARK_GRAY, bg_rect)
            pygame.draw.rect(screen, config.YELLOW, bg_rect, 4)
            screen.blit(feedback_surf, feedback_rect)
        
        # Draw particles
        for particle in self.particles:
            alpha = int(255 * particle['life'])
            size = int(8 * particle['life'])
            if size > 0:
                pygame.draw.rect(screen, config.YELLOW, 
                               (int(particle['x']), int(particle['y']), size, size))
        
        # Score popup
        if self.score_popup and time.time() - self.score_popup_timer < 1:
            popup_y = 20 - int((time.time() - self.score_popup_timer) * 30)
            popup_alpha = int(255 * (1 - (time.time() - self.score_popup_timer)))
            popup_text = self.font.render(self.score_popup, True, config.YELLOW)
            popup_rect = popup_text.get_rect(center=(config.SCREEN_WIDTH - 150, popup_y))
            screen.blit(popup_text, popup_rect)
        
        # ESC to exit
        esc_text = self.font.render('ESC = bumalik', True, config.WHITE)
        screen.blit(esc_text, (20, config.SCREEN_HEIGHT - 50))


class SentenceSummitState(State):
    """Reading Fluency - Phil IRI Grade 1-3 Reading Passages"""
    def __init__(self, game):
        super().__init__(game)
        self.font = pygame.font.Font(None, config.FONT_LARGE)
        self.text_font = pygame.font.Font(None, config.FONT_MEDIUM)
        self.small_font = pygame.font.Font(None, config.FONT_SMALL)
        
        self.current_passage = None
        self.passage_index = 0
        self.current_question = 0
        self.score = 0
        self.start_time = 0
        self.reading_start_time = 0
        self.choice_buttons = []
        self.showing_passage = True
        self.feedback_text = ''
        self.show_feedback = False
        self.feedback_timer = 0
    
    def enter(self):
        """Initialize reading assessment"""
        self.score = 0
        self.start_time = time.time()
        self.passage_index = 0
        self.load_passage()
    
    def load_passage(self):
        """Load a reading passage"""
        if self.passage_index >= len(config.READING_PASSAGES):
            self.next_state = 'menu'
            return
        
        self.current_passage = config.READING_PASSAGES[self.passage_index]
        self.current_question = 0
        self.showing_passage = True
        self.reading_start_time = time.time()
    
    def load_question(self):
        """Load next comprehension question"""
        if self.current_question >= len(self.current_passage['questions']):
            self.passage_index += 1
            self.load_passage()
            return
        
        question = self.current_passage['questions'][self.current_question]
        
        # Create choice buttons
        self.choice_buttons = []
        button_height = 60
        button_width = 700
        start_y = 420
        
        for i, choice in enumerate(question['choices']):
            button = pygame.Rect(150, start_y + i * 80, button_width, button_height)
            self.choice_buttons.append({
                'rect': button,
                'text': choice,
                'index': i
            })
    
    def exit(self):
        """Save progress"""
        time_spent = time.time() - self.start_time
        self.game.db.log_progress(
            config.DEFAULT_STUDENT_ID,
            'Reading Fluency',
            self.score,
            self.score // 10,  # Points as gems
            time_spent
        )
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.next_state = 'menu'
            elif event.key == pygame.K_SPACE and self.showing_passage:
                self.showing_passage = False
                self.load_question()
        
        if event.type == pygame.MOUSEBUTTONDOWN and not self.showing_passage and not self.show_feedback:
            mouse_pos = event.pos
            for button in self.choice_buttons:
                if button['rect'].collidepoint(mouse_pos):
                    question = self.current_passage['questions'][self.current_question]
                    if button['index'] == question['answer']:
                        self.score += config.POINTS_PER_CORRECT_ANSWER
                        self.feedback_text = 'Tama! ✓'
                    else:
                        self.feedback_text = f'Hindi tama. Tamang sagot: {question["choices"][question["answer"]]}'
                    self.show_feedback = True
                    self.feedback_timer = time.time()
    
    def update(self, dt):
        # Auto-advance after feedback
        if self.show_feedback and time.time() - self.feedback_timer > 3:
            self.show_feedback = False
            self.current_question += 1
            self.load_question()
    
    def draw(self, screen):
        screen.fill(config.ORANGE)
        
        # Title
        title = self.font.render('Reading Fluency', True, config.WHITE)
        screen.blit(title, (20, 20))
        
        # Score
        score_text = self.font.render(f'Score: {self.score}', True, config.YELLOW)
        screen.blit(score_text, (config.SCREEN_WIDTH - 250, 20))
        
        if self.showing_passage:
            # Level indicator
            level_text = self.font.render(self.current_passage['level'], True, config.YELLOW)
            screen.blit(level_text, (20, 70))
            
            # Title of passage
            title_text = self.font.render(self.current_passage['title'], True, config.WHITE)
            title_rect = title_text.get_rect(center=(config.SCREEN_WIDTH // 2, 150))
            screen.blit(title_text, title_rect)
            
            # Passage text with word wrap
            y_offset = 220
            words = self.current_passage['text'].split()
            lines = []
            current_line = []
            for word in words:
                test_line = ' '.join(current_line + [word])
                if self.text_font.size(test_line)[0] < 700:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            lines.append(' '.join(current_line))
            
            for line in lines:
                line_surf = self.text_font.render(line, True, config.WHITE)
                line_rect = line_surf.get_rect(center=(config.SCREEN_WIDTH // 2, y_offset))
                screen.blit(line_surf, line_rect)
                y_offset += 40
            
            # Instruction
            inst_text = self.font.render('Basahin mabuti. SPACE = Patuloy', True, config.YELLOW)
            inst_rect = inst_text.get_rect(center=(config.SCREEN_WIDTH // 2, 600))
            screen.blit(inst_text, inst_rect)
        
        elif not self.show_feedback:
            # Question
            question = self.current_passage['questions'][self.current_question]
            q_text = self.font.render(question['q'], True, config.WHITE)
            q_rect = q_text.get_rect(center=(config.SCREEN_WIDTH // 2, 200))
            screen.blit(q_text, q_rect)
            
            # Progress
            progress = self.text_font.render(
                f'Tanong {self.current_question + 1}/{len(self.current_passage["questions"])}',
                True, config.YELLOW
            )
            screen.blit(progress, (20, 70))
            
            # Choices
            for button in self.choice_buttons:
                pygame.draw.rect(screen, config.LIGHT_GRAY, button['rect'])
                pygame.draw.rect(screen, config.BLACK, button['rect'], 3)
                
                choice_text = self.text_font.render(button['text'], True, config.BLACK)
                choice_rect = choice_text.get_rect(center=button['rect'].center)
                screen.blit(choice_text, choice_rect)
        
        else:
            # Feedback
            feedback_surf = self.font.render(self.feedback_text, True, config.YELLOW)
            feedback_rect = feedback_surf.get_rect(center=(config.SCREEN_WIDTH // 2, 400))
            screen.blit(feedback_surf, feedback_rect)
        
        # ESC to exit
        esc_text = self.text_font.render('ESC = bumalik', True, config.WHITE)
        screen.blit(esc_text, (20, config.SCREEN_HEIGHT - 50))


class StorySeaState(State):
    """Advanced Reading Comprehension - Phil IRI Grade 4-6"""
    def __init__(self, game):
        super().__init__(game)
        self.font = pygame.font.Font(None, config.FONT_LARGE)
        self.text_font = pygame.font.Font(None, config.FONT_MEDIUM)
        self.small_font = pygame.font.Font(None, config.FONT_SMALL)
        
        self.current_story = None
        self.story_index = 0
        self.current_question = 0
        self.score = 0
        self.start_time = 0
        self.reading_start_time = 0
        self.choice_buttons = []
        self.showing_story = True
        self.feedback_text = ''
        self.show_feedback = False
        self.feedback_timer = 0
        self.scroll_offset = 0
    
    def enter(self):
        """Initialize comprehension assessment"""
        self.score = 0
        self.start_time = time.time()
        self.story_index = 0
        self.load_story()
    
    def load_story(self):
        """Load a comprehension story"""
        if self.story_index >= len(config.COMPREHENSION_STORIES):
            self.next_state = 'menu'
            return
        
        self.current_story = config.COMPREHENSION_STORIES[self.story_index]
        self.current_question = 0
        self.showing_story = True
        self.reading_start_time = time.time()
        self.scroll_offset = 0
    
    def load_question(self):
        """Load next comprehension question"""
        if self.current_question >= len(self.current_story['questions']):
            self.story_index += 1
            self.load_story()
            return
        
        question = self.current_story['questions'][self.current_question]
        
        # Create choice buttons
        self.choice_buttons = []
        button_height = 70
        button_width = 750
        start_y = 380
        
        for i, choice in enumerate(question['choices']):
            button = pygame.Rect(130, start_y + i * 90, button_width, button_height)
            self.choice_buttons.append({
                'rect': button,
                'text': choice,
                'index': i
            })
    
    def exit(self):
        """Save progress"""
        time_spent = time.time() - self.start_time
        self.game.db.log_progress(
            config.DEFAULT_STUDENT_ID,
            'Comprehension',
            self.score,
            self.score // 10,
            time_spent
        )
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.next_state = 'menu'
            elif event.key == pygame.K_SPACE and self.showing_story:
                self.showing_story = False
                self.load_question()
            elif event.key == pygame.K_DOWN and self.showing_story:
                self.scroll_offset = min(self.scroll_offset + 20, 100)
            elif event.key == pygame.K_UP and self.showing_story:
                self.scroll_offset = max(self.scroll_offset - 20, 0)
        
        if event.type == pygame.MOUSEBUTTONDOWN and not self.showing_story and not self.show_feedback:
            mouse_pos = event.pos
            for button in self.choice_buttons:
                if button['rect'].collidepoint(mouse_pos):
                    question = self.current_story['questions'][self.current_question]
                    if button['index'] == question['answer']:
                        self.score += config.POINTS_PER_CORRECT_ANSWER * 2  # Higher points for harder questions
                        self.feedback_text = 'Tama! Napakahusay! ✓'
                    else:
                        correct_answer = question['choices'][question['answer']]
                        self.feedback_text = f'Hindi tama. Tamang sagot: {correct_answer}'
                    self.show_feedback = True
                    self.feedback_timer = time.time()
    
    def update(self, dt):
        # Auto-advance after feedback
        if self.show_feedback and time.time() - self.feedback_timer > 3:
            self.show_feedback = False
            self.current_question += 1
            self.load_question()
    
    def draw(self, screen):
        screen.fill(config.PURPLE)
        
        # Title
        title = self.font.render('Reading Comprehension', True, config.WHITE)
        screen.blit(title, (20, 20))
        
        # Score
        score_text = self.font.render(f'Score: {self.score}', True, config.YELLOW)
        screen.blit(score_text, (config.SCREEN_WIDTH - 250, 20))
        
        if self.showing_story:
            # Level indicator
            level_text = self.font.render(self.current_story['level'], True, config.YELLOW)
            screen.blit(level_text, (20, 70))
            
            # Story title
            title_text = self.font.render(self.current_story['title'], True, config.WHITE)
            title_rect = title_text.get_rect(center=(config.SCREEN_WIDTH // 2, 130))
            screen.blit(title_text, title_rect)
            
            # Story text with scrolling support
            y_offset = 190 - self.scroll_offset
            paragraphs = self.current_story['text'].split('\\n\\n')
            
            for paragraph in paragraphs:
                words = paragraph.split()
                lines = []
                current_line = []
                for word in words:
                    test_line = ' '.join(current_line + [word])
                    if self.small_font.size(test_line)[0] < 900:
                        current_line.append(word)
                    else:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                lines.append(' '.join(current_line))
                
                for line in lines:
                    if 170 < y_offset < 550:  # Only show visible lines
                        line_surf = self.small_font.render(line, True, config.WHITE)
                        screen.blit(line_surf, (60, y_offset))
                    y_offset += 35
                y_offset += 20  # Space between paragraphs
            
            # Instruction
            inst_text = self.text_font.render('Basahin mabuti. SPACE = Patuloy', True, config.YELLOW)
            inst_rect = inst_text.get_rect(center=(config.SCREEN_WIDTH // 2, 650))
            screen.blit(inst_text, inst_rect)
            
            arrow_text = self.small_font.render('↑↓ = Scroll', True, config.WHITE)
            screen.blit(arrow_text, (20, 650))
        
        elif not self.show_feedback:
            # Question
            question = self.current_story['questions'][self.current_question]
            
            # Word wrap question
            q_words = question['q'].split()
            q_lines = []
            current_line = []
            for word in q_words:
                test_line = ' '.join(current_line + [word])
                if self.text_font.size(test_line)[0] < 900:
                    current_line.append(word)
                else:
                    q_lines.append(' '.join(current_line))
                    current_line = [word]
            q_lines.append(' '.join(current_line))
            
            y_offset = 200
            for line in q_lines:
                line_surf = self.text_font.render(line, True, config.WHITE)
                line_rect = line_surf.get_rect(center=(config.SCREEN_WIDTH // 2, y_offset))
                screen.blit(line_surf, line_rect)
                y_offset += 40
            
            # Progress
            progress = self.text_font.render(
                f'Tanong {self.current_question + 1}/{len(self.current_story["questions"])}',
                True, config.YELLOW
            )
            screen.blit(progress, (20, 70))
            
            # Choices
            for button in self.choice_buttons:
                pygame.draw.rect(screen, config.LIGHT_GRAY, button['rect'])
                pygame.draw.rect(screen, config.BLACK, button['rect'], 3)
                
                # Word wrap choices
                choice_words = button['text'].split()
                choice_lines = []
                current_line = []
                for word in choice_words:
                    test_line = ' '.join(current_line + [word])
                    if self.small_font.size(test_line)[0] < 720:
                        current_line.append(word)
                    else:
                        choice_lines.append(' '.join(current_line))
                        current_line = [word]
                choice_lines.append(' '.join(current_line))
                
                y_off = button['rect'].centery - (len(choice_lines) * 15)
                for line in choice_lines:
                    choice_text = self.small_font.render(line, True, config.BLACK)
                    choice_rect = choice_text.get_rect(center=(button['rect'].centerx, y_off))
                    screen.blit(choice_text, choice_rect)
                    y_off += 30
        
        else:
            # Feedback - word wrap
            feedback_words = self.feedback_text.split()
            feedback_lines = []
            current_line = []
            for word in feedback_words:
                test_line = ' '.join(current_line + [word])
                if self.text_font.size(test_line)[0] < 900:
                    current_line.append(word)
                else:
                    feedback_lines.append(' '.join(current_line))
                    current_line = [word]
            feedback_lines.append(' '.join(current_line))
            
            y_offset = 350
            for line in feedback_lines:
                feedback_surf = self.text_font.render(line, True, config.YELLOW)
                feedback_rect = feedback_surf.get_rect(center=(config.SCREEN_WIDTH // 2, y_offset))
                screen.blit(feedback_surf, feedback_rect)
                y_offset += 45
        
        # ESC to exit
        esc_text = self.text_font.render('ESC = bumalik', True, config.WHITE)
        screen.blit(esc_text, (20, config.SCREEN_HEIGHT - 50))


class TeacherDashboardState(State):
    """Teacher dashboard for viewing student progress"""
    def __init__(self, game):
        super().__init__(game)
        self.font = pygame.font.Font(None, config.FONT_MEDIUM)
        self.small_font = pygame.font.Font(None, config.FONT_SMALL)
        self.report = None
        self.authenticated = False
        self.password_input = ''
    
    def enter(self):
        """Load report data"""
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
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.next_state = 'menu'
    
    def update(self, dt):
        pass
    
    def draw(self, screen):
        screen.fill(config.DARK_GRAY)
        
        if not self.authenticated:
            # Password entry
            prompt = self.font.render('Teacher Password:', True, config.WHITE)
            prompt_rect = prompt.get_rect(center=(config.SCREEN_WIDTH // 2, 300))
            screen.blit(prompt, prompt_rect)
            
            password_display = '*' * len(self.password_input)
            pass_surf = self.font.render(password_display, True, config.YELLOW)
            pass_rect = pass_surf.get_rect(center=(config.SCREEN_WIDTH // 2, 350))
            screen.blit(pass_surf, pass_rect)
            
            hint = self.small_font.render('Press ENTER to submit, ESC to cancel', True, config.LIGHT_GRAY)
            hint_rect = hint.get_rect(center=(config.SCREEN_WIDTH // 2, 450))
            screen.blit(hint, hint_rect)
        
        else:
            # Dashboard
            title = self.font.render('Teacher Dashboard', True, config.WHITE)
            screen.blit(title, (50, 30))
            
            # Report data
            y_offset = 100
            
            total_sessions = self.font.render(f'Total Sessions: {self.report["total_sessions"]}', 
                                            True, config.WHITE)
            screen.blit(total_sessions, (50, y_offset))
            y_offset += 50
            
            avg_time = self.font.render(f'Avg Time per Module: {self.report["avg_time_per_module"]:.1f}s', 
                                       True, config.WHITE)
            screen.blit(avg_time, (50, y_offset))
            y_offset += 80
            
            # Student stats
            students_title = self.font.render('Student Progress:', True, config.YELLOW)
            screen.blit(students_title, (50, y_offset))
            y_offset += 50
            
            for student in self.report['students']:
                student_line = self.small_font.render(
                    f'{student[0]}: {student[1]} gems | P:{student[2]} S:{student[3]} St:{student[4]}',
                    True, config.WHITE
                )
                screen.blit(student_line, (70, y_offset))
                y_offset += 35
            
            # Exit hint
            esc_text = self.small_font.render('Press ESC to return', True, config.LIGHT_GRAY)
            screen.blit(esc_text, (50, config.SCREEN_HEIGHT - 50))


class BarangayCaptainState(State):
    """Barangay Captain Simulator - Decision making game"""
    def __init__(self, game):
        super().__init__(game)
        self.current_question = 0
        self.score = 0
        self.happiness = 50  # Start at 50
        self.selected_choice = None
        self.show_result = False
        self.result_timer = 0
        self.font = pygame.font.Font(config.FONT_PATH, 24)  # Use Pixelify Sans
        self.title_font = pygame.font.Font(config.FONT_PATH, 36)
        self.small_font = pygame.font.Font(config.FONT_PATH, 18)
    
    def enter(self):
        self.current_question = 0
        self.score = 0
        self.happiness = 50
        self.selected_choice = None
        self.show_result = False
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.next_state = 'menu'
            elif not self.show_result:
                if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                    choice_index = event.key - pygame.K_1
                    if choice_index < len(config.BARANGAY_COMPLAINTS[self.current_question]['choices']):
                        self.selected_choice = choice_index
                        self.show_result = True
                        self.result_timer = time.time()
                        # Update score and happiness
                        if choice_index == config.BARANGAY_COMPLAINTS[self.current_question]['correct']:
                            self.score += 1
                        self.happiness += config.BARANGAY_COMPLAINTS[self.current_question]['happiness_impact'][choice_index]
                        self.happiness = max(0, min(100, self.happiness))  # Clamp between 0-100
            elif self.show_result and time.time() - self.result_timer > 2:  # Show result for 2 seconds
                self.current_question += 1
                if self.current_question >= len(config.BARANGAY_COMPLAINTS):
                    # Game over, show final score
                    self.next_state = 'menu'  # Or a results state
                else:
                    self.show_result = False
                    self.selected_choice = None
    
    def draw(self, screen):
        screen.fill(config.BLUE)
        
        if self.current_question < len(config.BARANGAY_COMPLAINTS):
            complaint = config.BARANGAY_COMPLAINTS[self.current_question]
            
            # Title
            title = self.title_font.render('Barangay Captain Simulator', True, config.WHITE)
            screen.blit(title, (50, 50))
            
            # Happiness meter
            happiness_text = self.font.render(f'Happiness: {self.happiness}/100', True, config.YELLOW)
            screen.blit(happiness_text, (50, 120))
            
            # Complaint
            complaint_lines = self.wrap_text(complaint['complaint'], 60)
            y = 180
            for line in complaint_lines:
                text = self.font.render(line, True, config.WHITE)
                screen.blit(text, (50, y))
                y += 40
            
            # Choices
            y = 300
            for i, choice in enumerate(complaint['choices']):
                color = config.GREEN if not self.show_result else (config.RED if i != complaint['correct'] else config.GREEN)
                if self.show_result and i == self.selected_choice:
                    color = config.ORANGE
                choice_text = self.font.render(f'{i+1}. {choice}', True, color)
                screen.blit(choice_text, (50, y))
                y += 50
            
            if self.show_result:
                result_text = self.font.render('Correct!' if self.selected_choice == complaint['correct'] else 'Incorrect!', True, config.WHITE)
                screen.blit(result_text, (50, y + 20))
        else:
            # Game over
            end_text = self.title_font.render('Game Complete!', True, config.WHITE)
            screen.blit(end_text, (50, 200))
            score_text = self.font.render(f'Final Score: {self.score}/{len(config.BARANGAY_COMPLAINTS)}', True, config.WHITE)
            screen.blit(score_text, (50, 300))
            happiness_text = self.font.render(f'Final Happiness: {self.happiness}/100', True, config.WHITE)
            screen.blit(happiness_text, (50, 350))
    
    def wrap_text(self, text, max_chars):
        words = text.split()
        lines = []
        current_line = ''
        for word in words:
            if len(current_line + word) + 1 <= max_chars:
                current_line += ' ' + word if current_line else word
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines


class RecipeGameState(State):
    """Recipe Reading and Comprehension Game"""
    def __init__(self, game):
        super().__init__(game)
        self.current_recipe = 0
        self.current_question = 0
        self.score = 0
        self.selected_choice = None
        self.show_result = False
        self.result_timer = 0
        self.font = pygame.font.Font(config.FONT_PATH, 24)  # Use Pixelify Sans
        self.title_font = pygame.font.Font(config.FONT_PATH, 36)
        self.recipe_shown = False
    
    def enter(self):
        self.current_recipe = 0
        self.current_question = 0
        self.score = 0
        self.selected_choice = None
        self.show_result = False
        self.recipe_shown = False
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.next_state = 'menu'
            elif not self.recipe_shown:
                if event.key == pygame.K_SPACE:
                    self.recipe_shown = True
            elif self.current_question < len(config.RECIPES[self.current_recipe]['questions']):
                if not self.show_result:
                    if event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                        choice_index = event.key - pygame.K_1
                        question = config.RECIPES[self.current_recipe]['questions'][self.current_question]
                        if choice_index < len(question['choices']):
                            self.selected_choice = choice_index
                            self.show_result = True
                            self.result_timer = time.time()
                            if choice_index == question['answer']:
                                self.score += 1
                elif time.time() - self.result_timer > 2:
                    self.current_question += 1
                    if self.current_question >= len(config.RECIPES[self.current_recipe]['questions']):
                        # Recipe complete
                        self.next_state = 'menu'  # Or next recipe
                    else:
                        self.show_result = False
                        self.selected_choice = None
    
    def draw(self, screen):
        screen.fill(config.GREEN)
        
        recipe = config.RECIPES[self.current_recipe]
        
        # Title
        title = self.title_font.render(recipe['title'], True, config.BLACK)
        screen.blit(title, (50, 50))
        
        if not self.recipe_shown:
            # Show recipe
            y = 120
            ingredients_title = self.font.render('Ingredients:', True, config.BLACK)
            screen.blit(ingredients_title, (50, y))
            y += 40
            for ingredient in recipe['ingredients']:
                ing_text = self.font.render(f'• {ingredient}', True, config.BLACK)
                screen.blit(ing_text, (70, y))
                y += 30
            
            y += 20
            directions_title = self.font.render('Directions:', True, config.BLACK)
            screen.blit(directions_title, (50, y))
            y += 40
            for i, direction in enumerate(recipe['directions'], 1):
                dir_text = self.font.render(f'{i}. {direction}', True, config.BLACK)
                screen.blit(dir_text, (50, y))
                y += 30
            
            space_text = self.font.render('Press SPACE to start questions', True, config.BLUE)
            screen.blit(space_text, (50, config.SCREEN_HEIGHT - 100))
        elif self.current_question < len(recipe['questions']):
            question = recipe['questions'][self.current_question]
            
            # Question
            q_text = self.font.render(question['q'], True, config.BLACK)
            screen.blit(q_text, (50, 150))
            
            # Choices
            y = 220
            for i, choice in enumerate(question['choices']):
                color = config.BLUE
                if self.show_result:
                    if i == question['answer']:
                        color = config.GREEN
                    elif i == self.selected_choice:
                        color = config.RED
                choice_text = self.font.render(f'{i+1}. {choice}', True, color)
                screen.blit(choice_text, (50, y))
                y += 40
            
            if self.show_result:
                result = 'Correct!' if self.selected_choice == question['answer'] else 'Incorrect!'
                result_text = self.font.render(result, True, config.BLACK)
                screen.blit(result_text, (50, y + 20))
        else:
            # Complete
            complete_text = self.title_font.render('Recipe Complete!', True, config.BLACK)
            screen.blit(complete_text, (50, 200))
            score_text = self.font.render(f'Score: {self.score}/{len(recipe["questions"])}', True, config.BLACK)
            screen.blit(score_text, (50, 300))
