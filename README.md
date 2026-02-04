# KONEKTA

A literacy learning game built with Pygame, featuring multiple educational mini-games to help students improve reading comprehension, decision-making, and vocabulary skills.

## Features

- **Barangay Captain Simulator**: Decision-making game where players resolve community complaints by choosing appropriate responses.
- **Recipe Game**: Reading comprehension exercise where players follow cooking instructions and answer questions about recipes.
- **Synonym/Antonym Word Match**: Vocabulary game that tests knowledge of synonyms and antonyms through multiple-choice questions.
- Retro pixel art style with smooth animations
- Language selection: English, Filipino, and Bisaya
- Progress tracking with SQLite database
- Offline-first design

## Requirements

- Python 3.8+
- Pygame

## Installation

1. Clone or download the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the game:
   ```
   python main.py
   ```

## How to Play

The game starts with a main menu showing a tilemap with different zones. Click on a zone to start the corresponding game.

- **Barangay Captain**: Read complaints and select the best response from multiple choices.
- **Recipe Game**: Follow the recipe steps and answer comprehension questions.
- **Synonym/Antonym**: Match words by identifying synonyms or antonyms from options.

Use the language selector in each game to switch between English, Filipino, and Bisaya.

## Project Structure

- `main.py`: Main game loop and state management
- `states.py`: Game state classes for different screens and games
- `config.py`: Game data and configuration
- `database.py`: Progress tracking database
- `tilemap.py`: Map rendering and interaction zones
- `resources/`: Game assets (images, fonts, audio)

## Contributing

Feel free to submit issues or pull requests for improvements.
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