from .game import BossBattle
from .character import Squirrel, Player
from .utils import print_health_list
from .message import Message, InvalidMessageError

bosses = [
    Squirrel()
]

players = [
    Player("mrgallo")
]

battle = BossBattle(players=players, bosses=bosses)

print("Running game")
ending = 'es' if len(battle._bosses) > 1 else ''
boss_names = ', '.join(map(str.upper, [b._name for b in battle._bosses.values()]))
print(f"Boss{ending}: {boss_names}")
print()
print("Players:\n" + "\n".join(map(str.upper, [p._name for p in battle._players.values()])))
while battle.next_round():
    print("=" * 10 + " ROUND " + str(battle.get_round()) + " " + "=" * 10)
    print_health_list("BOSSES", battle._bosses.values())
    print_health_list("PLAYERS", battle._players.values())
    print()

    opportunity_tokens = battle.get_opportunity_tokens()
    print(f"OPPORTUNITY TOKEN{'S' if len(opportunity_tokens) > 1 else ''}")
    for token in opportunity_tokens:
        print(token)
    print()

    # get actions from players
    valid_messages = []
    for player in players:
        action = input(f"{player._name}, enter action string: ")
        try:
            valid_messages.append(Message(action))
        except InvalidMessageError as e:
            print(f"Invalid message: '{action}'")
    
    for action in valid_messages:
        result = battle.handle_action(action)
        print(result)

    # boss action

