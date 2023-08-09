import math
from dataclasses import dataclass
from typing import List, Optional

import pandas as pd


@dataclass
class GachaMeta:
    base_prob: float
    base_cnt: int
    up_percent: float
    up_list: Optional[List]
    prob_increase: Optional[float]
    pity_cnt: Optional[int]
    major_pity_round: Optional[int]  # only for single up


class GachaSystem:
    def __init__(
            self,
            base_prob: float,
            base_cnt: int,
            up_percent: float,
            up_list: Optional[List],
            prob_increase: Optional[float],
            pity_cnt: Optional[int],
            major_pity_round: Optional[int]
    ):
        self.meta = GachaMeta(
            base_prob,
            base_cnt,
            up_percent,
            up_list,
            prob_increase,
            pity_cnt,
            major_pity_round
        )
        self._adjust()
        self.prob_table = self._gen_prob_table()
        self.expectation = self._cal_expectation()
        self.theoretical_prob = 1 / self.expectation

    def __repr__(
            self
    ):
        return repr(self.meta).replace('GachaMeta', 'GachaSystem')

    def __str__(
            self
    ):
        return f"GachaSystem(expectation={self.expectation:.1f}, theoretical_prob={100 * self.theoretical_prob:.2f}%)"

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
            up_list,
            cur_prob,
            up_percent
    ):
        n_up = len(up_list)
        result = (
                [1 - cur_prob, cur_prob * (1 - up_percent)] +
                [cur_prob * up_percent / n_up for _ in up_list]
        )

        return list(map(lambda x: round(x, 4), result))

    def _gen_prob_table(
            self
    ):
        # ssr probability dict
        meta = self.meta
        result = [
            meta.base_prob + max(0, i - meta.base_cnt) * meta.prob_increase
            for i in range(1, meta.pity_cnt + 1)
        ]
        result[-1] = 1

        # probability to weights
        weights_result = []
        card_pool = ['no_ssr', 'other_ssr'] + meta.up_list
        for p in result:
            weights = self._split_weights(
                up_list=meta.up_list,
                cur_prob=p,
                up_percent=meta.up_percent
            )
            weights_result.append(weights)

        weights_df = pd.DataFrame(weights_result, columns=card_pool)
        weights_df.index += 1

        return weights_df

    def _cal_expectation(
            self
    ):
        result = 0
        cum_prob = 1
        for k, cur_row in self.prob_table.iterrows():
            ssr_prob = 1 - cur_row[0]
            result += k * cum_prob * ssr_prob # noqa
            cum_prob *= cur_row[0]

        return result
