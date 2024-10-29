import pytest
from unittest.mock import patch

from boss_battles.game_server import GameServer
from boss_battles.character import Squirrel, Stats
from boss_battles.ability import Ability, EffectType, AbilityRegistry

from helpers import FakeReader, FakeGameServer


class TestAttack(Ability):
    identifier = "testattack"
    name = "Test Attack"
    effect_type = EffectType.BLUDGEONING
    effect_die = (1, 1)
    modifier_type = Stats.Type.STRENGTH

    def algorithm(self, op_token):
        return "solvetoken"


def test_game_server_can_store_incoming_messages():
    reader = FakeReader()
    reader.add_messages([
        "one",
        "two"
    ])
    game_server = FakeGameServer(bosses=[], reader=reader)
    # in lieu of game_server.run()
    game_server._get_messages()
    assert len(game_server._action_strings) == 2
    
    game_server._current_phase()
    assert len(game_server._action_strings) == 0, "Handled messages get cleared from the messages queue"


def test_game_server_registers_users():
    reader = FakeReader()
    reader.add_messages([
        "user1/register",
        "user2/register"
    ])
    game_server = FakeGameServer(bosses=[], reader=reader)
    game_server.run()
    assert len(game_server._action_strings) == 0, "Handled messages get cleared"
    assert len(game_server._registered_usernames) == 2


def test_game_server_registers_users_who_register_properly():
    reader = FakeReader()
    reader.add_messages([
        "user1/register",
        "user2/bad_command",
        "bad_command",
        "user2/register"
    ])
    game_server = FakeGameServer(bosses=[], reader=reader)
    game_server.run()
    assert len(game_server._registered_usernames) == 2


def test_game_server_registers_only_unique_names_case_insensitive():
    reader = FakeReader()
    reader.add_messages([
        "user1/register",
        "user2/register",
        "usER2/register",
        "USER2/register",
    ])
    game_server = FakeGameServer(bosses=[], reader=reader)
    game_server.run()
    assert len(game_server._registered_usernames) == 2


def test_game_server_changes_to_battle_phase_when_registering_done():
    reader = FakeReader()
    reader.add_messages([
        "user1/register",
        "done"
    ])
    game_server = FakeGameServer(bosses=[], reader=reader)
    game_server.run()
    assert game_server._current_phase == game_server._battle_round_init


def test_gather_valid_commands():
    game_server = GameServer(bosses=[], reader=FakeReader())
    game_server._action_strings = [
        "player@blah/something valid"
    ]
    valid_commands = game_server._gather_valid_commands()
    assert len(valid_commands) == 1
    assert len(game_server._action_strings) == 0
    

def test_gather_valid_commands_rejects_invalid_with_error_message():
    game_server = GameServer(bosses=[], reader=FakeReader())
    game_server._action_strings = [
        "player@blah/something valid",
        "dee#doo invalid"
    ]
    valid_commands = game_server._gather_valid_commands()
    assert len(valid_commands) == 1
    assert len(game_server._error_messages) == 1


# Player: hit roll 20 (Crit) so double roll for damage
# boss: 
@patch("random.randint", side_effect=[20, 1, 1])
def test_game_server_starts_game_with_squirrel_boss(mock_randint):
    reader = FakeReader()
    reader.add_messages([
        "player1/register",
        "done"
    ])
    squirrel = Squirrel()
    game = FakeGameServer(bosses=[squirrel], reader=reader)
    game.run()
    assert game._current_phase == game._battle_round_init
    assert len(game.battle.bosses) == 1

    assert game.battle._round_count == 0
    assert game.battle.bosses[0] == squirrel

    game.run()
    assert game.battle._round_count == 1
    assert game._current_phase == game._battle_player_turn

    reader.add_messages([
        "player1@squirrel/testattack solvetoken"
    ])

    starting_health = squirrel.get_health()
    game.run()
    # roll 1, 1, + 3 (str modifier) = 5 damage
    # vs a 2 health squirrel
    assert squirrel._health == 0

# hit roll 20 (Crit) so double roll for damage
# boss too
@patch("random.randint", side_effect=[20, 1, 1, 20, 1, 1])
def test_game_server_rejects_multiple_commands_from_single_player(mock_randint):
    reader = FakeReader()
    reader.add_messages([
        "player1/register",
        "done",
    ])
    squirrel = Squirrel()
    squirrel._max_health = 100
    squirrel._health = 100
    squirrel.stats.dexterity= 10
    game = FakeGameServer(bosses=[squirrel], reader=reader)
    game.run()  # registration phase

    reader.add_messages([
        "player1@squirrel/testattack solvetoken",
        "player1@squirrel/testattack solvetoken",
    ])
    game.run()  # run battle init
    game.run()  # run battle player turn
    # assert squirrel._stats.dexterity == 10
    # 1, 1, +3 const modifier = 5 damage
    assert squirrel.get_health() == 95


def test_game_should_clear_actions_after_processed():
    squirrel = Squirrel()
    reader = FakeReader()
    reader.add_messages([
        "player1/register",
        "done"
    ])
    game = FakeGameServer(bosses=[squirrel], reader=reader)
    game.run()  # reg phase
    assert len(game._action_strings) == 0

    game.run()  # battle init
    reader.add_message("player1@squirrel/punch")
    assert len(game._reader.messages) == 1

    game.run()  # player turn phase
    assert len(game._action_strings) == 0
    assert len(game._reader.messages) == 0


