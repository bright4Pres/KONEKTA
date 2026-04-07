# config file
# all the settings and stuff for the game

import sys
import os

# dev footnotes / random brain dump:
# - this is basically the global knobs file. tweak stuff here first before panic-debugging.
# - question banks are NOT here anymore (db only now), so dont waste time hunting long arrays.
# - keeping colors + fonts here lets the states stay less noisy.
# - kiosk mode can be annoying during testing, flip it off if esc debugging gets weird.
# - path section at the bottom is super important for pyinstaller builds.
# - if assets "suddenly disappear", it is usually a bad path, not magic.

# screen settings
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1200
FPS = 165
KIOSK_MODE = True  # True = fullscreen, False = windowed (for testing)

# paths are defined at the bottom of the file

# colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)
BLUE = (0, 102, 204)
LIGHT_BLUE = (173, 216, 230)
RED = (220, 20, 60)
YELLOW = (255, 215, 0)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
ORANGE = (255, 140, 0)
PURPLE = (128, 0, 128)

# font sizes (bigger = easier to read i guess)
FONT_TITLE = 72
FONT_LARGE = 48
FONT_MEDIUM = 36
FONT_SMALL = 24

# points per answer
POINTS_PER_CORRECT_ANSWER = 10

# hint timing stuff
HINT_DELAY_MS = 5000  # 5 seconds
HOVER_HINT_DELAY_MS = 3000  # 3 seconds

# ---------------------------------------------------------------------------
# Question banks are now database-driven.
# Add/manage game questions in Teacher Mode (custom_questions table).
# ---------------------------------------------------------------------------
# Teacher dashboard settings
# ---------------------------------------------------------------------------
# note to self: yes password in plain text is ugly, but okay for local classroom setup rn.
TEACHER_PASSWORD = 'konekta2026'  # change this later or whatever
TEACHER_KEY_COMBO = ['LCTRL', 'T']  # Ctrl+T

# default student id for testing
DEFAULT_STUDENT_ID = 'student_demo'

# ---------------------------------------------------------------------------
# File paths
# ---------------------------------------------------------------------------
# pathing notes:
# - frozen build uses sys._MEIPASS, local run uses this file folder.
# - db path stays beside the app so teacher data survives normal reruns.
# sys._MEIPASS is where pyinstaller unpacks stuff at runtime
# otherwise just use the folder this file is in
if getattr(sys, 'frozen', False):
    _BASE = sys._MEIPASS
else:
    _BASE = os.path.dirname(os.path.abspath(__file__))

RESOURCES_PATH = os.path.join(_BASE, 'resources')
IMAGE_PATH = os.path.join(RESOURCES_PATH, 'images')
AUDIO_PATH = os.path.join(RESOURCES_PATH, 'audio')
FONT_PATH = os.path.join(
    IMAGE_PATH,
    'Sunnyside_World_ASSET_PACK_V2.1',
    'Sunnyside_World_Assets',
    'UI',
    'Winter Pixel Font.TTF',
)

# keep db in project folder for both source and packaged builds
DATABASE_NAME = os.path.join(_BASE, 'konekta.db')