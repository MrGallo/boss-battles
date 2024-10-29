from typing import Optional
from enum import Enum

from .character import Stats, Boss, Character


class AbilityRegistry:
    registry = {}

    @classmethod
    def register(cls, ability_identifier: str, ability_class):
        """
        Registers a new ability with the given name and class.
        """
        cls.registry[ability_identifier.lower()] = ability_class


class EffectType(Enum):
    SLASHING = 'slashing'
    """Represents cuts or gashes from sharp objects, such as swords or claws."""

    PIERCING = 'piercing'
    """Represents puncture wounds from sharp, thrusting weapons like spears or arrows."""

    BLUDGEONING = 'bludgeoning'
    """Represents blunt force trauma from heavy impacts, like hammers or fists."""

    FIRE = 'fire'
    """Represents damage from flames, explosions, or extreme heat."""

    COLD = 'cold'
    """Represents freezing effects or extreme cold, such as ice magic."""

    LIGHTNING = 'lightning'
    """Represents electrical energy or shocks, like from storms or magical bolts."""

    THUNDER = 'thunder'
    """Represents concussive sound waves or sonic booms."""

    ACID = 'acid'
    """Represents corrosive substances that dissolve or burn, such as acid pools or sprays."""

    POISON = 'poison'
    """Represents toxic substances that harm through ingestion, inhalation, or contact."""

    FORCE = 'force'
    """Represents pure magical energy, difficult to resist or block."""

    RADIANT = 'radiant'
    """Represents holy energy, often associated with divine magic or celestial beings."""

    NECROTIC = 'necrotic'
    """Represents life-draining energy or corruption, often used by undead or dark magic."""

    PSYCHIC = 'psychic'
    """Represents mental or emotional trauma, targeting the mind directly."""



class Ability:
    identifier: str
    name: str
    level: int = 1
    effect_type: EffectType
    effect_die: Optional[tuple[int, int]] = None  # XdY - num rolls, dice size
    modifier_type: Stats.Type     # abilities use a primary stat modifier


    def __init_subclass__(cls, **kwargs):
        """
        Automatically registers subclasses of Ability in the AbilityRegistry
        based on their defined 'name' attribute.
        """
        super().__init_subclass__(**kwargs)
        if hasattr(cls, 'identifier'):
            AbilityRegistry.register(cls.identifier, cls)

    def verify(self, op_token, solve_token):
        return solve_token == self.algorithm(op_token)

    def algorithm(self, op_token):
        pass


class Punch(Ability):
    identifier = "punch"
    name = "Punch"
    effect_type = EffectType.BLUDGEONING
    effect_die = (1, 2)
    modifier_type = Stats.Type.STRENGTH

    def algorithm(self, op_token):
        return ""

    def verify(self, op_token, solve_token):
        # punch is always usable
        return True


class Bite(Ability):
    identifier = "bite"
    name = "Bite"
    effect_type = EffectType.PIERCING
    effect_die = (1, 1)
    modifier_type = Stats.Type.STRENGTH

    def algorithm(self, op_token):
        return ""

    def verify(self, op_token, solve_token):
        # Bite is always castable
        return True


class Cower(Ability):
    identifier = "cower"
    name = "Cower"
    effect_die = (0, 0)
    modifier_type = Stats.Type.CONSTITUTION
    effect_type = EffectType.PSYCHIC

    def algorithm(self, op_token):
        return ""

    def verify(self, op_token, solve_token):
        # Cower is always castable
        return True


class Longsword(Ability):
    identifier = "lsword"
    name = "Longsword"
    effect_type = EffectType.SLASHING
    effect_die = (1, 8)
    modifier_type = Stats.Type.STRENGTH

    def algorithm(self, op_token):
        return op_token


class FireBolt(Ability):
    identifier = "fbolt"
    name = "Fire Bolt"
    effect_type = EffectType.FIRE
    effect_die = (1, 10)
    modifier_type = Stats.Type.INTELLIGENCE

    def algorithm(self, op_token):
        return op_token


class CureWounds(Ability):
    identifier = "cure"
    name = "Cure Wounds"
    effect_type = EffectType.RADIANT
    effect_die = (1, 8)
    modifier_type = Stats.Type.WISDOM

    def algorithm(self, op_token):
        return op_token

