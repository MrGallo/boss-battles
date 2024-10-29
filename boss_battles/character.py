from typing import Protocol, TYPE_CHECKING
from enum import Enum
from dataclasses import dataclass
import random


if TYPE_CHECKING:
    from .game import BossBattle
    from .ability import Ability, EffectType
    from .character import Character

# caster, ability identifier, target
Action = tuple['Character', str, 'Character']


@dataclass
class Stats:
    class Type(Enum):
        STRENGTH = 'strength'
        DEXTERITY = 'dexterity'
        CONSTITUTION = 'constitution'
        WISDOM = 'wisdom'
        INTELLIGENCE = 'intelligence'
        CHARISMA = 'charisma'
    
    strength: int = 0   
    dexterity: int = 0
    constitution: int = 0
    wisdom: int = 0
    intelligence: int = 0
    charisma: int = 0

    # Fighter (Tank)
    # Strength: 15
    # Constitution: 14
    # Dexterity: 13
    # Wisdom: 12
    # Charisma: 10
    # Intelligence: 8
    # hp based on class hit die + const modifier (stat - 10) // 2
    # fighter d10
    # wizard d6
    # cleric d8

    @staticmethod
    def calc_modifier(stat: int) -> int:
        return (stat - 10) // 2

    def __add__(self, other):
        return Stats(
            strength=self.strength + other.strength,
            dexterity=self.dexterity + other.dexterity,
            constitution=self.constitution + other.constitution,
            wisdom=self.wisdom + other.wisdom,
            intelligence=self.intelligence + other.intelligence,
            charisma=self.charisma + other.charisma
        )

    def copy(self) -> 'Stats':
        "Reuses the __add__ method"
        return self + Stats()

    def get(self, stat: 'Stats.Type') -> int:
        return getattr(self, stat.value)


class Skills(Enum):
    ATHLETICS = ("Athletics", Stats.Type.STRENGTH)
    ACROBATICS = ("Acrobatics", Stats.Type.DEXTERITY)
    SLEIGHT_OF_HAND = ("Sleight of Hand", Stats.Type.DEXTERITY)
    STEALTH = ("Stealth", Stats.Type.DEXTERITY)
    ARCANA = ("Arcana", Stats.Type.INTELLIGENCE)
    HISTORY = ("History", Stats.Type.INTELLIGENCE)
    INVESTIGATION = ("Investigation", Stats.Type.INTELLIGENCE)
    NATURE = ("Nature", Stats.Type.INTELLIGENCE)
    RELIGION = ("Religion", Stats.Type.INTELLIGENCE)
    ANIMAL_HANDLING = ("Animal Handling", Stats.Type.WISDOM)
    INSIGHT = ("Insight", Stats.Type.WISDOM)
    MEDICINE = ("Medicine", Stats.Type.WISDOM)
    PERCEPTION = ("Perception", Stats.Type.WISDOM)
    SURVIVAL = ("Survival", Stats.Type.WISDOM)
    DECEPTION = ("Deception", Stats.Type.CHARISMA)
    INTIMIDATION = ("Intimidation", Stats.Type.CHARISMA)
    PERFORMANCE = ("Performance", Stats.Type.CHARISMA)
    PERSUASION = ("Persuasion", Stats.Type.CHARISMA)


class CharacterClass(Enum):
    FIGHTER = 'fighter'
    WIZARD = 'wizard'
    CLERIC = 'cleric'

    @property
    def hit_die(self):
        return {
            CharacterClass.FIGHTER: (1, 10),
            CharacterClass.WIZARD: (1, 6),
            CharacterClass.CLERIC: (1, 8),
        }[self]


class Character:
    def __init__(self,
                 name: str,
                 hit_die: tuple[int, int],
                 base_stats: Stats,
                 level: int = 1,
                 resistances: list['EffectType'] = None,        # halves the damage
                 vulnerabilities: list['EffectType'] = None,    # doubles the damage
                 immunities: list['EffectType'] = None):        # negates all damage
        self._name = name
        self._level = level
        self._hit_die = hit_die
        self._base_stats = base_stats
        self._resistances = resistances if resistances else []
        self._vulnerabilities = vulnerabilities if vulnerabilities else []
        self._immunities = immunities if immunities else []
        self._calculate_hp()
    
    def _calculate_hp(self) -> None:
        raise NotImplementedError("Character subclasses must override this method.")

    def is_vulnerable_to(self, effect_type: 'EffectType') -> bool: 
        return effect_type in self._vulnerabilities

    def is_resistant_to(self, effect_type: 'EffectType') -> bool:
        return effect_type in self._resistances
    
    def is_immune_to(self, effect_type: 'EffectType') -> bool: 
        return effect_type in self._immunities
    
    def is_conscious(self) -> bool: 
        return self._health > 0
    
    @property
    def stats(self) -> Stats:
        return self.get_stats()

    def get_stats(self) -> Stats:
        # TODO: incorporate self._status_effects, eventually
        return self._base_stats.copy()

    def get_remaining_and_max_health(self) -> tuple[int, int]:
        return (self._health, self._max_health)
    
    def get_health(self) -> int:
        return self._health
    
    def get_max_health(self) -> int:
        return self._max_health

    def take_damage(self, amount: int) -> None:
        self._modify_health(-amount)
    
    def heal(self, amount: int) -> None:
        self._modify_health(amount)

    def _modify_health(self, amount: int) -> None:
        self._health = max(min(self._health + amount, self._max_health), 0)
    
    def get_proficiency_bonus(self) -> int:
        """Default behavior for proficiency bonus calculation."""
        raise NotImplementedError("This method should be implemented by subclasses.")



class Player(Character):
    def __init__(self,
                 name: str,
                 character_class: CharacterClass,
                 base_stats: Stats,
                 level: int = 1,
                 resistances: list['EffectType'] = None,        # halves the damage
                 vulnerabilities: list['EffectType'] = None,    # doubles the damage
                 immunities: list['EffectType'] = None):        # negates all damage
        self._character_class = character_class
        hit_die = self._character_class.hit_die
        super().__init__(name, hit_die, base_stats, level, resistances, vulnerabilities, immunities)

    def _calculate_hp(self) -> None:
        num_dice, die_type = self._hit_die
        self._max_health = die_type + Stats.calc_modifier(self._base_stats.constitution)
        for _ in range(1, self._level):
            self._max_health += (die_type // 2) + 1 + Stats.calc_modifier(self._base_stats.constitution)
        self._health = self._max_health

    @staticmethod
    def roll_fighter(name: str) -> 'Player':
        return Player(name, CharacterClass.FIGHTER, Stats(strength=16, dexterity=14, constitution=14, wisdom=12, intelligence=8, charisma=10))

    def get_proficiency_bonus(self) -> int:
        """Calculate proficiency bonus based on player level."""
        return (self._level - 1) // 4 + 2


class Boss(Character):
    _ability_set: tuple[str]
    _opportunity_token_length: int = 4

    def __init__(self,
                 name: str,
                 hit_die: tuple[int, int],
                 base_stats: Stats,
                 challenge_rating: int = 1,
                 resistances: list['EffectType'] = None,        # halves the damage
                 vulnerabilities: list['EffectType'] = None,    # doubles the damage
                 immunities: list['EffectType'] = None):        # negates all damage
        super().__init__(name, hit_die, base_stats, challenge_rating, resistances, vulnerabilities, immunities)
    
    def _calculate_hp(self) -> None:
        num_dice, hit_die = self._hit_die
        self._max_health = num_dice * ((hit_die // 2) + 1) + Stats.calc_modifier(self.stats.constitution)
        self._health = self._max_health

    def do_turn(self, battle: 'BossBattle') -> Action:
        """
        The idea is every boss requests to do an 
        action to a target(s) and returns that request in the form of an Action tuple
        """
        raise NotImplementedError("Bosses must override the do_turn method.")

    def get_proficiency_bonus(self) -> int:
        """Calculate proficiency bonus based on monster CR."""
        return (self._level - 1) // 4 + 2 if self._level > 0 else 2


class Squirrel(Boss):
    def __init__(self, hit_die: tuple[int, int] = (1, 4)):
        super().__init__("squirrel",
                         hit_die,
                         Stats(strength=2, dexterity=50, constitution=8, intelligence=2, wisdom=12, charisma=6),
                         challenge_rating=0)
        self._ability_set = ("bite", "cower")

    def do_turn(self, battle: 'BossBattle') -> Action:
        ability = random.choice(self._ability_set)
        random_player = random.choice(tuple(battle.players))
        return (self, ability, random_player)

class GiantWolfSpider(Boss):
    def __init__(self):
        super().__init__(name="giant wolf spider",
                         hit_die=(2, 8),
                         base_stats=Stats(12, 16, 13, 12, 3, 4),
                         challenge_rating=1)
        self._ability_set = ("wolfspiderbite", )

class PracticeDummy(Boss):
    def __init__(self):
        super().__init__("dummy", (495,1), Stats(constitution=20))

    def do_turn(self, battle: 'BossBattle') -> Action:
        # self-heal increasing health pool by 2x the damage deficit (if any)
        if self._health <= 0:
            self._max_health *= 2
        self._health = self._max_health
        return (self, 'pass', None)