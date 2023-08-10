from collections import Counter


def counter_contain(
        counter1: Counter,
        counter2: Counter
) -> bool:
    """
    Check if elements in `counter1` are more than those in `counter2`.

    Parameters
    ----------
    counter1 : Counter
        The assumed larger counter.
    counter2 : Counter
        The assumed smaller counter.

    Returns
    -------
    bool
        True if the assumption is correct, otherwise False.
    """
    return counter1 | counter2 == counter1


def combination(
        n: int,
        k: int
) -> int:
    """
    Calculate the number of combinations (n choose k).

    Parameters
    ----------
    n : int
        The total number of elements.
    k : int
        The number of elements to choose.

    Returns
    -------
    int
        The number of combinations (n choose k).
    """
    result = 1
    for i in range(1, k + 1):
        result *= (n - i + 1) / i
    return int(result)
