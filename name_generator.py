import random

from weights import WEIGHTS
from weights import WEIGHTS2


def generate_letters():
    letters = []
    letters2 = []

    for i in range(26):
        cvar = 0
        tvar = 0
        letters.append([])
        for j in range(26):
            cvar += WEIGHTS[i][j]
        for j in range(26):
            tvar += WEIGHTS[i][j]
            try:
                letters[i].append((tvar / cvar) * 1000)
            except ZeroDivisionError:
                letters[i].append(0)

    for h in range(26):
        letters2.append([])
        for i in range(26):
            cvar = 0
            tvar = 0
            letters2[h].append([])
            for j in range(26):
                cvar += WEIGHTS2[h][i][j]

            for j in range(26):
                tvar += WEIGHTS2[h][i][j]
                try:
                    letters2[h][i].append((tvar / cvar) * 1000)
                except ZeroDivisionError:
                    letters2[h][i].append(0)

    return letters, letters2


def alphalow(index):
    return chr(97 + index)


def alphaup(index):
    return chr(65 + index)


def rnd(ceiling):
    return random.randint(0, ceiling)


def get_random(min, max):
    return random.randint(0, max - min + 1) + min


def generate_name(min_length, max_length):
    try:
        length = random.randint(min_length, max_length)
        letters, letters2 = generate_letters()
        name_length = length

        curchar = rnd(26)
        nam = alphaup(curchar)

        firstchar = curchar
        ran = rnd(1000)
        secondchar = 0

        curar = letters[firstchar]
        while ran >= curar[secondchar]:
            secondchar += 1

        nam += alphalow(secondchar)

        for _ in range(2, name_length):
            ran = rnd(1000)
            nextchar = 0
            curar = letters2[firstchar][secondchar]

            while ran >= curar[nextchar]:
                nextchar += 1
            firstchar = secondchar
            secondchar = nextchar
            nam += alphalow(nextchar)

        return nam
    except IndexError:
        return generate_name(min_length, max_length)
