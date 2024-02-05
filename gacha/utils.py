from collections import Counter
from typing import List

import numpy as np
from scipy.optimize import minimize, OptimizeResult


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


def cal_individual_probs(
        base_prob: float,
        base_cnt: int,
        pity_cnt: int,
        prob_increase: float
) -> List[float]:
    """
    Calculate the individual probabilities based on the given parameters.

    Parameters:
    -----------
    base_prob : float
        The base probability of the event.
    base_cnt : int
        The base count or threshold after which the probability starts increasing.
    pity_cnt : int
        The number of times until which the probability increases.
    prob_increase : float
        The increment in probability for each count beyond the base count.

    Returns:
    --------
    individual_probs : List[float]
        A list containing the individual probabilities for each count.
    """
    return [
        base_prob + max(0, i - base_cnt) * prob_increase
        for i in range(1, pity_cnt)
    ] + [1]


def cal_conditional_probs(
        prob_list: List[float]
) -> List[float]:
    """
    Calculate the conditional probabilities based on the individual probabilities.

    Parameters:
    -----------
    prob_list : List[float]
        A list containing the individual probabilities for each count.

    Returns:
    --------
    conditional_probs : List[float]
        A list containing the conditional probabilities calculated based on the individual probabilities.
    """
    conditional_probs = []
    last_condi = 1
    for prob in prob_list:
        conditional_probs.append(last_condi * prob)
        last_condi *= 1 - prob

    return conditional_probs


def cal_expectation(
        prob_list: List[float]
) -> float:
    """
    Calculate the expectation based on the list of conditional probabilities.

    Parameters:
    -----------
    prob_list : List[float]
        A list containing the conditional probabilities.

    Returns:
    --------
    expectation : float
        The calculated expectation based on the conditional probabilities.
    """
    expectation = 0
    for i, p in enumerate(prob_list):
        expectation += (i + 1) * p

    return expectation


def estimate_prob_increase(
        base_prob: float,
        base_cnt: int,
        pity_cnt: int,
        target_prob: float
) -> OptimizeResult:
    """
    Estimate the probability increase to approximate the target probability by minimizing the loss function.
    Note that the probability increase is linearly incremented.

    Parameters:
    -----------
    base_prob : float
        The base probability of the event.
    base_cnt : int
        The base count or threshold after which the probability starts increasing.
    pity_cnt : int
        The number of times until which the probability increases.
    target_prob : float
        The target probability to be approximated.

    Returns:
    --------
    mini_result : OptimizeResult
        An object containing the result of the minimization process.
    """

    def _prob_loss(
            est_increase
    ):
        ind_probs = cal_individual_probs(
            base_prob,
            base_cnt,
            pity_cnt,
            est_increase[0]
        )
        condi_probs = cal_conditional_probs(ind_probs)
        total_prob = 1 / cal_expectation(condi_probs)

        return ((total_prob - target_prob) * 1e6) ** 2

    mini_result = minimize(
        fun=_prob_loss,
        x0=np.array([0.01]),
        options={"xrtol": 1e-4}
    )

    return mini_result
