import pygame




class Button:
    def __init__(self, screen, text, pos, width=160, height=56):
        self.screen = screen
        self.text = text
        self.pos = pos # center position
        self.width = width
        self.height = height
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = pos
        self.font = pygame.font.SysFont(None, 28)
        self.clicked = False


    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.clicked = True
        if event.type == pygame.MOUSEBUTTONUP:
            pass
        # for UI we often reset on up, but we keep click

    def draw(self, screen):
        # Draw button background
        pygame.draw.rect(screen, (100, 100, 100), self.rect)
        pygame.draw.rect(screen, (150, 150, 150), self.rect, 2)
        # Draw button text
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)