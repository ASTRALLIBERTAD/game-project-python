import pygame


class Player:
    def __init__(self, screen):
        w, h = screen.get_size()
        self.rect = pygame.Rect(0, 0, 60, 60)
        self.rect.center = (w // 2, h // 2)
        self.base_speed = 4

    def update(self, direction, screen):
        scale = screen.get_height() / 600
        speed = self.base_speed * scale

        self.rect.x += direction.x * speed
        self.rect.y += direction.y * speed

    def draw(self, screen):
        pygame.draw.rect(screen, (0, 200, 255), self.rect)
