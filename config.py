"""
Configuration file for Assistive Literacy Learning System
Contains all game constants, settings, and configuration values
"""

# Screen settings
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1200
FPS = 60
KIOSK_MODE = True  # Set to True for deployment, False for development

# Resource paths (defined at bottom of file with RESOURCES_PATH)

# Colors (High contrast for accessibility)
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

# Barangay Captain Simulator - Phil-IRI Aligned Reading Comprehension
BARANGAY_COMPLAINTS = [
    {
        'english': {
            'passage': "Maria approached the barangay captain with a worried look. 'Captain, my neighbor's pig escaped from its pen and destroyed my vegetable garden. According to the barangay ordinance on livestock, the owner should compensate me for the damages. But he refuses to pay. What should I do?'",
            'question': "Based on the passage, what legal document does Maria reference?",
            'choices': [
                "The barangay budget report",  # Incorrect
                "The barangay ordinance on livestock",  # Correct - Phil-IRI comprehension
                "The municipal tax records",  # Incorrect
                "The barangay meeting minutes"  # Incorrect
            ]
        },
        'tagalog': {
            'passage': "Lumapit si Maria sa barangay captain na may mukhang nag-aalala. 'Captain, tumakas ang baboy ng kapitbahay ko mula sa kulungan at sinira ang aking gulayan. Ayon sa barangay ordinance tungkol sa mga hayop, dapat bayaran ng may-ari ang mga pinsala. Ngunit ayaw niyang magbayad. Ano ang dapat kong gawin?'",
            'question': "Batay sa salaysay, ano ang legal na dokumento na binanggit ni Maria?",
            'choices': [
                "Ang ulat ng barangay budget",  # Incorrect
                "Ang barangay ordinance tungkol sa mga hayop",  # Correct
                "Ang municipal tax records",  # Incorrect
                "Ang mga minuto ng barangay meeting"  # Incorrect
            ]
        },
        'bisaya': {
            'passage': "Miabot si Maria sa barangay captain nga may worried nga nawong. 'Captain, mikalag ang baboy sa among silingan gikan sa iyang piniriso ug giguba ang akong utan. Sumala sa barangay ordinance bahin sa mga hayop, ang tag-iya kinahanglan nga mobayad sa mga kadaut. Apan dili siya buot mobayad. Unsa ang akong buhaton?'",
            'question': "Base sa istorya, unsa ang legal nga dokumento nga gihisgotan ni Maria?",
            'choices': [
                "Ang barangay budget report",  # Incorrect
                "Ang barangay ordinance bahin sa mga hayop",  # Correct
                "Ang municipal tax records",  # Incorrect
                "Ang mga minuto sa barangay meeting"  # Incorrect
            ]
        },
        'correct': 1,
        'phil_iri_level': 'primer',
        'skill': 'reading_comprehension',
        'happiness_impact': [0, 25, 0, 5]
    },
    {
        'english': {
            'passage': "The barangay captain received a complaint about a large pothole on Main Street. Residents reported that the hole was causing accidents and making it difficult to walk. The barangay has a maintenance budget for road repairs, but funds are limited.",
            'question': "What is the main problem described in the passage?",
            'choices': [
                "The barangay has too much money",  # Incorrect
                "A pothole is causing accidents and walking difficulties",  # Correct
                "Residents don't like Main Street",  # Incorrect
                "The barangay captain is new"  # Incorrect
            ]
        },
        'tagalog': {
            'passage': "Tumanggap ang barangay captain ng reklamo tungkol sa malaking butas sa Main Street. Ibinigay ng mga residente na ang butas ay nagiging sanhi ng mga aksidente at mahirap maglakad. May maintenance budget ang barangay para sa pag-aayos ng mga kalsada, ngunit limitado ang pondo.",
            'question': "Ano ang pangunahing problema na inilarawan sa salaysay?",
            'choices': [
                "Ang barangay ay may sobrang pera",  # Incorrect
                "Ang butas sa kalsada ay nagiging sanhi ng aksidente at mahirap maglakad",  # Correct
                "Ayaw ng mga residente sa Main Street",  # Incorrect
                "Bago ang barangay captain"  # Incorrect
            ]
        },
        'bisaya': {
            'passage': "Nadawat sa barangay captain ang usa ka reklamo bahin sa dagkong lungag sa Main Street. Gisulti sa mga residente nga ang lungag naghimo og aksidente ug lisud na maglakaw. Aduna ang barangay og maintenance budget para sa pag-ayo sa mga dalan, apan limitado ang pundo.",
            'question': "Unsa ang main nga problema nga gihulagway sa istorya?",
            'choices': [
                "Ang barangay aduna og sobra nga kwarta",  # Incorrect
                "Ang lungag sa dalan naghimo og aksidente ug lisud maglakaw",  # Correct
                "Dili gusto sa mga residente ang Main Street",  # Incorrect
                "Bag-o ang barangay captain"  # Incorrect
            ]
        },
        'correct': 1,
        'phil_iri_level': 'primer',
        'skill': 'main_idea',
        'happiness_impact': [0, 20, 0, 0]
    },
    # Add more Phil-IRI aligned complaints...
]

# Synonym/Antonym Game - Phil-IRI Aligned Vocabulary Building
SYNONYM_ANTONYM_WORDS = [
    {
        'context': {
            'english': 'Maria was very happy when she received her birthday gift.',
            'tagalog': 'Si Maria ay napakasaya nang matanggap niya ang kanyang regalo sa kaarawan.',
            'bisaya': 'Si Maria napadasig kaayo sa pagdawat sa iyang birthday gift.'
        },
        'word': {
            'english': 'happy',
            'tagalog': 'masaya',
            'bisaya': 'dasig'
        },
        'synonym': {
            'english': 'joyful',
            'tagalog': 'masigla',
            'bisaya': 'malipayon'
        },
        'antonym': {
            'english': 'sad',
            'tagalog': 'malungkot',
            'bisaya': 'masulub-on'
        },
        'choices': {
            'english': ['joyful', 'sad', 'angry', 'tired'],
            'tagalog': ['masigla', 'malungkot', 'galit', 'pagod'],
            'bisaya': ['malipayon', 'masulub-on', 'masuko', 'kapoy']
        },
        'correct_synonym': 0,
        'correct_antonym': 1,
        'phil_iri_level': 'pre_primer'
    },
    {
        'context': {
            'english': 'The elephant is a big animal that lives in the jungle.',
            'tagalog': 'Ang elepante ay isang malaking hayop na nakatira sa gubat.',
            'bisaya': 'Ang elepante usa ka dagkong mananap nga nagpuyo sa lasang.'
        },
        'word': {
            'english': 'big',
            'tagalog': 'malaki',
            'bisaya': 'dako'
        },
        'synonym': {
            'english': 'large',
            'tagalog': 'malaking',
            'bisaya': 'halapad'
        },
        'antonym': {
            'english': 'small',
            'tagalog': 'maliit',
            'bisaya': 'gamay'
        },
        'choices': {
            'english': ['large', 'small', 'tiny', 'huge'],
            'tagalog': ['malaking', 'maliit', 'napakaliit', 'napakalaki'],
            'bisaya': ['halapad', 'gamay', 'gamay kaayo', 'dako kaayo']
        },
        'correct_synonym': 0,
        'correct_antonym': 1,
        'phil_iri_level': 'pre_primer'
    },
    {
        'context': {
            'english': 'The rabbit runs fast to escape from danger.',
            'tagalog': 'Ang kuneho ay tumatakbo nang mabilis upang makatakas sa panganib.',
            'bisaya': 'Ang kuneho nagdagan nga paspas aron makalikay sa peligro.'
        },
        'word': {
            'english': 'fast',
            'tagalog': 'mabilis',
            'bisaya': 'paspos'
        },
        'synonym': {
            'english': 'quick',
            'tagalog': 'mabilis',
            'bisaya': 'paspos'
        },
        'antonym': {
            'english': 'slow',
            'tagalog': 'mabagal',
            'bisaya': 'hinay'
        },
        'choices': {
            'english': ['quick', 'slow', 'rapid', 'speedy'],
            'tagalog': ['mabilis', 'mabagal', 'mabilis na mabilis', 'napakabilis'],
            'bisaya': ['paspos', 'hinay', 'paspos kaayo', 'dali kaayo']
        },
        'correct_synonym': 0,
        'correct_antonym': 1,
        'phil_iri_level': 'primer'
    },
    # Continue with more context-based vocabulary...
]

# Recipe Game - Phil-IRI Aligned Reading Comprehension
RECIPES = [
    {
        'title': {
            'english': 'Tinola',
            'tagalog': 'Tinola',
            'bisaya': 'Tinola'
        },
        'description': {
            'english': 'Tinola is a traditional Filipino chicken soup that is both nutritious and comforting. It combines tender chicken with green papaya and aromatic spices.',
            'tagalog': 'Ang Tinola ay isang tradisyonal na sopas ng manok na Pilipino na parehong masustansya at nakakaaliw. Pinagsasama nito ang malambot na manok kasama ang green papaya at mabangong spices.',
            'bisaya': 'Ang Tinola usa ka tradisyonal nga Filipino chicken soup nga nutritious ug comforting. Gipangkombinar kini sa tender chicken uban sa green papaya ug aromatic spices.'
        },
        'reading_level': 'primer',  # Phil-IRI level
        'ingredients': {
            'english': [
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
            'tagalog': [
                '1 buong manok, hiniwa ng mga piraso',
                '2 kutsarang mantika',
                '1 sibuyas, tinadtad',
                '2 butil ng bawang, tinadtad',
                '1 daliri-sukat na luya, hiniwa',
                '4 tasa ng tubig',
                '2 green papaya, balat na tinanggal at hiniwa',
                '2 kutsarang bagoong alamang',
                'Asin at paminta sa lasa',
                'Calamansi (opsyonal)'
            ],
            'bisaya': [
                '1 tibuok nga manok, giputol og mga piraso',
                '2 kutsara nga lana',
                '1 sibuyas, giputol',
                '2 butil nga ahos, giputol',
                '1 daliri-sukat nga luya, gihiwa',
                '4 tasa nga tubig',
                '2 green papaya, balat ug giputol',
                '2 kutsara nga bagoong',
                'Asin ug paminta sa gusto',
                'Calamansi (opsyonal)'
            ]
        },
        'directions': {
            'english': [
                'Heat oil in a pot over medium heat.',
                'Sauté garlic, onion, and ginger until fragrant.',
                'Add chicken pieces and cook until lightly browned.',
                'Pour in water and bring to a boil.',
                'Add fish sauce, salt, and pepper.',
                'Simmer for 20 minutes or until chicken is tender.',
                'Add papaya cubes and cook for another 10 minutes.',
                'Serve hot with calamansi on the side.'
            ],
            'tagalog': [
                'Initin ang mantika sa kaldero sa katamtamang init.',
                'Igisa ang bawang, sibuyas, at luya hanggang mabango.',
                'Idagdag ang mga piraso ng manok at lutuin hanggang bahagyang kayumanggi.',
                'Ibuhos ang tubig at pakuluan.',
                'Idagdag ang bagoong alamang, asin, at paminta.',
                'Hayaang kumulo ng 20 minuto o hanggang malambot ang manok.',
                'Idagdag ang mga hiwa ng papaya at lutuin ng isa pang 10 minuto.',
                'Ihanda na mainit na may calamansi sa gilid.'
            ],
            'bisaya': [
                'Init ang lana sa kaldero sa katamtaman nga kainit.',
                'Igisa ang ahos, sibuyas, ug luya hangtud mabaho.',
                'Idugang ang mga piraso sa manok ug lutua hangtud bahagyang kayumanggi.',
                'Ibutang ang tubig ug pakulba.',
                'Idugang ang bagoong, asin, ug paminta.',
                'Hayaan nga magluto og 20 minutos o hangtud malambot ang manok.',
                'Idugang ang mga hiwa sa papaya ug lutua og laing 10 minutos.',
                'Ihanda nga init uban sa calamansi sa kilid.'
            ]
        },
        'questions': {
            'english': [
                {'q': 'What is the first step in cooking Tinola?', 'choices': ['Add chicken', 'Heat oil and sauté garlic, onion, and ginger', 'Add water'], 'answer': 1, 'skill': 'sequence'},
                {'q': 'How many cups of water are needed?', 'choices': ['2 cups', '4 cups', '6 cups'], 'answer': 1, 'skill': 'detail'},
                {'q': 'What vegetable is added last?', 'choices': ['Onion', 'Ginger', 'Green papaya'], 'answer': 2, 'skill': 'sequence'},
                {'q': 'According to the description, what makes Tinola both nutritious and comforting?', 'choices': ['The spices', 'Tender chicken with green papaya and aromatic spices', 'The calamansi'], 'answer': 1, 'skill': 'comprehension'}
            ],
            'tagalog': [
                {'q': 'Ano ang unang hakbang sa pagluluto ng Tinola?', 'choices': ['Idagdag ang manok', 'Initin ang mantika at igisa ang bawang, sibuyas, at luya', 'Idagdag ang tubig'], 'answer': 1, 'skill': 'sequence'},
                {'q': 'Ilang tasa ng tubig ang kailangan?', 'choices': ['2 tasa', '4 tasa', '6 tasa'], 'answer': 1, 'skill': 'detail'},
                {'q': 'Ano ang gulay na idinagdag sa huli?', 'choices': ['Sibuyas', 'Luya', 'Green papaya'], 'answer': 2, 'skill': 'sequence'},
                {'q': 'Ayon sa paglalarawan, ano ang nagiging nutritious at comforting sa Tinola?', 'choices': ['Ang spices', 'Malambot na manok kasama ang green papaya at mabangong spices', 'Ang calamansi'], 'answer': 1, 'skill': 'comprehension'}
            ],
            'bisaya': [
                {'q': 'Unsa ang una nga lakang sa pagluto sa Tinola?', 'choices': ['Idugang ang manok', 'Init ang lana ug igisa ang ahos, sibuyas, ug luya', 'Idugang ang tubig'], 'answer': 1, 'skill': 'sequence'},
                {'q': 'Pila ka tasa sa tubig ang kinahanglan?', 'choices': ['2 tasa', '4 tasa', '6 tasa'], 'answer': 1, 'skill': 'detail'},
                {'q': 'Unsa ang utan nga idugang sa katapusan?', 'choices': ['Sibuyas', 'Luya', 'Green papaya'], 'answer': 2, 'skill': 'sequence'},
                {'q': 'Sumala sa paghulagway, unsa ang naghimo sa Tinola nga nutritious ug comforting?', 'choices': ['Ang spices', 'Tender chicken uban sa green papaya ug aromatic spices', 'Ang calamansi'], 'answer': 1, 'skill': 'comprehension'}
            ]
        }
    },
    # Add more Phil-IRI aligned recipes...
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