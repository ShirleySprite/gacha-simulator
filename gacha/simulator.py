import math
from typing import Union, Dict, List, Tuple, Generator, Optional, Callable
from random import choices
from enum import Enum
from collections import Counter
from warnings import warn

from tqdm import tqdm

from .meta import GachaMeta
from .system import GachaSystem
from .utils import counter_contain
from .exceptions import SystemBuildError


class ProbIncreaseMode(Enum):
    ARITHMETIC = ('Consider the probability after base_cnt as an arithmetic progression.', 1)
    GEOMETRIC = ('Consider the probability after base_cnt as a geometric progression.', 2)
    LOG = ('Consider the probability after base_cnt as a logarithmic function.', 3)

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
    prob_increase_mode = ProbIncreaseMode

    def __init__(
            self,
            base_prob: float,
            base_cnt: int,
            up_percent: float,
            up_list: Optional[List] = None,
            prob_increase: Optional[float] = None,
            pity_cnt: Optional[int] = None,
            official_prob: Optional[float] = None,
            major_pity: Union[bool, int] = False,
            refresh: bool = True,
            name: str = 'unknown game'
    ):
        """
        A simulator for a specific gacha system.

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
        official_prob : Optional[float]
            The official theoretical probability, taking the pity system into account.
        major_pity : Union[bool, int], default `False`
            Specifies the presence and mode of the major pity mechanic in the gacha system.
            Note that the exchange system is not considered a part of the major pity system.
            - Set to `False` for an exchange system.
            - Set to `True` for a single-rate-up item pool.
              The probabilities undergo a complete change after obtaining a non-rate-up SSR item.
            - Pass an `int` to enforce obtaining the desired item when the number of attempts reaches this value,
              without altering any probabilities beforehand.
        refresh: bool, default `True`
            Refresh the item pool immediately after obtaining an SSR item?
            For most games, this setting is `True`.
        name : Optional[str], default 'unknown game'
            The name of your mobile game.
        """
        meta = GachaMeta(
            base_prob,
            base_cnt,
            up_percent,
            up_list,
            prob_increase,
            pity_cnt,
            official_prob,
            major_pity,
            refresh,
            name
        )
        self._meta = meta
        if self._check():
            self.gacha_system = GachaSystem(self._meta)
            del self._meta
        else:
            self.gacha_system = None

    def __repr__(
            self
    ):
        if self.gacha_system is None:
            meta = self._meta
        else:
            meta = self.gacha_system.meta

        return f"{self.__class__.__name__}{repr(meta).replace(meta.__class__.__name__, '')}"

    def __str__(
            self
    ):
        if self.gacha_system is None:
            name = self._meta.name
        else:
            name = self.gacha_system.meta.name

        return f"The {self.__class__.__name__} for {name}"

    def _check(self):
        meta = self._meta

        if meta.prob_increase is None:
            if meta.official_prob:
                warn('Failed to build the gacha system due to the lack of probability increment pattern.'
                     'Please first use `estimate_prob_list()` to construct the probability list '
                     'and then manually call `build_system()`')
                return False
            raise SystemBuildError("can't miss both `prob_increase` and `official_prob`")

        if not (0 < meta.base_prob < 1):
            raise SystemBuildError("invalid `base_prob`")

        if not (0 < meta.up_percent <= 1):
            raise SystemBuildError("invalid `up_percent`")

        if not (0 <= meta.prob_increase < 1):
            raise SystemBuildError("invalid `prob_increase`")

        if meta.base_cnt > meta.pity_cnt:
            raise SystemBuildError("`base_cnt` greater than `pity_cnt`")

        return True

    def estimate_prob_list(
            self,
            prob_increase_mode: Union[ProbIncreaseMode, Callable] = ProbIncreaseMode.ARITHMETIC,
            estimate_init: float = 0.02,
            step: float = 0.001,
            n_epoch: int = 1000
    ) -> Tuple:
        """
        This function is used to infer the probability increase in case there is a mechanism for probability increment
        but the per-time increase rate is not specified. By considering the cumulative probability,
        an arithmetic progression is utilized to estimate the probability increase.

        Parameters
        ----------
        prob_increase_mode : Union[ProbIncreaseMode, Callable]
            A built-in mode or custom function.
        estimate_init : float, default `0.02`
            The initial value for the estimation of the increase parameter.
            The default value `0.02` is a suitable choice for arithmetic progression.
        step : float
            The amount added or subtracted to the estimation of the increase parameter at each step.
        n_epoch : int
            Number of epochs to perform.

        Returns
        -------
        Tuple
            A probability list and the difference between the official probability and the calculated probability.
        """
        meta = self._meta
        mode_dict = {
            ProbIncreaseMode.ARITHMETIC: lambda base, cnt, k: base + cnt * k,
            ProbIncreaseMode.GEOMETRIC: lambda base, cnt, k: base * (k ** cnt),
            ProbIncreaseMode.LOG: lambda base, cnt, k: base + k * math.log2(cnt)
        }

        prob_list = []
        base_cum_exp = 0
        base_cum_prob = 1
        base_prob = meta.base_prob
        for i in range(1, meta.base_cnt + 1):
            prob_list.append(base_prob)
            base_cum_exp += i * base_cum_prob * base_prob
            base_cum_prob *= 1 - base_prob

        diff = None
        estimate = estimate_init
        for _ in range(n_epoch):
            prob_list = prob_list[:meta.base_cnt]
            cum_exp = 0
            cum_prob = base_cum_prob
            for j in range(meta.base_cnt + 1, meta.pity_cnt + 1):
                increase_func = mode_dict.get(prob_increase_mode, prob_increase_mode)
                prob = min(1, increase_func(base_prob, j - meta.base_cnt, estimate))
                prob_list.append(prob)
                cum_exp += j * cum_prob * prob
                cum_prob *= 1 - prob

            diff = round(meta.official_prob - (1 / (base_cum_exp + cum_exp)), 4)
            if diff > 0:
                estimate += step
            elif diff < 0:
                estimate -= step
            else:
                break

        meta.prob_list = prob_list

        return estimate, diff

    def build_system(
            self
    ) -> None:
        """
        Manually builds the gacha system if it was not built in the `.__init__()` method.

        Returns
        -------
        None
        """
        if not isinstance(self.gacha_system, GachaSystem):
            self.gacha_system = GachaSystem(self._meta)
            del self._meta

    def _multi_attempts_normal(
            self,
            n_attempts: int,
            start: int,
            major_pity_start: bool
    ):
        """
        For most normal games.
        Such as `Arknights`, `Genshin Impact` and so on.
        """
        # useful information
        drop_cols = 2
        reg_values = self.gacha_system.prob_table.regular_table.values[:, :-drop_cols]
        maj_values = None
        mp = self.gacha_system.meta.major_pity
        if mp:
            maj_values = self.gacha_system.prob_table.major_pity_table.values[:, :-drop_cols]
        item_pool = self.gacha_system.prob_table.regular_table.columns[:-drop_cols]
        values = maj_values if major_pity_start else reg_values

        # helper variables
        cur_cnt = start
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
                if result == 'other_ssr':
                    values = maj_values
                else:
                    values = reg_values

            yield cur_cnt, result

            # refresh
            cur_cnt = 0

    def _multi_attempts_not_refresh(
            self,
            n_attempts: int,
            start: int
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
        cur_cnt = start
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
            n_attempts,
            start,
            major_pity_start
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
        cur_cnt = start
        maj_cnt = major_pity_start
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
            n_attempts: int,
            start: int = 0,
            major_pity_start: Union[bool, int] = False
    ) -> Generator[Tuple, None, None]:

        """
        Function for performing multiple gacha attempts, returning the result of each attempt as a generator.

        Parameters
        ----------
        n_attempts : int
            Number of attempts to perform.
        start : int
            The starting point of the attempt, indicating at which draw it is located in the current item pool.
        major_pity_start: Union[bool, int], default `False`
            If `True`/`False`, it represents whether the major pity is approaching.
            If it is an `int`, it indicates that the major pity system is at the N-th guarantee,
            and the `major_pity_start` draws have already been completed.

        Yields
        -------
        Tuple
            Attempt results: The number of attempts made to obtain this SSR item and the obtained SSR item.
        """
        meta = self.gacha_system.meta
        if meta.refresh and type(meta.major_pity) == bool:
            return self._multi_attempts_normal(
                n_attempts=n_attempts,
                start=start,
                major_pity_start=major_pity_start
            )

        elif not meta.refresh:
            return self._multi_attempts_not_refresh(
                n_attempts=n_attempts,
                start=start
            )

        elif meta.refresh and type(meta.major_pity) == int:
            return self._multi_attempts_specific_major_pity(
                n_attempts=n_attempts,
                start=start,
                major_pity_start=int(major_pity_start)
            )

    def multi_experiments(
            self,
            mode: ExperimentMode,
            n_attempts: int = 10000,
            start: int = 0,
            major_pity_start: Union[bool, int] = False,
            total_round: int = 10000
    ) -> List:
        """
        Conveniently perform multiple sets of experiments, each involving multiple attempts.
        Includes built-in common statistical methods.

        Parameters
        ----------
        mode : ExperimentMode
            Desired type of experimental results.
        n_attempts : int, default `10000`
            Number of attempts per single experiment, default is `10000`.
        start : int
            The starting point of the attempt, indicating at which draw it is located in the current item pool.
        major_pity_start: Union[bool, int], default `False`
            If `True`/`False`, it represents whether the major pity is approaching.
            If it is an `int`, it indicates that the major pity system is at the N-th guarantee,
            and the `major_pity_start` draws have already been completed.
        total_round : int
            Total number of experiment rounds.

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
            single_result = list(
                self.multi_attempts(
                    n_attempts=n_attempts,
                    start=start,
                    major_pity_start=major_pity_start
                )
            )
            rec.append(
                regular_methods[mode](n_attempts, single_result)
            )

        return rec

    def simulate_by_attempts(
            self,
            n_attempts: int,
            targets: Union[Dict, List],
            start: int = 0,
            major_pity_start: Union[bool, int] = False,
            total_round: int = 10000
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
        start : int
            The starting point of the attempt, indicating at which draw it is located in the current item pool.
        major_pity_start: Union[bool, int], default `False`
            If `True`/`False`, it represents whether the major pity is approaching.
            If it is an `int`, it indicates that the major pity system is at the N-th guarantee,
            and the `major_pity_start` draws have already been completed.
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
            ssr_rec = self.multi_attempts(
                n_attempts,
                start=start,
                major_pity_start=major_pity_start
            )
            rec_cnt = Counter([x[1] for x in ssr_rec])

            yield counter_contain(rec_cnt, target_cnt)

    def simulate_by_targets(
            self,
            targets: Union[Dict, List],
            start: int = 0,
            major_pity_start: Union[bool, int] = False,
            total_round: int = 10000
    ) -> Generator[int, None, None]:
        """
        Perform multiple simulations to achieve SSR targets and yield the number of gacha attempts needed,
        in the form of a generator.

        Parameters
        ----------
        targets : Union[Dict, List]
            The desired SSR targets. Can be in dictionary or list format.
        start : int
            The starting point of the attempt, indicating at which draw it is located in the current item pool.
        major_pity_start: Union[bool, int], default `False`
            If `True`/`False`, it represents whether the major pity is approaching.
            If it is an `int`, it indicates that the major pity system is at the N-th guarantee,
            and the `major_pity_start` draws have already been completed.
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
            ssr_rec = self.multi_attempts(
                10 ** 8,
                start=start,
                major_pity_start=major_pity_start
            )
            i = -start
            for n_attempts, ssr_item in ssr_rec:
                i += n_attempts
                cur_cnt[ssr_item] += 1
                if counter_contain(cur_cnt, target_cnt):
                    ssr_rec.close()

            yield i

    def exceed_percent(
            self,
            targets: Union[Dict, List],
            n_attempts: int,
            start: int,
            major_pity_start: Union[bool, int] = False,
            total_round: int = 10000
    ) -> float:
        """
        Analyze the gacha results and return the percentage of people exceeded in decimal form.

        Parameters
        ----------
        targets : Union[Dict, List]
            The desired SSR targets. Can be in dictionary or list format.
        n_attempts : int
            The total number of attempts made.
        start : int
            The starting point of the attempt, indicating at which draw it is located in the current item pool.
        major_pity_start: Union[bool, int], default `False`
            If `True`/`False`, it represents whether the major pity is approaching.
            If it is an `int`, it indicates that the major pity system is at the N-th guarantee,
            and the `major_pity_start` draws have already been completed.
        total_round : int
            The total number of simulation rounds.

        Returns
        -------
        float
            The percentage of people exceeded.
        """
        result = self.simulate_by_targets(
            targets=targets,
            start=start,
            major_pity_start=major_pity_start,
            total_round=total_round
        )

        n_exceed = 0
        for x in result:
            if x >= n_attempts:
                n_exceed += 1

        return n_exceed / total_round
