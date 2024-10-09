from typing import Any, Optional, Type
import random

from .message import Message
from .character import Character, Boss, Player
from .ability import AbilityRegistry, Ability


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
    
    @property
    def players(self) -> tuple[Character]:
        return self._players.values()
    
    def next_round(self) -> bool:
        if not self._should_continue():
            return False
        
        self._round_count += 1
        self._generate_opportunity_tokens()
        
        return True

    def _generate_opportunity_tokens(self):
        for boss in self._bosses.values():
            if not BossBattle.character_is_alive(boss):
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
        return [c for c in characters if BossBattle.character_is_alive(c)]

    @staticmethod
    def character_is_alive(character: Character) -> bool:
        return character._stats.health > 0

    def get_opportunity_tokens(self) -> list[str]:
        return [name + ":" + tokens[-1] for name, tokens in self._boss_tokens.items()]

    def get_opportunity_token(self, boss: Boss) -> str:
        return self._boss_tokens[boss._name][-1]
            
    def handle_action(self, m: Message) -> str:
        # TODO: should This be here or just raise error when we try to apply the action?
        # if not self._player_is_registered(m.user):
        #     # TODO: problem: fails silently, possible to collect all invalid and print at the end? 
        #     #       Or as it goes?
        #     continue

        # if not self._target_is_registered(m.target):
        #     continue

        player = self._players[m.user]
        target = self._bosses[m.target]
        ChosenAbility = AbilityRegistry.registry.get(m.action)
        if not ChosenAbility:
            return f"{player._name.upper()}: INVALID ACTION!"
        return self._apply_action(player, ChosenAbility, target)


    def _player_is_registered(self, name: str) -> bool:
        return name in self._players.keys()


    def _target_is_registered(self, name: str) -> bool:
        return name in self._bosses.keys()


    def _apply_action(self, caster: Character, chosen_ability: Ability, target: Character) -> str:
        # Stand in until issue #1 is resolved
        target._stats += chosen_ability.effect

        log_string = f"{caster._name} used {chosen_ability.name} on {target._name}"
        
        # could be that a target is defeated, so append that.
        return log_string
    
    def players_turn(self, actions: tuple[Player, str, Boss, str]):
        log_string = ""
        for caster, ability_ident, target, solve_token in actions:
            chosen_ability = AbilityRegistry.registry.get(ability_ident)()
            op_token = self.get_opportunity_token(target)
            print(solve_token)
            print(chosen_ability.verify(op_token, solve_token))
            if chosen_ability.verify(op_token, solve_token):
                log_string += self._apply_action(caster, chosen_ability, target) + "\n"
            else:
                log_string += f"{caster._name.upper()}: WRONG SOLVE TOKEN!"
        return log_string

    def bosses_turn(self):
        log_string = ""
        for boss in self._bosses.values():
            # caster, ability identifier, target
            caster, ability_ident, target = boss.do_turn(self)
            ChosenAbility = AbilityRegistry.registry.get(ability_ident)
            log_string += self._apply_action(caster, ChosenAbility, target) + "\n"
            
        return log_string
