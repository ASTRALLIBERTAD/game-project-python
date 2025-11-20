import sys
import os
import pygame
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from input.joystick import Joystick
from input.aim_joystick import AimJoystick
from input.button import Button


class MultiplayerGameScene:
    """
    Main multiplayer dungeon game scene with:
    - Procedurally generated dungeons
    - Role-based players (Scout, Tank, Mage, Builder)
    - Builder block placement that syncs across network
    - Camera system
    - Simple enemy AI
    """
    
    def __init__(self, manager, screen, network_client=None, dungeon_gen=None, player_role=None):
        self.manager = manager
        self.screen = screen
        self.network_client = network_client
        
        # Import here to avoid circular imports
        from dungeon_procgen import DungeonGenerator, TileType
        from dungeon_roles import MultiplayerPlayer, PlayerRole, BuilderBlock
        from dungeon_networking import MessageType, create_player_update, create_block_place, create_block_remove
        
        self.DungeonGenerator = DungeonGenerator
        self.TileType = TileType
        self.MultiplayerPlayer = MultiplayerPlayer
        self.PlayerRole = PlayerRole
        self.BuilderBlock = BuilderBlock
        self.MessageType = MessageType
        self.create_player_update = create_player_update
        self.create_block_place = create_block_place
        self.create_block_remove = create_block_remove
        
        # Generate or load dungeon
        if dungeon_gen is None:
            self.dungeon = self.DungeonGenerator(width=80, height=60, num_rooms=8)
            self.grid, self.rooms = self.dungeon.generate()
        else:
            self.dungeon = dungeon_gen
            self.grid = dungeon_gen.grid
            self.rooms = dungeon_gen.rooms
        
        # Tile rendering
        self.tile_size = 32
        
        # Local player
        role = player_role or self.PlayerRole.SCOUT
        self.local_player = self.MultiplayerPlayer(screen, role, "local_player", is_local=True)
        
        # Spawn player at spawn point
        if self.dungeon.spawn_point:
            spawn_x, spawn_y = self.dungeon.spawn_point
            self.local_player.rect.center = (
                spawn_x * self.tile_size + self.tile_size // 2,
                spawn_y * self.tile_size + self.tile_size // 2
            )
        
        # Other players (from network)
        self.other_players = {}  # {player_id: MultiplayerPlayer}
        
        # Builder blocks (synced across network)
        self.builder_blocks = {}  # {(grid_x, grid_y): BuilderBlock}
        
        # Camera
        self.camera_x = 0
        self.camera_y = 0
        
        # UI / Input
        self.move_joy = Joystick(screen, anchor=(0.15, 0.85))
        self.aim_joy = AimJoystick(screen, anchor=(0.85, 0.85))
        
        # Role-specific buttons
        w, h = screen.get_size()
        if role == self.PlayerRole.BUILDER:
            self.action_btn = Button(screen, "Place", 
                                     (w - 100, h - 140), 140, 50)
            self.remove_btn = Button(screen, "Remove", 
                                     (w - 100, h - 80), 140, 50)
        else:
            self.action_btn = Button(screen, "Special", 
                                     (w - 100, h - 100), 140, 50)
        
        # Add back to menu button
        self.menu_btn = Button(screen, "Menu", (70, 30), 100, 40)
        
        # Keyboard state
        self.keys_pressed = {'w': False, 'a': False, 's': False, 'd': False}
        
        # Game state
        self.game_time = 0
        self.session_duration = 600  # 10 minutes per session
        
        # Setup network handlers
        if self.network_client:
            self._setup_network_handlers()
    
    def _setup_network_handlers(self):
        """Setup handlers for network messages"""
        self.network_client.register_handler(
            self.MessageType.PLAYER_UPDATE.value,
            self._handle_player_update
        )
        self.network_client.register_handler(
            self.MessageType.BLOCK_PLACE.value,
            self._handle_block_place
        )
        self.network_client.register_handler(
            self.MessageType.BLOCK_REMOVE.value,
            self._handle_block_remove
        )
        self.network_client.register_handler(
            self.MessageType.GAME_STATE.value,
            self._handle_game_state
        )
    
    def _handle_player_update(self, data):
        """Handle other player position updates"""
        player_id = data.get('player_id')
        if player_id != self.local_player.player_id:
            if player_id not in self.other_players:
                self.other_players[player_id] = self.MultiplayerPlayer.from_dict(data, self.screen)
            else:
                # Update existing player
                player = self.other_players[player_id]
                player.rect.x = data['x']
                player.rect.y = data['y']
                player.health = data['health']
    
    def _handle_block_place(self, data):
        """Handle builder block placement from network"""
        block = self.BuilderBlock.from_dict(data, self.tile_size)
        self.builder_blocks[(block.grid_x, block.grid_y)] = block
    
    def _handle_block_remove(self, data):
        """Handle builder block removal from network"""
        pos = (data[0], data[1])
        if pos in self.builder_blocks:
            del self.builder_blocks[pos]
    
    def _handle_game_state(self, data):
        """Handle initial game state from server"""
        game_state = data['game_state']
        self.local_player.player_id = data['player_id']
        
        # Load other players
        for player_id, player_data in game_state['players'].items():
            if player_id != self.local_player.player_id:
                self.other_players[player_id] = self.MultiplayerPlayer.from_dict(
                    player_data, self.screen
                )
        
        # Load builder blocks
        for block_data in game_state['blocks']:
            block = self.BuilderBlock.from_dict(block_data, self.tile_size)
            self.builder_blocks[(block.grid_x, block.grid_y)] = block
    
    def handle_event(self, event):
        """Handle input events"""
        # UI events
        self.move_joy.handle_event(event)
        self.aim_joy.handle_event(event)
        self.action_btn.handle_event(event)
        self.menu_btn.handle_event(event)
        if hasattr(self, 'remove_btn'):
            self.remove_btn.handle_event(event)
        
        # Menu button
        if self.menu_btn.clicked:
            self.menu_btn.clicked = False
            self.manager.change_scene("menu")
        
        # Keyboard
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                self.keys_pressed['w'] = True
            elif event.key == pygame.K_a:
                self.keys_pressed['a'] = True
            elif event.key == pygame.K_s:
                self.keys_pressed['s'] = True
            elif event.key == pygame.K_d:
                self.keys_pressed['d'] = True
            elif event.key == pygame.K_SPACE:
                self._use_special_ability()
            elif event.key == pygame.K_e:
                self._interact()
            elif event.key == pygame.K_ESCAPE:
                self.manager.change_scene("pause")
        
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_w:
                self.keys_pressed['w'] = False
            elif event.key == pygame.K_a:
                self.keys_pressed['a'] = False
            elif event.key == pygame.K_s:
                self.keys_pressed['s'] = False
            elif event.key == pygame.K_d:
                self.keys_pressed['d'] = False
        
        # Mouse click for builder
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.local_player.role == self.PlayerRole.BUILDER:
                self._handle_builder_click(event.pos)
        
        # Window resize
        if event.type == pygame.VIDEORESIZE or event.type == pygame.WINDOWSIZECHANGED:
            self._update_ui_layout()
    
    def _get_keyboard_direction(self):
        """Get direction from WASD keys"""
        direction = pygame.Vector2(0, 0)
        if self.keys_pressed['w']:
            direction.y -= 1
        if self.keys_pressed['s']:
            direction.y += 1
        if self.keys_pressed['a']:
            direction.x -= 1
        if self.keys_pressed['d']:
            direction.x += 1
        if direction.length() > 0:
            direction = direction.normalize()
        return direction
    
    def _use_special_ability(self):
        """Use role-specific special ability"""
        result = self.local_player.use_special_ability()
        if result:
            print(f"Used special ability: {result['type']}")
    
    def _interact(self):
        """Interact with objects"""
        print("Interact!")
    
    def _handle_builder_click(self, pos):
        """Handle builder placing/removing blocks"""
        # Convert screen pos to grid pos
        world_x = pos[0] + self.camera_x
        world_y = pos[1] + self.camera_y
        grid_x = world_x // self.tile_size
        grid_y = world_y // self.tile_size
        
        # Check if clicking on existing block (remove)
        if (grid_x, grid_y) in self.builder_blocks:
            result = self.local_player.remove_block(grid_x, grid_y)
            if result:
                del self.builder_blocks[(grid_x, grid_y)]
                # Send to network
                if self.network_client:
                    self.network_client.send_message(
                        self.create_block_remove(grid_x, grid_y)
                    )
        else:
            # Place new block
            result = self.local_player.place_block(grid_x, grid_y)
            if result:
                block = self.BuilderBlock(grid_x, grid_y, 'platform', self.tile_size)
                self.builder_blocks[(grid_x, grid_y)] = block
                # Send to network
                if self.network_client:
                    self.network_client.send_message(
                        self.create_block_place(grid_x, grid_y)
                    )
    
    def _update_ui_layout(self):
        """Update UI element positions on resize"""
        self.move_joy.update_layout(self.screen)
        self.aim_joy.update_layout(self.screen)
        w, h = self.screen.get_size()
        
        if hasattr(self, 'remove_btn'):
            self.action_btn.pos = (w - 100, h - 140)
            self.action_btn.rect.center = self.action_btn.pos
            self.remove_btn.pos = (w - 100, h - 80)
            self.remove_btn.rect.center = self.remove_btn.pos
        else:
            self.action_btn.pos = (w - 100, h - 100)
            self.action_btn.rect.center = self.action_btn.pos
        
        self.menu_btn.pos = (70, 30)
        self.menu_btn.rect.center = self.menu_btn.pos
    
    def update(self):
        """Update game logic"""
        # Update joysticks
        self.move_joy.update_drag_state()
        self.aim_joy.update_drag_state()
        
        # Get input
        joy_dir = self.move_joy.get_direction()
        kb_dir = self._get_keyboard_direction()
        move_dir = kb_dir if kb_dir.length() > 0 else joy_dir
        
        # Update local player
        self.local_player.apply_input(move_dir)
        self.local_player.update_physics()
        
        # Collision with dungeon walls
        self._handle_dungeon_collision()
        
        # Collision with builder blocks
        self._handle_builder_block_collision()
        
        # Update camera to follow player
        self._update_camera()
        
        # Send player update to network
        if self.network_client and self.network_client.connected:
            player_data = self.local_player.to_dict()
            self.network_client.send_message(self.create_player_update(player_data))
        
        # Handle action button
        if self.action_btn.clicked:
            if self.local_player.role == self.PlayerRole.BUILDER:
                # Place block at player position
                grid_x = self.local_player.rect.centerx // self.tile_size
                grid_y = self.local_player.rect.centery // self.tile_size + 1
                result = self.local_player.place_block(grid_x, grid_y)
                if result:
                    block = self.BuilderBlock(grid_x, grid_y, 'platform', self.tile_size)
                    self.builder_blocks[(grid_x, grid_y)] = block
                    if self.network_client:
                        self.network_client.send_message(
                            self.create_block_place(grid_x, grid_y)
                        )
            else:
                self._use_special_ability()
            self.action_btn.clicked = False
        
        if hasattr(self, 'remove_btn') and self.remove_btn.clicked:
            # Remove block at player position
            grid_x = self.local_player.rect.centerx // self.tile_size
            grid_y = self.local_player.rect.centery // self.tile_size + 1
            if (grid_x, grid_y) in self.builder_blocks:
                result = self.local_player.remove_block(grid_x, grid_y)
                if result:
                    del self.builder_blocks[(grid_x, grid_y)]
                    if self.network_client:
                        self.network_client.send_message(
                            self.create_block_remove(grid_x, grid_y)
                        )
            self.remove_btn.clicked = False
        
        # Update game time
        self.game_time += 1/60  # Assuming 60 FPS
    
    def _handle_dungeon_collision(self):
        """Handle collision with dungeon walls"""
        grid_x = self.local_player.rect.centerx // self.tile_size
        grid_y = self.local_player.rect.centery // self.tile_size
        
        # Check surrounding tiles in a 3x3 grid
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                check_x = grid_x + dx
                check_y = grid_y + dy
                
                if 0 <= check_y < len(self.grid) and 0 <= check_x < len(self.grid[0]):
                    if self.grid[check_y][check_x] == self.TileType.WALL:
                        tile_rect = pygame.Rect(
                            check_x * self.tile_size,
                            check_y * self.tile_size,
                            self.tile_size,
                            self.tile_size
                        )
                        if self.local_player.rect.colliderect(tile_rect):
                            self._resolve_collision(tile_rect)
    
    def _handle_builder_block_collision(self):
        """Handle collision with builder-placed blocks"""
        for block in self.builder_blocks.values():
            block_rect = block.get_rect()
            if self.local_player.rect.colliderect(block_rect):
                self._resolve_collision(block_rect)
    
    def _resolve_collision(self, obstacle_rect):
        """Simple AABB collision resolution"""
        player_rect = self.local_player.rect
        
        # Calculate overlap on each axis
        overlap_x = min(player_rect.right - obstacle_rect.left,
                       obstacle_rect.right - player_rect.left)
        overlap_y = min(player_rect.bottom - obstacle_rect.top,
                       obstacle_rect.bottom - player_rect.top)
        
        # Push out on smallest overlap axis
        if overlap_x < overlap_y:
            if player_rect.centerx < obstacle_rect.centerx:
                player_rect.right = obstacle_rect.left
            else:
                player_rect.left = obstacle_rect.right
        else:
            if player_rect.centery < obstacle_rect.centery:
                player_rect.bottom = obstacle_rect.top
            else:
                player_rect.top = obstacle_rect.bottom
    
    def _update_camera(self):
        """Update camera to follow player"""
        screen_w, screen_h = self.screen.get_size()
        
        # Center camera on player
        self.camera_x = self.local_player.rect.centerx - screen_w // 2
        self.camera_y = self.local_player.rect.centery - screen_h // 2
        
        # Clamp to dungeon bounds
        max_x = len(self.grid[0]) * self.tile_size - screen_w
        max_y = len(self.grid) * self.tile_size - screen_h
        self.camera_x = max(0, min(self.camera_x, max_x))
        self.camera_y = max(0, min(self.camera_y, max_y))
    
    def draw(self):
        """Draw everything"""
        self.screen.fill((15, 15, 20))
        
        # Draw dungeon
        self._draw_dungeon()
        
        # Draw builder blocks
        for block in self.builder_blocks.values():
            block.draw(self.screen, (self.camera_x, self.camera_y), self.tile_size)
        
        # Draw players
        self.local_player.draw(self.screen, (self.camera_x, self.camera_y))
        for player in self.other_players.values():
            player.draw(self.screen, (self.camera_x, self.camera_y))
        
        # Draw UI
        self._draw_ui()
        self._draw_minimap()  # Add minimap
        
        # Draw joysticks last
        self.move_joy.draw(self.screen)
        self.aim_joy.draw(self.screen)
        self.action_btn.draw(self.screen)
        if hasattr(self, 'remove_btn'):
            self.remove_btn.draw(self.screen)
    
    def _draw_dungeon(self):
        """Draw visible dungeon tiles"""
        screen_w, screen_h = self.screen.get_size()
        
        # Calculate visible tile range
        start_x = max(0, self.camera_x // self.tile_size)
        end_x = min(len(self.grid[0]), (self.camera_x + screen_w) // self.tile_size + 1)
        start_y = max(0, self.camera_y // self.tile_size)
        end_y = min(len(self.grid), (self.camera_y + screen_h) // self.tile_size + 1)
        
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile = self.grid[y][x]
                draw_x = (x * self.tile_size) - self.camera_x
                draw_y = (y * self.tile_size) - self.camera_y
                rect = pygame.Rect(draw_x, draw_y, self.tile_size, self.tile_size)
                
                if tile == self.TileType.WALL:
                    pygame.draw.rect(self.screen, (60, 60, 80), rect)
                    # Add darker border for walls
                    pygame.draw.rect(self.screen, (40, 40, 60), rect, 1)
                elif tile == self.TileType.FLOOR:
                    pygame.draw.rect(self.screen, (40, 40, 50), rect)
                elif tile == self.TileType.SPAWN:
                    pygame.draw.rect(self.screen, (40, 40, 50), rect)
                    pygame.draw.circle(self.screen, (100, 255, 100), rect.center, self.tile_size // 3)
                elif tile == self.TileType.BOSS:
                    pygame.draw.rect(self.screen, (40, 40, 50), rect)
                    pygame.draw.circle(self.screen, (255, 100, 100), rect.center, self.tile_size // 3)
                elif tile == self.TileType.TRAP:
                    pygame.draw.rect(self.screen, (40, 40, 50), rect)
                    # Draw warning pattern
                    pygame.draw.line(self.screen, (255, 150, 0), 
                                   (draw_x, draw_y), (draw_x + self.tile_size, draw_y + self.tile_size), 2)
                    pygame.draw.line(self.screen, (255, 150, 0), 
                                   (draw_x + self.tile_size, draw_y), (draw_x, draw_y + self.tile_size), 2)
                elif tile == self.TileType.CHEST:
                    pygame.draw.rect(self.screen, (40, 40, 50), rect)
                    # Draw chest
                    chest_rect = pygame.Rect(draw_x + 8, draw_y + 12, self.tile_size - 16, self.tile_size - 16)
                    pygame.draw.rect(self.screen, (255, 215, 0), chest_rect)
                    pygame.draw.rect(self.screen, (200, 160, 0), chest_rect, 2)
    
    def _draw_ui(self):
        """Draw UI elements"""
        font = pygame.font.SysFont(None, 28)
        small_font = pygame.font.SysFont(None, 20)
        
        # Top-left panel background
        panel = pygame.Surface((250, 120), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 180))
        self.screen.blit(panel, (5, 5))
        
        # Role display
        role_text = font.render(f"Role: {self.local_player.role.value.upper()}", True, (255, 255, 100))
        self.screen.blit(role_text, (15, 15))
        
        # Health bar
        health_text = font.render(f"HP: {self.local_player.health}/{self.local_player.max_health}", True, (255, 255, 255))
        self.screen.blit(health_text, (15, 45))
        
        # Health bar visual
        bar_x, bar_y = 15, 75
        bar_width, bar_height = 220, 12
        pygame.draw.rect(self.screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))
        health_ratio = self.local_player.health / self.local_player.max_health
        health_bar_width = int(bar_width * health_ratio)
        health_color = (0, 255, 0) if health_ratio > 0.5 else (255, 255, 0) if health_ratio > 0.25 else (255, 0, 0)
        pygame.draw.rect(self.screen, health_color, (bar_x, bar_y, health_bar_width, bar_height))
        
        # Builder inventory
        if self.local_player.role == self.PlayerRole.BUILDER:
            inv_text = small_font.render(f"Blocks: {self.local_player.block_inventory}", True, (255, 200, 100))
            self.screen.blit(inv_text, (15, 95))
        
        # Timer (top-right)
        time_left = max(0, self.session_duration - int(self.game_time))
        mins = time_left // 60
        secs = time_left % 60
        timer_text = font.render(f"{mins:02d}:{secs:02d}", True, (255, 255, 255))
        timer_rect = timer_text.get_rect()
        timer_rect.topright = (self.screen.get_width() - 15, 15)
        
        # Timer background
        timer_bg = pygame.Surface((timer_rect.width + 20, timer_rect.height + 10), pygame.SRCALPHA)
        timer_bg.fill((0, 0, 0, 180))
        self.screen.blit(timer_bg, (timer_rect.x - 10, timer_rect.y - 5))
        self.screen.blit(timer_text, timer_rect)
        
        # Controls hint (bottom-center)
        hint_text = small_font.render("WASD: Move | SPACE: Special | ESC: Menu", True, (180, 180, 180))
        hint_rect = hint_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() - 15))
        self.screen.blit(hint_text, hint_rect)
        
        # Draw menu button
        self.menu_btn.draw(self.screen)