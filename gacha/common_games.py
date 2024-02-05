from enum import Enum


class Games(Enum):
    KLEINS = 1
    # MILKY_WAY = 2
    NOWHERE = 3
    ARKNIGHTS = 4
    THRUD_CHARACTER = 5
    THRUD_WEAPON = 6
    GENSHIN = 7
    DEEPSPACE = 8

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
            'major_pity_list': ['A', 'B'],
            'name': 'Kleins'
        },
        # 2: {
        #     'base_prob': 0.02,
        #     'base_cnt': 50,
        #     'up_percent': 0.5,
        #     'up_list': ['A'],
        #     'prob_increase': 0.02,
        #     'pity_cnt': 80,
        #     'official_prob': None,
        #     'major_pity_list': 150,
        #     'name': 'Milky Way'
        # },
        3: {
            'base_prob': 0.02,
            'base_cnt': 50,
            'up_percent': 0.5,
            'up_list': ['A'],
            'prob_increase': None,
            'pity_cnt': 80,
            'official_prob': 0.0284,
            'major_pity_list': ['A'],
            'name': 'Nowhere'
        },
        4: {
            'base_prob': 0.02,
            'base_cnt': 50,
            'up_percent': 0.5,
            'up_list': ['A'],
            'prob_increase': 0.02,
            'pity_cnt': 99,
            'official_prob': None,
            'major_pity_list': None,
            'name': 'Arknights'
        },
        5: {
            'base_prob': 0.0085,
            'base_cnt': 70,
            'up_percent': 0.5,
            'up_list': ['A'],
            'prob_increase': 0.05,
            'pity_cnt': 80,
            'official_prob': 0.018,
            'major_pity_list': ['A'],
            'name': 'Thrud Character'
        },
        6: {
            'base_prob': 0.01,
            'base_cnt': 50,
            'up_percent': 1,
            'up_list': ['A'],
            'prob_increase': 0,
            'pity_cnt': 50,
            'official_prob': 0.025,
            'major_pity_list': ['A'],
            'name': 'Thrud Weapon'
        },
        7: {
            'base_prob': 0.006,
            'base_cnt': 73,
            'up_percent': 0.5,
            'up_list': ['A'],
            'prob_increase': 0.06,
            'pity_cnt': 90,
            'official_prob': 0.016,
            'major_pity_list': ['A'],
            'name': 'Genshin Impact'
        },
        8: {
            'base_prob': 0.01,
            'base_cnt': 60,
            'up_percent': 0.5,
            'up_list': ['A'],
            'prob_increase': 0.1,
            'pity_cnt': 70,
            'official_prob': 0.021,
            'major_pity_list': ['A'],
            'name': 'Love and Deepspace'
        }
    }

    return common.get(game_id)
