from curses import wrapper

from boss_battles.game_server import GameServer
from boss_battles.character import Squirrel, Player


class FakeReader:
    messages: list[str]

    def open(self): ...
    def close(self): ...
    def read(self):
        return self.messages



def test_registration_phase(stdscr):
    reader = FakeReader()
    reader.messages = [f"user{n}/register" for n in range(30)]
    game = GameServer(bosses=[], reader=reader, stdscr=stdscr)
    game.run()

def test_player_turn_phase(stdscr):
    reader = FakeReader()
    reader.messages = [
        "player1@squirrel/punch"
    ]
    boss = Squirrel()
    boss._stats.health -= 1
    game = GameServer(bosses=[boss], reader=reader, stdscr=stdscr, player_turn_time_seconds=2)
    game._registered_usernames.add('player1')
    game._wrap_up_registration_phase()
    game.run()

def main(stdscr):
    # test_registration_phase(stdscr)
    test_player_turn_phase(stdscr)


if __name__ == "__main__":
    wrapper(main)