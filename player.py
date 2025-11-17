import pygame


class Player:
    def __init__(self, screen):
        w, h = screen.get_size()
        self.rect = pygame.Rect(0, 0, 60, 60)
        self.rect.center = (w // 2, h // 2)
        self.base_speed = 4
        self.velocity = pygame.math.Vector2(0, 0)
        self.gravity = 0.3

    def apply_input(self, move_dir, aim_dir):
        # Apply movement input
        if move_dir.length() > 0:
            move_dir = move_dir.normalize()
        self.velocity.x = move_dir.x * self.base_speed
        self.velocity.y += self.gravity  # Apply gravity

    def update_physics(self):
        # Update position based on velocity
        self.rect.x += self.velocity.x
        self.rect.y += self.velocity.y

    def update(self, direction, screen):
        scale = screen.get_height() / 600
        speed = self.base_speed * scale

        self.rect.x += direction.x * speed
        self.rect.y += direction.y * speed

    def draw(self, screen):
        pygame.draw.rect(screen, (0, 200, 255), self.rect)
