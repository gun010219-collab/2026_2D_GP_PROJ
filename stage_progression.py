"""Authenticate combat outcomes and prepare sessions before consuming upgrades."""
from chapter_run import ChapterRun
from game import GameState, StageGame
from stage_manager import StageCatalog
from upgrades import ChapterBuild, upgrade_kind


class StageProgression:
    def __init__(self, game, run=None):
        self.run = ChapterRun() if run is None else run
        self.game = game
        self.error = False
        self._require_scope()

    def _require_scope(self):
        if (not isinstance(self.game, StageGame) or not isinstance(self.run, ChapterRun)
                or self.run.retired or self.game.chapter != self.run.chapter
                or self.game.stage_number != self.run.current_stage):
            raise ValueError('Combat and chapter progression do not match')

    def _require_clear(self):
        self._require_scope()
        g = self.game
        if (g.boss or g.state is not GameState.UPGRADE or not g.player.alive
                or not g.resolver.stopped or g.transition_count != 1
                or not all(not e.alive for e in g.encounter.enemies)):
            raise ValueError('Upgrade requires the active ordinary combat to be cleared')

    def sync_offer(self):
        if self.game.state is not GameState.UPGRADE:
            return None
        self._require_clear()
        return self.run.offer_after_clear(self.game.stage_number, self.game.combat.stage_instance_id)

    @property
    def offer(self):
        return self.run.active_offer

    def _candidate(self, number, stats, factory, prepare):
        candidate = factory(number, stats=stats)
        d = StageCatalog.load().get_stage(number)
        g = candidate
        if (not isinstance(g, StageGame) or g is self.game or g.stage_number != number
                or g.chapter != d.chapter or g.boss != d.boss or not g.playing
                or g.combat.tick != 0 or g.encounter.tick != -1 or g.resolver.stopped
                or g.player.health.max_hp != stats.max_hp or g.player.health.current_hp != stats.max_hp
                or g.resolver.player_damage != stats.attack_damage or g.player.position != d.player_spawn
                or g.player.facing != 'up' or g.combat.pending_attack_bonus != 0
                or g.combat.next_attack_tick != 0 or g.parry.next_parry_tick != 0
                or g.parry.last_attempt is not None or g.resolver.last_parry_result is not None
                or g.resolver.player_invulnerable_until_tick != 0
                or g.encounter.ledger.pending
                or g.combat.stage_instance_id == self.game.combat.stage_instance_id
                or g.combat.combat_session_id == self.game.combat.combat_session_id
                or g.encounter.ledger.stage_instance_id != g.combat.stage_instance_id
                or g.encounter.ledger.combat_session_id != g.combat.combat_session_id):
            raise ValueError('Prepared combat has incorrect stats, destination or session state')
        if (g.player.health is self.game.player.health or g.parry is self.game.parry
                or g.combat is self.game.combat or g.encounter is self.game.encounter):
            raise ValueError('Prepared combat reused runtime objects')
        old_ids = {self.game.player.entity_instance_id, *(e.entity_instance_id for e in self.game.encounter.enemies)}
        if old_ids & {g.player.entity_instance_id, *(e.entity_instance_id for e in g.encounter.enemies)}:
            raise ValueError('Prepared combat reused entity instances')
        old_health = {id(self.game.player.health), *(id(e.health) for e in self.game.encounter.enemies)}
        if old_health & {id(g.player.health), *(id(e.health) for e in g.encounter.enemies)}:
            raise ValueError('Prepared combat reused Health objects')
        expected = [(e.kind, e.position, e.initial_delay_ticks) for e in g.encounter.enemies]
        from enemy_factory import create_stage_enemies
        original = create_stage_enemies(d)
        if (expected != [(e.kind, e.position, e.initial_delay_ticks) for e in original]
                or [e.health.current_hp for e in g.encounter.enemies] != [e.health.max_hp for e in original]
                or [e.health.max_hp for e in g.encounter.enemies] != [e.health.max_hp for e in original]
                or any(not e.active or e.stun_until_tick or e.current_attack is not None for e in g.encounter.enemies)):
            raise ValueError('Prepared combat has altered enemy data')
        prepared = prepare(stats)
        return g, prepared

    def choose(self, offer, kind, factory, prepare=lambda stats: None):
        self._require_clear()
        if (offer is not self.offer or offer is None or offer.run_id != self.run.run_id
                or offer.stage_instance_id != self.game.combat.stage_instance_id
                or offer.before_build != self.run.build):
            raise ValueError('Upgrade offer is stale, foreign or not active')
        kind = upgrade_kind(kind)
        build = self.run.build.upgraded(kind)
        g, prepared = self._candidate(self.game.stage_number + 1, build.stats, factory, prepare)
        receipt = self.run.select(offer, kind)
        if self.run.verify_receipt(receipt).after_build != build:
            raise RuntimeError('Committed receipt differs from prepared build')
        self.game = g
        self.error = False
        return g, prepared

    def restart(self, factory, prepare=lambda stats: None):
        self._require_scope()
        state = self.game.state
        if not self.game.resolver.stopped:
            raise ValueError('Restart requires a stopped terminal combat')
        if state is GameState.GAME_OVER and not self.game.player.alive:
            stats, destination = ChapterBuild().stats, 1
        elif (state is GameState.BOSS_CLEAR and self.game.boss and self.game.player.alive
              and all(not e.alive for e in self.game.encounter.enemies)):
            stats, destination = self.run.boss_replay_stats(), 5
        else:
            raise ValueError('Ordinary upgrades cannot restart or skip')
        g, prepared = self._candidate(destination, stats, factory, prepare)
        if state is GameState.GAME_OVER:
            self.run = self.run.restart_after_game_over()
        self.game = g
        self.error = False
        return g, prepared
