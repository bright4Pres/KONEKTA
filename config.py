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

# Word Recognition Zone - Phil IRI Grade 6 Vocabulary
GRADE6_WORDS = [
    'kapaligiran', 'kalikasan', 'kabataan', 'kalayaan', 'kaunlaran',
    'pagkakaisa', 'pakikipagkapwa', 'responsibilidad', 'demokrasya', 'edukasyon',
    'teknolohiya', 'agrikultura', 'industriya', 'ekonomiya', 'kasaysayan',
    'pamahalaan', 'konstitusyon', 'kultura', 'tradisyon', 'pagkakakilanlan',
    'biodiversity', 'sustainabilidad', 'imprastraktura', 'komunidad', 'literatura',
    'sibilisasyon', 'pag-unlad', 'lipunan', 'kahirapan', 'solusyon',
    'karapatan', 'tungkulin', 'pagbabago', 'kinabukasan', 'pag-asa',
    'pagsisikap', 'determinasyon', 'integridad', 'kahusayan', 'pagkakaibigan'
]

ALL_SIGHT_WORDS = GRADE6_WORDS

# Reading Fluency - Phil IRI Grade 6 Passages
READING_PASSAGES = [
    {
        'level': 'Grade 6',
        'title': 'Ang Kahalagahan ng Edukasyon',
        'text': 'Ang edukasyon ay susi sa tagumpay ng isang bansa. Sa pamamagitan nito, natututo ang mga kabataan ng mga kasanayang kailangan upang maging produktibong mamamayan. Hindi lamang akademikong kaalaman ang natututunan sa paaralan, kundi pati na rin ang mga pagpapahalagang tulad ng pagkakaisa, respeto, at responsibilidad. Ang bawat mag-aaral ay may tungkuling magsikap at samantalahin ang pagkakataong mag-aral. Sa ganitong paraan, makakatulong sila sa pag-unlad ng lipunan at ng buong bansa.',
        'questions': [
            {'q': 'Ayon sa teksto, ano ang susi sa tagumpay ng bansa?', 'choices': ['Yaman', 'Edukasyon', 'Teknolohiya'], 'answer': 1},
            {'q': 'Ano-ano ang natututunan sa paaralan bukod sa akademikong kaalaman?', 'choices': ['Paglalaro lang', 'Pagpapahalagang tulad ng pagkakaisa at respeto', 'Paggamit ng gadget'], 'answer': 1},
            {'q': 'Paano makakatulong ang mga mag-aaral sa pag-unlad ng bansa?', 'choices': ['Sa pamamagitan ng pagsisikap at pag-aaral', 'Sa pamamagitan ng panonood ng TV', 'Sa pamamagitan ng paglalaro'], 'answer': 0}
        ]
    },
    {
        'level': 'Grade 6',
        'title': 'Teknolohiya at Kalikasan',
        'text': 'Sa modernong panahon, ang teknolohiya ay mahalagang bahagi ng ating buhay. Ngunit may kaakibat itong responsibilidad sa pag-aalaga ng kalikasan. Maraming gadget at appliances ang gumagamit ng kuryente na nagmumula sa mga fossil fuels. Ang labis na paggamit nito ay nakakapinsala sa kapaligiran. Bilang kabataan, dapat nating matutunan ang tamang paggamit ng teknolohiya. Magtipid ng kuryente, gumamit ng renewable energy, at iwasan ang mga produktong nakakasama sa kalikasan. Sa ganitong paraan, makakamit natin ang balanse sa pagitan ng pag-unlad at pag-aalaga sa ating planeta.',
        'questions': [
            {'q': 'Ano ang kaakibat na responsibilidad ng paggamit ng teknolohiya?', 'choices': ['Walang responsibilidad', 'Pag-aalaga ng kalikasan', 'Paggamit ng maraming kuryente'], 'answer': 1},
            {'q': 'Bakit nakakapinsala ang labis na paggamit ng kuryente?', 'choices': ['Dahil ito ay galing sa fossil fuels na nakakasama sa kapaligiran', 'Dahil mahal ito', 'Dahil hindi maganda'], 'answer': 0},
            {'q': 'Ano ang dapat gawin ng kabataan?', 'choices': ['Gumamit ng maraming gadget', 'Magtipid ng kuryente at gumamit ng renewable energy', 'Huwag gumamit ng teknolohiya'], 'answer': 1}
        ]
    },
    {
        'level': 'Grade 6',
        'title': 'Ang Kultura ng mga Pilipino',
        'text': 'Ang Pilipinas ay mayaman sa kultura at tradisyon. Mula sa ating mga sayaw, musika, pagkain, hanggang sa ating mga kaugalian, makikita ang ating pagkakakilanlan bilang Pilipino. Ang pagiging maka-Diyos, mapagmahal sa pamilya, at mapagpatuloy ay ilan lamang sa mga katangiang dapat nating ipagmalaki. Sa kabila ng impluwensya ng ibang kultura, mahalaga na panatilihin natin ang ating sariling pagkakakilanlan. Responsibilidad ng bawat henerasyon na ipasa sa susunod ang mga tradisyong ito. Sa pamamagitan ng pagpapahalaga sa ating kultura, pinapakita natin ang ating pagmamahal sa bayan.',
        'questions': [
            {'q': 'Ano-ano ang bahagi ng kultura ng mga Pilipino?', 'choices': ['Sayaw, musika, at pagkain lamang', 'Sayaw, musika, pagkain, at kaugalian', 'Teknolohiya'], 'answer': 1},
            {'q': 'Ano ang responsibilidad ng bawat henerasyon?', 'choices': ['Kalimutan ang tradisyon', 'Ipasa sa susunod ang mga tradisyon', 'Gumaya sa ibang bansa'], 'answer': 1},
            {'q': 'Paano natin maipapakita ang pagmamahal sa bayan?', 'choices': ['Sa pamamagitan ng pagpapahalaga sa ating kultura', 'Sa pamamagitan ng pag-alis sa Pilipinas', 'Sa pamamagitan ng pagtanggi sa ating tradisyon'], 'answer': 0}
        ]
    }
]

# Advanced Reading Comprehension - Phil IRI Grade 6 Level
COMPREHENSION_STORIES = [
    {
        'level': 'Grade 6',
        'title': 'Ang Hamon ng Climate Change',
        'text': '''Ang climate change o pagbabago ng klima ay isa sa pinakamalaking hamon na kinakaharap ng mundo ngayon. Ang pagtaas ng temperatura ng mundo ay dulot ng greenhouse gases na pumapaloob sa atmospera. Ang mga gawaing pantao tulad ng deforestation, paggamit ng fossil fuels, at industrialisasyon ay nag-aambag sa problemang ito.\n\nSa Pilipinas, ramdam na ang epekto nito. Mas madalas at mas malakas ang mga bagyo. Tumataas ang lebel ng dagat na nagbabanta sa mga pulo. Nagbabago ang pattern ng tag-ulan at tag-init na nakakaapekto sa agrikultura. Maraming magsasaka ang nahihirapan dahil hindi na stable ang ani.\n\nNgunit hindi pa huli ang lahat. Mayroong mga hakbang na maaaring gawin. Ang pagtatanim ng puno ay tumutulong na sumipsip ng carbon dioxide. Ang paggamit ng renewable energy tulad ng solar at wind power ay nagbabawas ng carbon emissions. Ang wastong segregasyon at recycling ng basura ay nakakatulong din.\n\nBilang kabataan, may mahalagang papel din tayo. Magsimula sa simpleng bagay - magtipid ng kuryente, gumamit ng reusable bags, at magbahagi ng kaalaman sa iba. Ang pagbabago ay nagsisimula sa sarili. Kung sama-sama tayong kikilos, maaari nating protektahan ang kinabukasan ng ating planeta para sa susunod na henerasyon.''',
        'questions': [
            {
                'q': 'Ano ang pangunahing sanhi ng climate change ayon sa teksto?',
                'choices': [
                    'Likas na pagbabago ng mundo',
                    'Greenhouse gases mula sa mga gawaing pantao',
                    'Pagtaas ng populasyon'
                ],
                'answer': 1
            },
            {
                'q': 'Paano nakakaapekto ang climate change sa agrikultura ng Pilipinas?',
                'choices': [
                    'Tumutulong sa mas maraming ani',
                    'Nagbabago ang pattern ng tag-ulan at tag-init kaya hindi stable ang ani',
                    'Walang epekto sa agrikultura'
                ],
                'answer': 1
            },
            {
                'q': 'Ano ang mensahe ng huling talata tungkol sa papel ng kabataan?',
                'choices': [
                    'Ang mga kabataan ay walang magagawa',
                    'Hintayin na lang ang gobyerno',
                    'Ang pagbabago ay nagsisimula sa sarili at sama-samang kilos'
                ],
                'answer': 2
            },
            {
                'q': 'Bakit mahalagang magtanim ng puno sa paglutas ng climate change?',
                'choices': [
                    'Para maganda ang paligid',
                    'Dahil sumusipsip ito ng carbon dioxide',
                    'Para may lilim'
                ],
                'answer': 1
            }
        ]
    },
    {
        'level': 'Grade 6',
        'title': 'Si Jose Rizal: Bayani ng Pilipinas',
        'text': '''Si Dr. Jose Rizal ay isa sa pinakadakilang bayani ng Pilipinas. Ipinanganak siya noong Hunyo 19, 1861 sa Calamba, Laguna. Hindi siya bayaning may hawak na espada at sumali sa labanan, ngunit sa pamamagitan ng kanyang mga sulatin, nagising niya ang diwa ng mga Pilipino laban sa pang-aapi ng mga Espanyol.\n\nSa murang edad, ipinakita na ni Rizal ang kanyang kahusayan. Nag-aral siya sa Europa kung saan niya sinulat ang Noli Me Tangere at El Filibusterismo. Ang mga nobela ay naglalahad ng mga kasamaan ng pamahalaan noon. Bagama't alam niyang delikado, hindi siya tumigil sa pagsusulat. Para sa kanya, mas malakas ang kapangyarihan ng pluma kaysa sa espada.\n\nNoong Disyembre 30, 1896, binaril si Rizal sa Bagumbayan (ngayong Luneta). Bago siya namatay, sinabi niya, "Consummatum est" - tapos na. Ngunit hindi doon nagtapos ang kanyang misyon. Ang kanyang kamatayan ang naging sindi ng himagsikan. Naging inspirasyon siya ng mga Pilipinong lumaban para sa kalayaan.\n\nAng mga aral ni Rizal ay may kabuluhan pa rin ngayon. Ang kanyang pagiging makabayan, pagmamahal sa edukasyon, at tapang na harapin ang kawalan ng katarungan ay mga pagpapahalagang dapat nating tularan. Bilang kabataan, maaari tayong maging bayani sa sariling paraan - sa pamamagitan ng pag-aaral, paglilingkod sa bayan, at paninindigan sa katotohanan.''',
        'questions': [
            {
                'q': 'Paano naging bayani si Rizal kahit hindi siya nakipaglaban sa gera?',
                'choices': [
                    'Sa pamamagitan ng pagbibigay ng pera',
                    'Sa pamamagitan ng pagsusulat ng mga nobela na nagpamulat sa Pilipino',
                    'Sa pamamagitan ng pagtakas sa ibang bansa'
                ],
                'answer': 1
            },
            {
                'q': 'Ano ang ibig sabihin ng "mas malakas ang kapangyarihan ng pluma kaysa sa espada"?',
                'choices': [
                    'Ang pagsusulat at edukasyon ay mas makapangyarihan kaysa sa karahasan',
                    'Ang pluma ay mas mabigat kaysa espada',
                    'Mas mahina ang espada'
                ],
                'answer': 0
            },
            {
                'q': 'Bakit sinabi na hindi nagtapos ang misyon ni Rizal sa kanyang kamatayan?',
                'choices': [
                    'Dahil nabuhay siyang muli',
                    'Dahil ang kanyang kamatayan ay naging inspirasyon at sindi ng himagsikan',
                    'Dahil may naiwan siyang pera'
                ],
                'answer': 1
            },
            {
                'q': 'Ano ang pangunahing aral na makukuha natin mula kay Rizal?',
                'choices': [
                    'Ang kahalagahan ng yaman',
                    'Ang pagiging makabayan, pagmamahal sa edukasyon, at tapang na harapin ang kawalan ng katarungan',
                    'Ang paglalakbay sa ibang bansa'
                ],
                'answer': 1
            }
        ]
    },
    {
        'level': 'Grade 6',
        'title': 'Ang Digital Age at Responsableng Paggamit',
        'text': '''Nabubuhay tayo sa digital age - panahon kung saan ang teknolohiya ay bahagi na ng araw-araw nating buhay. Mula sa online classes, research, komunikasyon, hanggang sa entertainment, gumagamit tayo ng internet at iba't ibang digital devices. Ang teknolohiyang ito ay nagdulot ng maraming benepisyo, ngunit may kaakibat din itong mga responsibilidad at panganib.\n\nAng social media ay naging malaking bahagi ng buhay ng kabataan. Sa pamamagitan nito, nakakapag-connect tayo sa mga kaibigan at pamilya kahit malayo. Nakakakuha rin tayo ng impormasyon at nag-eenjoy ng content. Ngunit may dark side din ito. Ang cyberbullying ay isa sa mga problema. May mga taong gumagamit ng anonymity ng internet upang manakit ng iba. Ang spread ng fake news ay isa pang malaking isyu na nakakaapekto sa lipunan.\n\nKaya mahalaga ang digital literacy at responsible online behavior. Hindi lahat ng nababasa online ay totoo - kailangan nating mag-fact check. Dapat nating protektahan ang ating personal information at iwasan ang oversharing. Maging mabuti tayong digital citizen - mag-isip bago mag-post, mag-comment nang may respeto, at i-report ang inappropriate content.\n\nAng teknolohiya ay tool - maaaring magdulot ng kabutihan o kasamaan depende sa paggamit natin. Bilang Generation Z, nasa atin ang kapangyarihang gamitin ito para sa positive change. Gawing platform ang social media para magbahagi ng kaalaman, magsulong ng advocacy, at makipag-connect sa meaningful way. Sa responsableng paggamit ng teknolohiya, maaari tayong maging bahagi ng solusyon sa mga problema ng lipunan.''',
        'questions': [
            {
                'q': 'Ano ang "dark side" ng social media na binanggit sa teksto?',
                'choices': [
                    'Mataas na presyo ng internet',
                    'Cyberbullying at spread ng fake news',
                    'Mabagal na connection'
                ],
                'answer': 1
            },
            {
                'q': 'Ano ang ibig sabihin ng "digital literacy"?',
                'choices': [
                    'Ang kakayahang gumamit ng computer',
                    'Ang kaalaman at kasanayan sa responsableng paggamit ng teknolohiya',
                    'Ang pagkakaroon ng maraming gadgets'
                ],
                'answer': 1
            },
            {
                'q': 'Paano natin magiging "mabuting digital citizen"?',
                'choices': [
                    'Mag-post ng maraming selfie',
                    'Mag-isip bago mag-post, mag-comment nang may respeto, at i-report ang inappropriate content',
                    'Magsabi ng opinyon kahit hindi totoo'
                ],
                'answer': 1
            },
            {
                'q': 'Ano ang pangunahing mensahe ng teksto?',
                'choices': [
                    'Iwasan ang paggamit ng teknolohiya',
                    'Ang teknolohiya ay tool na maaaring gamitin para sa kabutihan o kasamaan, kaya responsable tayong dapat gumamit',
                    'Ang social media ay masama'
                ],
                'answer': 1
            }
        ]
    }
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

# Database settings
DATABASE_NAME = 'progress.db'
