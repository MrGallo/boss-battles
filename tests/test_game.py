import pytest
from unittest.mock import patch


from boss_battles.game import BossBattle, InvalidTargetError, InvalidAbilityError
from boss_battles.character import Squirrel, Player, Stats, Boss
from boss_battles.ability import EffectType, AbilityRegistry, Ability
from boss_battles.command import Command


@pytest.fixture
def test_boss():
    class TestBoss(Boss):
        def do_turn(self):
            pass

    return TestBoss("TestBoss", (1, 4), Stats())


def test_boss_battle_roll():
    assert BossBattle.roll(1, 1) == 1
    assert BossBattle.roll(2, 1) == 2


@patch("random.randint", side_effect=[2, 3, 5])
def test_boss_battle_roll_with_controlled_random(mock_randint):
    assert BossBattle.roll(1, 6) == 2  # roll of 2
    assert BossBattle.roll(2, 6) == 8  # rolls of 3 and 5


@patch("random.randint", side_effect=lambda *args: 2)
def test_boss_battle_roll_with_only_2s(mock_randint):
    assert BossBattle.roll(3, 4) == 6


@patch("random.randint", side_effect=lambda *args: 1)
def test_boss_battle_hit_roll_accounts_for_ability_modifier(mock_randint, test_boss):
    test_boss._base_stats.strength = 10
    test_boss._base_stats.dexterity = 12
    assert BossBattle.hit_roll(test_boss, Stats.Type.STRENGTH) == (3, False)  # roll of 1, 2 proficiency bonus, plus a 0 modifier
    assert BossBattle.hit_roll(test_boss, Stats.Type.DEXTERITY) == (4, False)  # roll of 1 plus a 1 modifier


@patch("random.randint", side_effect=lambda *args: 20)
def test_boss_battle_hit_roll_accounts_for_ability_modifier_with_crit(mock_randint, test_boss):
    test_boss._base_stats.strength = 10
    test_boss._base_stats.dexterity = 12

    assert BossBattle.hit_roll(test_boss, Stats.Type.STRENGTH) == (22, True)  # roll of 20 plus a 0  (+2 proficiency bonus)
    assert BossBattle.hit_roll(test_boss, Stats.Type.DEXTERITY) == (23, True)  # roll of 20 plus a 1 modifier (+2 proficiency bonus)


@patch("random.randint", side_effect=lambda *args: 19)
def test_boss_battle_hit_roll_of_20_not_necessarily_a_crit(mock_randint, test_boss):
    test_boss._base_stats.dexterity = 12
    assert BossBattle.hit_roll(test_boss, Stats.Type.DEXTERITY) == (22, False)  # roll of 19 plus a 1 modifier, NOT a crit (+2 proficiency bonus)

@patch("random.randint", side_effect=[6, 5, 4, 3])
def test_boss_battle_damage_roll_no_crit(mock_randint):
    effect_die = (1, 6)
    ability_modifier = 0
    proficiency_points = 0
    crit = False

    assert BossBattle.damage_roll(  # roll of 6
        effect_die=(1, 6),
        ability_modifier=0,
        crit=False
    ) == 6

    assert BossBattle.damage_roll(  # roll of 5
        effect_die=(1, 6),
        ability_modifier=0,
        crit=False
    ) == 5

    assert BossBattle.damage_roll(  # roll of 4 and 3
        effect_die=(2, 6),
        ability_modifier=0,
        crit=False
    ) == 7

@patch("random.randint", side_effect=lambda *args: 1)
def test_boss_battle_damage_roll_accounts_for_modifier(mock_randint):
    assert BossBattle.damage_roll((1, 6), 2, False) == 3, "roll of 1 plus modifier of 2"
    assert BossBattle.damage_roll((1, 6), 3, False) == 4, "roll of 1 plus modifier of 3"


@patch("random.randint", side_effect=[2, 4, 5, 3])
def test_boss_battle_damage_roll_accounts_for_crit(mock_randint):
    assert BossBattle.damage_roll((1, 6), 0, True) == 6, "roll of 2,4"
    assert BossBattle.damage_roll((1, 6), 0, True) == 8, "roll of 5,3"


def test_boss_battle_actual_damage_without_resistances_or_immunities(test_boss):

    assert BossBattle.calc_actual_damage(
        target=test_boss,
        damage=10,
        effect_type=EffectType.BLUDGEONING
    ) == 10
    
    assert BossBattle.calc_actual_damage(
        target=test_boss,
        damage=15,
        effect_type=EffectType.BLUDGEONING
    ) == 15


def test_boss_battle_actual_damage_with_resistances(test_boss):
    test_boss._resistances = [EffectType.BLUDGEONING, EffectType.SLASHING]

    assert BossBattle.calc_actual_damage(
        target=test_boss,
        damage=10,
        effect_type=EffectType.BLUDGEONING
    ) == 5
    
    assert BossBattle.calc_actual_damage(
        target=test_boss,
        damage=15,
        effect_type=EffectType.SLASHING
    ) == 7


def test_boss_battle_actual_damage_with_vunerabilities(test_boss):
    test_boss._vulnerabilities = [EffectType.BLUDGEONING, EffectType.SLASHING]
    
    assert BossBattle.calc_actual_damage(
        target=test_boss,
        damage=10,
        effect_type=EffectType.BLUDGEONING
    ) == 20
    
    assert BossBattle.calc_actual_damage(
        target=test_boss,
        damage=15,
        effect_type=EffectType.SLASHING
    ) == 30


def test_boss_battle_actual_damage_with_immunities(test_boss):
    test_boss._immunities = [EffectType.BLUDGEONING, EffectType.SLASHING]
    
    assert BossBattle.calc_actual_damage(
        target=test_boss,
        damage=10,
        effect_type=EffectType.BLUDGEONING
    ) == 0
    
    assert BossBattle.calc_actual_damage(
        target=test_boss,
        damage=15,
        effect_type=EffectType.SLASHING
    ) == 0
    

def test_boss_battle_calculates_ac(test_boss):
    test_boss._base_stats.dexterity = 10
    assert BossBattle.calc_ac(test_boss) == 10

    test_boss._base_stats.dexterity = 12
    assert BossBattle.calc_ac(test_boss) == 11


def test_can_create_new_battle():
    battle = BossBattle(players=[Player.roll_fighter("mrgallo"), Player.roll_fighter("dave")], bosses=[Squirrel()])
    assert len(battle._players) == 2
    assert len(battle._bosses) == 1


def test_players_and_bosses_correctly_indexed():
    player_one = Player.roll_fighter("mrgallo")
    player_two = Player.roll_fighter("dave")
    boss = Squirrel()
    battle = BossBattle(players=[player_one, player_two], bosses=[boss])
    assert battle._players["mrgallo"] is player_one
    assert battle._players["dave"] is player_two
    assert battle._bosses["squirrel"] is boss


def test_multiple_bosses_of_same_type_have_unique_names():
    b1 = Squirrel()
    b2 = Squirrel()
    b3 = Squirrel()
    battle = BossBattle(players=[], bosses=[b1, b2, b3])

    assert len(battle._bosses) == 3
    assert battle._bosses["squirrel1"] is b1
    assert battle._bosses["squirrel2"] is b2
    assert battle._bosses["squirrel3"] is b3

    assert type(battle._bosses["squirrel1"]) is Squirrel

    # ensure it removed the reference to the first squirrel
    assert battle._bosses.get("squirrel", False) is False

    # test that the object's name was also changed, not just
    # the reference in the dict
    assert b1._name == "squirrel1"


def test_should_continue_returns_false_with_one_character_per_team():
    p = Player.roll_fighter("player")
    b = Squirrel()
    battle = BossBattle(players=[p], bosses=[b])
    
    assert battle._should_continue() == True

    b._health = 0
    assert battle._should_continue() == False

    p._health = 0
    assert battle._should_continue() == False

    b._health = 100
    assert battle._should_continue() == False


def test_should_get_opportunity_tokens_for_all_bosses():
    b1 = Squirrel()
    b2 = Squirrel()
    b3 = Squirrel()
    p = Player.roll_fighter("test")
    battle = BossBattle(players=[p], bosses=[b1, b2, b3])

    # need to generate tokens first
    with pytest.raises(IndexError):
        battle.get_opportunity_tokens()

    battle.next_round()
    tokens = battle.get_opportunity_tokens()
    assert len(tokens) == 3

    boss_names = tuple(t.split(":")[0] for t in tokens)
    assert "squirrel1" in boss_names
    assert "squirrel2" in boss_names
    assert "squirrel3" in boss_names

    unique_tokens = set(t.split(":")[1] for t in tokens)
    assert len(unique_tokens) == 3, "should fail VERY rarely due to RNG"


@patch("random.randint", side_effect=[20, 2, 2])
def test_boss_battle_apply_action(mock_randint):
    player = Player.roll_fighter("test")
    boss = Squirrel()

    battle = BossBattle(players=[player], bosses=[boss])
    
    ability = AbilityRegistry.registry.get('punch')  # has die of (1, 2)
    # hit roll: 20

    result_string = battle._apply_action(player, ability, boss)
    assert Stats.calc_modifier(player.stats.get(ability.modifier_type)) == 3
    # damage roll: 2, 2 + 3 (strength modifier) = 7
    assert "test inflicts 7 (CRIT)" in result_string


@patch("random.randint", side_effect=[19])
def test_boss_battle_apply_action_misses_squirrel(mock_randint):
    player = Player.roll_fighter("test")
    boss = Squirrel()

    battle = BossBattle(players=[player], bosses=[boss])
    
    ability = AbilityRegistry.registry.get('punch')  # has die of (1, 2)
    # hit roll: 19, will be lower than squirrel's AC (DEX 100)

    assert BossBattle.calc_ac(boss) == 30

    result_string = battle._apply_action(player, ability, boss)
    assert "test's Punch MISSES squirrel" in result_string


def test_handle_action_throws_error_targeting_invalid_character_name():
    cmd = Command("player1@wrongname/punch")
    boss = Squirrel()
    player = Player.roll_fighter('player1')
    battle = BossBattle(bosses=[boss], players=[player])

    with pytest.raises(InvalidTargetError):
        battle.handle_action(cmd)


def test_get_ability():
    class TestAbility(Ability):
        identifier = "test-ability"
        name = "Test Ability"

    ability = BossBattle.get_ability('test-ability')
    assert ability.name == "Test Ability"

    with pytest.raises(InvalidAbilityError):
        ability = BossBattle.get_ability('some non-existant ability')


def test_minimum_damage_roll_is_1():
    assert BossBattle.damage_roll(effect_die=(1, 1),
                                  ability_modifier=-5,
                                  crit=False) == 1    
