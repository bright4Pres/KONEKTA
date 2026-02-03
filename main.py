"""
Main game loop for Assistive Literacy Learning System
Handles state management, event processing, and game flow
"""

import pygame
import sys
import time
import config
from database import Database
from states import (
    MenuState, 
    PhonicsForestState, 
    SentenceSummitState, 
    StorySeaState,
    TeacherDashboardState
)

class Game:
    """Main game class with state machine"""
    def __init__(self):
        # Initialize Pygame
        pygame.init()
        pygame.mixer.init()
        
        # Screen setup
        if config.KIOSK_MODE:
            self.screen = pygame.display.set_mode(
                (config.SCREEN_WIDTH, config.SCREEN_HEIGHT),
                pygame.FULLSCREEN
            )
        else:
            self.screen = pygame.display.set_mode(
                (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
            )
        
        pygame.display.set_caption("BAYOT SI JARED 2.0")
        
        # Clock for FPS
        self.clock = pygame.time.Clock()
        
        # Fonts
        self.font_title = pygame.font.Font(None, config.FONT_TITLE)
        self.font_large = pygame.font.Font(None, config.FONT_LARGE)
        self.font_medium = pygame.font.Font(None, config.FONT_MEDIUM)
        self.font_small = pygame.font.Font(None, config.FONT_SMALL)
        
        # Database
        self.db = Database()
        
        # State management
        self.states = {
            'menu': MenuState(self),
            'phonics': PhonicsForestState(self),
            'summit': SentenceSummitState(self),
            'story': StorySeaState(self),
            'teacher': TeacherDashboardState(self)
        }
        
        self.current_state = self.states['menu']
        self.current_state.enter()
        
        # Session tracking
        self.session_id = self.db.start_session(config.DEFAULT_STUDENT_ID)
        self.session_start = time.time()
        
        # Teacher dashboard key combo tracking
        self.keys_pressed = set()
    
    def handle_events(self):
        """Process all pygame events"""
        for event in pygame.event.get():
            # Quit event (disabled in kiosk mode)
            if event.type == pygame.QUIT:
                if not config.KIOSK_MODE:
                    return False
            
            # Key tracking for teacher dashboard
            if event.type == pygame.KEYDOWN:
                key_name = pygame.key.name(event.key).upper()
                self.keys_pressed.add(key_name)
                
                # Check for teacher dashboard combo (Ctrl+T)
                if 'LEFT CTRL' in self.keys_pressed or 'RIGHT CTRL' in self.keys_pressed:
                    if 'T' in self.keys_pressed:
                        self.change_state('teacher')
                        self.keys_pressed.clear()
                        continue
                
                # ESC key behavior in kiosk mode
                if event.key == pygame.K_ESCAPE and config.KIOSK_MODE:
                    # Only allow ESC to go back to menu, not quit
                    if self.current_state != self.states['menu']:
                        self.change_state('menu')
                    continue
            
            if event.type == pygame.KEYUP:
                key_name = pygame.key.name(event.key).upper()
                self.keys_pressed.discard(key_name)
            
            # Pass event to current state
            self.current_state.handle_event(event)
        
        return True
    
    def update(self):
        """Update game logic"""
        dt = self.clock.get_time()
        self.current_state.update(dt)
        
        # Check for state changes
        if self.current_state.next_state:
            self.change_state(self.current_state.next_state)
    
    def change_state(self, new_state_name):
        """Change to a new game state"""
        if new_state_name in self.states:
            self.current_state.exit()
            self.current_state.next_state = None
            self.current_state = self.states[new_state_name]
            self.current_state.enter()
    
    def draw(self):
        """Render current state"""
        self.current_state.draw(self.screen)
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(config.FPS)
        
        self.cleanup()
    
    def cleanup(self):
        """Cleanup before exit"""
        # End session
        session_duration = time.time() - self.session_start
        self.db.end_session(self.session_id, session_duration)
        
        pygame.quit()
        sys.exit()

def main():
    """Entry point"""
    game = Game()
    game.run()

if __name__ == '__main__':
    main()