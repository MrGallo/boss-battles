import pytest


from boss_battles.character import Boss, Stats, Squirrel, Player, CharacterClass
from boss_battles.game import BossBattle
from boss_battles.ability import EffectType


@pytest.fixture
def base_stats():
    return Stats(strength=14, dexterity=12, constitution=15, wisdom=10, intelligence=8, charisma=10)

@pytest.fixture
def player(base_stats):
    return Player(name="Hero", character_class=CharacterClass.FIGHTER, base_stats=base_stats)

@pytest.fixture
def boss(base_stats):
    return Boss(name="Villain", hit_die=(1, 10), base_stats=base_stats, challenge_rating=5)


def test_boss_do_turn_raises_not_implemented_error():
    class TestBoss(Boss):
        pass

    boss = TestBoss(name="TestBoss", hit_die=(1, 8), base_stats=Stats())
    
    with pytest.raises(NotImplementedError):
        boss.do_turn(BossBattle([], []))


def test_stats_add_together():
    a = Stats(
        strength = 2,
        constitution = 3,
        dexterity = 4,
        wisdom = 5,
        charisma = 6,
        intelligence = 7
    )
    b = Stats(
        strength = 30,
        constitution = 40,
        dexterity = 50,
        wisdom = 60,
        charisma = 70,
        intelligence = 80
    )

    a += b
    assert a.strength == 32
    assert a.constitution == 43
    assert a.dexterity == 54
    assert a.wisdom == 65
    assert a.charisma == 76
    assert a.intelligence == 87


def test_multiple_bosses_shouldnt_share_stats():
    s1 = Squirrel()
    s2 = Squirrel()
    battle = BossBattle(players=[], bosses=[s1, s2])

    s1.take_damage(1)
    assert s1.get_health() != s2.get_health()


def test_character_initialization(player):
    assert player.get_health() == player._max_health
    assert player._name == "Hero"
    assert player._level == 1
    assert player.is_conscious()

def test_character_take_damage(player):
    player.take_damage(5)
    assert player.get_health() == player._max_health - 5

def test_character_heal(player):
    player.take_damage(5)
    player.heal(3)
    assert player.get_health() == player._max_health - 2

def test_character_health_bounds(player):
    starting_health = player.get_health()
    player.take_damage(100)  # More than current health
    assert player.get_health() == 0  # Health should not go below 0
    player.heal(starting_health + 10)  # overhealing
    assert player.get_health() == starting_health  # Should be starting health, no overhealing

def test_player_proficiency_bonus(player):
    assert player.get_proficiency_bonus() == 2  # Level 1, proficiency bonus should be 2

def test_proficiency_bonus_level_1(player):
    player._level = 1
    assert player.get_proficiency_bonus() == 2, "At level 1, proficiency bonus should be 2"

def test_proficiency_bonus_level_4(player):
    player._level = 4
    assert player.get_proficiency_bonus() == 2, "At level 4, proficiency bonus should still be 2"

def test_proficiency_bonus_level_5(player):
    player._level = 5
    assert player.get_proficiency_bonus() == 3, "At level 5, proficiency bonus increases to 3"

def test_boss_initialization(boss):
    assert boss._name == "Villain"
    assert boss._level == 5
    assert boss.get_health() == boss.get_max_health()

def test_proficiency_bonus_level_1(boss):
    boss._level = 0
    assert boss.get_proficiency_bonus() == 2, "At level 0, proficiency bonus should be 2"

def test_proficiency_bonus_level_1(boss):
    boss._level = 1
    assert boss.get_proficiency_bonus() == 2, "At level 1, proficiency bonus should be 2"

def test_proficiency_bonus_level_4(boss):
    boss._level = 4
    assert boss.get_proficiency_bonus() == 2, "At level 4, proficiency bonus should still be 2"

def test_proficiency_bonus_level_5(boss):
    boss._level = 5
    assert boss.get_proficiency_bonus() == 3, "At level 5, proficiency bonus increases to 3"

def test_proficiency_bonus_level_8(boss):
    boss._level = 8
    assert boss.get_proficiency_bonus() == 3, "At level 8, proficiency bonus remains 3"

def test_boss_vulnerability(boss):
    effect_type = EffectType.FIRE
    boss._vulnerabilities.append(effect_type)
    assert boss.is_vulnerable_to(effect_type) is True
    assert boss.is_resistant_to(effect_type) is False
    assert boss.is_immune_to(effect_type) is False

def test_boss_resistance(boss):
    effect_type = EffectType.COLD
    boss._resistances.append(effect_type)
    assert boss.is_vulnerable_to(effect_type) is False
    assert boss.is_resistant_to(effect_type) is True
    assert boss.is_immune_to(effect_type) is False

def test_boss_immunity(boss):
    effect_type = EffectType.POISON
    boss._immunities.append(effect_type)
    assert boss.is_vulnerable_to(effect_type) is False
    assert boss.is_resistant_to(effect_type) is False
    assert boss.is_immune_to(effect_type) is True



# test_multiple_bosses_shouldnt_have_the_same_resistances():
    "They should to start, but suffer different effect vulnerabilities individually"
