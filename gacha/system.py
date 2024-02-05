from dataclasses import dataclass
from typing import Optional

import pandas as pd

from .utils import combination
from .meta import GachaMeta


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
            meta: GachaMeta
    ):
        self.meta = meta
        self.prob_table = self._gen_prob_table()
        self.expectation = self._cal_expectation()
        self.theoretical_prob = 1 / self.expectation

    def __repr__(
            self
    ):
        return f"{self.__class__.__name__}(meta={repr(self.meta)})"

    def __str__(
            self
    ):
        return f"The {self.__class__.__name__} for {self.meta.name}, " \
               f"expectation={self.expectation:.1f}, " \
               f"theoretical_prob={100 * self.theoretical_prob:.2f}%"

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
        result = meta.prob_list
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

    def _cal_expectation(
            self
    ):
        regular_df = self.prob_table.regular_table

        return sum(regular_df.index * regular_df['ssr_n_gacha'])
