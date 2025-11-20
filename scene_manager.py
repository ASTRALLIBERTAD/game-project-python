import pygame
from scenes.menu_scene import MenuScene
from scenes.pause_scene import PauseScene


class DungeonSceneManager:
    """
    Scene manager for Pocket Dungeon Online
    Manages transitions between menu, role selection, and game scenes
    """
    
    def __init__(self, screen):
        self.screen = screen
        
        # Import scenes
        from scenes.dungeon_role_select import RoleSelectionScene
        from scenes.dungeon_multiplayer_scene import MultiplayerGameScene
        
        # Initialize scenes
        self.menu = MenuScene(self, screen)
        self.role_select = RoleSelectionScene(self, screen)
        self.pause = PauseScene(self, screen)
        
        # Game scene will be created when player selects role
        self.game = None
        
        # Start at menu
        self.active = self.menu
        self.previous_scene = None
    
    def change_scene(self, name):
        """Change to a different scene"""
        self.previous_scene = self.active
        
        if name == "menu":
            self.active = self.menu
        elif name == "role_select":
            self.active = self.role_select
        elif name == "game":
            if self.game is None:
                # If no game scene exists, go to role selection first
                self.active = self.role_select
            else:
                self.active = self.game
        elif name == "pause":
            self.active = self.pause
        else:
            print(f"Unknown scene: {name}")
    
    def handle_event(self, event):
        """Forward events to active scene"""
        if self.active:
            self.active.handle_event(event)
    
    def update(self):
        """Update active scene"""
        if self.active:
            self.active.update()
    
    def draw(self):
        """Draw active scene"""
        if self.active:
            self.active.draw()


# Update the menu scene to include "Play" button that goes to role selection
class UpdatedMenuScene:
    """Updated menu scene with Pocket Dungeon options"""
    
    def __init__(self, manager, screen):
        self.manager = manager
        self.screen = screen
        
        from input.button import Button
        
        w, h = screen.get_size()
        self.play_btn = Button(screen, "Play Dungeon", (w // 2, h // 2 - 80), 240, 70)
        self.settings_btn = Button(screen, "Settings", (w // 2, h // 2), 240, 70)
        self.quit_btn = Button(screen, "Quit", (w // 2, h // 2 + 80), 240, 70)
        
        self.title_font = pygame.font.SysFont(None, 64)
        self.subtitle_font = pygame.font.SysFont(None, 28)
    
    def handle_event(self, event):
        self.play_btn.handle_event(event)
        self.settings_btn.handle_event(event)
        self.quit_btn.handle_event(event)
        
        if self.play_btn.clicked:
            self.play_btn.clicked = False
            self.manager.change_scene("role_select")
        
        if self.settings_btn.clicked:
            self.settings_btn.clicked = False
            print("Settings not implemented yet")
        
        if self.quit_btn.clicked:
            self.quit_btn.clicked = False
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        
        # Handle resize
        if event.type == pygame.VIDEORESIZE or event.type == pygame.WINDOWSIZECHANGED:
            w, h = self.screen.get_size()
            self.play_btn.pos = (w // 2, h // 2 - 80)
            self.settings_btn.pos = (w // 2, h // 2)
            self.quit_btn.pos = (w // 2, h // 2 + 80)
    
    def update(self):
        pass
    
    def draw(self):
        self.screen.fill((15, 15, 20))
        
        # Title
        title = self.title_font.render("POCKET DUNGEON", True, (255, 200, 100))
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, 150))
        self.screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = self.subtitle_font.render("Online Co-op Adventure", True, (200, 200, 200))
        subtitle_rect = subtitle.get_rect(center=(self.screen.get_width() // 2, 200))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Draw buttons
        self.play_btn.draw(self.screen)
        self.settings_btn.draw(self.screen)
        self.quit_btn.draw(self.screen)
        
        # Instructions at bottom
        info_font = pygame.font.SysFont(None, 20)
        info_text = info_font.render("5-10 min sessions • 4 player co-op • Procedural dungeons", True, (150, 150, 150))
        info_rect = info_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() - 30))
        self.screen.blit(info_text, info_rect)