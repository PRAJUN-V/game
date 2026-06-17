import random
from typing import List, Dict, Optional, Tuple

# Ludo Constants
COLORS = ["red", "green", "yellow", "blue"]
HOME_POS = -1
WIN_POS = 57  # 52 steps + 5 home run steps

class Piece:
    def __init__(self, color: str, id: int):
        self.color = color
        self.id = id
        self.position = HOME_POS  # -1 means at base
        self.is_home = False
        self.is_finished = False

    def reset(self):
        self.position = HOME_POS
        self.is_home = False
        self.is_finished = False

class Player:
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        self.pieces = [Piece(color, i) for i in range(4)]
        self.has_won = False

    def is_all_finished(self):
        return all(p.is_finished for p in self.pieces)

class LudoGame:
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.players: List[Player] = []
        self.current_turn_index = 0
        self.dice_value = 0
        self.game_started = False
        self.winner = None
        self.logs = []
        self.last_roll_six = False

    def add_player(self, name: str) -> bool:
        if len(self.players) >= 4 or self.game_started:
            return False
        color = COLORS[len(self.players)]
        self.players.append(Player(name, color))
        self.add_log(f"{name} joined as {color}")
        return True

    def start_game(self):
        if len(self.players) >= 2:
            self.game_started = True
            self.add_log("Game started!")
            return True
        return False

    def roll_dice(self) -> int:
        self.dice_value = random.randint(1, 6)
        self.last_roll_six = (self.dice_value == 6)
        self.add_log(f"{self.current_player.name} rolled a {self.dice_value}")
        return self.dice_value

    @property
    def current_player(self) -> Player:
        return self.players[self.current_turn_index]

    def get_piece(self, color: str, piece_id: int) -> Optional[Piece]:
        for player in self.players:
            if player.color == color:
                return player.pieces[piece_id]
        return None

    def move_piece(self, piece_id: int) -> Dict:
        player = self.current_player
        piece = player.pieces[piece_id]
        
        if self.dice_value == 0:
            return {"error": "Roll dice first"}

        # Logic for starting a piece
        if piece.position == HOME_POS:
            if self.dice_value == 6:
                piece.position = 0  # Starting point
                self.add_log(f"{player.name} moved piece {piece_id} out of base")
                return self.handle_post_move(True)
            else:
                return {"error": "Need a 6 to start"}

        # Logic for moving a piece
        new_pos = piece.position + self.dice_value
        if new_pos > WIN_POS:
            return {"error": "Cannot move beyond finish"}

        piece.position = new_pos
        if piece.position == WIN_POS:
            piece.is_finished = True
            self.add_log(f"{player.name}'s piece {piece_id} finished!")
            if player.is_all_finished():
                self.winner = player.name
                self.add_log(f"{player.name} WON THE GAME!")

        # Check for hitting other players
        hit = self.check_hits(piece)
        
        return self.handle_post_move(hit or self.last_roll_six or piece.is_finished)

    def check_hits(self, moved_piece: Piece) -> bool:
        # Simplified hit logic - only on main path (0-51)
        # Safe spots: 0, 8, 13, 21, 26, 34, 39, 47
        SAFE_SPOTS = [0, 8, 13, 21, 26, 34, 39, 47]
        
        if moved_piece.position >= 52 or moved_piece.position in SAFE_SPOTS:
            return False

        global_pos = self.get_global_position(moved_piece)
        hit_occurred = False

        for player in self.players:
            if player.color == moved_piece.color:
                continue
            for piece in player.pieces:
                if piece.position != HOME_POS and piece.position < 52:
                    other_global = self.get_global_position(piece)
                    if other_global == global_pos and piece.position not in SAFE_SPOTS:
                        piece.reset()
                        hit_occurred = True
                        self.add_log(f"{moved_piece.color} hit {player.color}!")
        
        return hit_occurred

    def get_global_position(self, piece: Piece) -> int:
        # Red starts at 0, Green at 13, Yellow at 26, Blue at 39
        offsets = {"red": 0, "green": 13, "yellow": 26, "blue": 39}
        if piece.position == HOME_POS or piece.position >= 52:
            return -1
        return (piece.position + offsets[piece.color]) % 52

    def handle_post_move(self, extra_turn: bool) -> Dict:
        self.dice_value = 0 # Reset dice
        if not extra_turn:
            self.current_turn_index = (self.current_turn_index + 1) % len(self.players)
        
        return self.get_state()

    def add_log(self, message: str):
        self.logs.append(message)
        if len(self.logs) > 10:
            self.logs.pop(0)

    def hydrate(self, state: Dict):
        self.players = []
        for p_data in state["players"]:
            player = Player(p_data["name"], p_data["color"])
            for i, pc_data in enumerate(p_data["pieces"]):
                player.pieces[i].position = pc_data["pos"]
                player.pieces[i].is_finished = pc_data["finished"]
            self.players.append(player)
        
        # Colors list to index turn
        colors = [p.color for p in self.players]
        if state["current_turn"] in colors:
            self.current_turn_index = colors.index(state["current_turn"])
        
        self.dice_value = state["dice_value"]
        self.game_started = state["game_started"]
        self.winner = state["winner"]
        self.logs = state["logs"]

    def get_state(self) -> Dict:
        return {
            "room_id": self.room_id,
            "players": [
                {
                    "name": p.name,
                    "color": p.color,
                    "pieces": [{"id": pc.id, "pos": pc.position, "finished": pc.is_finished} for pc in p.pieces]
                } for p in self.players
            ],
            "current_turn": self.current_player.color if self.players else None,
            "dice_value": self.dice_value,
            "game_started": self.game_started,
            "winner": self.winner,
            "logs": self.logs
        }
