from typing import Union, Dict, List
from random import choices
from enum import Enum
from collections import Counter

import numpy as np
from tqdm import tqdm

from .system import GachaSystem
from .utils import counter_contain


class ExperimentMode(Enum):
    SSR_CNT = ('record SSR count', 1)
    SAMPLE_MEAN = ('record sample mean', 2)
    EMPIRICAL_PROB = ('record empirical probability', 3)

    def __init__(
            self,
            description,
            value
    ):
        self._description = description
        self._value = value

    @property
    def description(self):
        return self._description

    @property
    def value(self):
        return self._value


class GachaSimulator:
    experiment_mode = ExperimentMode

    def __init__(
            self,
            gacha_system: GachaSystem
    ):
        self.gacha_system = gacha_system

    def __repr__(
            self
    ):
        return f"{self.__class__.__name__}(gacha_system={repr(self.gacha_system)})"

    def __str__(
            self
    ):

        return f"The {self.__class__.__name__} for {self.gacha_system.meta.name}"

    def multi_choices(
            self,
            times
    ):
        cur_cnt = 0
        drop_cols = 2
        reg_values = self.gacha_system.prob_table.regular_table.values[:, :-drop_cols]
        maj_values = None
        if self.gacha_system.meta.major_pity:
            maj_values = self.gacha_system.prob_table.major_pity_table.values[:, :-drop_cols]
        card_pool = self.gacha_system.prob_table.regular_table.columns[:-drop_cols]
        values = reg_values
        for _ in range(times):
            weight = values[cur_cnt]
            result = choices(card_pool, weight)[0]
            cur_cnt += 1

            cur_up = self.gacha_system.meta.up_list[0]
            if result != 'no_ssr':
                # major pity system
                if self.gacha_system.meta.major_pity:
                    if result != cur_up:
                        values = maj_values
                    else:
                        values = reg_values

                yield cur_cnt, result
                cur_cnt = 0

    def multi_experiments(
            self,
            mode: ExperimentMode,
            total_round: int,
            single_experiment: int = 10000
    ):
        regular_methods = {
            ExperimentMode.SSR_CNT: lambda n_attempts, record: len(record),
            ExperimentMode.SAMPLE_MEAN: lambda n_attempts, record: n_attempts / len(record),
            ExperimentMode.EMPIRICAL_PROB: lambda n_attempts, record: len(record) / n_attempts,
        }

        rec = []
        for _ in tqdm(range(total_round)):
            single_result = list(self.multi_choices(single_experiment))
            rec.append(
                regular_methods[mode](single_experiment, single_result)
            )

        return rec

    def simulate_by_attempts(
            self,
            n_attempts: int,
            targets: Union[Dict, List],
            total_round: int,
    ):
        target_cnt = Counter(targets)
        result = []
        for _ in tqdm(range(total_round)):
            ssr_rec = self.multi_choices(n_attempts)
            rec_cnt = Counter([x[1] for x in ssr_rec])
            result.append(counter_contain(rec_cnt, target_cnt))

        return result

    def simulate_by_targets(
            self,
            targets: Union[Dict, List],
            total_round: int,
    ):
        target_cnt = Counter(targets)
        result = []
        for _ in tqdm(range(total_round)):
            cur_cnt = Counter()
            ssr_rec = self.multi_choices(10 ** 8)
            i = 0
            for n_attempts, ssr_item in ssr_rec:
                i += n_attempts
                cur_cnt[ssr_item] += 1
                if counter_contain(cur_cnt, target_cnt):
                    ssr_rec.close()
            result.append(i)

        return result
