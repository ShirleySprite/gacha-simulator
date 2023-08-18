import math

from dataclasses import dataclass, field
from typing import List, Optional, Union


@dataclass
class GachaMeta:
    base_prob: float
    base_cnt: int
    up_percent: float
    up_list: Optional[List]
    prob_increase: Optional[float]
    pity_cnt: Optional[int]
    official_prob: Optional[float]
    major_pity: Union[bool, int]
    refresh: bool
    name: str
    prob_list: List = field(init=False, repr=False)

    def __post_init__(
            self
    ):
        if self.up_list is None:
            self.up_list = []

        if self.pity_cnt is None:
            self.pity_cnt = self.base_cnt + math.ceil((1 - self.base_prob) / self.prob_increase)

        if type(self.prob_increase) in [int, float]:
            self.prob_list = [
                self.base_prob + max(0, i - self.base_cnt) * self.prob_increase
                for i in range(1, self.pity_cnt + 1)
            ]
        else:
            self.prob_list = []
