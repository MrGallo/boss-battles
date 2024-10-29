import pytest

from boss_battles.character import Stats


def test_stats_calculates_modifiers():
    assert Stats.calc_modifier(8) == -1
    assert Stats.calc_modifier(9) == -1
    assert Stats.calc_modifier(10) == 0
    assert Stats.calc_modifier(11) == 0
    assert Stats.calc_modifier(12) == 1
    assert Stats.calc_modifier(13) == 1
    assert Stats.calc_modifier(14) == 2
