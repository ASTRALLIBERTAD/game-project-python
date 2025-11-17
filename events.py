import pygame


class EventHandler:
    def __init__(self, joystick):
        self.joystick = joystick

    def process(self, event, screen):
        if event.type == pygame.VIDEORESIZE or event.type == pygame.WINDOWSIZECHANGED:
            self.joystick.update_layout(screen)
            self.joystick.handle_up()

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.Vector2(event.pos)
            self.joystick.handle_down(pos)

        if event.type == pygame.MOUSEBUTTONUP:
            self.joystick.handle_up()
