import argparse
import curses


from .game_server import GameServer, SerialReader
from .character import Squirrel
from tests.helpers import FakeReader

def main(stdscr):
    curses.curs_set(0)
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Read from a serial port.")
    
    # Optional arguments with default values
    parser.add_argument(
        '--port', 
        type=str, 
        default='/dev/ttyACM0', 
        help='The serial port to connect to.'
    )
    parser.add_argument(
        '--baud-rate', 
        type=int, 
        default=115200, 
        help='The baud rate for the serial connection.'
    )
    parser.add_argument(
        '--debug', 
        type=bool, 
        default=False, 
        help='Enter into debug mode.'
    )

    # Parse arguments
    args = parser.parse_args()
    reader = SerialReader(port=args.port, baud_rate=args.baud_rate)
    if args.debug:
        reader = FakeReader()
    game = GameServer(bosses=[Squirrel()], reader=reader, stdscr=stdscr)
    game.run()

if __name__ == "__main__":
    curses.wrapper(main)
