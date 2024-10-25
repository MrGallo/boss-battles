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
    player = Player("player")
    battle = BossBattle(players=[player], bosses=[boss])
    battle._generate_opportunity_tokens()
    assert len(battle._boss_tokens) == 1
    assert type(battle._boss_tokens['dummy']) is list

    assert boss._stats.health == 500

    # PLAYER TURN
    message = Command("player@dummy/punch")
    battle.handle_action(message)

    # Confirm the punch was made on the boss
    ability = AbilityRegistry.registry.get(message.action)
    assert ability.identifier == "punch"

    assert BossBattle.calc_modifier(boss._stats.dexterity) <= 0  # AC of stationary practice dummy

    assert boss._stats.health == 500 - 1

    # BOSS TURN
    boss.do_turn(battle)

    # the practice dummy restores whatever damage it took
    assert boss._stats.health == 500


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
    player = Player("player")
    battle = BossBattle(players=[player], bosses=[boss])
    battle._generate_opportunity_tokens()

    assert boss._stats.health == 500

    # PLAYER TURN
    message = Command("player@dummy/monstertest")
    battle.handle_action(message)

    assert boss._stats.health == 500 - 1000

    # BOSS TURN
    boss.do_turn(battle)

    # Dummy should add x2 the damage deficit caused by the last round
    # 500 - 1000 = -500
    # so it should add 250 hp to base stats
    assert boss._base_stats.health == 500 + 250
    assert boss._stats.health == 500 + 250

