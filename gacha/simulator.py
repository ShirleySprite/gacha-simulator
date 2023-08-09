from random import choices
from enum import Enum

from tqdm import tqdm

from .system import GachaSystem


class ExperimentMode(Enum):
    RAW = ('raw record', 0)
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
    ):
        self.gacha_system = None

    def __repr__(
            self
    ):
        pass

    def apply_system(
            self,
            gacha_system: GachaSystem
    ):
        self.gacha_system = gacha_system

    def multi_choice(
            self,
            times
    ):
        ssr_rec = []
        cur_cnt = 0
        prob_table = self.gacha_system.prob_table
        values = prob_table.values
        card_pool = prob_table.columns
        for _ in range(times):
            weight = values[cur_cnt]
            result = choices(card_pool, weight)[0]
            cur_cnt += 1

            major_pity_round = self.gacha_system.meta.major_pity_round
            cur_up = self.gacha_system.meta.up_list[0]
            if result != 'no_ssr':
                # is major pity?
                if major_pity_round is not None:
                    latest_rec = [x[1] for x in ssr_rec[-major_pity_round + 1:]]
                    if cur_up not in latest_rec:
                        result = cur_up

                ssr_rec.append((cur_cnt, result))
                cur_cnt = 0

        return ssr_rec

    def multi_experiment(
            self,
            mode: ExperimentMode,
            total_round: int,
            single_experiment: int = 10000
    ):
        rec = []
        for _ in tqdm(range(total_round)):
            single_result = self.multi_choice(single_experiment)
            if mode == ExperimentMode.RAW:
                rec.append(single_result)
            elif mode == ExperimentMode.SSR_CNT:
                rec.append(len(single_result))
            elif mode == ExperimentMode.SAMPLE_MEAN:
                rec.append(single_experiment / len(single_result))
            elif mode == ExperimentMode.EMPIRICAL_PROB:
                rec.append(len(single_result) / single_experiment)

        return rec
