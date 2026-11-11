"""Temporary, read-only health labels and hit feedback; no external font assets.

All feedback reads actual Health state. Rendering never consumes attack events,
advances combat time, or changes health. The small glyphs are original procedural
UI placeholders and can be replaced with a proper text renderer later.
"""
from config import TILE_SIZE, cell_center


# Three by five pixel glyphs, top row first. Only the small HUD's alphabet is used.
_GLYPHS = {
    '0': ('111', '101', '101', '101', '111'),
    '1': ('010', '110', '010', '010', '111'),
    '2': ('111', '001', '111', '100', '111'),
    '3': ('111', '001', '111', '001', '111'),
    '4': ('101', '101', '111', '001', '001'),
    '5': ('111', '100', '111', '001', '111'),
    '6': ('111', '100', '111', '101', '111'),
    '7': ('111', '001', '010', '010', '010'),
    '8': ('111', '101', '111', '101', '111'),
    '9': ('111', '101', '111', '001', '111'),
    'A': ('010', '101', '111', '101', '101'),
    'B': ('110', '101', '110', '101', '110'),
    'C': ('111', '100', '100', '100', '111'),
    'D': ('110', '101', '101', '101', '110'),
    'E': ('111', '100', '110', '100', '111'),
    'F': ('111', '100', '110', '100', '100'),
    'G': ('111', '100', '101', '101', '111'),
    'H': ('101', '101', '111', '101', '101'),
    'I': ('111', '010', '010', '010', '111'),
    'K': ('101', '101', '110', '101', '101'),
    'L': ('100', '100', '100', '100', '111'),
    'M': ('101', '111', '111', '101', '101'),
    'N': ('101', '111', '111', '111', '101'),
    'O': ('111', '101', '101', '101', '111'),
    'P': ('111', '101', '111', '100', '100'),
    'R': ('110', '101', '110', '101', '101'),
    'S': ('111', '100', '111', '001', '111'),
    'T': ('111', '010', '010', '010', '010'),
    'U': ('101', '101', '101', '101', '111'),
    'V': ('101', '101', '101', '101', '010'),
    'W': ('101', '101', '111', '111', '101'),
    'X': ('101', '101', '010', '101', '101'),
    'Y': ('101', '101', '010', '010', '010'),
    '/': ('001', '001', '010', '100', '100'),
    '+': ('000', '010', '111', '010', '000'),
    ':': ('000', '010', '000', '010', '000'),
    ' ': ('000', '000', '000', '000', '000'),
}


class HealthRenderer:
    HIT_FLASH_TICKS = 6
    TEXT = (232, 231, 220)
    HEALTH = (143, 209, 158)
    HIT = (225, 199, 255)

    @staticmethod
    def _text(canvas, text, x, y, scale=2, color=TEXT):
        """Draw a bottom-left-anchored small label with no native resources."""
        for index, char in enumerate(text):
            for row, bits in enumerate(_GLYPHS[char]):
                for col, bit in enumerate(bits):
                    if bit == '1':
                        left = x + index * 4 * scale + col * scale
                        bottom = y + (4 - row) * scale
                        canvas.draw_rectangle(left, bottom, left + scale - 1,
                                              bottom + scale - 1, *color, filled=True)

    @classmethod
    def _hit_flash(cls, canvas, entity, tick):
        last_hit = entity.health.last_damage_tick
        # Dead-player combat time is frozen: do not leave a short flash stuck on.
        if (not entity.health.alive or last_hit is None
                or not 0 <= tick - last_hit < cls.HIT_FLASH_TICKS):
            return
        x, y = cell_center(*entity.position)
        # Corner marks stay inside the cell, away from full-cell warning outlines.
        extent, length = TILE_SIZE * 0.37, TILE_SIZE * 0.10
        for sx in (-1, 1):
            for sy in (-1, 1):
                px, py = x + sx * extent, y + sy * extent
                canvas.draw_line(px, py, px - sx * length, py, *cls.HIT)
                canvas.draw_line(px, py, px, py - sy * length, *cls.HIT)

    def draw(self, canvas, player, enemies, tick, attack_bonus=None, show_feedback=True):
        health = player.health
        # Compact actual information in the left margin; no fixed right HUD.
        canvas.draw_rectangle(30, 704, 270, 844, 17, 22, 27, filled=True)
        self._text(canvas, 'PLAYER HP', 44, 817, scale=3)
        self._text(canvas, f'{health.current_hp}/{health.max_hp}', 44, 788, scale=3,
                   color=self.HEALTH if health.alive else self.HIT)
        canvas.draw_rectangle(44, 772, 255, 778, 55, 65, 63, filled=True)
        if health.current_hp:
            right = 44 + round(212 * health.current_hp / health.max_hp) - 1
            canvas.draw_rectangle(44, 772, right, 778, *self.HEALTH, filled=True)
        if health.alive and show_feedback:
            if attack_bonus is not None and attack_bonus > 0:
                self._text(canvas, f'NEXT +{attack_bonus}', 150, 755, color=(255, 226, 116))
            self._text(canvas, 'PARRY WINDOW', 44, 743)
            self._text(canvas, 'SHIFT TO PARRY', 44, 723)
        elif not health.alive:
            self._text(canvas, 'DEAD', 44, 743, color=self.HIT)
            self._text(canvas, 'INPUT LOCKED', 44, 723)
        if show_feedback:
            self._hit_flash(canvas, player, tick)

        for enemy in enemies:
            if not enemy.active:
                continue
            x, y = cell_center(*enemy.position)
            label = f'{enemy.health.current_hp}/{enemy.health.max_hp}'
            label_width = (len(label) * 4 - 1) * 2
            canvas.draw_rectangle(x - label_width / 2 - 3, y + 30,
                                  x + label_width / 2 + 3, y + 41,
                                  17, 22, 27, filled=True)
            self._text(canvas, label, x - label_width / 2, y + 31,
                       color=self.HEALTH)
            if (getattr(enemy, 'state', None) == 'stunned'
                    and tick < enemy.stun_until_tick):
                canvas.draw_rectangle(x - 18, y - 41, x + 18, y - 28,
                                      17, 22, 27, filled=True)
                self._text(canvas, 'STUN', x - 15, y - 39, color=(255, 226, 116))
            if show_feedback:
                self._hit_flash(canvas, enemy, tick)
