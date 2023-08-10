from typing import Union, Dict, List, Tuple, Generator
from random import choices
from enum import Enum
from collections import Counter

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

    def _multi_attempts_normal(
            self,
            n_attempts: int
    ):
        """
        For most normal games.
        Such as `Arknights`, `Genshin Impact` and so on.
        """
        # useful information
        drop_cols = 2
        cur_up = self.gacha_system.meta.up_list[0]
        reg_values = self.gacha_system.prob_table.regular_table.values[:, :-drop_cols]
        maj_values = None
        mp = self.gacha_system.meta.major_pity
        if mp:
            maj_values = self.gacha_system.prob_table.major_pity_table.values[:, :-drop_cols]
        item_pool = self.gacha_system.prob_table.regular_table.columns[:-drop_cols]
        values = reg_values

        # helper variables
        cur_cnt = 0
        for _ in range(n_attempts):
            # attempt once
            weight = values[cur_cnt]
            result = choices(item_pool, weight)[0]
            cur_cnt += 1

            # do not record normal items
            if result == 'no_ssr':
                continue

            # trigger major pity system
            if mp:
                if result != cur_up:
                    values = maj_values
                else:
                    values = reg_values

            yield cur_cnt, result

            # refresh
            cur_cnt = 0

    def _multi_attempts_not_refresh(
            self,
            n_attempts: int
    ):
        """
        For games that do not reset the pity system upon obtaining an SSR item,
        the reset occurs when the count reaches the maximum limit, as seen in games like 'Honkai Impact 2nd'.
        Please note that this function does not take into account the major pity system.
        """
        # useful information
        drop_cols = 2
        pity_cnt = self.gacha_system.meta.pity_cnt
        item_pool = self.gacha_system.prob_table.regular_table.columns[:-drop_cols]
        weight = self.gacha_system.prob_table.regular_table.iloc[0][:-drop_cols].tolist()

        # helper variables, remain `cur_cnt` var for record purpose
        cur_cnt = 0
        get_ssr = False
        for total_cnt in range(1, n_attempts + 1):
            if total_cnt % pity_cnt == 1:
                get_ssr = False

            cur_cnt += 1
            # attempt once
            result = choices(item_pool, weight)[0]

            # pity system
            if total_cnt % pity_cnt == 0:
                if not get_ssr:
                    result = choices(item_pool, [0] + weight[1:])[0]

            if result == 'no_ssr':
                continue

            yield cur_cnt, result

            cur_cnt = 0
            get_ssr = True

    def _multi_attempts_specific_major_pity(
            self,
            n_attempts
    ):
        """
        For games that guarantee obtaining the rate-up SSR when the count reaches a specific number
        and the SSR hasn't been obtained yet, such as in the game 'Milky Way'.
        """
        # useful information
        drop_cols = 2
        cur_up = self.gacha_system.meta.up_list[0]
        values = self.gacha_system.prob_table.regular_table.values[:, :-drop_cols]
        mp = self.gacha_system.meta.major_pity
        item_pool = self.gacha_system.prob_table.regular_table.columns[:-drop_cols]

        # helper variables
        cur_cnt = 0
        maj_cnt = 0
        for _ in range(n_attempts):
            # attempt once
            weight = values[cur_cnt]
            result = choices(item_pool, weight)[0]
            cur_cnt += 1

            # specific-attempts major pity system
            maj_cnt += 1
            if maj_cnt % mp == 0:
                result = cur_up

            # do not record normal items
            if result == 'no_ssr':
                continue

            # specific-attempts major pity system
            if result == cur_up:
                maj_cnt = 0

            yield cur_cnt, result

            # refresh
            cur_cnt = 0

    def multi_attempts(
            self,
            n_attempts: int
    ) -> Generator[Tuple, None, None]:
        """
        Function for performing multiple gacha attempts, returning the result of each attempt as a generator.

        Parameters
        ----------
        n_attempts : int
            Number of attempts to perform.

        Yields
        -------
        Tuple
            Attempt results: The number of attempts made to obtain this SSR item and the obtained SSR item.
        """
        meta = self.gacha_system.meta
        if meta.refresh and type(meta.major_pity) == bool:
            return self._multi_attempts_normal(n_attempts)
        elif not meta.refresh:
            return self._multi_attempts_not_refresh(n_attempts)
        elif meta.refresh and type(meta.major_pity) == int:
            return self._multi_attempts_specific_major_pity(n_attempts)

    def multi_experiments(
            self,
            mode: ExperimentMode,
            total_round: int,
            n_attempts: int = 10000
    ) -> List:
        """
        Conveniently perform multiple sets of experiments, each involving multiple attempts.
        Includes built-in common statistical methods.

        Parameters
        ----------
        mode : ExperimentMode
            Desired type of experimental results.
        total_round : int
            Total number of experiment rounds.
        n_attempts : int, default `10000`
            Number of attempts per single experiment, default is `10000`.

        Returns
        -------
        List
            List recording the results of each experiment.
        """
        regular_methods = {
            ExperimentMode.SSR_CNT: lambda attempts, record: len(record),
            ExperimentMode.SAMPLE_MEAN: lambda attempts, record: attempts / len(record),
            ExperimentMode.EMPIRICAL_PROB: lambda attempts, record: len(record) / attempts,
        }

        rec = []
        for _ in tqdm(range(total_round)):
            single_result = list(self.multi_attempts(n_attempts))
            rec.append(
                regular_methods[mode](n_attempts, single_result)
            )

        return rec

    def simulate_by_attempts(
            self,
            n_attempts: int,
            targets: Union[Dict, List],
            total_round: int,
    ) -> Generator[bool, None, None]:
        """
        Perform multiple simulations with given gacha attempts and SSR targets,
        yielding results as a generator indicating whether the targets are achieved or not.

        Parameters
        ----------
        n_attempts : int
            Number of gacha attempts per simulation.
            Usually depending on your plan.
        targets : Union[Dict, List]
            The desired SSR targets. Can be in dictionary or list format.
        total_round : int
            The total number of simulation rounds.

        Yields
        -------
        bool
            Generator yielding results. Each result is `True` or `False`,
            representing whether the targets are achieved or not.
        """
        target_cnt = Counter(targets)
        for _ in tqdm(range(total_round)):
            ssr_rec = self.multi_attempts(n_attempts)
            rec_cnt = Counter([x[1] for x in ssr_rec])
            yield counter_contain(rec_cnt, target_cnt)

    def simulate_by_targets(
            self,
            targets: Union[Dict, List],
            total_round: int,
    ) -> Generator[int, None, None]:
        """
        Perform multiple simulations to achieve SSR targets and yield the number of gacha attempts needed,
        in the form of a generator.

        Parameters
        ----------
        targets : Union[Dict, List]
            The desired SSR targets. Can be in dictionary or list format.
        total_round : int
            The total number of simulation rounds.

        Yields
        -------
        int
            The number of gacha attempts needed to achieve the targets for each simulation round.
        """
        target_cnt = Counter(targets)
        for _ in tqdm(range(total_round)):
            cur_cnt = Counter()
            ssr_rec = self.multi_attempts(10 ** 8)
            i = 0
            for n_attempts, ssr_item in ssr_rec:
                i += n_attempts
                cur_cnt[ssr_item] += 1
                if counter_contain(cur_cnt, target_cnt):
                    ssr_rec.close()
            yield i
