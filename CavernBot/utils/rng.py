from secrets import randbelow

from random import shuffle

def rec_shuffle(_list, count=5):
    if count != 0:
        shuffle(_list)
        return rec_shuffle(_list, count=count-1)
    else:
        return

def get_random_element(values: list):
    return values[randbelow(len(values))]
