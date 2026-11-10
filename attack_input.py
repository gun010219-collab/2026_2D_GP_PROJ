"""SPACE press/release latch, independent of SDL, movement and combat balance."""


class AttackInput:
    def __init__(self):
        self.held = False

    def key_down(self, player, combat, blocked=False):
        if self.held:
            return None
        self.held = True
        return None if blocked else combat.request_attack(player)

    def key_up(self):
        self.held = False

    def reconcile(self, held):
        """On focus/display changes only: synchronize without requesting attacks."""
        self.held = bool(held)
