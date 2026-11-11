"""SDL event adapter with transition-only physical-key reconciliation."""
from attack_input import AttackInput
from input_controller import InputController
from parry_input import ParryInput


class GameplayInput:
    def __init__(self, canvas):
        self.canvas = canvas
        self.movement = InputController()
        self.attack = AttackInput()
        self.parry = ParryInput()
        self.arrows = {canvas.SDLK_UP: 'up', canvas.SDLK_DOWN: 'down',
                       canvas.SDLK_LEFT: 'left', canvas.SDLK_RIGHT: 'right'}
        self.shifts = {canvas.SDLK_LSHIFT: 'left', canvas.SDLK_RSHIFT: 'right'}

    @property
    def focused(self):
        c = self.canvas
        return bool(c.SDL_GetWindowFlags(c.window) & c.SDL_WINDOW_INPUT_FOCUS)

    def handle_key(self, event, player, combat, blocked=False, parry=None, occupied=()):
        c = self.canvas
        if event.type not in (c.SDL_KEYDOWN, c.SDL_KEYUP):
            return False
        if event.key in self.shifts:
            if event.type == c.SDL_KEYUP:
                self.parry.key_up(self.shifts[event.key])
            else:
                self.parry.key_down(self.shifts[event.key], parry, combat.tick,
                                    blocked=blocked or parry is None)
            return True
        if event.key in self.arrows:
            if event.type == c.SDL_KEYUP:
                self.movement.key_up(self.arrows[event.key])
            else:
                self.movement.key_down(self.arrows[event.key], player, blocked, occupied)
            return True
        if event.key == c.SDLK_SPACE:
            if event.type == c.SDL_KEYUP:
                self.attack.key_up()
            else:
                self.attack.key_down(player, combat, blocked)
            return True
        return False

    def release_on_focus_loss(self):
        self.movement.reconcile(())
        self.attack.reconcile(False)
        self.parry.reconcile(())

    def reconcile_physical_keys(self):
        c = self.canvas
        keys = c.SDL_GetKeyboardState(None)
        self.movement.reconcile(direction for scan, direction in (
            (c.SDL_SCANCODE_UP, 'up'), (c.SDL_SCANCODE_DOWN, 'down'),
            (c.SDL_SCANCODE_LEFT, 'left'), (c.SDL_SCANCODE_RIGHT, 'right')) if keys[scan])
        self.attack.reconcile(keys[c.SDL_SCANCODE_SPACE])
        self.parry.reconcile(side for scan, side in (
            (c.SDL_SCANCODE_LSHIFT, 'left'), (c.SDL_SCANCODE_RSHIFT, 'right')) if keys[scan])
