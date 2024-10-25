import pytest
from unittest.mock import patch


from boss_battles.game import BossBattle, InvalidTargetError
from boss_battles.character import Squirrel, Player, Stats, Boss
from boss_battles.ability import EffectType, AbilityRegistry
from boss_battles.command import Command


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
def test_boss_battle_hit_roll_accounts_for_ability_modifier(mock_randint):
    class TestChar:
        _stats = Stats(strength=10, dexterity=12)

    test_char = TestChar()

    assert BossBattle.hit_roll(test_char, Stats.Type.STRENGTH) == (1, False)  # roll of 1 plus a 0 modifier
    assert BossBattle.hit_roll(test_char, Stats.Type.DEXTERITY) == (2, False)  # roll of 1 plus a 1 modifier


@patch("random.randint", side_effect=lambda *args: 20)
def test_boss_battle_hit_roll_accounts_for_ability_modifier_with_crit(mock_randint):
    class TestChar:
        _stats = Stats(strength=10, dexterity=12)

    test_char = TestChar()

    assert BossBattle.hit_roll(test_char, Stats.Type.STRENGTH) == (20, True)  # roll of 20 plus a 0 modifier
    assert BossBattle.hit_roll(test_char, Stats.Type.DEXTERITY) == (21, True)  # roll of 20 plus a 1 modifier


@patch("random.randint", side_effect=lambda *args: 19)
def test_boss_battle_hit_roll_of_20_not_necessarily_a_crit(mock_randint):
    class TestChar:
        _stats = Stats(strength=10, dexterity=12)

    test_char = TestChar()

    assert BossBattle.hit_roll(test_char, Stats.Type.DEXTERITY) == (20, False)  # roll of 19 plus a 1 modifier, NOT a crit

@patch("random.randint", side_effect=[6, 5, 4, 3])
def test_boss_battle_damage_roll_no_crit(mock_randint):
    effect_die = (1, 6)
    ability_modifier = 0
    proficiency_points = 0
    crit = False

    assert BossBattle.damage_roll(  # roll of 6
        effect_die=(1, 6),
        ability_modifier=0,
        proficiency_bonus=0,
        crit=False
    ) == 6

    assert BossBattle.damage_roll(  # roll of 5
        effect_die=(1, 6),
        ability_modifier=0,
        proficiency_bonus=0,
        crit=False
    ) == 5

    assert BossBattle.damage_roll(  # roll of 4 and 3
        effect_die=(2, 6),
        ability_modifier=0,
        proficiency_bonus=0,
        crit=False
    ) == 7

@patch("random.randint", side_effect=lambda *args: 1)
def test_boss_battle_damage_roll_accounts_for_modifier(mock_randint):
    assert BossBattle.damage_roll((1, 6), 2, 0, False) == 3, "roll of 1 plus modifier of 2"
    assert BossBattle.damage_roll((1, 6), 3, 0, False) == 4, "roll of 1 plus modifier of 3"


@patch("random.randint", side_effect=lambda *args: 1)
def test_boss_battle_damage_roll_accounts_for_proficiency_bonus(mock_randint):
    assert BossBattle.damage_roll((1, 6), 0, 1, False) == 2, "roll of 1 plus prof of 1"
    assert BossBattle.damage_roll((1, 6), 0, 2, False) == 3, "roll of 1 plus prof of 2"


@patch("random.randint", side_effect=[2, 4, 5, 3])
def test_boss_battle_damage_roll_accounts_for_crit(mock_randint):
    assert BossBattle.damage_roll((1, 6), 0, 0, True) == 6, "roll of 2,4"
    assert BossBattle.damage_roll((1, 6), 0, 0, True) == 8, "roll of 5,3"


def test_boss_battle_actual_damage_without_resistances_or_immunities():
    class TestBoss(Boss):
        _resistances = []
        _vulnerabilities = []
        _immunities = []
    
    assert BossBattle.calc_actual_damage(
        target=TestBoss(),
        damage=10,
        effect_type=EffectType.BLUDGEONING
    ) == 10
    
    assert BossBattle.calc_actual_damage(
        target=TestBoss(),
        damage=15,
        effect_type=EffectType.BLUDGEONING
    ) == 15


def test_boss_battle_actual_damage_with_resistances():
    class TestBoss(Boss):
        _name = "Test Boss"
        _resistances = [EffectType.BLUDGEONING, EffectType.SLASHING]
        _vulnerabilities = []
        _immunities = []
    
    assert BossBattle.calc_actual_damage(
        target=TestBoss(),
        damage=10,
        effect_type=EffectType.BLUDGEONING
    ) == 5
    
    assert BossBattle.calc_actual_damage(
        target=TestBoss(),
        damage=15,
        effect_type=EffectType.SLASHING
    ) == 7


def test_boss_battle_actual_damage_with_vunerabilities():
    class TestBoss(Boss):
        _name = "Test Boss"
        _resistances = []
        _vulnerabilities = [EffectType.BLUDGEONING, EffectType.SLASHING]
        _immunities = []
    
    assert BossBattle.calc_actual_damage(
        target=TestBoss(),
        damage=10,
        effect_type=EffectType.BLUDGEONING
    ) == 20
    
    assert BossBattle.calc_actual_damage(
        target=TestBoss(),
        damage=15,
        effect_type=EffectType.SLASHING
    ) == 30


def test_boss_battle_actual_damage_with_immunities():
    class TestBoss(Boss):
        _name = "Test Boss"
        _resistances = []
        _vulnerabilities = []
        _immunities = [EffectType.BLUDGEONING, EffectType.SLASHING]
    
    assert BossBattle.calc_actual_damage(
        target=TestBoss(),
        damage=10,
        effect_type=EffectType.BLUDGEONING
    ) == 0
    
    assert BossBattle.calc_actual_damage(
        target=TestBoss(),
        damage=15,
        effect_type=EffectType.SLASHING
    ) == 0



def test_boss_battle_calculates_modifiers():
    assert BossBattle.calc_modifier(8) == -1
    assert BossBattle.calc_modifier(9) == -1
    assert BossBattle.calc_modifier(10) == 0
    assert BossBattle.calc_modifier(11) == 0
    assert BossBattle.calc_modifier(12) == 1
    assert BossBattle.calc_modifier(13) == 1
    assert BossBattle.calc_modifier(14) == 2
    

def test_boss_battle_calculates_ac():
    class TestCharacter:
        _stats = Stats(dexterity=10)
    
    test_char = TestCharacter()
    assert BossBattle.calc_ac(test_char) == 10

    test_char._stats.dexterity = 12
    assert BossBattle.calc_ac(test_char) == 11


def test_can_create_new_battle():
    battle = BossBattle(players=[Player("mrgallo"), Player("dave")], bosses=[Squirrel()])
    assert len(battle._players) == 2
    assert len(battle._bosses) == 1


def test_players_and_bosses_correctly_indexed():
    player_one = Player("mrgallo")
    player_two = Player("dave")
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
    p = Player("player")
    b = Squirrel()
    battle = BossBattle(players=[p], bosses=[b])
    
    assert battle._should_continue() == True

    b._stats.health = 0
    assert battle._should_continue() == False

    p._stats.health = 0
    assert battle._should_continue() == False

    b._stats.health = 100
    assert battle._should_continue() == False


def test_should_get_opportunity_tokens_for_all_bosses():
    b1 = Squirrel()
    b2 = Squirrel()
    b3 = Squirrel()
    p = Player("test")
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
    player = Player("test")
    boss = Squirrel()

    battle = BossBattle(players=[player], bosses=[boss])
    
    ability = AbilityRegistry.registry.get('punch')  # has die of (1, 2)
    # hit roll: 20
    # damage roll: 2, 2 = 4 (no effect resistances)

    result_string = battle._apply_action(player, ability, boss)
    assert "test inflicts 4 (CRIT)" in result_string


@patch("random.randint", side_effect=[19])
def test_boss_battle_apply_action_misses_squirrel(mock_randint):
    player = Player("test")
    boss = Squirrel()

    battle = BossBattle(players=[player], bosses=[boss])
    
    ability = AbilityRegistry.registry.get('punch')  # has die of (1, 2)
    # hit roll: 19, will be lower than squirrel's AC (DEX 100)

    result_string = battle._apply_action(player, ability, boss)
    assert "test's Punch MISSES squirrel" in result_string


def test_handle_action_throws_error_targeting_invalid_character_name():
    cmd = Command("player1@wrongname/punch")
    boss = Squirrel()
    player = Player('player1')
    battle = BossBattle(bosses=[boss], players=[player])

    with pytest.raises(InvalidTargetError):
        battle.handle_action(cmd)