import pytest
from unittest.mock import patch

from boss_battles.game import BossBattle
from boss_battles.character import Player, PracticeDummy, Stats
from boss_battles.command import Command
from boss_battles.ability import AbilityRegistry, Ability, EffectType


# hit roll 10 (hits practice dummy 100%), roll of 1 on punch does 1 damage
@patch("random.randint", side_effect=[10, 1])
def test_practice_dummy_battle(mock_randint):
    boss = PracticeDummy()
    player = Player.roll_fighter("player")
    battle = BossBattle(players=[player], bosses=[boss])
    battle._generate_opportunity_tokens()
    assert len(battle._boss_tokens) == 1
    assert type(battle._boss_tokens['dummy']) is list

    assert boss.get_health() == 500

    # PLAYER TURN
    message = Command("player@dummy/punch")
    battle.handle_action(message)

    # Confirm the punch was made on the boss
    ability = AbilityRegistry.registry.get(message.action)
    assert ability.identifier == "punch"

    assert Stats.calc_modifier(boss.stats.dexterity) <= 0  # AC of stationary practice dummy

    # punch is 1 dmg +3 str mod = 4 damage
    assert boss.get_health() == 500 - 4

    # BOSS TURN
    boss.do_turn(battle)

    # the practice dummy restores whatever damage it took
    assert boss.get_health() == 500


@patch("random.randint", side_effect=[19] + [1] * 1000)
def test_practice_dummy_health_expands_when_damaged_beyond_capacity(mock_randint):
    class MonsterTestAttack(Ability):
        identifier = "monstertest"
        name = "Monster Test Attack"
        effect_die = (1000, 1)  # XdY - num rolls, dice size
        effect_type = EffectType.BLUDGEONING
        modifier_type = Stats.Type.STRENGTH

        def verify(self, op_token, solve_token) -> bool:
            return True


    boss = PracticeDummy()
    player = Player.roll_fighter("player")
    battle = BossBattle(players=[player], bosses=[boss])
    battle._generate_opportunity_tokens()

    assert boss.get_health() == 500

    # PLAYER TURN
    message = Command("player@dummy/monstertest")
    battle.handle_action(message)

    assert boss.get_health() == 0

    # BOSS TURN
    boss.do_turn(battle)

    # Dummy should add x2 the previous health
    # 500 * 2 = 1000
    assert boss.get_max_health() == 1000
    assert boss.get_health() == 1000

