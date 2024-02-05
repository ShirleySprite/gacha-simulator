from dataclasses import dataclass
from typing import List, Optional


@dataclass
class GachaMeta:
    base_prob: float
    base_cnt: int
    up_percent: float
    up_list: Optional[List]
    prob_increase: Optional[float]
    pity_cnt: int
    official_prob: Optional[float]
    major_pity_list: Optional[List]
    refresh: bool
    name: str
