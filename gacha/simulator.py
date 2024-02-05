from typing import Union, Dict, List, Generator, Optional, Tuple, Any
from random import choices
from collections import Counter
from copy import deepcopy

import pandas as pd

from gacha.meta import GachaMeta
from gacha.utils import counter_contain, cal_individual_probs, cal_conditional_probs, cal_expectation, \
    estimate_prob_increase
from gacha.exceptions import SystemBuildError


class GachaSimulator:
    def __init__(
            self,
            base_prob: float,
            base_cnt: int,
            up_percent: float,
            up_list: Optional[List] = None,
            prob_increase: Optional[float] = None,
            pity_cnt: Optional[int] = None,
            official_prob: Optional[float] = None,
            major_pity_list: Optional[List] = None,
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
        major_pity_list: Optional[List], default `None`
            The list of all SSR characters in the major pity cycle.
            `None` indicates no major pity mechanism, meaning all SSR characters are equally likely to be drawn.
        name : Optional[str], default 'unknown game'
            The name of your mobile game.
        """
        if prob_increase is None and official_prob is not None:
            prob_increase = estimate_prob_increase(
                base_prob=base_prob,
                base_cnt=base_cnt,
                pity_cnt=pity_cnt,
                target_prob=official_prob
            ).x[0]

        # store meta data
        self.meta = GachaMeta(
            base_prob,
            base_cnt,
            up_percent,
            up_list,
            prob_increase,
            pity_cnt,
            official_prob,
            major_pity_list,
            name
        )

        # check parameters
        self._check()

        # probabilities
        individual_probs = cal_individual_probs(
            base_prob=self.meta.base_prob,
            base_cnt=self.meta.base_cnt,
            pity_cnt=self.meta.pity_cnt,
            prob_increase=self.meta.prob_increase
        )
        conditional_probs = cal_conditional_probs(
            individual_probs
        )
        self.expectation = cal_expectation(conditional_probs)
        self.theoretical_prob = 1 / self.expectation

        # detailed probabilities
        n_up = len(up_list)
        regular_probs = []
        for indi_p, condi_p in zip(individual_probs, conditional_probs):
            cur_up = indi_p * up_percent
            regular_probs.append(
                {
                    "no_ssr": 1 - indi_p,
                    "other_ssr": indi_p - cur_up,
                    **{x: cur_up / n_up for x in up_list},
                    "total_ssr": indi_p,
                    "ssr_n_gacha": condi_p
                }
            )
        self.regular_probs = regular_probs

        major_pity_probs = deepcopy(regular_probs)
        if major_pity_list:
            n_up = len(major_pity_list)
            for x in major_pity_probs:
                x["other_ssr"] = 0
                indi_p = x["total_ssr"]
                single_ssr_p = indi_p / n_up
                for item in up_list:
                    x[item] = 0 if item not in major_pity_list else single_ssr_p

        self.major_pity_probs = major_pity_probs

    def __repr__(
            self
    ):
        return f"{self.__class__.__name__}{repr(self.meta).replace(self.meta.__class__.__name__, '')}"

    def __str__(
            self
    ):
        return f"The {self.__class__.__name__} for {self.meta.name}"

    def _check(
            self
    ):
        meta = self.meta

        if meta.prob_increase is None:
            if not meta.official_prob:
                raise SystemBuildError("can't miss both `prob_increase` and `official_prob`")

        if not (0 < meta.base_prob < 1):
            raise SystemBuildError("invalid `base_prob`")

        if not (0 < meta.up_percent <= 1):
            raise SystemBuildError("invalid `up_percent`")

        if not (0 <= meta.prob_increase < 1):
            raise SystemBuildError("invalid `prob_increase`")

        if meta.base_cnt > meta.pity_cnt:
            raise SystemBuildError("`base_cnt` greater than `pity_cnt`")

    @property
    def regular_table(
            self
    ):
        df = pd.DataFrame(self.regular_probs)
        df.index += 1

        return df

    @property
    def major_pity_table(
            self
    ):
        df = pd.DataFrame(self.major_pity_probs)
        df.index += 1

        return df

    def multi_attempts(
            self,
            n_attempts: int,
            start: int,
            major_pity_start: bool
    ) -> Generator[Tuple[int, Any], None, None]:
        major_pity_list = self.meta.major_pity_list

        if major_pity_start:
            values = self.major_pity_probs
        else:
            values = self.regular_probs

        cur_cnt = start
        for _ in range(n_attempts):
            # attempt once
            cur_value = values[cur_cnt]
            result = choices(list(cur_value.keys())[:-2], list(cur_value.values())[:-2])[0]
            cur_cnt += 1

            # do not record normal items
            if result == 'no_ssr':
                continue

            # trigger major pity system
            if major_pity_list and result in major_pity_list:
                values = self.regular_probs
            else:
                values = self.major_pity_probs

            yield cur_cnt, result

            # refresh
            cur_cnt = 0

    @staticmethod
    def _is_reach_target(
            records,
            target_list
    ):
        return any([counter_contain(records, t) for t in target_list])

    def simulate_by_attempts(
            self,
            n_attempts: int,
            targets: Union[Dict, List[Dict]],
            start: int = 0,
            major_pity_start: bool = False,
            total_round: int = 10000
    ) -> Generator[bool, None, None]:
        """
        Perform multiple simulations with given number of gacha attempts and SSR targets,
        yielding results as a generator indicating whether the targets are achieved or not.

        Parameters
        ----------
        n_attempts : int
            Number of gacha attempts per simulation.
            Usually depends on your plan.
        targets : Union[Dict, List[Dict]]
            The desired SSR items to obtain.
            `Dict` represents each SSR item and its corresponding quantity.
            `List` represents optional targets, and achieving any of them is considered a success.
        start : int
            The starting point of the attempt, indicating at which draw it is located in the current item pool.
        major_pity_start: bool, default `False`
            Indicates whether the major pity is approaching.
        total_round : int
            The total number of simulation rounds.

        Returns
        -------
        bool
            Generator yielding results. Each result is `True` or `False`,
            representing whether the targets are achieved or not.
        """
        if isinstance(targets, Dict):
            targets = [targets]
        targets = [Counter(x) for x in targets]

        for _ in range(total_round):
            rec = list(
                self.multi_attempts(
                    n_attempts=n_attempts,
                    start=start,
                    major_pity_start=major_pity_start
                )
            )
            rec_cnt = Counter([x[1] for x in rec])

            yield self._is_reach_target(rec_cnt, targets)

    def simulate_by_targets(
            self,
            targets: Union[Dict, List[Dict]],
            start: int = 0,
            major_pity_start: bool = False,
            total_round: int = 10000,
    ) -> Generator[int, None, None]:
        """
        Perform multiple simulations to achieve SSR targets and yield the number of gacha attempts needed,
        in the form of a generator.

        Parameters
        ----------
        targets : Union[Dict, List[Dict]]
            The desired SSR items to obtain.
            `Dict` represents each SSR item and its corresponding quantity.
            `List` represents optional targets, and achieving any of them is considered a success.
        start : int
            The starting point of the attempt, indicating at which draw it is located in the current item pool.
        major_pity_start: bool, default `False`
            Indicates whether the major pity is approaching.
        total_round : int
            The total number of simulation rounds.

        Yields
        -------
        int
            The number of gacha attempts needed to achieve the targets for each simulation round.
        """
        if isinstance(targets, Dict):
            targets = [targets]
        targets = [Counter(x) for x in targets]

        for _ in range(total_round):
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
                if self._is_reach_target(cur_cnt, targets):
                    ssr_rec.close()

            yield i
