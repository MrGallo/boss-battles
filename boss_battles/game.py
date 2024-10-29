from typing import Any, Optional, Type, Tuple
import random
import logging


from .command import Command
from .character import Character, Boss, Player, Stats
from .ability import AbilityRegistry, Ability, EffectType


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


class InvalidTargetError(Exception):
    pass

class InvalidAbilityError(Exception):
    pass

class TurnAlreadyTakenError(Exception):
    pass


class BossBattle:
    def __init__(self, players: list[Character], bosses: list[Character]):
        # TODO: need a check to ensure all players and bosses have a unique name, or give them one like boss1, boss2.
        
        # Dictionary indexed by player name
        self._players = {p._name: p for p in players}

        # self._all_player_names: set[str] = set(p._name for p in players)

        # Dictionary indexed by boss name
        # Need to assign unique names to bosses of same type
        boss_type_registry = {}
        # dict[Type, list[Character]]

        self._bosses = {}
        for b in bosses:
            try:
                boss_type_registry[type(b)].append(b)
            except KeyError:
                boss_type_registry[type(b)] = [b]
            else:
                b._name += str(len(boss_type_registry[type(b)]))

                # if more than one, need to go back and change the first one's name
                if len(boss_type_registry[type(b)]) == 2:
                    first_boss_of_type = boss_type_registry[type(b)][0]
                    prev_ident = first_boss_of_type._name
                    new_ident = first_boss_of_type._name + "1"
                    first_boss_of_type._name = new_ident
                    self._bosses[new_ident] = first_boss_of_type
                    del self._bosses[prev_ident]
            
            self._bosses[b._name] = b

        self._boss_tokens = {}
        for boss_name in self._bosses.keys():
            self._boss_tokens[boss_name] = []

        # self._all_character_names: set[str] = set(b._name for b in bosses) | self._all_player_names
        self._round_count = 0

        self._players_who_have_acted = set()
    
    @property
    def players(self) -> tuple[Character]:
        return tuple(self._players.values())

    def get_player(self, name: str) -> Character:
        return self._players[name]

    @property
    def bosses(self) -> tuple[Character]:
        return tuple(self._bosses.values())

    def get_boss(self, name: str) -> Character:
        return self._bosses[name]
    
    def next_round(self) -> bool:
        if not self._should_continue():
            return False
        
        self._round_count += 1
        self._generate_opportunity_tokens()
        
        return True

    def _generate_opportunity_tokens(self):
        for boss in self._bosses.values():
            if not boss.is_conscious():
                continue
            token = BossBattle.generate_opportunity_token(boss._opportunity_token_length)
            self._boss_tokens[boss._name].append(token)
    
    @staticmethod
    def generate_opportunity_token(self, length: int = 4):
        characters = "abcedfghijkmnpqrstuvwxyz0123456789"
        return ''.join(random.choice(characters) for _ in range(length)).lower()

    
    def get_round(self) -> int:
        return self._round_count
    
    def _should_continue(self) -> bool:
        if len(BossBattle._filter_active(self._bosses.values())) < 1:
            return False

        if len(BossBattle._filter_active(self._players.values())) < 1:
            return False
        
        return True
        
    @staticmethod
    def _filter_active(characters: list[Character]) -> list[Character]:
        return [c for c in characters if c.is_conscious()]

    def get_opportunity_tokens(self) -> list[str]:
        return [name + ":" + tokens[-1] for name, tokens in self._boss_tokens.items()]

    def get_opportunity_token(self, boss: Boss) -> str:
        return self._boss_tokens[boss._name][-1]
            
    def handle_action(self, m: Command) -> str:
        # TODO: should This be here or just raise error when we try to apply the action?
        # if not self._player_is_registered(m.user):
        #     # TODO: problem: fails silently, possible to collect all invalid and print at the end? 
        #     #       Or as it goes?
        #     continue

        # if not self._target_is_registered(m.target):
        #     continue

        caster = self._players[m.user]
        try:
            target = self._bosses[m.target]
        except KeyError:
            raise InvalidTargetError(f"Character named '{m.target}' does not exist.")
        
        ability: Ability = BossBattle.get_ability(m.action)
        
        # print(ability.identifier)
        if type(caster) is Player:
            if caster._name in self._players_who_have_acted:
                raise TurnAlreadyTakenError(f"'{caster._name}' has already acted this round.")
            try:
                solve_token = m.args[0]
            except IndexError:  # abilities like "Punch" don't require a solve token
                solve_token = ""

            if not ability.verify(self.get_opportunity_token(target), solve_token):
                return f"WRONG SOLVE TOKEN - {caster._name}/{ability.identifier} {solve_token}"
        
            self._players_who_have_acted.add(caster._name)

        return self._apply_action(caster, ability, target)

    @staticmethod
    def get_ability(ability_name: str) -> Ability:
        ChosenAbility = AbilityRegistry.registry.get(ability_name)
        if not ChosenAbility:
            raise InvalidAbilityError(f"INVALID ABILITY '{ability_name}'.")
        return ChosenAbility()

    def _player_is_registered(self, name: str) -> bool:
        return name in self._players.keys()


    def _target_is_registered(self, name: str) -> bool:
        return name in self._bosses.keys()


    def _apply_action(self, caster: Character, chosen_ability: Ability, target: Character) -> str:
        if type(chosen_ability) is AbilityRegistry.registry.get('cower'):
            # TODO: perhaps impart a disadvantage to the caster
            return f"{caster._name} COWERS before {target._name}"
        
        # TODO: implement ready state waiting for a trigger
        """
        await, ready, readyfor?
        player1@squirrel/readyfor cower punch
        player1@battlemage/await fireball shieldslam
        mrhealz@player1/readyfor healthbelow 5 heal  # can help against multiple attacks from bosses
        """

        # hit roll
        # print(chosen_ability)
        hit_roll, crit = BossBattle.hit_roll(caster, chosen_ability.modifier_type)
        # logging.info(f"{caster._name} rolled {hit_roll}.{' CRIT!' if crit else ''} ")

        if not BossBattle.is_hit(crit, hit_roll, target):
            return f"{caster._name}'s {chosen_ability.name} MISSES {target._name}."

        # damage roll   
        ability_modifier = Stats.calc_modifier(caster.stats.get(chosen_ability.modifier_type))
        damage_roll = BossBattle.damage_roll(
            effect_die=chosen_ability.effect_die,
            ability_modifier=ability_modifier,
            crit=crit
        )

        # check resistances/immunity
        ability_effect_type = chosen_ability.effect_type
        actual_damage = BossBattle.calc_actual_damage(target, damage_roll, ability_effect_type)
        

        # apply damage
        target.take_damage(actual_damage)
        effect_reaction_string = ""
        if target.is_immune_to(ability_effect_type):
            effect_reaction_string = " IMMUNE"
        elif target.is_resistant_to(ability_effect_type):
            effect_reaction_string = " RESISTANT"
        elif target.is_vulnerable_to(ability_effect_type):
            effect_reaction_string = " VULNERABLE"

        log_string = f"{caster._name} inflicts {actual_damage}{' (CRIT)' if crit else ''} on {target._name} ({chosen_ability.name}){effect_reaction_string}."

        if not target.is_conscious():
            log_string += f"\n{target._name} IS DEFETED!"
        
        return log_string

    @staticmethod
    def is_hit(is_crit: bool, hit_roll: int, target: Character) -> bool:
        target_ac = BossBattle.calc_ac(target)
        return is_crit is True or (hit_roll >= target_ac)

    @staticmethod
    def calc_actual_damage(target: Character, damage: int, effect_type: EffectType) -> int:
        if target.is_resistant_to(effect_type):
            logging.info(f"{target._name} is RESISTANT to {effect_type.value}! (damage halved)")
            return damage // 2
        elif target.is_vulnerable_to(effect_type):
            logging.info(f"{target._name} is VULNERABLE to {effect_type.value}! (damage doubled)")
            return damage * 2
        elif target.is_immune_to(effect_type):
            logging.info(f"{target._name} is IMMUNE to {effect_type.value}! (no damage done)")
            return 0
        return damage

    @staticmethod
    def damage_roll(effect_die: Tuple[int, int],
                    ability_modifier: int,
                    crit: bool) -> int:
        total = 0
        num_rolls, die_size = effect_die

        if crit:
            num_rolls *= 2

        for _ in range(num_rolls):
            total += random.randint(1, die_size)

        return max(total + ability_modifier, 1)

    @staticmethod
    def hit_roll(caster: Character, ability_modifier: Stats.Type) -> Tuple[int, bool]:
        log_string = ""
        caster_ability_points = caster.stats.get(ability_modifier)
        attack_modifier = Stats.calc_modifier(caster_ability_points)
        roll = BossBattle.roll(1, 20)
        crit = roll == 20
        proficiency_bonus = caster.get_proficiency_bonus()  # TODO: factor in if caster is ACTUALLY proficient
        return (roll + attack_modifier + proficiency_bonus, crit)

    @staticmethod
    def roll(num_rolls: int, die_size: int) -> int:
        "Rolls an XdY where X is num_rolls of a Y size dice"
        total = 0
        for _ in range(num_rolls):
            total += random.randint(1, die_size)
        return total

    @staticmethod
    def calc_ac(target: Character):
        # if has shield: +2 AC

        # if target has no armor
        return 10 + Stats.calc_modifier(target.stats.dexterity)
        # Light armor: AC 11 + Dex modifier
        # Medium armor: AC 13 + min(Dex modifier, 2)
        # Heavy armor: AC of item, no dex modifier
    
    def players_turn(self, actions: tuple[Player, str, Boss, str]):
        log_string = ""
        for caster, ability_ident, target, solve_token in actions:
            chosen_ability = AbilityRegistry.registry.get(ability_ident)()
            op_token = self.get_opportunity_token(target)
            # print(solve_token)
            # print(chosen_ability.verify(op_token, solve_token))
            if chosen_ability.verify(op_token, solve_token):
                log_string += self._apply_action(caster, chosen_ability, target) + "\n"
            else:
                log_string += f"{caster._name.upper()}: WRONG SOLVE TOKEN!"
        return log_string

    def bosses_turn(self):
        log_string = ""
        for boss in self._bosses.values():
            # caster, ability identifier, target
            if not boss.is_conscious():
                continue
            caster, ability_ident, target = boss.do_turn(self)
            ChosenAbility = AbilityRegistry.registry.get(ability_ident)
            log_string += self._apply_action(caster, ChosenAbility(), target) + "\n"
            
        return log_string
