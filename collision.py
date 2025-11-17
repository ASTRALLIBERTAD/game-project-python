class Collider:
    def __init__(self, x: float, y: float, width: float, height: float):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @property
    def rect(self):
        return (self.x, self.y, self.width, self.height)

    def update_position(self, x: float, y: float):
        self.x = x
        self.y = y

    def resolve(self, player):
        # Update collider position to match player position
        self.update_position(player.rect.x, player.rect.y)


def aabb_collision(a: Collider, b: Collider) -> bool:
    ax, ay, aw, ah = a.rect
    bx, by, bw, bh = b.rect

    return (
        ax < bx + bw and
        ax + aw > bx and
        ay < by + bh and
        ay + ah > by
    )


class CollisionSystem:
    def __init__(self):
        self.colliders = []

    def add(self, collider: Collider):
        self.colliders.append(collider)

    def remove(self, collider: Collider):
        if collider in self.colliders:
            self.colliders.remove(collider)

    def check_all(self):
        collisions = []
        for i in range(len(self.colliders)):
            for j in range(i + 1, len(self.colliders)):
                a = self.colliders[i]
                b = self.colliders[j]
                if aabb_collision(a, b):
                    collisions.append((a, b))
        return collisions
