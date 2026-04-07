# KONEKTA

KONEKTA is a classroom literacy arcade built with Pygame. Students move around a tilemap, enter mini-games, answer questions, and get tracked on a local leaderboard.

The project is designed for offline school deployment, with local data storage through SQLite.

## What is in the game right now

- Overworld map navigation
- Three mini-games:
   - Barangay Captain Simulator
   - Recipe Game
   - Word Match Game
- Language options: English, Tagalog, and Bisaya/Cebuano
- Teacher dashboard (overview + leaderboard + question editor)
- Player profile input (student ID)
- Local progress/session tracking

## Important architecture note

Question banks are now database-driven.

The games read questions from the `custom_questions` table, not from hardcoded arrays in config. If no questions exist for a game/language, that game will show a "NO QUESTIONS FOUND" screen.

Before classroom use, add questions in Teacher Mode.

## Requirements

- Python 3.8+
- Dependencies from `requirements.txt`:
   - `pygame-ce`
   - `pyinstaller` (only needed when building an executable)

## Local setup

1. Clone or download this repository.
2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3. Run the game:
    ```bash
    python main.py
    ```

## Build executable (Windows)

Use the included PyInstaller spec file:

```bash
pyinstaller KONEKTA.spec
```

Build output folders:

- `dist/KONEKTA/`
- `build/KONEKTA/`

## Controls

### Global controls

- Arrow keys or WASD: Move on map
- Shift: Run
- Space or E: Enter nearby game zone
- Tab (while on map): Edit player ID
- Ctrl+T: Open Teacher Mode
- Esc:
   - In mini-game screens: return to map
   - On the map screen: exit the app

### Mini-game controls

- 1 / 2 / 3: Select language
- 1 / 2 / 3 / 4: Pick answer choice
- Enter (end screen): Save score to leaderboard
- Esc: Return to map

### Teacher Mode controls

- Password screen:
   - Enter: submit password
   - Esc: return to map
- Tabs:
   - 1: Overview
   - 2: Leaderboard
   - 3: Question Forge
- F5: Refresh dashboard data

Question Forge shortcuts:

- Left/Right: Change target game
- PageUp/PageDown: Change language
- Up/Down/Tab: Move between fields
- Enter: Next field (or save on last field)
- F6: Save question

## Teacher workflow (recommended)

1. Launch game.
2. Press Ctrl+T to open Teacher Mode.
3. Log in.
4. Open Question Forge.
5. Add question sets for each game and language you will use.
6. Run each mini-game once to verify content loads.

## Configuration

Main settings live in `config.py`.

Most important values:

- `KIOSK_MODE`
   - `True`: fullscreen kiosk behavior
   - `False`: windowed development mode
- `TEACHER_PASSWORD`
- `DEFAULT_STUDENT_ID`
- `SCREEN_WIDTH`, `SCREEN_HEIGHT`, `FPS`

Database file path is also configured there (`DATABASE_NAME`, defaulting to `konekta.db`).

## Data storage

The app uses a local SQLite file:

- `konekta.db`

Main tables:

- `progress`: per-game completion logs
- `student_stats`: cumulative student counters
- `sessions`: session start/end + duration
- `leaderboard`: ranked score submissions
- `custom_questions`: teacher-authored content used by all mini-games

## Project structure

- `main.py`: app bootstrap, game loop, state switching
- `states.py`: all game states (menu, teacher dashboard, mini-games)
- `database.py`: SQLite schema and data access layer
- `tilemap.py`: CSV map loading, rendering, interactions, player movement
- `config.py`: global settings, colors/fonts, asset/database paths
- `resources/`: map CSVs, image assets, fonts, audio
- `KONEKTA.spec`: PyInstaller build config

## Asset notes

Expected asset locations:

- `resources/konekta/` for map CSV layers
- `resources/images/` for sprite/tile/UI assets
- `resources/audio/` for sound files

The game can still launch with missing assets, but visuals/audio will be incomplete.

## Troubleshooting

- "NO QUESTIONS FOUND" in a mini-game:
   - Add questions for that game/language in Teacher Mode -> Question Forge.
- Teacher Mode does not open:
   - Make sure the game window is focused, then press Ctrl+T.
- Scores are not on leaderboard:
   - Finish the mini-game and press Enter on the end screen to submit score.
- Need a clean test reset:
   - Close the app, rename/delete `konekta.db`, then relaunch.

## Credits

Project KONEKTA - Horizon 2

Philippine Science High School - Zamboanga Research Center (PSHS-ZRC)

Partner school: San Alfonso Elementary School (SAES)

## Legal Notice

Primary legal terms are in:

- `LICENSE.txt`

Supplemental project notice file:

- `COPYRIGHT_AND_DISTRIBUTION_NOTICE.md`

Use these files to enforce ownership attribution and prohibit unauthorized redistribution or false authorship claims.