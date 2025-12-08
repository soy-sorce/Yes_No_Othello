"""Utility helpers for loading and rendering GIF overlays."""

import io
import pygame
import requests

# gif_pygame expects pygame-ce's FRect type; provide a noop placeholder for vanilla pygame.
if not hasattr(pygame, "FRect"):
    pygame.FRect = pygame.Rect

from gif_pygame import load as load_gif, transform as gif_transform

from constants import SCREEN_WIDTH, SCREEN_HEIGHT, BG_COLOR, TEXT_COLOR


def load_gif_from_url(url, enabled):
    """Download and prepare a GIF animation if overlays are enabled."""
    if not (enabled and url):
        return None
    try:
        response = requests.get(url, timeout=4)
        if not response.ok:
            return None
        buffer = io.BytesIO(response.content)
        gif = load_gif(buffer, loops=-1) # Loop indefinitely
        _fit_gif_to_screen(gif) # Resize to fit screen
        return gif
    except Exception:
        return None


def play_gif_popup(screen, font, gif, answer_text, turn_text):
    """Display the animated GIF overlay until the player dismisses it."""
    if not gif or not screen:
        return
    pygame.time.wait(200) # Brief pause before showing GIF
    gif.reset()
    title = font.render(f"API says: {answer_text.upper()}", True, TEXT_COLOR)
    turn_label = font.render(f"Turn: {turn_text}", True, TEXT_COLOR)
    instruction = font.render("Click anywhere to continue", True, TEXT_COLOR)
    width, height = gif.frames[0][0].get_size() if gif.frames else (100, 100)
    img_rect = pygame.Rect(0, 0, width, height)
    img_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    waiting = True
    clock = pygame.time.Clock()
    while waiting:
        for event in pygame.event.get():
            # Handle quit or click to dismiss
            if event.type == pygame.QUIT:
                waiting = False
                return False
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                waiting = False
        screen.fill(BG_COLOR)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 40))
        turn_rect = turn_label.get_rect(center=(SCREEN_WIDTH // 2, 80))
        instruction_rect = instruction.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
        screen.blit(title, title_rect)
        screen.blit(turn_label, turn_rect)
        gif.render(screen, img_rect.topleft)
        screen.blit(instruction, instruction_rect)
        pygame.display.flip()
        clock.tick(30)
    return True


def play_turn_banner(screen, font, player_text, duration=1.5):
    """Show an auto-advancing banner announcing which player's turn just began."""
    if not screen:
        pygame.time.wait(int(duration * 1000))
        return True
    clock = pygame.time.Clock()
    banner_message = font.render(f"{player_text} turn!!", True, TEXT_COLOR)
    sub_message = font.render("Get ready...", True, TEXT_COLOR)
    title_rect = banner_message.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
    sub_rect = sub_message.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
    target_ms = duration * 1000
    start = pygame.time.get_ticks() # Start time
    while pygame.time.get_ticks() - start < target_ms:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        screen.fill(BG_COLOR)
        screen.blit(banner_message, title_rect)
        screen.blit(sub_message, sub_rect)
        pygame.display.flip()
        clock.tick(60)
    return True


def _fit_gif_to_screen(gif):
    """Resize GIF frames so they fit comfortably inside the overlay."""
    if not gif.frames:
        # No frames to resize
        return
    width, height = gif.frames[0][0].get_size()
    max_width = SCREEN_WIDTH - 80
    max_height = SCREEN_HEIGHT - 140
    scale = min(max_width / width, max_height / height, 1)
    if scale < 1:
        new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
        gif_transform.smoothscale(gif, new_size)
