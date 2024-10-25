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
        HEALTH = 'health'
        STRENGTH = 'strength'
        CONSTITUTION = 'constitution'
        DEXTERITY = 'dexterity'
        WISDOM = 'wisdom'
        CHARISMA = 'charisma'
        INTELLIGENCE = 'intelligence'
    
    health: int = 0
    strength: int = 0   
    constitution: int = 0
    dexterity: int = 0
    wisdom: int = 0
    charisma: int = 0
    intelligence: int = 0

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
            health=self.health + other.health,
            constitution=self.constitution + other.constitution,
            intelligence=self.intelligence + other.intelligence,
            dexterity=self.dexterity + other.dexterity,
            strength=self.strength + other.strength,
            wisdom=self.wisdom + other.wisdom,
            charisma=self.charisma + other.charisma
        )

    def copy(self) -> 'Stats':
        "Reuses the __add__ method"
        return self + Stats()

    def get(self, stat_name: str) -> int:
        return getattr(self, stat_name)


class CharacterClass(Enum):
    FIGHTER = 'fighter'
    WIZARD = 'wizard'
    CLERIC = 'cleric'

    CLASS_HIT_DIE = {
        FIGHTER: 10,
        WIZARD: 6,
        CLERIC: 8,
    }

    @staticmethod
    def hit_die(class_name: 'CharacterClass') -> int:
        return CharacterClass.CLASS_HIT_DIE[class_name]


class Character(Protocol):
    _name: str
    _base_stats: Stats
    _stats: Stats
    _class: CharacterClass
    _resistances: list['EffectType']      # halves the damage
    _vulnerabilities: list['EffectType']  # doubles the damage
    _immunities: list['EffectType']       # negates all damage
    
    def is_vulnerable_to(self, effect_type: 'EffectType') -> bool: ...
    def is_resistant_to(self, effect_type: 'EffectType') -> bool: ...
    def is_immune_to(self, effect_type: 'EffectType') -> bool: ...
    def is_alive(self) -> bool: ...


class Player:
    _name: str
    _base_stats: Stats
    _stats: Stats
    _resistances: list['EffectType']      # halves the damage
    _vulnerabilities: list['EffectType']  # doubles the damage
    _immunities: list['EffectType']       # negates all damage

    def __init__(self, name: str):
        self._name = name.lower()
        self._base_stats = Stats(50, 10, 10, 10, 10, 10)
        self._stats =      Stats(50, 10, 10, 10, 10, 10)
        self._resistances = []
        self._vulnerabilities = []
        self._immunities = []

    def is_alive(self):
        return self._stats.health > 0
    
    def get_starting_hp(self) -> int:
        return (
            CharacterClass.hit_die(self._class) 
            + self._stats.calc_modifier(self._stats.constitution)
        )
    
    def is_vulnerable_to(self, effect_type: 'EffectType') -> bool:
        return effect_type in self._vulnerabilities
    
    def is_resistant_to(self, effect_type: 'EffectType') -> bool:
        return effect_type in self._resistances
    
    def is_immune_to(self, effect_type: 'EffectType') -> bool:
        return effect_type in self._immunities


class Boss:
    _name: str
    _stats: Stats
    _base_stats: Stats
    _ability_set: tuple[str]
    _opportunity_token_length: int = 4
    _resistances: list['EffectType'] = []
    _vulnerabilities: list['EffectType'] = []  
    _immunities: list['EffectType'] = []

    def __init__(self):
        self._resistances = getattr(self, '_resistances', [])
        self._vulnerabilities = getattr(self, '_vulnerabilities', [])
        self._immunities = getattr(self, '_immunities', [])


    def is_alive(self):
        return self._stats.health > 0
    
    def do_turn(self, battle: 'BossBattle') -> Action:
        """
        The idea is every boss requests to do an 
        action to a target(s) and returns that request in the form of an Action tuple
        """
        raise NotImplementedError("Bosses must override the do_turn method.")
    
    def get_starting_hp(self) -> int:
        return (
            CharacterClass.hit_die(self._class) 
            + self._stats.calc_modifier(self._stats.constitution)
        )
    
    def is_vulnerable_to(self, effect_type: 'EffectType') -> bool:
        return effect_type in self._vulnerabilities
    
    def is_resistant_to(self, effect_type: 'EffectType') -> bool:
        return effect_type in self._resistances
    
    def is_immune_to(self, effect_type: 'EffectType') -> bool:
        return effect_type in self._immunities


class Squirrel(Boss):
    _name: str = "squirrel"
    _base_stats: Stats = Stats(health=5, strength=10, constitution=5, dexterity=100, wisdom=1, charisma=1, intelligence=1)
    _ability_set = ("bite", "cower")

    def __init__(self):
        super().__init__()
        self._stats = self._base_stats.copy()

    def do_turn(self, battle: 'BossBattle') -> Action:
        ability = random.choice(self._ability_set)
        random_player = random.choice(tuple(battle.players))
        return (self, ability, random_player)


class PracticeDummy(Boss):
    _name: str = "dummy"
    _stats: Stats = Stats(health=500, dexterity=0)
    _base_stats: Stats = Stats(health=500, dexterity=0)

    def do_turn(self, battle: 'BossBattle') -> Action:
        # self-heal increasing health pool by 2x the damage deficit (if any)
        if self._stats.health < 0:
            deficit = -self._stats.health
            increase = deficit // 2
            self._base_stats.health += increase
        self._stats.health = self._base_stats.health
        return (self, 'pass', None)