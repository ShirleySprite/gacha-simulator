from collections import Counter


def counter_contain(
        counter1: Counter,
        counter2: Counter
):
    return counter1 | counter2 == counter1
