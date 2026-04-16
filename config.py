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
# Question  nks are now database-driven.
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
# - frozen build reads bundled assets from sys._MEIPASS.
# - local source run reads assets from the project folder.
# - db writes go to a user-writable app-data folder in packaged mode.
if getattr(sys, 'frozen', False):
    RESOURCE_BASE = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.executable)))
else:
    RESOURCE_BASE = os.path.dirname(os.path.abspath(__file__))

RESOURCES_PATH = os.path.join(RESOURCE_BASE, 'resources')
IMAGE_PATH = os.path.join(RESOURCES_PATH, 'images')
AUDIO_PATH = os.path.join(RESOURCES_PATH, 'audio')
FONT_PATH = os.path.join(
    IMAGE_PATH,
    'Sunnyside_World_ASSET_PACK_V2.1',
    'Sunnyside_World_Assets',
    'UI',
    'Winter Pixel Font.TTF',
)


def _pick_image_path(*candidate_names):
    """Return first existing image path from candidates; fallback to first name."""
    for filename in candidate_names:
        candidate = os.path.join(IMAGE_PATH, filename)
        if os.path.exists(candidate):
            return candidate
    return os.path.join(IMAGE_PATH, candidate_names[0])


LOGO_IMAGE_PATH = _pick_image_path('konekta_logo.png')
TITLE_SCREEN_IMAGE_PATH = _pick_image_path('konekta_title_screen.png', 'konekta_title_page.png')
WINDOW_ICON_PATH = _pick_image_path('konekta_logo.ico', 'konekta_logo.png')

def resolve_app_data_path():
    """Choose a writable folder for persistent data."""
    if not getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(__file__))

    local_appdata = os.environ.get('LOCALAPPDATA')
    if local_appdata:
        return os.path.join(local_appdata, 'KONEKTA')

    return os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'KONEKTA')


APP_DATA_PATH = resolve_app_data_path()
try:
    os.makedirs(APP_DATA_PATH, exist_ok=True)
except OSError:
    # emergency fallback so runtime can still continue even if app-data path fails
    APP_DATA_PATH = os.path.dirname(
        os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__)
    )

DATABASE_NAME = os.path.join(APP_DATA_PATH, 'konekta.db')