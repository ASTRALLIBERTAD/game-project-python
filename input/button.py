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
        self.hovered = False
        
        # Color schemes
        self.normal_bg = (100, 100, 100)
        self.hover_bg = (130, 130, 130)
        self.active_bg = (80, 80, 80)
        self.border_color = (150, 150, 150)
        self.hover_border_color = (200, 200, 200)

    def update_hover(self):
        """Check if mouse is hovering over button"""
        mouse_pos = pygame.mouse.get_pos()
        self.hovered = self.rect.collidepoint(mouse_pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.clicked = True
        if event.type == pygame.MOUSEBUTTONUP:
            pass
        # for UI we often reset on up, but we keep click

    def draw(self, screen):
        # Update hover state
        self.update_hover()
        
        # Choose colors based on state
        if self.clicked and self.hovered:
            bg_color = self.active_bg
            border_color = self.hover_border_color
        elif self.hovered:
            bg_color = self.hover_bg
            border_color = self.hover_border_color
        else:
            bg_color = self.normal_bg
            border_color = self.border_color
        
        # Draw button background
        pygame.draw.rect(screen, bg_color, self.rect)
        
        # Draw border (thicker on hover)
        border_width = 3 if self.hovered else 2
        pygame.draw.rect(screen, border_color, self.rect, border_width)
        
        # Draw button text
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)