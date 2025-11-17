import pygame
from joystick import Joystick
from player import Player
from events import EventHandler


class Game:
    def __init__(self):
        pygame.init()

        # Fullscreen auto-sized
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Virtual Joystick OOP")

        self.clock = pygame.time.Clock()
        self.running = True

        # Game objects
        self.joystick = Joystick(self.screen)
        self.player = Player(self.screen)
        self.events = EventHandler(self.joystick)

    def run(self):
        while self.running:

            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE) :
                    self.running = False

                self.events.process(event, self.screen)

            # Touch / drag support
            if self.joystick.dragging:
                pos = pygame.Vector2(pygame.mouse.get_pos())
                self.joystick.handle_drag(pos)

            direction = self.joystick.get_direction()
            self.player.update(direction, self.screen)

            # Draw phase
            self.screen.fill((20, 20, 20))
            self.player.draw(self.screen)
            self.joystick.draw(self.screen)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
