# KONEKTA - Assistive Literacy Learning System

An offline-first educational game system designed for Project KONEKTA to improve literacy and digital skills for students at San Alfonso Elementary School (SAES). Built with Python and Pygame for deployment on refurbished hardware.

## 🎯 Mission

Provide an introductory foundation for children with limited technology access through an assistive, game-based learning system that strengthens literacy comprehension and digital competence.

## 🎮 Game Structure

### The Explorer's Map (Hub)
Students navigate a culturally relevant map of the Zamboanga Peninsula with three zones:

1. **Phonics Forest** (Always Unlocked)
   - Sound-catching mechanic where letters fall from the sky
   - Students use mouse/trackpad to catch letters matching phonemes
   - Teaches visual-auditory association and mouse coordination
   - **Unlock Requirement**: None (starter zone)

2. **Sentence Summit** (Unlocks at 10 gems)
   - Bridge repair mechanic with draggable word-blocks
   - Students construct sentences by arranging words in correct order
   - Locked words require typing to unlock
   - Hover hints provide audio support after 3 seconds
   - **Unlock Requirement**: 10 Knowledge Gems

3. **Story Sea** (Unlocks at 20 gems)
   - Interactive dialogue with local NPCs (Teacher Maria, Farmer Juan)
   - Branching narratives based on reading comprehension
   - Wrong answers trigger learning loops with simpler explanations
   - Stories aligned with community themes (agriculture, education)
   - **Unlock Requirement**: 20 Knowledge Gems

### Teacher Dashboard (Ctrl+T)
- Password-protected access for teachers
- View student progress, completion rates, time spent per module
- Generate usage reports for administrative records
- Default password: `konekta2026` (change in config.py)

## 🛠️ Technical Specifications

### Requirements
- Python 3.11+ (tested on 3.14)
- pygame-ce (Pygame Community Edition)
- SQLite3 (built into Python)
- pyinstaller (for deployment)

### System Features
- **Offline-First**: Runs locally without internet
- **Low-Resource**: Optimized for refurbished hardware
- **Kiosk Mode**: Fullscreen, prevents accidental exits
- **Assistive Features**: Timer-based hints, hover tooltips, audio feedback
- **Progress Tracking**: Local SQLite database
- **Safety**: No external links, closed system

## 📦 Installation

### Development Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the game
python main.py
```

### Deployment (Standalone Executable)
```bash
# Install PyInstaller
pip install pyinstaller

# Create executable
pyinstaller --onefile --windowed main.py

# Executable will be in dist/ folder
# Copy entire folder to USB drive for deployment
```

## 📁 Project Structure

```
KONEKTA/
├── main.py              # Main game loop and state machine
├── config.py            # Game constants and settings
├── database.py          # SQLite progress tracking
├── states.py            # All game state classes
├── requirements.txt     # Python dependencies
├── progress.db          # SQLite database (auto-created)
├── resources/
│   ├── audio/           # Audio files (.wav/.ogg)
│   │   └── README.txt   # Audio recording guidelines
│   └── images/          # Image assets (.png)
│       └── README.txt   # Image creation guidelines
└── README.md            # This file
```

## 🎨 Asset Guidelines

The game is **fully functional without assets** (uses geometric shapes and text).

### To Add Audio:
1. Record phoneme sounds for each letter (A="Ah", B="Buh", etc.)
2. Save as .wav or .ogg in `resources/audio/`
3. Follow naming: `ah.wav`, `buh.wav`, etc.
4. See `resources/audio/README.txt` for details

### To Add Images:
1. Create PNG images with transparency
2. Use high-contrast colors for accessibility
3. Save in `resources/images/`
4. See `resources/images/README.txt` for specifications

## 🎓 Pedagogy

### Grade 6 Learning Objectives
- **Phonics**: Letter-sound recognition, visual-auditory association
- **Sentence Structure**: Word order, grammar basics, typing skills
- **Reading Comprehension**: Context understanding, inference, critical thinking
- **Digital Literacy**: Mouse control, keyboard skills, UI navigation

### Assistive Features
- **5-second inactivity timer**: Triggers audio/text hints
- **3-second hover delay**: Provides contextual help
- **Immediate feedback**: Corrects misconceptions in real-time
- **Learning loops**: Re-explains concepts after wrong answers

## 👥 Configuration

### Kiosk Mode
Set in [config.py](config.py):
```python
KIOSK_MODE = True   # Production (fullscreen, locked)
KIOSK_MODE = False  # Development (windowed, ESC quits)
```

### Difficulty Adjustment
Modify in [config.py](config.py):
- `GEMS_TO_UNLOCK_SUMMIT`: Change unlock threshold
- `SENTENCES`: Add/edit sentence challenges
- `STORIES`: Add/edit comprehension stories

### Teacher Password
Change in [config.py](config.py):
```python
TEACHER_PASSWORD = 'your_password_here'
```

## 📊 Database Schema

### Tables
- **progress**: Individual module completions
- **student_stats**: Cumulative student data
- **sessions**: Login/logout tracking

### Teacher Reports
Access via Ctrl+T → Enter password
- Total sessions
- Average time per module
- Student-by-student breakdown
- Identifies learning bottlenecks

## 🚀 Deployment Checklist

### For SAES Installation:
1. ✅ Set `KIOSK_MODE = True` in config.py
2. ✅ Change `TEACHER_PASSWORD` in config.py
3. ✅ Build executable: `pyinstaller --onefile --windowed main.py`
4. ✅ Copy `dist/` folder + `resources/` to USB drive
5. ✅ Test on oldest available hardware
6. ✅ Print troubleshooting guide for ICT teacher
7. ✅ Provide teacher training on dashboard access

### Troubleshooting Guide (for SAES ICT Teacher)
- **Game won't start**: Check if Python is installed (not needed if using .exe)
- **Game freezes**: Restart computer, ensure no other programs running
- **Can't exit**: Press Ctrl+T → ESC to exit to menu
- **Lost progress**: Check if progress.db file exists in game folder

## 🔧 For Developers

### Critical Action Items
- **Bright Bastasa**: Add more Grade 6-aligned stories to config.STORIES
- **Lorenz Wee**: Record phoneme audio files per guidelines
- **Jared Campricio**: Stress-test on PSHS-ZRC lab's oldest unit

### Extending the System
1. **Add new zones**: Create new State class in states.py
2. **Add stories**: Edit config.STORIES with new narratives
3. **Modify difficulty**: Adjust timers and thresholds in config.py
4. **Custom reports**: Modify database.py generate_report()

## 📄 License & Credits

**Project KONEKTA** - Horizon 2  
Philippine Science High School - Zamboanga Research Center (PSHS-ZRC)  
Partner: San Alfonso Elementary School (SAES)

Built with integrity, designed for impact.

## 🆘 Support

For technical issues during development:
- Check [config.py](config.py) for settings
- Review [database.py](database.py) for data structure
- Examine [states.py](states.py) for game logic

For deployment support:
- Refer to troubleshooting guide above
- Contact PSHS-ZRC ICT coordinator
- Review session logs in progress.db