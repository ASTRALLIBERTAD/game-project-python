import pygame
from .joystick import Joystick


class AimJoystick(Joystick):
    def __init__(self, screen, anchor=(0.85, 0.75)):
        # call parent constructor
        super().__init__(screen, anchor)
        # override visual settings for aiming joystick
        self.color_base = (80, 40, 40)
        self.color_knob = (220, 80, 80)

    def draw(self, screen):
        # custom colored joystick for aiming
        pygame.draw.circle(screen, self.color_base, self.center, self.radius)
        pygame.draw.circle(screen, self.color_knob, self.stick_pos, self.knob_radius)