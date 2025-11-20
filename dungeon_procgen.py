import random
import json
from enum import Enum


class TileType(Enum):
    EMPTY = 0
    WALL = 1
    FLOOR = 2
    DOOR = 3
    TRAP = 4
    CHEST = 5
    SPAWN = 6
    BOSS = 7
    BUILDER_BLOCK = 8


class Room:
    def __init__(self, x, y, width, height, room_type="normal"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.room_type = room_type  # normal, trap, boss, treasure
        self.connected = False
        self.enemies = []
        
    def center(self):
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    def intersects(self, other):
        return (self.x < other.x + other.width and
                self.x + self.width > other.x and
                self.y < other.y + other.height and
                self.y + self.height > other.y)


class DungeonGenerator:
    def __init__(self, width=80, height=60, num_rooms=8):
        self.width = width
        self.height = height
        self.num_rooms = num_rooms
        self.grid = [[TileType.WALL for _ in range(width)] for _ in range(height)]
        self.rooms = []
        self.spawn_point = None
        self.boss_room = None
        
    def generate(self):
        """Generate a complete dungeon"""
        self.rooms = []
        self.grid = [[TileType.WALL for _ in range(self.width)] for _ in range(self.height)]
        
        # Generate rooms
        for i in range(self.num_rooms):
            room = self._create_random_room(i)
            if room:
                self.rooms.append(room)
                self._carve_room(room)
        
        # Connect rooms with corridors
        self._connect_rooms()
        
        # Set spawn and boss rooms
        if self.rooms:
            self.rooms[0].room_type = "spawn"
            self.spawn_point = self.rooms[0].center()
            self._mark_tile(self.spawn_point[0], self.spawn_point[1], TileType.SPAWN)
            
            self.rooms[-1].room_type = "boss"
            self.boss_room = self.rooms[-1]
            boss_center = self.boss_room.center()
            self._mark_tile(boss_center[0], boss_center[1], TileType.BOSS)
        
        # Add traps and chests
        self._add_features()
        
        return self.grid, self.rooms
    
    def _create_random_room(self, attempt):
        """Try to create a room that doesn't overlap"""
        max_attempts = 30
        for _ in range(max_attempts):
            width = random.randint(5, 12)
            height = random.randint(5, 12)
            x = random.randint(1, self.width - width - 1)
            y = random.randint(1, self.height - height - 1)
            
            new_room = Room(x, y, width, height)
            
            # Check if room overlaps with existing rooms
            overlaps = False
            for room in self.rooms:
                if new_room.intersects(room):
                    overlaps = True
                    break
            
            if not overlaps:
                return new_room
        
        return None
    
    def _carve_room(self, room):
        """Carve out a room in the grid"""
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.grid[y][x] = TileType.FLOOR
    
    def _connect_rooms(self):
        """Connect all rooms with corridors"""
        for i in range(len(self.rooms) - 1):
            room_a = self.rooms[i]
            room_b = self.rooms[i + 1]
            
            cx1, cy1 = room_a.center()
            cx2, cy2 = room_b.center()
            
            # Create L-shaped corridor
            if random.random() < 0.5:
                self._carve_h_corridor(cx1, cx2, cy1)
                self._carve_v_corridor(cy1, cy2, cx2)
            else:
                self._carve_v_corridor(cy1, cy2, cx1)
                self._carve_h_corridor(cx1, cx2, cy2)
    
    def _carve_h_corridor(self, x1, x2, y):
        """Horizontal corridor"""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                self.grid[y][x] = TileType.FLOOR
    
    def _carve_v_corridor(self, y1, y2, x):
        """Vertical corridor"""
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                self.grid[y][x] = TileType.FLOOR
    
    def _add_features(self):
        """Add traps and chests to rooms"""
        for room in self.rooms[1:-1]:  # Skip spawn and boss rooms
            if random.random() < 0.4:  # 40% chance for trap
                tx = random.randint(room.x + 1, room.x + room.width - 2)
                ty = random.randint(room.y + 1, room.y + room.height - 2)
                self.grid[ty][tx] = TileType.TRAP
                room.room_type = "trap"
            
            if random.random() < 0.3:  # 30% chance for chest
                cx = random.randint(room.x + 1, room.x + room.width - 2)
                cy = random.randint(room.y + 1, room.y + room.height - 2)
                if self.grid[cy][cx] == TileType.FLOOR:
                    self.grid[cy][cx] = TileType.CHEST
    
    def _mark_tile(self, x, y, tile_type):
        """Mark a specific tile"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = tile_type
    
    def to_dict(self):
        """Convert dungeon to dictionary for saving/networking"""
        return {
            'width': self.width,
            'height': self.height,
            'grid': [[tile.value for tile in row] for row in self.grid],
            'rooms': [
                {
                    'x': room.x,
                    'y': room.y,
                    'width': room.width,
                    'height': room.height,
                    'type': room.room_type
                }
                for room in self.rooms
            ],
            'spawn_point': self.spawn_point
        }
    
    @staticmethod
    def from_dict(data):
        """Load dungeon from dictionary"""
        gen = DungeonGenerator(data['width'], data['height'])
        gen.grid = [[TileType(val) for val in row] for row in data['grid']]
        gen.rooms = [
            Room(r['x'], r['y'], r['width'], r['height'], r['type'])
            for r in data['rooms']
        ]
        gen.spawn_point = tuple(data['spawn_point'])
        return gen
    
    def save_to_file(self, filename):
        """Save dungeon to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.to_dict(), f)
    
    @staticmethod
    def load_from_file(filename):
        """Load dungeon from JSON file"""
        with open(filename, 'r') as f:
            data = json.load(f)
        return DungeonGenerator.from_dict(data)


if __name__ == "__main__":
    # Test generation
    dungeon = DungeonGenerator(width=60, height=40, num_rooms=8)
    grid, rooms = dungeon.generate()
    
    print(f"Generated {len(rooms)} rooms")
    print(f"Spawn point: {dungeon.spawn_point}")
    
    # Save to file
    dungeon.save_to_file("test_dungeon.json")
    print("Dungeon saved to test_dungeon.json")