"""Core gameplay logic, API interaction, and AI helpers for Yes/No Othello."""

import random
import time

import numpy as np
import pygame
import requests

from constants import (
    AI_MINIMAX,
    AI_NONE,
    AI_RANDOM,
    API_URL,
    BOARD_SIZE,
    DIRECTIONS,
    EMPTY,
    NO_STONE,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    STONE_TO_TEXT,
    YES_STONE,
)
from gif_utils import load_gif_from_url, play_gif_popup, play_turn_banner
from ui import draw_board


class OthelloGame:
    """Manages the board, players, API state, and optional AI opponent."""

    def __init__(self, ai_type=AI_NONE, show_gifs=False, screen=None, font=None):
        """Initialize the board, players, and immediately fetch the first API stone."""
        self.board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)
        self.board[3, 3], self.board[4, 4] = NO_STONE, NO_STONE
        self.board[3, 4], self.board[4, 3] = YES_STONE, YES_STONE
        self.current_side = YES_STONE
        self.active_stone = YES_STONE
        self.last_answer = "-"
        self.status_message = "Game start"
        self.maybe_flash_ticks = 0
        self.awaiting_api = False
        self.running = True
        self.ai_type = ai_type
        self.ai_player = NO_STONE if ai_type != AI_NONE else None
        self.pass_count = 0
        self.ai_ready_time = None
        self.show_gifs = show_gifs
        self.screen = screen
        self.font = font or pygame.font.Font(None, 36)
        self.gif_animation = None
        self.needs_board_pause = False
        self._prepare_active_stone()
        self._schedule_ai_delay()

    def is_valid_move(self, row, col, stone=None):
        """Return True if placing `stone` at (row, col) would capture an opponent stone."""
        stone = stone if stone is not None else self.current_side
        if stone is None or self.board[row, col] != EMPTY:
            return False
        for dr, dc in DIRECTIONS:
            if self._can_flip(row, col, dr, dc, stone):
                return True
        return False

    def _can_flip(self, row, col, dr, dc, stone):
        """Check a single direction to see whether flips are possible."""
        opponent = self._opponent(stone)
        r, c = row + dr, col + dc
        flipped = False
        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.board[r, c] == opponent:
            r += dr
            c += dc
            flipped = True
        if flipped and 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.board[r, c] == stone:
            return True
        return False

    def place_piece(self, row, col):
        """Attempt to place the active stone and advance the turn if successful."""
        if self.awaiting_api or not self.is_valid_move(row, col, self.current_side):
            return False
        if not self._maybe_show_gif_popup():
            return False
        stone = self.active_stone
        owner = self.current_side
        self.board[row, col] = stone
        if stone == owner:
            for dr, dc in DIRECTIONS:
                self._flip_pieces(row, col, dr, dc, stone)
            self.status_message = f"API result: {STONE_TO_TEXT.get(stone, '-')}"
        else:
            self.status_message = f"Cannot flip due to API result: {STONE_TO_TEXT.get(stone, '-')}"
        if self.last_answer == "maybe":
            self._apply_maybe_event(row, col, stone)
        self.pass_count = 0
        self._advance_turn()
        return True

    def _flip_pieces(self, row, col, dr, dc, stone):
        """Flip opponent pieces in one direction after a successful capture."""
        opponent = self._opponent(stone)
        r, c = row + dr, col + dc
        to_flip = []
        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.board[r, c] == opponent:
            to_flip.append((r, c))
            r += dr
            c += dc
        if not (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.board[r, c] == stone):
            return
        for rr, cc in to_flip:
            self.board[rr, cc] = stone

    def has_valid_moves(self, stone=None):
        """Return True if the given player currently has any legal moves."""
        stone = stone if stone is not None else self.current_side
        if stone is None:
            return False
        return any(self.is_valid_move(r, c, stone) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE))

    def get_valid_moves(self):
        """Return a list of coordinates representing all legal moves for the current player."""
        return [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if self.is_valid_move(r, c, self.current_side)]

    def get_winner(self):
        """Return a string describing the outcome once the board is locked."""
        yes_score, no_score = self.get_scores()
        if yes_score > no_score:
            return "Yes player wins!"
        if no_score > yes_score:
            return "No player wins!"
        return "Draw!"

    def get_scores(self):
        """Return the total YES and NO stone counts as a tuple."""
        return np.sum(self.board == YES_STONE), np.sum(self.board == NO_STONE)

    def ai_move(self):
        """Have the AI choose a move if it is the AI's turn."""
        if self.ai_player != self.current_side or self.awaiting_api or not self.running:
            return
        if self.ai_ready_time is None:
            self._schedule_ai_delay()
        if self.ai_ready_time is not None and time.time() < self.ai_ready_time:
            return
        self.ai_ready_time = None
        moves = self.get_valid_moves()
        if not moves:
            self._handle_pass()
            return
        if self.ai_type == AI_RANDOM:
            move = random.choice(moves)
        elif self.ai_type == AI_MINIMAX:
            move = self._minimax_move(moves)
        else:
            return
        self.place_piece(*move)

    def _advance_turn(self):
        """Switch to the next player or finish the game if no moves remain."""
        if not np.any(self.board == EMPTY):
            self.running = False
            self.status_message = "Board is full"
            return
        self.current_side = self._opponent(self.current_side)
        self._prepare_active_stone()
        self._schedule_ai_delay()
        if not self.get_valid_moves():
            self._handle_pass()

    def _handle_pass(self):
        """Handle pass turns, ending the game if both players must pass."""
        self.pass_count += 1
        self.status_message = f"{self.player_name(self.current_side)} must pass"
        if self.pass_count >= 2 or not np.any(self.board == EMPTY):
            self.running = False
            return
        self.current_side = self._opponent(self.current_side)
        self._prepare_active_stone()
        self._schedule_ai_delay()
        if not self.get_valid_moves():
            self._handle_pass()

    def _maybe_show_gif_popup(self):
        """Display the yesno.wtf GIF if enabled, returning False if the window was closed."""
        if not (self.show_gifs and self.screen and self.gif_animation is not None and self.running):
            return True
        turn_label = self.player_name(self.current_side)
        result = play_gif_popup(self.screen, self.font, self.gif_animation, self.last_answer, turn_label)
        if result is False:
            self.running = False
            return False
        self.needs_board_pause = True
        return True

    def _schedule_ai_delay(self):
        """Randomize a 'thinking' delay before the AI is allowed to move."""
        if self.ai_player == self.current_side and self.running:
            delay = random.uniform(0.5, 3.0)
            self.ai_ready_time = time.time() + delay
            self.status_message = f"Opponent is thinking... (API: {self.last_answer.upper()})"
        else:
            self.ai_ready_time = None

    def _show_turn_banner(self):
        """Show the YES/NO turn banner for 1.5 seconds."""
        if not (self.screen and self.running):
            return
        if self.needs_board_pause:
            self._pause_on_board(3.0)
            self.needs_board_pause = False
        turn_text = self.player_name(self.current_side)
        result = play_turn_banner(self.screen, self.font, turn_text)
        if result is False:
            self.running = False

    def _pause_on_board(self, seconds):
        """Keep the standard board view on screen for a few seconds."""
        if not self.screen:
            pygame.time.wait(int(seconds * 1000))
            return
        clock = pygame.time.Clock()
        end_time = pygame.time.get_ticks() + int(seconds * 1000)
        while pygame.time.get_ticks() < end_time and self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
            draw_board(self.screen, self, self.font)
            pygame.display.flip()
            clock.tick(60)

    def _prepare_active_stone(self):
        """Call the API to determine which stone can be placed on the upcoming turn."""
        if not self.running:
            self.active_stone = None
            return
        self.awaiting_api = True
        self.status_message = f"Fetching API result for {self.player_name(self.current_side)}..."
        if pygame.display.get_init():
            pygame.display.flip()
        answer, image_url = self._fetch_api_answer()
        self.awaiting_api = False
        pygame.event.get(pygame.MOUSEBUTTONDOWN)
        self.last_answer = answer
        self.gif_animation = load_gif_from_url(image_url, self.show_gifs)
        if answer == "maybe":
            self.active_stone = self.current_side
            self.maybe_flash_ticks = 30
            self.status_message = "MAYBE! Flipping surrounding stones"
        elif answer == "yes":
            self.active_stone = YES_STONE
            self.maybe_flash_ticks = 0
            self.status_message = "API result: YES"
        elif answer == "no":
            self.active_stone = NO_STONE
            self.maybe_flash_ticks = 0
            self.status_message = "API result: NO"
        else:
            self.active_stone = random.choice([YES_STONE, NO_STONE])
            self.status_message = "API result unclear → random pick"
        self._show_turn_banner()

    def _apply_maybe_event(self, row, col, placed_stone):
        """Resolve the MAYBE result by flipping all adjacent opponent stones."""
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                    if self.board[r, c] == self._opponent(placed_stone):
                        self.board[r, c] = placed_stone

    def _fetch_api_answer(self):
        """Query yesno.wtf and return the answer text plus the GIF URL."""
        try:
            response = requests.get(API_URL, timeout=2)
            if response.ok:
                data = response.json()
                answer = data.get("answer", "yes").lower()
                image_url = data.get("image")
                return answer, image_url
        except Exception:
            pass
        return random.choice(["yes", "no"]), None

    def _opponent(self, stone):
        """Return the numeric ID of the opposite stone color."""
        return YES_STONE if stone == NO_STONE else NO_STONE

    def player_name(self, stone):
        """Return a user-friendly string for the provided stone constant."""
        return STONE_TO_TEXT.get(stone, "-")

    def _minimax_move(self, moves):
        """Evaluate moves with a simple greedy heuristic."""
        best_move = None
        best_score = -1
        for move in moves:
            score = self._simulate_move(move)
            if score > best_score:
                best_score = score
                best_move = move
        if best_move is None and moves:
            return random.choice(moves)
        return best_move

    def _simulate_move(self, move):
        """Simulate a move on a temporary board to estimate how many stones it gains."""
        intended = self.current_side
        placed = self.active_stone
        temp_board = np.copy(self.board)
        row, col = move
        temp_board[row, col] = placed
        if placed == intended:
            opponent = self._opponent(intended)
            for dr, dc in DIRECTIONS:
                r, c = row + dr, col + dc
                captured = []
                while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and temp_board[r, c] == opponent:
                    captured.append((r, c))
                    r += dr
                    c += dc
                if captured and 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and temp_board[r, c] == intended:
                    for rr, cc in captured:
                        temp_board[rr, cc] = intended
            if self.last_answer == "maybe":
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        r, c = row + dr, col + dc
                        if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                            if temp_board[r, c] == self._opponent(intended):
                                temp_board[r, c] = intended
        return np.sum(temp_board == intended)
