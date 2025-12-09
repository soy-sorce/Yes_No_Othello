"""Rendering helpers for the Yes/No Othello board and info pane."""

import pygame

from constants import (
    BG_COLOR,
    BOARD_SIZE,
    CELL_SIZE,
    FLASH_COLOR,
    GREEN,
    INFO_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    STONE_TO_TEXT,
    TEXT_COLOR,
    YES_COLOR,
    YES_STONE,
    NO_COLOR,
    NO_STONE,
)


def draw_board(screen, game, font):
    """Render the grid, stones, and status panel."""
    screen.fill(GREEN)
    for i in range(1, BOARD_SIZE):
        # Draw grid lines
        pygame.draw.line(screen, YES_COLOR, (i * CELL_SIZE, 0), (i * CELL_SIZE, SCREEN_HEIGHT), 2)
        pygame.draw.line(screen, YES_COLOR, (0, i * CELL_SIZE), (SCREEN_HEIGHT, i * CELL_SIZE), 2)

    # Dedicated font keeps the YES/NO overlay sized for the stone diameter.
    piece_font = pygame.font.Font(None, max(18, CELL_SIZE // 2))
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            stone = game.board[r, c]
            if stone in (YES_STONE, NO_STONE):
                draw_piece(screen, (c, r), stone, piece_font)

    info_rect = pygame.Rect(BOARD_SIZE * CELL_SIZE, 0, INFO_WIDTH, SCREEN_HEIGHT)
    pygame.draw.rect(screen, BG_COLOR, info_rect) # Info panel background
    yes_score, no_score = game.get_scores()
    screen.blit(font.render(f"YES: {yes_score}", True, TEXT_COLOR), (BOARD_SIZE * CELL_SIZE + 15, 30))
    screen.blit(font.render(f"NO : {no_score}", True, TEXT_COLOR), (BOARD_SIZE * CELL_SIZE + 15, 70))
    screen.blit(font.render(f"TURN : {game.player_name(game.current_side)}", True, TEXT_COLOR), (BOARD_SIZE * CELL_SIZE + 15, 120))
    screen.blit(font.render(f"STONE: {STONE_TO_TEXT.get(game.active_stone, '-')}", True, TEXT_COLOR), (BOARD_SIZE * CELL_SIZE + 15, 160))
    screen.blit(font.render(f"API  : {game.last_answer.upper()}", True, TEXT_COLOR), (BOARD_SIZE * CELL_SIZE + 15, 200))

    for idx, line in enumerate(wrap_text(game.status_message, font, INFO_WIDTH - 30)):
        screen.blit(font.render(line, True, TEXT_COLOR), (BOARD_SIZE * CELL_SIZE + 15, 250 + idx * 28))
    if game.awaiting_api:
        # Indicate waiting for API
        screen.blit(font.render("Fetching result...", True, TEXT_COLOR), (BOARD_SIZE * CELL_SIZE + 15, 340))
    if game.maybe_flash_ticks > 0:
        # Flash overlay to indicate recent change
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(FLASH_COLOR)
        screen.blit(overlay, (0, 0))
        game.maybe_flash_ticks -= 1


def draw_piece(screen, cell_pos, stone, piece_font):
    """Draw a single stone with its YES/NO label centered on top."""
    c, r = cell_pos
    center = (c * CELL_SIZE + CELL_SIZE // 2, r * CELL_SIZE + CELL_SIZE // 2)
    radius = CELL_SIZE // 2 - 5
    fill_color = YES_COLOR if stone == YES_STONE else NO_COLOR
    text_color = NO_COLOR if stone == YES_STONE else YES_COLOR
    pygame.draw.circle(screen, fill_color, center, radius)
    text = STONE_TO_TEXT[stone]
    text_surface = piece_font.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=center)
    screen.blit(text_surface, text_rect)


def wrap_text(text, font, max_width):
    """Break a string into multiple lines that fit within the info panel."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]
