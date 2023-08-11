from enum import Enum


class Games(Enum):
    KLEINS = 1
    MILKY_WAY = 2
    NOWHERE = 3
    ARKNIGHTS = 4
    HONKAI_IMPACT_2_HIME = 5
    HONKAI_IMPACT_2_MAJO = 6

    @property
    def gacha_data(
            self
    ):
        return _g_sys(self.value)


def _g_sys(
        game_id
):
    common = {
        1: {
            'base_prob': 0.016,
            'base_cnt': 60,
            'up_percent': 0.5,
            'up_list': ['A', 'B'],
            'prob_increase': 0.02,
            'pity_cnt': 80,
            'official_prob': None,
            'major_pity': True,
            'refresh': True,
            'name': 'Kleins'
        },
        2: {
            'base_prob': 0.02,
            'base_cnt': 50,
            'up_percent': 0.5,
            'up_list': ['A'],
            'prob_increase': 0.02,
            'pity_cnt': 80,
            'official_prob': None,
            'major_pity': 150,
            'refresh': True,
            'name': 'Milky Way'
        },
        3: {
            'base_prob': 0.02,
            'base_cnt': 50,
            'up_percent': 0.5,
            'up_list': ['A'],
            'prob_increase': None,
            'pity_cnt': 80,
            'official_prob': 0.0284,
            'major_pity': True,
            'refresh': True,
            'name': 'Nowhere'
        },
        4: {
            'base_prob': 0.02,
            'base_cnt': 50,
            'up_percent': 0.5,
            'up_list': ['A'],
            'prob_increase': 0.02,
            'pity_cnt': None,
            'official_prob': None,
            'major_pity': False,
            'refresh': True,
            'name': 'Arknights'
        },
        5: {
            'base_prob': 0.05,
            'base_cnt': 10,
            'up_percent': 0.5,
            'up_list': ['A', 'B', 'C', 'D', 'E', 'F'],
            'prob_increase': 0,
            'pity_cnt': 10,
            'official_prob': None,
            'major_pity': False,
            'refresh': False,
            'name': 'Honkai Impact 2 Hime'
        },
        6: {
            'base_prob': 0.05,
            'base_cnt': 7,
            'up_percent': 0.5,
            'up_list': ['A', 'B', 'C', 'D'],
            'prob_increase': 0,
            'pity_cnt': 7,
            'official_prob': None,
            'major_pity': False,
            'refresh': False,
            'name': 'Honkai Impact 2 Hime'
        }
    }

    return common.get(game_id)
