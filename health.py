"""Bounded, integer HP state, independent of clocks, events and rendering."""


class Health:
    def __init__(self, max_hp):
        if type(max_hp) is not int:
            raise TypeError('Maximum HP must be an integer')
        if max_hp <= 0:
            raise ValueError('Maximum HP must be positive')
        self._max_hp = max_hp
        self._current_hp = max_hp
        self._last_damage_tick = None
        self._last_damage_amount = 0

    @property
    def max_hp(self):
        return self._max_hp

    @property
    def current_hp(self):
        return self._current_hp

    @property
    def alive(self):
        return self.current_hp > 0

    @property
    def last_damage_tick(self):
        return self._last_damage_tick

    @property
    def last_damage_amount(self):
        return self._last_damage_amount

    def apply_damage(self, amount, tick=None):
        """Apply positive integer damage; return the actual HP reduction.

        Event ownership and duplicate suppression belong to the resolver. The
        optional tick is supplied by Combat, never measured by this object.
        Invalid input is rejected even when this object is already dead.
        """
        if type(amount) is not int:
            raise TypeError('Damage must be an integer')
        if amount <= 0:
            raise ValueError('Damage must be positive')
        if tick is not None:
            if type(tick) is not int:
                raise TypeError('Damage tick must be an integer')
            if tick < 0:
                raise ValueError('Damage tick cannot be negative')
        if not self.alive:
            return 0
        actual = min(amount, self.current_hp)
        self._current_hp -= actual
        self._last_damage_tick = tick
        self._last_damage_amount = actual
        return actual
