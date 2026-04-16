# main game file or whatever
# this runs everything i think

import pygame
import sys
import time
import os
import config
from database import Database
from states import (
    TitleScreenState,
    MenuState, 
    TeacherDashboardState,
    BarangayCaptainState,
    RecipeGameState,
    SynonymAntonymState
)
# - if controls feel dead, check handle_events first before blaming pygame.
# - session tracking starts here and closes in cleanup.
# - student id now matters for leaderboard rows, so menu -> game flow needs it set.
# - esc behavior: in-game goes menu first, menu esc exits app.

class Game:
    """core runtime shell.

    Footnotes:
    - Keeps one state active at a time.
    - Owns shared systems (db, fonts, screen, clock).
    - Probably the first file to inspect when flow feels cursed.
    """
    def __init__(self):
        # start pygame
        pygame.init()
        self.audio_enabled = False
        try:
            pygame.mixer.init()
            self.audio_enabled = True
        except pygame.error:
            # run silently without audio if mixer init fails on target machine
            self.audio_enabled = False
        
        # screen stuff
        if config.KIOSK_MODE:
            # get the screen size idk
            infoObject = pygame.display.Info()
            self.screen = pygame.display.set_mode(
                (infoObject.current_w, infoObject.current_h),
                pygame.FULLSCREEN
            )
            # update size values
            config.SCREEN_WIDTH = self.screen.get_width()
            config.SCREEN_HEIGHT = self.screen.get_height()
        else:
            self.screen = pygame.display.set_mode(
                (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
            )
        
        pygame.display.set_caption("Konekta the Game")
        try:
            if os.path.exists(config.WINDOW_ICON_PATH):
                pygame.display.set_icon(pygame.image.load(config.WINDOW_ICON_PATH).convert_alpha())
        except Exception:
            # icon load failure should never block app startup
            pass
        
        # clock for timing
        self.clock = pygame.time.Clock()
        
        # load the fonts
        self.font_title = pygame.font.Font(None, config.FONT_TITLE)
        self.font_large = pygame.font.Font(None, config.FONT_LARGE)
        self.font_medium = pygame.font.Font(None, config.FONT_MEDIUM)
        self.font_small = pygame.font.Font(None, config.FONT_SMALL)
        
        # db
        self.db = Database()

        # active player profile used for score logging
        self.current_student_id = config.DEFAULT_STUDENT_ID
        
        # all the different game screens (singletons per run)
        self.states = {
            'title': TitleScreenState(self),
            'menu': MenuState(self),
            'teacher': TeacherDashboardState(self),
            'barangay': BarangayCaptainState(self),
            'recipe': RecipeGameState(self),
            'synonym_antonym': SynonymAntonymState(self)
        }
        
        self.current_music_track = None
        self.current_state = self.states['title']
        self.current_state.enter()
        self._update_music_for_state('title')
        
        # track how long they play
        self.session_id = self.db.start_session(self.current_student_id)
        self.session_start = time.time()
        
        # keys being held rn
        self.keys_pressed = set()

    def _music_track_for_state(self, state_name):
        """Mini-games use game music; menu/title/teacher use background music."""
        if state_name in {'barangay', 'recipe', 'synonym_antonym'}:
            return config.GAME_MUSIC_PATH
        return config.BG_MUSIC_PATH

    def _play_looping_music(self, track_path):
        """Load a music file and loop it forever, avoiding redundant reloads."""
        if not self.audio_enabled or not track_path:
            return

        normalized = os.path.normcase(os.path.normpath(track_path))
        if self.current_music_track == normalized:
            if not pygame.mixer.music.get_busy():
                try:
                    pygame.mixer.music.play(-1)
                except pygame.error:
                    pass
            return

        if not os.path.exists(track_path):
            return

        try:
            pygame.mixer.music.load(track_path)
            pygame.mixer.music.set_volume(config.MUSIC_VOLUME)
            pygame.mixer.music.play(-1)
            self.current_music_track = normalized
        except pygame.error:
            pass

    def _update_music_for_state(self, state_name):
        """Switch track whenever game context changes."""
        self._play_looping_music(self._music_track_for_state(state_name))
    
    def handle_events(self):
        """handle events"""
        # event fan-out rules live here; states only get events after global hotkeys run.
        for event in pygame.event.get():
            # quit (doesnt work in kiosk mode tho)
            if event.type == pygame.QUIT:
                if not config.KIOSK_MODE:
                    return False
            
            # check what keys are pressed
            if event.type == pygame.KEYDOWN:
                key_name = pygame.key.name(event.key).upper()
                self.keys_pressed.add(key_name)
                
                # ctrl+t opens the teacher thing
                if 'LEFT CTRL' in self.keys_pressed or 'RIGHT CTRL' in self.keys_pressed:
                    if 'T' in self.keys_pressed:
                        self.change_state('teacher')
                        self.keys_pressed.clear()
                        continue
                
                # esc key doesnt quit in kiosk mode
                if event.key == pygame.K_ESCAPE:
                    if self.current_state != self.states['menu']:
                        # in-game ESC always returns to menu first
                        self.change_state('menu')
                        continue

                    # on menu, ESC exits even in kiosk so teacher can close app quickly
                    return False
            
            if event.type == pygame.KEYUP:
                key_name = pygame.key.name(event.key).upper()
                self.keys_pressed.discard(key_name)
            
            # give the event to whatever screen is active
            self.current_state.handle_event(event)
        
        return True
    
    def update(self):
        """update stuff"""
        # dt is seconds, not ms, so movement math elsewhere assumes that.
        dt = self.clock.get_time() / 1000.0   # milliseconds to seconds
        self.current_state.update(dt)
        
        # switch screens if needed
        if self.current_state.next_state:
            self.change_state(self.current_state.next_state)
    
    def change_state(self, new_state_name):
        """switch to a different screen"""
        if new_state_name in self.states:
            self.current_state.exit()
            self.current_state.next_state = None
            self.current_state = self.states[new_state_name]
            self.current_state.enter()
            self._update_music_for_state(new_state_name)

    def set_current_student(self, student_id):
        """switch active profile and start a fresh session for that profile"""
        sid = str(student_id).strip() or config.DEFAULT_STUDENT_ID
        if sid == self.current_student_id:
            return

        now = time.time()
        if getattr(self, 'session_id', None):
            session_duration = max(0.0, now - self.session_start)
            self.db.end_session(self.session_id, session_duration)

        self.current_student_id = sid
        self.session_id = self.db.start_session(sid)
        self.session_start = now
    
    def draw(self):
        """draw everything"""
        self.current_state.draw(self.screen)
        pygame.display.flip()
    
    def run(self):
        """the main loop that keeps everything going"""
        running = True
        
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(config.FPS)
        
        self.cleanup()
    
    def cleanup(self):
        """clean up before closing"""
        # end the session and save it (even if user rage-quits with esc lol)
        session_duration = time.time() - self.session_start
        self.db.end_session(self.session_id, session_duration)

        if self.audio_enabled:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
            except pygame.error:
                pass
        
        pygame.quit()
        sys.exit()

def main():
    """runs the game"""
    game = Game()
    game.run()

if __name__ == '__main__':
    main()