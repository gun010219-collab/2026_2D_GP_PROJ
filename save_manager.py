"""Versioned chapter checkpoints with atomic replacement and recoverable backups."""
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from game_audio import AudioSettings
from upgrades import UPGRADE_VALUES, UpgradeKind

MAX_ATTACK = len(UPGRADE_VALUES[UpgradeKind.ATTACK])-1
HP_VALUES = UPGRADE_VALUES[UpgradeKind.HP]

VERSION = 1


def save_path():
    local = os.environ.get('LOCALAPPDATA')
    root = Path(local) if local else Path.home() / 'AppData' / 'Local'
    return root / 'CHECKMATE' / 'save.json'


@dataclass(frozen=True)
class FinalClear:
    tick: int
    hp: int
    max_hp: int
    attack_level: int


@dataclass(frozen=True)
class SaveData:
    unlocked: tuple = (1,)
    cleared: tuple = ()
    continue_chapter: int | None = None
    entry_attack: tuple = (0,)
    final_clear: FinalClear | None = None
    bgm: int = 45
    sfx: int = 75
    bgm_mute: bool = False
    sfx_mute: bool = False
    fullscreen: bool = False

    def audio(self):
        return AudioSettings(self.bgm,self.sfx,self.bgm_mute,self.sfx_mute)


def within(value, low, high):
    return type(value) is int and low <= value <= high


class UnsupportedSave(ValueError):
    pass


def decode(raw):
    obj = json.loads(raw)
    if not isinstance(obj,dict) or type(obj.get('version')) is not int:
        raise ValueError('Missing save version')
    if obj.pop('version') != VERSION:
        raise UnsupportedSave('Unsupported save version')
    try:
        for key in ('unlocked','cleared','entry_attack'):
            if not isinstance(obj[key],list) or any(type(v) is not int for v in obj[key]):
                raise ValueError('Invalid chapter array')
            obj[key] = tuple(obj[key])
        final = obj['final_clear']
        if final is not None:
            obj['final_clear'] = FinalClear(**final)
        data = SaveData(**obj)
        if set(obj) != set(asdict(data)):
            raise ValueError('Missing fields')
    except (KeyError,TypeError) as exc:
        raise ValueError('Invalid save fields') from exc
    if (not 0 <= len(data.cleared) <= 5 or data.cleared != tuple(range(1,len(data.cleared)+1))
            or data.unlocked != tuple(range(1,min(5,len(data.cleared)+1)+1))
            or len(data.entry_attack) != len(data.unlocked)
            or not all(within(level,0,min(i*4,MAX_ATTACK)) for i,level in enumerate(data.entry_attack))
            or (data.continue_chapter is not None and
                not within(data.continue_chapter,1,len(data.unlocked)))
            or not within(data.bgm,0,100) or not within(data.sfx,0,100)
            or any(type(x) is not bool for x in (data.bgm_mute,data.sfx_mute,data.fullscreen))
            or bool(data.final_clear) != (len(data.cleared)==5)):
        raise ValueError('Inconsistent chapter checkpoint or settings')
    if data.final_clear:
        f = data.final_clear
        if not (within(f.tick,0,2**63-1) and type(f.max_hp) is int and f.max_hp in HP_VALUES
                and within(f.hp,1,f.max_hp) and within(f.attack_level,0,MAX_ATTACK)):
            raise ValueError('Invalid final clear')
    return data


def encode(data):
    payload = (json.dumps(dict(version=VERSION,**asdict(data)),indent=2)+'\n').encode('utf-8')
    decode(payload)
    return payload


def _read(path):
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def _atomic(path, payload):
    temporary = None
    try:
        with NamedTemporaryFile(mode='wb',dir=path.parent,prefix='.checkmate-',suffix='.tmp',delete=False) as out:
            temporary = Path(out.name)
            out.write(payload)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temporary,path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


@contextmanager
def _write_lock(path):
    with path.open('a+b') as handle:
        handle.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield  # Closing the handle releases the OS lock, including after a crash.


class SaveStore:
    def __init__(self, path):
        self.path = Path(path)
        self.backup = self.path.with_suffix('.bak')
        self.data = SaveData()
        self.notice = ''
        self.pending = False
        self.blocked = False
        self._primary = self._good = None
        try:
            self._primary = _read(self.path)
            if self._primary is not None:
                self.data = decode(self._primary)
                self._good = self._primary
                return
        except UnsupportedSave:
            self.blocked = True
            self.notice = 'SAVE VERSION UNSUPPORTED  /  READ ONLY'
        except OSError:
            self.blocked = True
            self.notice = 'SAVE UNREADABLE  /  READ ONLY'
        except (ValueError,UnicodeError):
            self.notice = 'SAVE DAMAGED  /  RECOVERY REQUIRED'
        try:
            previous = _read(self.backup)
            if previous is not None:
                self.data = decode(previous)
                self._good = previous
                self.notice += '  /  BACKUP LOADED' if self.notice else 'BACKUP LOADED'
                self.pending = not self.blocked
        except (ValueError,OSError,UnicodeError):
            self.notice += '  /  BACKUP UNAVAILABLE' if self.notice else 'BACKUP UNAVAILABLE'

    def remember(self, data):
        if data != self.data:
            self.data = data
            self.pending = True
        return self.flush()

    def flush(self):
        if self.blocked:
            return False
        if not self.pending:
            return True
        raw = encode(self.data)
        try:
            self.path.parent.mkdir(parents=True,exist_ok=True)
            with _write_lock(self.path.with_suffix('.lock')):
                if _read(self.path) != self._primary:
                    self.blocked = True
                    self.notice = 'SAVE CHANGED ELSEWHERE  /  SESSION ONLY'
                    return False
                if self._primary is not None and self._primary != self._good:
                    archive = self.path.with_name('save-recovery-'+uuid4().hex+'.json')
                    _atomic(archive,self._primary)
                if self._good is not None:
                    _atomic(self.backup,self._good)
                _atomic(self.path,raw)
        except OSError:
            self.notice = 'SAVE FAILED  /  SESSION ONLY'
            return False
        self._primary = self._good = raw
        self.pending = False
        self.notice = ''
        return True

    def settings(self, audio, fullscreen):
        return self.remember(replace(self.data,fullscreen=fullscreen,**asdict(audio)))
