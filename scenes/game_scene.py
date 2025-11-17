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
        
        # Keyboard state tracking
        self.keys_pressed = {
            'w': False,
            'a': False,
            's': False,
            'd': False
        }

    def handle_event(self, event):
        # propagate events to UI elements
        self.move_joy.handle_event(event)
        self.aim_joy.handle_event(event)
        self.jump_btn.handle_event(event)
        self.interact_btn.handle_event(event)

        # WASD keyboard events
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                self.keys_pressed['w'] = True
            elif event.key == pygame.K_a:
                self.keys_pressed['a'] = True
            elif event.key == pygame.K_s:
                self.keys_pressed['s'] = True
            elif event.key == pygame.K_d:
                self.keys_pressed['d'] = True
            elif event.key == pygame.K_SPACE:
                # Jump on space press
                self.player.velocity.y -= 8
            elif event.key == pygame.K_e:
                # Interact on E press
                print("Interact pressed")
            elif event.key == pygame.K_ESCAPE:
                # Pause game
                self.manager.change_scene("pause")
        
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_w:
                self.keys_pressed['w'] = False
            elif event.key == pygame.K_a:
                self.keys_pressed['a'] = False
            elif event.key == pygame.K_s:
                self.keys_pressed['s'] = False
            elif event.key == pygame.K_d:
                self.keys_pressed['d'] = False

        # resize -> update layouts
        if event.type == pygame.VIDEORESIZE or event.type == pygame.WINDOWSIZECHANGED:
            self.move_joy.update_layout(self.screen)
            self.aim_joy.update_layout(self.screen)
            # reposition buttons
            self.jump_btn.pos = (self.screen.get_width() - 90, self.screen.get_height() - 140)
            self.interact_btn.pos = (self.screen.get_width() - 90, self.screen.get_height() - 60)

    def get_keyboard_direction(self):
        """Calculate direction vector from currently pressed WASD keys"""
        direction = pygame.Vector2(0, 0)
        
        if self.keys_pressed['w']:
            direction.y -= 1
        if self.keys_pressed['s']:
            direction.y += 1
        if self.keys_pressed['a']:
            direction.x -= 1
        if self.keys_pressed['d']:
            direction.x += 1
        
        # Normalize diagonal movement
        if direction.length() > 0:
            direction = direction.normalize()
        
        return direction

    def update(self):
        # update joystick dragging positions using current mouse/touch pos
        self.move_joy.update_drag_state()
        self.aim_joy.update_drag_state()

        # Get input from both joystick and keyboard
        joy_move_dir = self.move_joy.get_direction()
        keyboard_dir = self.get_keyboard_direction()
        
        # Combine joystick and keyboard input (keyboard takes priority if both used)
        if keyboard_dir.length() > 0:
            move_dir = keyboard_dir
        else:
            move_dir = joy_move_dir
        
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