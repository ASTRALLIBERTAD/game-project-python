import pygame
from enum import Enum


class PlayerRole(Enum):
    SCOUT = "scout"
    TANK = "tank"
    MAGE = "mage"
    BUILDER = "builder"


class RoleStats:
    """Stats for each role"""
    STATS = {
        PlayerRole.SCOUT: {
            'speed': 6.0,
            'health': 80,
            'damage': 15,
            'color': (100, 200, 100),
            'special': 'dash',
            'description': 'Fast movement, can dash through enemies'
        },
        PlayerRole.TANK: {
            'speed': 3.0,
            'health': 150,
            'damage': 20,
            'color': (200, 100, 100),
            'special': 'shield',
            'description': 'High health, can block damage for allies'
        },
        PlayerRole.MAGE: {
            'speed': 4.0,
            'health': 70,
            'damage': 30,
            'color': (100, 100, 200),
            'special': 'fireball',
            'description': 'Ranged attacks, area damage spells'
        },
        PlayerRole.BUILDER: {
            'speed': 4.5,
            'health': 100,
            'damage': 10,
            'color': (200, 200, 100),
            'special': 'place_block',
            'description': 'Can place/remove blocks that sync to all players'
        }
    }
    
    @staticmethod
    def get_stats(role):
        return RoleStats.STATS.get(role, RoleStats.STATS[PlayerRole.SCOUT])


class MultiplayerPlayer:
    """Enhanced player with role-based abilities"""
    def __init__(self, screen, role=PlayerRole.SCOUT, player_id="local", is_local=True):
        self.player_id = player_id
        self.is_local = is_local
        self.role = role
        
        # Get role stats
        stats = RoleStats.get_stats(role)
        self.base_speed = stats['speed']
        self.max_health = stats['health']
        self.health = self.max_health
        self.damage = stats['damage']
        self.color = stats['color']
        self.special_ability = stats['special']
        
        # Position and movement
        w, h = screen.get_size()
        self.rect = pygame.Rect(0, 0, 28, 28)  # Smaller player (was 40x40)
        self.rect.center = (w // 2, h // 2)
        self.velocity = pygame.math.Vector2(0, 0)
        
        # Abilities
        self.dash_cooldown = 0
        self.shield_active = False
        self.shield_cooldown = 0
        self.fireball_cooldown = 0
        
        # Builder specific
        self.block_inventory = 10 if role == PlayerRole.BUILDER else 0
        self.selected_block_type = 'platform'
        
    def apply_input(self, move_dir):
        """Apply movement input"""
        if move_dir.length() > 0:
            move_dir = move_dir.normalize()
        
        # Apply speed multiplier
        self.velocity.x = move_dir.x * self.base_speed
        self.velocity.y = move_dir.y * self.base_speed
        
    def update_physics(self, dt=1.0):
        """Update position"""
        self.rect.x += self.velocity.x * dt
        self.rect.y += self.velocity.y * dt
        
        # Update cooldowns
        if self.dash_cooldown > 0:
            self.dash_cooldown -= dt
        if self.shield_cooldown > 0:
            self.shield_cooldown -= dt
        if self.fireball_cooldown > 0:
            self.fireball_cooldown -= dt
            
    def use_special_ability(self):
        """Use role-specific special ability"""
        if self.role == PlayerRole.SCOUT and self.dash_cooldown <= 0:
            return self._dash()
        elif self.role == PlayerRole.TANK and self.shield_cooldown <= 0:
            return self._activate_shield()
        elif self.role == PlayerRole.MAGE and self.fireball_cooldown <= 0:
            return self._cast_fireball()
        return None
        
    def _dash(self):
        """Scout dash ability"""
        if self.velocity.length() > 0:
            dash_dir = self.velocity.normalize()
            self.velocity = dash_dir * self.base_speed * 3
            self.dash_cooldown = 3.0  # 3 second cooldown
            return {'type': 'dash', 'direction': (dash_dir.x, dash_dir.y)}
        return None
        
    def _activate_shield(self):
        """Tank shield ability"""
        self.shield_active = True
        self.shield_cooldown = 5.0
        return {'type': 'shield'}
        
    def _cast_fireball(self):
        """Mage fireball ability"""
        self.fireball_cooldown = 2.0
        # Return fireball data for spawning projectile
        return {
            'type': 'fireball',
            'pos': (self.rect.centerx, self.rect.centery),
            'damage': self.damage
        }
        
    def place_block(self, grid_x, grid_y):
        """Builder places a block"""
        if self.role == PlayerRole.BUILDER and self.block_inventory > 0:
            self.block_inventory -= 1
            return {
                'type': 'place_block',
                'x': grid_x,
                'y': grid_y,
                'block_type': self.selected_block_type
            }
        return None
        
    def remove_block(self, grid_x, grid_y):
        """Builder removes a block"""
        if self.role == PlayerRole.BUILDER:
            self.block_inventory += 1
            return {
                'type': 'remove_block',
                'x': grid_x,
                'y': grid_y
            }
        return None
        
    def take_damage(self, amount):
        """Take damage"""
        if self.shield_active:
            amount *= 0.2  # Tank shield reduces damage by 80%
        self.health = max(0, self.health - amount)
        return self.health <= 0  # Return True if dead
        
    def draw(self, screen, camera_offset=(0, 0)):
        """Draw player"""
        draw_x = self.rect.x - camera_offset[0]
        draw_y = self.rect.y - camera_offset[1]
        draw_rect = pygame.Rect(draw_x, draw_y, self.rect.width, self.rect.height)
        
        # Draw player
        pygame.draw.rect(screen, self.color, draw_rect)
        
        # Draw shield effect for tank
        if self.shield_active and self.role == PlayerRole.TANK:
            pygame.draw.circle(
                screen, 
                (100, 200, 255), 
                draw_rect.center, 
                self.rect.width, 
                3
            )
        
        # Draw health bar
        self._draw_health_bar(screen, draw_rect)
        
        # Draw player ID (for debugging)
        if not self.is_local:
            font = pygame.font.SysFont(None, 20)
            text = font.render(self.player_id, True, (255, 255, 255))
            screen.blit(text, (draw_x, draw_y - 20))
            
    def _draw_health_bar(self, screen, draw_rect):
        """Draw health bar above player"""
        bar_width = 40
        bar_height = 4
        bar_x = draw_rect.centerx - bar_width // 2
        bar_y = draw_rect.top - 10
        
        # Background
        pygame.draw.rect(screen, (100, 100, 100), 
                        (bar_x, bar_y, bar_width, bar_height))
        
        # Health
        health_width = int((self.health / self.max_health) * bar_width)
        health_color = (0, 255, 0) if self.health > 50 else (255, 255, 0) if self.health > 25 else (255, 0, 0)
        pygame.draw.rect(screen, health_color, 
                        (bar_x, bar_y, health_width, bar_height))
    
    def to_dict(self):
        """Convert to dictionary for networking"""
        return {
            'player_id': self.player_id,
            'role': self.role.value,
            'x': self.rect.x,
            'y': self.rect.y,
            'health': self.health,
            'velocity': (self.velocity.x, self.velocity.y),
            'shield_active': self.shield_active
        }
    
    @staticmethod
    def from_dict(data, screen):
        """Create player from dictionary"""
        role = PlayerRole(data['role'])
        player = MultiplayerPlayer(screen, role, data['player_id'], is_local=False)
        player.rect.x = data['x']
        player.rect.y = data['y']
        player.health = data['health']
        player.velocity = pygame.math.Vector2(data['velocity'])
        player.shield_active = data.get('shield_active', False)
        return player


class BuilderBlock:
    """Block that builders can place"""
    def __init__(self, grid_x, grid_y, block_type='platform', tile_size=32):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.block_type = block_type
        self.tile_size = tile_size
        
        # Physics properties
        self.solid = True
        self.color = (120, 80, 40) if block_type == 'platform' else (80, 80, 120)
        
    def get_rect(self):
        """Get world rect for collision"""
        return pygame.Rect(
            self.grid_x * self.tile_size,
            self.grid_y * self.tile_size,
            self.tile_size,
            self.tile_size
        )
        
    def draw(self, screen, camera_offset=(0, 0), tile_size=32):
        """Draw the block"""
        draw_x = (self.grid_x * tile_size) - camera_offset[0]
        draw_y = (self.grid_y * tile_size) - camera_offset[1]
        
        rect = pygame.Rect(draw_x, draw_y, tile_size, tile_size)
        pygame.draw.rect(screen, self.color, rect)
        pygame.draw.rect(screen, (200, 200, 200), rect, 2)  # Border
        
    def to_dict(self):
        return {
            'x': self.grid_x,
            'y': self.grid_y,
            'type': self.block_type
        }
    
    @staticmethod
    def from_dict(data, tile_size=32):
        return BuilderBlock(data['x'], data['y'], data['type'], tile_size)