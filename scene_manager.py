import pygame
from scenes.menu_scene import MenuScene
from scenes.game_scene import GameScene
from scenes.pause_scene import PauseScene




class SceneManager:
    def __init__(self, screen):
        self.screen = screen
        # instantiate scenes (they can request a change_scene callback)
        self.menu = MenuScene(self, screen)
        self.game = GameScene(self, screen)
        self.pause = PauseScene(self, screen)
        self.active = self.menu

    def change_scene(self, name):
        if name == "menu":
            self.active = self.menu
        elif name == "game":
            self.active = self.game
        elif name == "pause":
            self.active = self.pause

    def handle_event(self, event):
        self.active.handle_event(event)

    def update(self):
        self.active.update()

    def draw(self):
        self.active.draw()