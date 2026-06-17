import os
import unittest
from game_logic import LudoGame, Player, Piece, HOME_POS, WIN_POS
from database import save_game, load_game

class TestLudoLogic(unittest.TestCase):
    def setUp(self):
        # Ensure a fresh DB for each test if possible, 
        # but since we use room_id we can just use unique IDs
        self.room_id = "test-room-" + os.urandom(4).hex()
        self.game = LudoGame(self.room_id)
        self.game.add_player("Alice") # Red
        self.game.add_player("Bob")   # Green

    def test_add_players(self):
        self.assertEqual(len(self.game.players), 2)
        self.assertEqual(self.game.players[0].color, "red")
        self.assertEqual(self.game.players[1].color, "green")
        # Try adding 3rd and 4th
        self.assertTrue(self.game.add_player("Charlie"))
        self.assertTrue(self.game.add_player("Dave"))
        # 5th should fail
        self.assertFalse(self.game.add_player("Eve"))

    def test_start_game(self):
        self.assertFalse(self.game.game_started)
        self.game.start_game()
        self.assertTrue(self.game.game_started)

    def test_roll_dice(self):
        val = self.game.roll_dice()
        self.assertTrue(1 <= val <= 6)
        self.assertEqual(self.game.dice_value, val)

    def test_move_out_of_base(self):
        self.game.start_game()
        # Alice needs a 6
        self.game.dice_value = 3
        res = self.game.move_piece(0)
        self.assertIn("error", res)
        self.assertEqual(self.game.players[0].pieces[0].position, HOME_POS)
        
        # Now Alice rolls a 6
        self.game.dice_value = 6
        res = self.game.move_piece(0)
        self.assertNotIn("error", res)
        self.assertEqual(self.game.players[0].pieces[0].position, 0)
        # Should still be Alice's turn because she got a 6
        self.assertEqual(res["current_turn"], "red")

    def test_normal_movement(self):
        self.game.start_game()
        piece = self.game.players[0].pieces[0]
        piece.position = 10 # Already on board
        
        self.game.dice_value = 4
        res = self.game.move_piece(0)
        self.assertEqual(piece.position, 14)
        # Turn should switch to Bob (green)
        self.assertEqual(res["current_turn"], "green")

    def test_hit_opponent(self):
        self.game.start_game()
        alice_piece = self.game.players[0].pieces[0]
        bob_piece = self.game.players[1].pieces[0]
        
        # Red start is global 0. Alice piece at pos 5 is global 5.
        # Green start is global 13. Bob piece at pos 44 is global (44+13)%52 = 5.
        alice_piece.position = 5
        bob_piece.position = 44 # Bob's pos 44 is Alice's pos 5
        
        self.game.dice_value = 0 # Alice rolls (doesn't matter for this test setup)
        # We need to force Alice's turn and dice value
        self.game.current_turn_index = 0
        self.game.dice_value = 2
        alice_piece.position = 3 # Move Alice to 3, so a roll of 2 puts her at 5
        
        res = self.game.move_piece(0)
        self.assertEqual(alice_piece.position, 5)
        self.assertEqual(bob_piece.position, HOME_POS) # Bob was hit!
        # Alice should get another turn for hitting
        self.assertEqual(res["current_turn"], "red")

    def test_win_condition(self):
        self.game.start_game()
        
        # Finish first 3 pieces for Alice
        for i in range(1, 4):
            self.game.players[0].pieces[i].is_finished = True
            
        piece = self.game.players[0].pieces[0]
        piece.position = WIN_POS - 2
        
        self.game.dice_value = 2
        self.game.move_piece(0)
        self.assertTrue(piece.is_finished)
        
        # Winner should be Alice
        state = self.game.get_state()
        self.assertEqual(state["winner"], "Alice")

    def test_database_persistence(self):
        self.game.start_game()
        self.game.dice_value = 6
        self.game.move_piece(0) # Alice piece 0 at pos 0
        
        save_game(self.room_id, self.game)
        
        loaded_game = load_game(self.room_id)
        self.assertIsNotNone(loaded_game)
        self.assertEqual(loaded_game.players[0].pieces[0].position, 0)
        self.assertEqual(loaded_game.game_started, True)
        self.assertEqual(loaded_game.current_player.color, "red")

if __name__ == "__main__":
    unittest.main()
