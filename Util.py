import random
import string

def generate_username(name):
    names = name.split(" ")

    if len(names) <= 1:
        return ""

    first_letter = name[0][0]
    three_letters_surname = names[-1][:3]
    number = '{:03d}'.format(random.randrange(1, 999))

    return "{0}{1}{2}".format(first_letter, three_letters_surname, number)

def generate_random_nickname():
    minLength = 8
    maxLength = 15
    length = random.randint(minLength, maxLength)

    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))
