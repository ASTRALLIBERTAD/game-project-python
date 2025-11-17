import pygame
from scene_manager import SceneManager


class Game:
    def __init__(self):
        pygame.init()
        # Fullscreen auto sized (change to RESIZABLE if you want)
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Pygame OOP Mobile Game")
        self.clock = pygame.time.Clock()
        self.running = True
        # Scene manager holds current scene
        self.scenes = SceneManager(self.screen)

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                # Forward event to scene manager
                self.scenes.handle_event(event)
            # Update current scene
            self.scenes.update()
            # Draw
            self.scenes.draw()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()