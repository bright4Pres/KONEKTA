"""
Configuration file for Assistive Literacy Learning System
Contains all game constants, settings, and configuration values
"""

# Screen settings
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60
KIOSK_MODE = True  # Set to True for deployment, False for development

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