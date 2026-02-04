"""
Configuration file for Assistive Literacy Learning System
Contains all game constants, settings, and configuration values
"""

# Screen settings
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60
KIOSK_MODE = False  # Set to True for deployment, False for development

# Resource paths
IMAGE_PATH = 'resources/images'
AUDIO_PATH = 'resources/audio'

# Colors (High contrast for accessibility)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)
BLUE = (0, 102, 204)
RED = (220, 20, 60)
YELLOW = (255, 215, 0)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
ORANGE = (255, 140, 0)
PURPLE = (128, 0, 128)

# Font sizes (Large for accessibility)
FONT_TITLE = 72
FONT_LARGE = 48
FONT_MEDIUM = 36
FONT_SMALL = 24

# Game progression - All zones unlocked (Phil IRI approach)
POINTS_PER_CORRECT_ANSWER = 10

# Assistive features
HINT_DELAY_MS = 5000  # 5 seconds
HOVER_HINT_DELAY_MS = 3000  # 3 seconds

# Barangay Captain Simulator
BARANGAY_COMPLAINTS = [
    {
        'complaint': "Captain, my neighbor's pig escaped and ate my camote patch! The law says he should pay, but he won't!",
        'choices': [
            "Tell the neighbor to be nicer.",  # Emotional, low score
            "Refer to the Barangay Ordinance on Livestock.",  # Legal/Literacy, high score
            "Go buy more camote.",  # Irrelevant, failure
            "Organize a community meeting to discuss animal control."  # Practical, medium score
        ],
        'correct': 1,  # Index of correct answer
        'happiness_impact': [5, 20, -10, 10]  # Happiness points for each choice
    },
    {
        'complaint': "Captain, there's a big pothole on our street that's causing accidents. The barangay should fix it!",
        'choices': [
            "Say sorry for the inconvenience.",  # Emotional
            "Check the barangay budget for road repairs.",  # Legal/Literacy
            "Tell them to avoid the pothole.",  # Irrelevant
            "Report it to the municipal engineer."  # Practical
        ],
        'correct': 1,
        'happiness_impact': [5, 20, -5, 15]
    },
    {
        'complaint': "Captain, my child was bullied at school and the teacher did nothing. What should I do?",
        'choices': [
            "Talk to the bully's parents personally.",  # Emotional
            "File a formal complaint with the school administration.",  # Legal/Literacy
            "Tell my child to fight back.",  # Irrelevant
            "Seek counseling for both children."  # Practical
        ],
        'correct': 1,
        'happiness_impact': [10, 25, -15, 20]
    },
    {
        'complaint': "Captain, the barangay hall roof is leaking during rains. It's been like this for months!",
        'choices': [
            "Express sympathy for the inconvenience.",  # Emotional
            "Review maintenance records and allocate funds for repair.",  # Legal/Literacy
            "Suggest they use buckets to catch the water.",  # Irrelevant
            "Contact the municipal office for assistance."  # Practical
        ],
        'correct': 1,
        'happiness_impact': [5, 20, -5, 15]
    },
    {
        'complaint': "Captain, someone is dumping garbage in our clean barangay. The ordinance says it's illegal!",
        'choices': [
            "Ask them politely to stop.",  # Emotional
            "Cite the specific anti-littering ordinance and issue a warning.",  # Legal/Literacy
            "Ignore it since it's not your property.",  # Irrelevant
            "Organize a barangay clean-up drive."  # Practical
        ],
        'correct': 1,
        'happiness_impact': [10, 25, -10, 20]
    },
    # Add more complaints here... up to 50
]

# Synonym/Antonym Game - 50 words with 4 choices each
SYNONYM_ANTONYM_WORDS = [
    {'word': 'happy', 'synonym': 'joyful', 'antonym': 'sad', 'choices': ['joyful', 'sad', 'angry', 'tired']},
    {'word': 'big', 'synonym': 'large', 'antonym': 'small', 'choices': ['large', 'small', 'tiny', 'huge']},
    {'word': 'fast', 'synonym': 'quick', 'antonym': 'slow', 'choices': ['quick', 'slow', 'rapid', 'speedy']},
    {'word': 'hot', 'synonym': 'warm', 'antonym': 'cold', 'choices': ['warm', 'cold', 'cool', 'freezing']},
    {'word': 'bright', 'synonym': 'brilliant', 'antonym': 'dark', 'choices': ['brilliant', 'dark', 'shiny', 'dim']},
    {'word': 'strong', 'synonym': 'powerful', 'antonym': 'weak', 'choices': ['powerful', 'weak', 'mighty', 'feeble']},
    {'word': 'easy', 'synonym': 'simple', 'antonym': 'difficult', 'choices': ['simple', 'difficult', 'hard', 'complex']},
    {'word': 'new', 'synonym': 'fresh', 'antonym': 'old', 'choices': ['fresh', 'old', 'modern', 'ancient']},
    {'word': 'rich', 'synonym': 'wealthy', 'antonym': 'poor', 'choices': ['wealthy', 'poor', 'broke', 'affluent']},
    {'word': 'clean', 'synonym': 'spotless', 'antonym': 'dirty', 'choices': ['spotless', 'dirty', 'neat', 'filthy']},
    {'word': 'brave', 'synonym': 'courageous', 'antonym': 'cowardly', 'choices': ['courageous', 'cowardly', 'fearless', 'timid']},
    {'word': 'beautiful', 'synonym': 'pretty', 'antonym': 'ugly', 'choices': ['pretty', 'ugly', 'gorgeous', 'hideous']},
    {'word': 'good', 'synonym': 'excellent', 'antonym': 'bad', 'choices': ['excellent', 'bad', 'great', 'terrible']},
    {'word': 'smart', 'synonym': 'intelligent', 'antonym': 'stupid', 'choices': ['intelligent', 'stupid', 'clever', 'dumb']},
    {'word': 'loud', 'synonym': 'noisy', 'antonym': 'quiet', 'choices': ['noisy', 'quiet', 'booming', 'silent']},
    {'word': 'sweet', 'synonym': 'sugary', 'antonym': 'bitter', 'choices': ['sugary', 'bitter', 'tasty', 'sour']},
    {'word': 'empty', 'synonym': 'vacant', 'antonym': 'full', 'choices': ['vacant', 'full', 'hollow', 'packed']},
    {'word': 'high', 'synonym': 'tall', 'antonym': 'low', 'choices': ['tall', 'low', 'elevated', 'short']},
    {'word': 'young', 'synonym': 'youthful', 'antonym': 'old', 'choices': ['youthful', 'old', 'juvenile', 'elderly']},
    {'word': 'wide', 'synonym': 'broad', 'antonym': 'narrow', 'choices': ['broad', 'narrow', 'spacious', 'tight']},
    {'word': 'thick', 'synonym': 'dense', 'antonym': 'thin', 'choices': ['dense', 'thin', 'heavy', 'slim']},
    {'word': 'rough', 'synonym': 'coarse', 'antonym': 'smooth', 'choices': ['coarse', 'smooth', 'bumpy', 'soft']},
    {'word': 'hard', 'synonym': 'solid', 'antonym': 'soft', 'choices': ['solid', 'soft', 'firm', 'tender']},
    {'word': 'wet', 'synonym': 'damp', 'antonym': 'dry', 'choices': ['damp', 'dry', 'moist', 'arid']},
    {'word': 'safe', 'synonym': 'secure', 'antonym': 'dangerous', 'choices': ['secure', 'dangerous', 'protected', 'risky']},
    {'word': 'light', 'synonym': 'bright', 'antonym': 'heavy', 'choices': ['bright', 'heavy', 'illuminated', 'dark']},
    {'word': 'near', 'synonym': 'close', 'antonym': 'far', 'choices': ['close', 'far', 'nearby', 'distant']},
    {'word': 'early', 'synonym': 'prompt', 'antonym': 'late', 'choices': ['prompt', 'late', 'timely', 'delayed']},
    {'word': 'tight', 'synonym': 'snug', 'antonym': 'loose', 'choices': ['snug', 'loose', 'firm', 'slack']},
    {'word': 'sharp', 'synonym': 'keen', 'antonym': 'dull', 'choices': ['keen', 'dull', 'pointed', 'blunt']},
    {'word': 'deep', 'synonym': 'profound', 'antonym': 'shallow', 'choices': ['profound', 'shallow', 'bottomless', 'superficial']},
    {'word': 'true', 'synonym': 'genuine', 'antonym': 'false', 'choices': ['genuine', 'false', 'real', 'fake']},
    {'word': 'kind', 'synonym': 'gentle', 'antonym': 'cruel', 'choices': ['gentle', 'cruel', 'nice', 'mean']},
    {'word': 'cheap', 'synonym': 'inexpensive', 'antonym': 'expensive', 'choices': ['inexpensive', 'expensive', 'affordable', 'costly']},
    {'word': 'wild', 'synonym': 'untamed', 'antonym': 'tame', 'choices': ['untamed', 'tame', 'savage', 'domesticated']},
    {'word': 'funny', 'synonym': 'humorous', 'antonym': 'serious', 'choices': ['humorous', 'serious', 'comical', 'solemn']},
    {'word': 'right', 'synonym': 'correct', 'antonym': 'wrong', 'choices': ['correct', 'wrong', 'accurate', 'incorrect']},
    {'word': 'fresh', 'synonym': 'crisp', 'antonym': 'stale', 'choices': ['crisp', 'stale', 'new', 'rotten']},
    {'word': 'calm', 'synonym': 'peaceful', 'antonym': 'stormy', 'choices': ['peaceful', 'stormy', 'serene', 'turbulent']},
    {'word': 'modern', 'synonym': 'contemporary', 'antonym': 'ancient', 'choices': ['contemporary', 'ancient', 'current', 'archaic']},
    {'word': 'sick', 'synonym': 'ill', 'antonym': 'healthy', 'choices': ['ill', 'healthy', 'unwell', 'fit']},
    {'word': 'simple', 'synonym': 'plain', 'antonym': 'complex', 'choices': ['plain', 'complex', 'basic', 'complicated']},
    {'word': 'polite', 'synonym': 'courteous', 'antonym': 'rude', 'choices': ['courteous', 'rude', 'respectful', 'impolite']},
    {'word': 'strange', 'synonym': 'odd', 'antonym': 'normal', 'choices': ['odd', 'normal', 'weird', 'ordinary']},
    {'word': 'famous', 'synonym': 'renowned', 'antonym': 'unknown', 'choices': ['renowned', 'unknown', 'celebrated', 'obscure']},
    {'word': 'lazy', 'synonym': 'idle', 'antonym': 'active', 'choices': ['idle', 'active', 'sluggish', 'energetic']},
    {'word': 'proud', 'synonym': 'confident', 'antonym': 'humble', 'choices': ['confident', 'humble', 'arrogant', 'modest']},
    {'word': 'hungry', 'synonym': 'starving', 'antonym': 'full', 'choices': ['starving', 'full', 'famished', 'satisfied']},
    {'word': 'scared', 'synonym': 'frightened', 'antonym': 'brave', 'choices': ['frightened', 'brave', 'terrified', 'fearless']},
    {'word': 'angry', 'synonym': 'furious', 'antonym': 'calm', 'choices': ['furious', 'calm', 'mad', 'peaceful']},
]

# Recipe Game
RECIPES = [
    {
        'title': 'Tinola',
        'ingredients': [
            '1 whole chicken, cut into pieces',
            '2 tablespoons cooking oil',
            '1 onion, chopped',
            '2 cloves garlic, minced',
            '1 thumb-sized ginger, sliced',
            '4 cups water',
            '2 green papaya, peeled and cubed',
            '2 tablespoons fish sauce',
            'Salt and pepper to taste',
            'Calamansi (optional)'
        ],
        'directions': [
            'Heat oil in a pot over medium heat.',
            'Sauté garlic, onion, and ginger until fragrant.',
            'Add chicken pieces and cook until lightly browned.',
            'Pour in water and bring to a boil.',
            'Add fish sauce, salt, and pepper.',
            'Simmer for 20 minutes or until chicken is tender.',
            'Add papaya cubes and cook for another 10 minutes.',
            'Serve hot with calamansi on the side.'
        ],
        'questions': [
            {'q': 'What is the first step in cooking Tinola?', 'choices': ['Add chicken', 'Heat oil and sauté garlic, onion, and ginger', 'Add water'], 'answer': 1},
            {'q': 'How many cups of water are needed?', 'choices': ['2 cups', '4 cups', '6 cups'], 'answer': 1},
            {'q': 'What vegetable is added last?', 'choices': ['Onion', 'Ginger', 'Green papaya'], 'answer': 2}
        ]
    },
    # Add more recipes here
]

# Teacher Dashboard
TEACHER_PASSWORD = 'konekta2026'  # Change this for deployment
TEACHER_KEY_COMBO = ['LCTRL', 'T']  # Ctrl+T

# Student IDs (for demo purposes)
DEFAULT_STUDENT_ID = 'student_demo'

# Asset paths
RESOURCES_PATH = 'resources'
AUDIO_PATH = f'{RESOURCES_PATH}/audio'
IMAGE_PATH = f'{RESOURCES_PATH}/images'
FONT_PATH = f'{RESOURCES_PATH}/font/PixelifySans/static/PixelifySans-Regular.ttf'

# Database settings
DATABASE_NAME = 'progress.db'