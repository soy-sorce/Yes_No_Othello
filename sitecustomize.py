"""Project specific sitecustomize to keep pygame compatible with gif_pygame."""

try:
    import pygame

    if not hasattr(pygame, "FRect"):
        pygame.FRect = pygame.Rect
except Exception:
    pass
