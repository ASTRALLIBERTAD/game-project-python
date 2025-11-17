import pygame
import math


class Joystick:
    def __init__(self, screen):
        self.update_layout(screen)
        self.dragging = False
        self.stick_pos = self.center.copy()

    def update_layout(self, screen):
        w, h = screen.get_size()

        self.center = pygame.Vector2(w * 0.15, h * 0.75)
        self.radius = int(h * 0.10)
        self.knob_radius = int(h * 0.04)

    def clamp_to_circle(self, pos):
        offset = pos - self.center
        dist = offset.length()

        if dist > self.radius:
            offset.scale_to_length(self.radius)

        return self.center + offset

    def handle_down(self, pos):
        if (pos - self.center).length() <= self.radius:
            self.dragging = True

    def handle_drag(self, pos):
        if self.dragging:
            self.stick_pos = self.clamp_to_circle(pos)

    def handle_up(self):
        self.dragging = False
        self.stick_pos = self.center.copy()

    def get_direction(self):
        return (self.stick_pos - self.center) / self.radius

    def draw(self, screen):
        pygame.draw.circle(screen, (70, 70, 70), self.center, self.radius)
        pygame.draw.circle(screen, (180, 180, 180), self.stick_pos, self.knob_radius)
