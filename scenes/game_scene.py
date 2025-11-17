import sys
import os
import pygame
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from input.joystick import Joystick
from input.aim_joystick import AimJoystick
from input.button import Button
from player import Player
from collision import Collider


class GameScene:
    def __init__(self, manager, screen):
        self.manager = manager
        self.screen = screen

        # UI / Input
        self.move_joy = Joystick(screen, anchor=(0.15, 0.75))
        self.aim_joy = AimJoystick(screen, anchor=(0.85, 0.75))
        self.jump_btn = Button(screen, "Jump", (screen.get_width() - 90, screen.get_height() - 140), 140, 60)
        self.interact_btn = Button(screen, "Use", (screen.get_width() - 90, screen.get_height() - 60), 140, 60)

        # Player & world
        self.player = Player(screen)
        self.collision = Collider(self.player.rect.x, self.player.rect.y, self.player.rect.width, self.player.rect.height)

    def handle_event(self, event):
        # propagate events to UI elements
        self.move_joy.handle_event(event)
        self.aim_joy.handle_event(event)
        self.jump_btn.handle_event(event)
        self.interact_btn.handle_event(event)

        # scene change (pause)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.manager.change_scene("pause")

        # resize -> update layouts
        if event.type == pygame.VIDEORESIZE or event.type == pygame.WINDOWSIZECHANGED:
            self.move_joy.update_layout(self.screen)
            self.aim_joy.update_layout(self.screen)
            # reposition buttons
            self.jump_btn.pos = (self.screen.get_width() - 90, self.screen.get_height() - 140)
            self.interact_btn.pos = (self.screen.get_width() - 90, self.screen.get_height() - 60)

    def update(self):
        # update joystick dragging positions using current mouse/touch pos
        self.move_joy.update_drag_state()
        self.aim_joy.update_drag_state()

        move_dir = self.move_joy.get_direction()
        aim_dir = self.aim_joy.get_direction()

        # jump pressed
        if self.jump_btn.clicked:
            # simple example: boost up on y (negative y is up)
            self.player.velocity.y -= 8
            self.jump_btn.clicked = False

        if self.interact_btn.clicked:
            # placeholder for interaction
            print("Interact pressed")
            self.interact_btn.clicked = False

        # apply movement with collision
        self.player.apply_input(move_dir, aim_dir)
        self.collision.resolve(self.player)
        self.player.update_physics()

    def draw(self):
        self.screen.fill((25, 25, 30))

        # draw player
        self.player.draw(self.screen)

        # draw UI on top
        self.move_joy.draw(self.screen)
        self.aim_joy.draw(self.screen)
        self.jump_btn.draw(self.screen)
        self.interact_btn.draw(self.screen)