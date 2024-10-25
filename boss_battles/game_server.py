import serial
from typing import Protocol, Optional
import time
import curses
import itertools

from .character import Boss, Player
from .game import BossBattle, InvalidTargetError, TurnAlreadyTakenError
from .utils import print_health_list, print_health_bar
from .command import InvalidActionStringError, Command
from .display import draw_char, draw_text, calc_text_width


class Reader(Protocol):
    def read(self) -> list[str]:
        pass

    def open(self):
        pass

    def close(self):
        pass


class SerialReader:
    def __init__(self, port: str = "COM3", baud_rate: int = 115200):
        self.port = port
        self.baud_rate = baud_rate
        self.ser = None  # Serial connection initialized to None

    def open(self):
        """Open the serial connection."""
        self.ser = serial.Serial(self.port, self.baud_rate, timeout=1)

    def close(self):
        """Close the serial connection."""
        if self.ser and self.ser.is_open:
            self.ser.close()

    def read(self) -> list[str]:
        messages = []
        while self.ser.in_waiting > 0:
            message = self.ser.readline().decode('utf-8').strip()
            messages.append(message)
            # print(f"received: {message}")
        return messages


"""
Phases
- Registration
- Battle
    - Draw interface
    - Players turn
    - Boss turn
"""

class GameServer:
    def __init__(self, bosses: list[Boss], reader: Optional[Reader] = None, player_turn_time_seconds: int = 10, stdscr = None):
        self._bosses = bosses
        if reader is None:
            reader = SerialReader()
        self._reader = reader
        self._action_strings = []
        self._registered_usernames = set()
        self._battle = None
        self._current_phase = self._registration_phase
        self._battle_phases = [
            self._battle_round_init,
            self._battle_player_turn,
            self._battle_boss_turn
        ]
        self._battle_phase_counter = 0
        self._player_turn_time = player_turn_time_seconds
        self._player_timer_start = 0.0
        
        self._stdscr = stdscr
        self._battle_messages_players = []
        self._battle_messages_bosses = []
        self._error_messages = []
    
    def _get_next_battle_phase(self):
        next_phase = self._battle_phases[self._battle_phase_counter % len(self._battle_phases)]
        self._battle_phase_counter += 1
        return next_phase
    
    def _next_battle_phase(self):
        self._current_phase = self._get_next_battle_phase()
        if self._current_phase == self._battle_player_turn:
            self._player_timer_start = time.time()
        # print(self._current_phase.__name__)
    
    @property
    def battle(self) -> BossBattle:
        return self._battle
    
    def run(self):
        self._reader.open()
        try:
            while True:
                self._print_display()
                self._get_messages()
                self._current_phase()

        except KeyboardInterrupt:
            pass

        self._reader.close()

    def _get_messages(self):
        self._action_strings += self._reader.read()
    
    def _get_action_strings(self):
        "Returns action strings and removes them from the queue"
        strings = self._action_strings
        self._action_strings = []
        return strings

    def _wrap_up_registration_phase(self):
        players = [Player(n) for n in self._registered_usernames]
        self._battle = BossBattle(bosses=self._bosses, players=players)
        self._next_battle_phase()

    def _registration_phase(self):
        for message in self._get_action_strings():
            if message.lower() == "done":
                return self._wrap_up_registration_phase()
            
            try:
                user, command = message.split("/")
            except ValueError:
                continue

            if command.lower() != "register":
                continue

            user = user.lower()
            if user in self._registered_usernames:
                self._error_messages.append("Error: " + user + " already added.")
                continue

            self._registered_usernames.add(user)
            self._battle_messages_players.append("Welcome " + user.upper() + "!")

    def _battle_round_init(self):
        if not self._battle.next_round():
            "some sort of end phase"
            self._current_phase = None
            return

        self._next_battle_phase()
    
    def _print_display(self):
        scr = self._stdscr
        if scr is None:
            return
        
        height, width = scr.getmaxyx()
        
        scr.erase()
        
        # Test screen
        # draw_text(scr, 0, 9, "abcdefghij")
        # draw_text(scr, 0, 18, "klmnopqrst")
        # draw_text(scr, 0, 27, "uvwxyz")
        # draw_text(scr, 0, 36, "0123456789")

        curses.curs_set(0)
        # scr.timeout(100)
        if self._current_phase == self._registration_phase:
            # TITLE
            title_panel_height = 13
            title_panel = curses.newwin(title_panel_height, width, 0, 0)
            draw_text(title_panel, 0, 2, "BOSS BATTLES", align="center")

            text = "REGISTER NOW!"
            title_panel.addstr(11, (width - len(text)) // 2, text)

            text = "radio.send('username/register') on group 255"
            title_panel.addstr(12, (width - len(text)) // 2, text)
            title_panel.refresh()

            # REGISTERED USERS
            p1_y = title_panel_height + 1
            p1_width = 50
            mid_padding = 10
            p1_height = height - p1_y - mid_padding//2
            p1_x = (width // 2) - (p1_width) - mid_padding//2
            panel1 = curses.newwin(p1_height, p1_width, p1_y, p1_x)
            panel1.border()  # Add a border around the window
            panel1.addstr(0, 2, "Welcome Players!")

            left = []
            right = []

            for i, user in enumerate(self._registered_usernames):
                if i % 2 == 0:
                    left.append(user)
                else:
                    right.append(user)

            for i, (user_a, user_b) in enumerate(itertools.zip_longest(left, right, fillvalue=None)):
                line = f"• {user_a:<20}"
                if user_b is not None:
                    line += f"• {user_b}"

                try:
                    panel1.addstr(i + 2, 2, line)
                except curses.error:
                    pass

            panel1.refresh()

            # LOGGING
            p2_y = title_panel_height + 1
            p2_width = 50
            mid_padding = 10
            p2_height = height - p2_y - mid_padding//2
            p2_x = (width // 2) + mid_padding//2
            panel2 = curses.newwin(p2_height, p2_width, 14, p2_x)
            panel2.border()  # Add a border around the window
            panel2.addstr(0, 2, "Log")


            for i, msg in enumerate(self._error_messages[-(p2_height-3):]):
                panel2.addstr(i + 2, 2, msg)

            panel2.refresh()
        elif self._current_phase == self._battle_player_turn:
            # DRAW BOSS HEALTH BARS
            bar_panel_height = 10
            bar_panel = curses.newwin(bar_panel_height, width, 0, 0)
            bar_width = width // 2
            for i, boss in enumerate(self._battle.bosses):
                percent = boss._stats.health / boss._base_stats.health
                remaining = int(bar_width * percent)
                gone = bar_width - remaining
                bar = f"{boss._name.upper():>10} {'█' * remaining}{'░' * gone} ({boss._stats.health} / {boss._base_stats.health})"
                bar_panel.addstr(i + 2, (width//2) - (len(bar)//2), bar)
            
            bar_panel.refresh()

            # TIMER
            timer_panel_height = 7
            timer_panel = curses.newwin(timer_panel_height, width, bar_panel_height, 0)
            current_time = time.time()
            elapsed_time = current_time - self._player_timer_start
            time_remaining = self._player_turn_time - elapsed_time
            draw_text(timer_panel, 0, 0, f"{round(time_remaining, 2):.2f}", align="center")
            timer_panel.refresh()

            # COMBAT LOG
            combat_log_panel_width = 50
            combat_log_panel_height = 20
            combat_log_panel = curses.newwin(combat_log_panel_height, combat_log_panel_width,
                                             bar_panel_height + timer_panel_height + 2, 
                                             (width // 2) - (combat_log_panel_width))
            combat_log_panel.border()
            combat_log_panel.addstr(0, 2, "Combat Log")
            for i, msg in enumerate(self._battle_messages_players[-combat_log_panel_height+2:]):
                combat_log_panel.addstr(i+1, 2, msg)

            combat_log_panel.refresh()

            # ERROR LOG
            error_log_panel_width = 50
            error_log_panel_height = 20
            error_log_panel = curses.newwin(error_log_panel_height, error_log_panel_width,
                                             bar_panel_height + timer_panel_height + 2, 
                                             (width // 2))
            error_log_panel.border()
            error_log_panel.addstr(0, 2, "Error Log")
            for i, msg in enumerate(self._error_messages[-error_log_panel_height+2:]):
                error_log_panel.addstr(i+1, 2, msg)

            error_log_panel.refresh()

        # time.sleep(0.5)
        # print op tokens
        # opportunity_tokens = self._battle.get_opportunity_tokens()
        # print(f"OPPORTUNITY TOKEN{'S' if len(opportunity_tokens) > 1 else ''}")
        # for token in opportunity_tokens:
        #     print(token)
        # print()

        # scr.refresh()
        # scr.getkey()
        
        # print("=" * 10 + " ROUND " + str(self._battle.get_round()) + " " + "=" * 10)
        # print_health_list("BOSSES", self._battle._bosses.values())
        # print_health_list("PLAYERS", self._battle._players.values())
        # print()

    def _battle_player_turn(self):
        # get actions from players
        valid_commands = []
        for action in self._get_action_strings():
            try:
                command = Command(action)
            except InvalidActionStringError as e:
                self._error_messages.append(f"Invalid message: '{action}'")

            if not any(c.user == command.user for c in valid_commands):
                valid_commands.append(command)
        
        for command in valid_commands:
            try:
                result = self._battle.handle_action(command)
            except InvalidTargetError as e:
                self._error_messages.append(str(e))
            except TurnAlreadyTakenError as e:
                self._error_messages.append(str(e))
            else:
                self._battle_messages_players.append(result)
        
        current_time = time.time()
        elapsed_time = current_time - self._player_timer_start
        time_remaining = self._player_turn_time - elapsed_time
        if time_remaining <= 0:
            self._battle._players_who_have_acted = set()
            self._next_battle_phase()
    
    def _battle_boss_turn(self):
        result = self._battle.bosses_turn()
        self._battle_messages_bosses.append(result)
        self._next_battle_phase()