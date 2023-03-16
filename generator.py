import string
from random import choice
from random import randint

from name_generator import generate_name


def get_random_date(start_year=1985, end_year=2002):
    year = randint(start_year, end_year)
    month = randint(1, 12)
    day = randint(1, 28)
    return f'{year}-{month:02d}-{day:02d}'


def generate_accounts(count=1, region='EUW', email_host='gmail.com', password_length=32):
    accounts = []
    for _ in range(count):
        username = generate_name(4, 8) + generate_name(4, 8)
        accounts.append({
            'username': username,
            'password': generate_password(password_length),
            'email': f'{username}@{email_host}',
            'dob': get_random_date(),
            'region': region,
        })
    return accounts


def generate_password(length=32):
    characters = string.ascii_letters + string.digits + '!#$%&*+-.<=>?@^_~'
    password = choice(string.ascii_letters) + choice(string.digits)
    password += "".join(choice(characters) for x in range(length - 2))
    return password
