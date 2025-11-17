import pygame
from input.button import Button


class PauseScene:
    def __init__(self, manager, screen):
        self.manager = manager
        self.screen = screen
        w, h = screen.get_size()
        self.resume_btn = Button(screen, "Resume", (w // 2, h // 2 - 40), 200, 60)
        self.menu_btn = Button(screen, "Menu", (w // 2, h // 2 + 40), 200, 60)

    def handle_event(self, event):
        self.resume_btn.handle_event(event)
        self.menu_btn.handle_event(event)

        if self.resume_btn.clicked:
            self.resume_btn.clicked = False
            self.manager.change_scene("game")

        if self.menu_btn.clicked:
            self.menu_btn.clicked = False
            self.manager.change_scene("menu")

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.manager.change_scene("game")

        if event.type == pygame.VIDEORESIZE or event.type == pygame.WINDOWSIZECHANGED:
            w, h = self.screen.get_size()
            self.resume_btn.pos = (w // 2, h // 2 - 40)
            self.menu_btn.pos = (w // 2, h // 2 + 40)

    def update(self):
        pass

    def draw(self):
        # translucent overlay
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        self.resume_btn.draw(self.screen)
        self.menu_btn.draw(self.screen)