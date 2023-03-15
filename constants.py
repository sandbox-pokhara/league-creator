REGIONS = {
    'EUW': 'EUW1',
    'EUNE': 'EUN1',
    'NA': 'NA1',
    'BR': 'BR1',
    'TR': 'TR1',
    'RU': 'RU',
    'OCE': 'OC1',
    'LAN': 'LA1',
    'LAS': 'LA2',
    'JP': 'JP1',
}

REGION_CHOICES = [r for r in REGIONS]

LOCALES = {
    'EUW': 'en',
    'EUNE': 'en',
    'NA': 'en',
    'BR': 'pt',
    'TR': 'tr',
    'RU': 'ru',
    'OCE': 'en',
    'LAN': 'en',
    'LAS': 'en',
    'JP': 'ja',
}

SITE_KEY = 'a010c060-9eb5-498c-a7b9-9204c881f9dc'

URLS = {
    'EUW': 'https://signup.leagueoflegends.com/en-gb/signup/index#/',
    'EUNE': 'https://signup.leagueoflegends.com/en-pl/signup/index#/',
    'NA': 'https://signup.leagueoflegends.com/en-us/signup/index#/',
    'BR': 'https://signup.leagueoflegends.com/pt-br/signup/index#/',
    'TR': 'https://signup.leagueoflegends.com/tr-tr/signup/index#/',
    'RU': 'https://signup.leagueoflegends.com/ru-ru/signup/index#/',
    'OCE': 'https://signup.leagueoflegends.com/en-au/signup/index#/',
    'LAN': 'https://signup.leagueoflegends.com/es-mx/signup/index#/',
    'LAS': 'https://signup.leagueoflegends.com/es-ar/signup/index#/',
    'JP': 'https://signup.leagueoflegends.com/ja-jp/signup/index#/',
    'PH': 'https://signup.leagueoflegends.com/en-ph/signup/index#/',
    'SG': 'https://signup.leagueoflegends.com/en-sg/signup/index#/',
    'TH': 'https://signup.leagueoflegends.com/th-th/signup/index#/',
    'TW': 'https://signup.leagueoflegends.com/zh-tw/signup/index#/',
}

SIGNUP_URL = 'https://signup-api.leagueoflegends.com/v1/accounts'
CONFIG_URL = 'https://signup-api.leagueoflegends.com/v1/config'

WRITE_FORMATS = [
    'username:password',
]

BANNED_COUNTRIES = [
    'KR',
    'PA',
    'VN',
]

CAPTCHAS = [
    '2captcha',
    'anti-captcha',
]
