"""SDL event adapter with transition-only physical-key reconciliation."""
from attack_input import AttackInput
from input_controller import InputController
from parry_input import ParryInput


class GameplayInput:
    def __init__(self, canvas, *, move_interval_ticks=None):
        self.canvas = canvas
        self.movement = InputController(move_interval_ticks=move_interval_ticks)
        self.attack = AttackInput()
        self.parry = ParryInput()
        self.restart_held = False
        self.next_held = False
        self.arrows = {canvas.SDLK_UP: 'up', canvas.SDLK_DOWN: 'down',
                       canvas.SDLK_LEFT: 'left', canvas.SDLK_RIGHT: 'right'}
        self.shifts = {canvas.SDLK_LSHIFT: 'left', canvas.SDLK_RSHIFT: 'right'}

    @property
    def focused(self):
        c = self.canvas
        return bool(c.SDL_GetWindowFlags(c.window) & c.SDL_WINDOW_INPUT_FOCUS)

    def is_gameplay_key(self, event):
        c = self.canvas
        return (event.type in (c.SDL_KEYDOWN, c.SDL_KEYUP)
                and (event.key in self.arrows or event.key in self.shifts
                     or event.key == c.SDLK_SPACE))

    def handle_restart(self, event, enabled=False, blocked=False):
        """R is edge-triggered and immediate, outside the combat input queue."""
        return self._handle_flow_key(event, ord('r'), 'restart_held', enabled, blocked)

    def handle_next(self, event, enabled=False, blocked=False):
        """N has its own latch; blocked presses are never buffered for later."""
        return self._handle_flow_key(event, ord('n'), 'next_held', enabled, blocked)

    def _handle_flow_key(self, event, key, latch, enabled, blocked):
        c = self.canvas
        if event.type not in (c.SDL_KEYDOWN, c.SDL_KEYUP) or event.key != key:
            return False
        if event.type == c.SDL_KEYUP:
            setattr(self, latch, False)
            return False
        was_held = getattr(self, latch)
        setattr(self, latch, True)
        return enabled and not blocked and not was_held and not getattr(event, 'repeat', False)

    def reset_after_restart(self):
        """Quarantine physically held keys without producing gameplay commands."""
        self.reset_after_transition(ord('r'))

    def reset_after_transition(self, trigger_key):
        if trigger_key not in (ord('r'), ord('n')):
            raise ValueError('Stage transitions require an R or N press')
        self.reconcile_physical_keys()
        if trigger_key == ord('r'):
            self.restart_held = True
        else:
            self.next_held = True

    def prepare_session(self):
        """Reconcile before committing a prepared session, including held combat keys."""
        self.reconcile_physical_keys()

    def handle_key(self, event, player, combat, blocked=False, parry=None, occupied=(),
                   on_attack=None, on_parry=None):
        """Preserve the bool consumption contract; deliver new attacks immediately.

        The callback receives only the event returned by this SPACE press, never
        the renderer's active effect. Releases remain live when gameplay is dead
        or blocked by a menu/display transition.
        """
        c = self.canvas
        if event.type not in (c.SDL_KEYDOWN, c.SDL_KEYUP):
            return False
        blocked = blocked or not player.alive
        if event.key in self.shifts:
            if event.type == c.SDL_KEYUP:
                self.parry.key_up(self.shifts[event.key])
            else:
                attempt = self.parry.key_down(self.shifts[event.key], parry, combat.tick,
                                              blocked=blocked or parry is None)
                if attempt is not None and on_parry is not None:
                    on_parry(attempt)
            return True
        if event.key in self.arrows:
            if event.type == c.SDL_KEYUP:
                self.movement.key_up(self.arrows[event.key])
            else:
                self.movement.key_down(self.arrows[event.key], player, blocked, occupied,
                                       tick=combat.tick)
            return True
        if event.key == c.SDLK_SPACE:
            if event.type == c.SDL_KEYUP:
                self.attack.key_up()
            else:
                attack = self.attack.key_down(player, combat, blocked)
                if attack is not None and on_attack is not None:
                    on_attack(attack)
            return True
        return False

    def release_on_focus_loss(self):
        self.movement.reconcile(())
        self.attack.reconcile(False)
        self.parry.reconcile(())
        self.restart_held = False
        self.next_held = False

    def reconcile_physical_keys(self):
        c = self.canvas
        keys = c.SDL_GetKeyboardState(None)
        self.movement.reconcile(direction for scan, direction in (
            (c.SDL_SCANCODE_UP, 'up'), (c.SDL_SCANCODE_DOWN, 'down'),
            (c.SDL_SCANCODE_LEFT, 'left'), (c.SDL_SCANCODE_RIGHT, 'right')) if keys[scan])
        self.attack.reconcile(keys[c.SDL_SCANCODE_SPACE])
        self.parry.reconcile(side for scan, side in (
            (c.SDL_SCANCODE_LSHIFT, 'left'), (c.SDL_SCANCODE_RSHIFT, 'right')) if keys[scan])
        scan = getattr(c, 'SDL_SCANCODE_R', None)
        if type(scan) is int:
            self.restart_held = bool(keys[scan])
        scan = getattr(c, 'SDL_SCANCODE_N', None)
        if type(scan) is int:
            self.next_held = bool(keys[scan])
