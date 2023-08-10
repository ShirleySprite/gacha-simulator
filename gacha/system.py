import math
from dataclasses import dataclass
from typing import List, Optional, Union

import pandas as pd

from .utils import combination


@dataclass
class GachaMeta:
    base_prob: float
    base_cnt: int
    up_percent: float
    up_list: Optional[List]
    prob_increase: Optional[float]
    pity_cnt: Optional[int]
    major_pity: Union[bool, int]
    refresh: bool
    name: str


@dataclass
class ProbTable:
    regular_table: pd.DataFrame
    major_pity_table: Optional[pd.DataFrame]

    def __repr__(
            self
    ):
        regular_repr = self.regular_table.shape
        major_repr = self.major_pity_table.shape if self.major_pity_table is not None else None

        return f"{self.__class__.__name__}(regular_table: {regular_repr}, major_pity_table: {major_repr})"


class GachaSystem:
    def __init__(
            self,
            base_prob: float,
            base_cnt: int,
            up_percent: float,
            up_list: Optional[List],
            prob_increase: Optional[float],
            pity_cnt: Optional[int],
            major_pity: Union[bool, int] = False,
            refresh: bool = True,
            name: str = 'unknown game'
    ):
        """
        Represents a gacha system of a specific mobile games.

        Parameters
        ----------
        base_prob : float
            The base probability of obtaining an SSR item.
        base_cnt : int
            The number of initial gacha attempts before the probability starts to increase.
        up_percent : float
            The percentage of rate-up items among all SSR items.
        up_list : Optional[List]
            List of rate-up items. Use `None` for no rate-up items, resulting in a regular item pool.
        prob_increase : Optional[float]
            The increase in probability each time the gacha is attempted after reaching `base_cnt`.
        pity_cnt : Optional[int]
            The number of gacha attempts needed to trigger the pity system.
        major_pity : Union[bool, int], default `False`
            Specifies the presence and mode of the major pity mechanic in the gacha system.
            Note that the exchange system is not considered a part of the major pity system.
            - Set to `False` for a multi-rate-ups item pool.
            - Set to `True` for a single-rate-up item pool.
              The probabilities undergo a complete change after obtaining a non-rate-up SSR item.
            - Pass an `int` to enforce obtaining the desired item when the number of attempts reaches this value,
              without altering any probabilities beforehand.
        refresh: bool
            Refresh the item pool immediately after obtaining an SSR item?
            For most games, this setting is `True`.
        name : Optional[str]
            The name of your mobile game.
        """
        self.meta = GachaMeta(
            base_prob,
            base_cnt,
            up_percent,
            up_list,
            prob_increase,
            pity_cnt,
            major_pity,
            refresh,
            name
        )
        self._adjust()
        self.prob_table = self._gen_prob_table()
        self.expectation = self._cal_expectation()
        self.theoretical_prob = 1 / self.expectation

    def __repr__(
            self
    ):
        return repr(self.meta).replace('GachaMeta', self.__class__.__name__)

    def __str__(
            self
    ):
        return f"The {self.__class__.__name__} for {self.meta.name}, " \
               f"expectation={self.expectation:.1f}, " \
               f"theoretical_prob={100 * self.theoretical_prob:.2f}%"

    def _adjust(
            self
    ):
        if self.meta.up_list is None:
            self.meta.up_list = []
        if self.meta.prob_increase is None:
            self.meta.prob_increase = 0
        if self.meta.pity_cnt is None:
            self.meta.pity_cnt = self.meta.base_cnt + math.ceil((1 - self.meta.base_prob) / self.meta.prob_increase)

    @staticmethod
    def _split_weights(
            n_up,
            cur_prob,
            up_percent
    ):
        result = (
                [1 - cur_prob, cur_prob * (1 - up_percent)] +
                [cur_prob * up_percent / n_up for _ in range(n_up)] +
                [cur_prob]
        )

        return list(map(lambda x: round(x, 4), result))

    def _gen_prob_table(
            self
    ):
        # ssr probability
        meta = self.meta
        result = [
            meta.base_prob + max(0, i - meta.base_cnt) * meta.prob_increase
            for i in range(1, meta.pity_cnt + 1)
        ]
        if meta.refresh:
            result[-1] = 1

        # n-gacha prob
        n_up = len(meta.up_list)
        ssr_n_gacha = []
        cum_prob = 1
        for prob in result:
            ssr_n_gacha.append(cum_prob * prob)
            cum_prob *= 1 - prob

        # no_major / major weights
        card_pool = ['no_ssr', 'other_ssr'] + meta.up_list + ['total_ssr']
        regular_result = [
            self._split_weights(
                n_up=n_up,
                cur_prob=p,
                up_percent=meta.up_percent
            )
            for p in result
        ]
        regular_df = pd.DataFrame(regular_result, columns=card_pool)
        regular_df.index += 1
        regular_df['ssr_n_gacha'] = ssr_n_gacha

        if type(meta.major_pity) == bool and meta.major_pity:
            major_pity_df = regular_df.copy()
            major_pity_df[card_pool] = [
                self._split_weights(
                    n_up=n_up,
                    cur_prob=p,
                    up_percent=1
                )
                for p in result
            ]
        else:
            major_pity_df = None

        return ProbTable(regular_df, major_pity_df)

    def _cal_refresh_expectation(
            self
    ):
        regular_df = self.prob_table.regular_table

        return sum(regular_df.index * regular_df['ssr_n_gacha'])

    def _cal_not_refresh_expectation(
            self
    ):
        ssr = self.meta.base_prob
        no_ssr = 1 - ssr
        n = self.meta.pity_cnt
        expectation = 0
        for i in range(n + 1):
            cur = combination(n, i) * (no_ssr ** (n - i)) * (ssr ** i)
            if i == 0:
                i = 1
            expectation += i * cur

        return n / expectation

    def _cal_expectation(
            self
    ):
        if self.meta.refresh:
            return self._cal_refresh_expectation()
        else:
            return self._cal_not_refresh_expectation()
