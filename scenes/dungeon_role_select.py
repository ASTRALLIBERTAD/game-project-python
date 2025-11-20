import pygame
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from input.button import Button


class RoleSelectionScene:
    """Scene for selecting player role before joining game"""
    
    def __init__(self, manager, screen):
        self.manager = manager
        self.screen = screen
        self.selected_role = None
        
        # Import role classes
        from dungeon_roles import PlayerRole, RoleStats
        self.PlayerRole = PlayerRole
        self.RoleStats = RoleStats
        
        # Create buttons for each role
        w, h = screen.get_size()
        self.role_buttons = {}
        
        roles = [
            self.PlayerRole.SCOUT,
            self.PlayerRole.TANK,
            self.PlayerRole.MAGE,
            self.PlayerRole.BUILDER
        ]
        
        button_y_start = h // 2 - 150
        for i, role in enumerate(roles):
            btn = Button(
                screen,
                role.value.upper(),
                (w // 2, button_y_start + i * 80),
                220,
                60
            )
            self.role_buttons[role] = btn
        
        # Start button (appears after role selected)
        self.start_btn = Button(screen, "START GAME", (w // 2, h - 100), 250, 70)
        self.back_btn = Button(screen, "Back", (w // 2, h - 30), 150, 40)
        
        # Network mode selection
        self.host_btn = Button(screen, "Host Game", (w // 4, h // 2 + 200), 200, 60)
        self.join_btn = Button(screen, "Join Game", (w // 2, h // 2 + 200), 200, 60)
        self.solo_btn = Button(screen, "Solo Play", (3 * w // 4, h // 2 + 200), 200, 60)
        
        self.network_mode = None  # 'host', 'join', or 'solo'
        
        # Font
        self.title_font = pygame.font.SysFont(None, 56)
        self.desc_font = pygame.font.SysFont(None, 24)
    
    def handle_event(self, event):
        # Handle role buttons
        for role, btn in self.role_buttons.items():
            btn.handle_event(event)
            if btn.clicked:
                self.selected_role = role
                btn.clicked = False
        
        # Network mode buttons
        self.host_btn.handle_event(event)
        self.join_btn.handle_event(event)
        self.solo_btn.handle_event(event)
        
        if self.host_btn.clicked:
            self.network_mode = 'host'
            self.host_btn.clicked = False
        if self.join_btn.clicked:
            self.network_mode = 'join'
            self.join_btn.clicked = False
        if self.solo_btn.clicked:
            self.network_mode = 'solo'
            self.solo_btn.clicked = False
        
        # Start button
        self.start_btn.handle_event(event)
        if self.start_btn.clicked and self.selected_role and self.network_mode:
            self.start_btn.clicked = False
            self._start_game()
        
        # Back button
        self.back_btn.handle_event(event)
        if self.back_btn.clicked:
            self.back_btn.clicked = False
            self.manager.change_scene("menu")
        
        # Window resize
        if event.type == pygame.VIDEORESIZE or event.type == pygame.WINDOWSIZECHANGED:
            self._update_layout()
    
    def _update_layout(self):
        """Update UI positions on window resize"""
        w, h = self.screen.get_size()
        
        button_y_start = h // 2 - 150
        for i, (role, btn) in enumerate(self.role_buttons.items()):
            btn.pos = (w // 2, button_y_start + i * 80)
        
        self.start_btn.pos = (w // 2, h - 100)
        self.back_btn.pos = (w // 2, h - 30)
        
        self.host_btn.pos = (w // 4, h // 2 + 200)
        self.join_btn.pos = (w // 2, h // 2 + 200)
        self.solo_btn.pos = (3 * w // 4, h // 2 + 200)
    
    def _start_game(self):
        """Start the game with selected role and network mode"""
        from dungeon_procgen import DungeonGenerator
        from dungeon_networking import NetworkServer, NetworkClient
        
        # Generate dungeon
        dungeon = DungeonGenerator(width=80, height=60, num_rooms=8)
        dungeon.generate()
        
        # Setup networking
        network_client = None
        
        if self.network_mode == 'host':
            # Start server
            server = NetworkServer(host='0.0.0.0', port=5555, max_players=4)
            server.start()
            
            # Connect as client
            network_client = NetworkClient('localhost', 5555)
            if network_client.connect(self.selected_role.value):
                print("Hosting game and connected as player")
            else:
                print("Failed to connect to own server")
                network_client = None
        
        elif self.network_mode == 'join':
            # Get IP from user (simplified - you'd want a proper input dialog)
            # For now, connect to localhost
            network_client = NetworkClient('localhost', 5555)
            if not network_client.connect(self.selected_role.value):
                print("Failed to connect to server")
                network_client = None
        
        # Change to game scene with dungeon and network client
        from scenes.dungeon_multiplayer_scene import MultiplayerGameScene
        
        game_scene = MultiplayerGameScene(
            self.manager,
            self.screen,
            network_client=network_client,
            dungeon_gen=dungeon,
            player_role=self.selected_role
        )
        
        # Replace the game scene in the manager
        self.manager.game = game_scene
        self.manager.change_scene("game")
    
    def update(self):
        pass
    
    def draw(self):
        self.screen.fill((20, 20, 25))
        
        # Title
        title = self.title_font.render("POCKET DUNGEON ONLINE", True, (255, 200, 100))
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, 50))
        self.screen.blit(title, title_rect)
        
        # Instructions
        if not self.selected_role:
            instruction = self.desc_font.render("Select your role:", True, (200, 200, 200))
        elif not self.network_mode:
            instruction = self.desc_font.render("Choose game mode:", True, (200, 200, 200))
        else:
            instruction = self.desc_font.render("Ready to start!", True, (100, 255, 100))
        
        inst_rect = instruction.get_rect(center=(self.screen.get_width() // 2, 120))
        self.screen.blit(instruction, inst_rect)
        
        # Draw role buttons with descriptions
        for role, btn in self.role_buttons.items():
            # Highlight selected role
            if role == self.selected_role:
                btn.normal_bg = (150, 150, 150)
            else:
                btn.normal_bg = (100, 100, 100)
            
            btn.draw(self.screen)
            
            # Draw role stats below button
            stats = self.RoleStats.get_stats(role)
            desc_text = self.desc_font.render(
                stats['description'],
                True,
                (180, 180, 180)
            )
            desc_rect = desc_text.get_rect(center=(btn.rect.centerx, btn.rect.bottom + 20))
            self.screen.blit(desc_text, desc_rect)
        
        # Draw network mode buttons
        if self.selected_role:
            # Highlight selected mode
            for btn, mode in [(self.host_btn, 'host'), (self.join_btn, 'join'), (self.solo_btn, 'solo')]:
                if self.network_mode == mode:
                    btn.normal_bg = (150, 150, 150)
                else:
                    btn.normal_bg = (100, 100, 100)
                btn.draw(self.screen)
        
        # Draw start and back buttons
        if self.selected_role and self.network_mode:
            self.start_btn.draw(self.screen)
        
        self.back_btn.draw(self.screen)


class ConnectionScene:
    """Simple scene for entering server IP"""
    
    def __init__(self, manager, screen):
        self.manager = manager
        self.screen = screen
        self.ip_input = ""
        self.port = "5555"
        self.active_input = "ip"  # 'ip' or 'port'
        
        w, h = screen.get_size()
        self.connect_btn = Button(screen, "Connect", (w // 2, h // 2 + 100), 200, 60)
        self.back_btn = Button(screen, "Back", (w // 2, h // 2 + 180), 200, 60)
        
        self.font = pygame.font.SysFont(None, 32)
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                if self.active_input == "ip":
                    self.ip_input = self.ip_input[:-1]
                else:
                    self.port = self.port[:-1]
            elif event.key == pygame.K_TAB:
                self.active_input = "port" if self.active_input == "ip" else "ip"
            elif event.key == pygame.K_RETURN:
                self._try_connect()
            else:
                if self.active_input == "ip" and len(self.ip_input) < 15:
                    self.ip_input += event.unicode
                elif self.active_input == "port" and len(self.port) < 5:
                    if event.unicode.isdigit():
                        self.port += event.unicode
        
        self.connect_btn.handle_event(event)
        if self.connect_btn.clicked:
            self.connect_btn.clicked = False
            self._try_connect()
        
        self.back_btn.handle_event(event)
        if self.back_btn.clicked:
            self.back_btn.clicked = False
            self.manager.change_scene("role_select")
    
    def _try_connect(self):
        """Attempt to connect to server"""
        # This would be handled in the role selection scene
        print(f"Connecting to {self.ip_input}:{self.port}")
    
    def update(self):
        pass
    
    def draw(self):
        self.screen.fill((20, 20, 25))
        
        w, h = self.screen.get_size()
        
        # Title
        title = self.font.render("Connect to Server", True, (255, 255, 255))
        title_rect = title.get_rect(center=(w // 2, h // 2 - 100))
        self.screen.blit(title, title_rect)
        
        # IP input
        ip_label = self.font.render("IP Address:", True, (200, 200, 200))
        self.screen.blit(ip_label, (w // 2 - 150, h // 2 - 40))
        
        ip_color = (255, 255, 255) if self.active_input == "ip" else (150, 150, 150)
        ip_rect = pygame.Rect(w // 2 - 150, h // 2 - 10, 300, 40)
        pygame.draw.rect(self.screen, ip_color, ip_rect, 2)
        ip_text = self.font.render(self.ip_input or "localhost", True, (255, 255, 255))
        self.screen.blit(ip_text, (w // 2 - 140, h // 2))
        
        # Port input
        port_label = self.font.render("Port:", True, (200, 200, 200))
        self.screen.blit(port_label, (w // 2 - 150, h // 2 + 40))
        
        port_color = (255, 255, 255) if self.active_input == "port" else (150, 150, 150)
        port_rect = pygame.Rect(w // 2 - 150, h // 2 + 70, 300, 40)
        pygame.draw.rect(self.screen, port_color, port_rect, 2)
        port_text = self.font.render(self.port, True, (255, 255, 255))
        self.screen.blit(port_text, (w // 2 - 140, h // 2 + 80))
        
        # Buttons
        self.connect_btn.draw(self.screen)
        self.back_btn.draw(self.screen)