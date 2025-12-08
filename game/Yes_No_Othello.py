"""Entry point for launching the Yes/No Othello pygame application."""

import pygame

from constants import (
    AI_MINIMAX,
    AI_NONE,
    AI_RANDOM,
    BOARD_SIZE,
    CELL_SIZE,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from core import OthelloGame
from ui import draw_board


def select_ai_mode():
    """Prompt the user for an AI mode selection and return the matching constant."""
    mode = input("Select mode (0: Human, 1: Random AI, 2: Minimax AI) → ")
    try:
        mode = int(mode)
    except ValueError:
        mode = 0
    if mode == 1:
        return AI_RANDOM
    if mode == 2:
        return AI_MINIMAX
    return AI_NONE


def select_gif_mode():
    """Prompt whether the animated GIF overlay should be enabled."""
    choice = input("Enable GIF popup mode? (True/False) → ").strip().lower()
    return choice in ("true", "t", "1", "yes", "y")


def create_font():
    """Load the preferred font, falling back to pygame's default if unavailable."""
    # I think this function is not necessary, but oh well
    try:
        return pygame.font.Font("/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf", 20)
    except Exception:
        return pygame.font.Font(None, 36)


def main():
    """Initialize pygame, start the main loop, and run until the game finishes."""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Yes/No Othello")
    font = create_font()
    ai_type = select_ai_mode()
    show_gifs = select_gif_mode() # Prompt for GIF mode
    game = OthelloGame(ai_type=ai_type, show_gifs=show_gifs, screen=screen, font=font)

    clock = pygame.time.Clock()
    while game.running:
        if not game.awaiting_api:
            game.ai_move()
        draw_board(screen, game, font)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
            elif (
                event.type == pygame.MOUSEBUTTONDOWN
                and game.current_side != game.ai_player
                and not game.awaiting_api
            ):
                x, y = pygame.mouse.get_pos()
                if x < BOARD_SIZE * CELL_SIZE:
                    row, col = y // CELL_SIZE, x // CELL_SIZE
                    game.place_piece(row, col)
        clock.tick(60)

    print(game.get_winner())
    pygame.quit() 


if __name__ == "__main__":
    # Entry point for the application
    main()
