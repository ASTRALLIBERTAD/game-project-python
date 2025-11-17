import pygame


class Joystick:
    def __init__(self, screen, anchor=(0.15, 0.75)):
        self.screen = screen
        self.anchor = anchor # fraction of screen (x, y)
        self.dragging = False
        self.center = pygame.Vector2(0, 0)
        self.stick_pos = pygame.Vector2(0, 0)
        self.radius = 50
        self.knob_radius = 22
        self.update_layout(screen)


    def update_layout(self, screen):
        w, h = screen.get_size()
        self.center = pygame.Vector2(w * self.anchor[0], h * self.anchor[1])
        self.radius = int(h * 0.10)
        self.knob_radius = int(h * 0.04)
        if not hasattr(self, 'stick_pos'):
            self.stick_pos = self.center.copy()
        else:
            self.stick_pos = self.center.copy()


    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.Vector2(event.pos)
            if (pos - self.center).length() <= self.radius:
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
            self.stick_pos = self.center.copy()


    def update_drag_state(self):
        if self.dragging:
            pos = pygame.Vector2(pygame.mouse.get_pos())
            offset = pos - self.center
            if offset.length() > self.radius:
                offset.scale_to_length(self.radius)
                self.stick_pos = self.center + offset


    def get_direction(self):
        return (self.stick_pos - self.center) / self.radius


    def draw(self, screen):
        pygame.draw.circle(screen, (60, 60, 70), self.center, self.radius)
        pygame.draw.circle(screen, (160, 160, 160), self.stick_pos, self.knob_radius)