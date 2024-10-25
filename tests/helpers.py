from boss_battles.game_server import GameServer


class FakeRadio:
    def __init__(self, messages: list[str] = None):
        if messages == None:
            messages = []
        self.messages = messages

    def receive(self):
        try:
            return self.messages.pop()
        except IndexError:
            return ""


class FakeReader:
    def __init__(self):
        self.messages = []
    
    def open(self):
        pass
    
    def close(self): 
        pass

    def add_message(self, msg: str):
        self.messages.append(msg)

    def add_messages(self, messages: list[str]):
        self.messages += messages

    def read(self) -> list[str]:
        tmp = self.messages
        self.messages = []
        return tmp
    

class FakeGameServer(GameServer):
    def run(self):
        self._get_messages()
        self._current_phase()