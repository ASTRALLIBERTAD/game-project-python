import sys
import os
import pygame
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from input.button import Button


class MenuScene:
    def __init__(self, manager, screen):
        self.manager = manager
        self.screen = screen
        w, h = screen.get_size()
        self.start_btn = Button(screen, "Start", (w // 2, h // 2 - 40), 200, 60)
        self.quit_btn = Button(screen, "Quit", (w // 2, h // 2 + 40), 200, 60)


    def handle_event(self, event):
        self.start_btn.handle_event(event)
        self.quit_btn.handle_event(event)


        if self.start_btn.clicked:
            self.start_btn.clicked = False
            self.manager.change_scene("game")


        if self.quit_btn.clicked:
            self.quit_btn.clicked = False
            pygame.event.post(pygame.event.Event(pygame.QUIT))


        # handle resize
        if event.type == pygame.VIDEORESIZE or event.type == pygame.WINDOWSIZECHANGED:
            w, h = self.screen.get_size()
            self.start_btn.pos = (w // 2, h // 2 - 40)
            self.quit_btn.pos = (w // 2, h // 2 + 40)


    def update(self):
        pass


    def draw(self):
        self.screen.fill((18, 18, 20))
        self.start_btn.draw(self.screen)
        self.quit_btn.draw(self.screen)