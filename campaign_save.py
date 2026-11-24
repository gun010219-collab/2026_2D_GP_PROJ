"""Translate verified progression receipts into chapter checkpoints."""
from dataclasses import replace

from chapter_run import ChapterRun
from save_manager import FinalClear, within
from stage_progression import StageProgression


def start_chapter(store, chapter, factory):
    data = store.data
    if not within(chapter,1,len(data.unlocked)):
        raise ValueError('Chapter is locked')
    run = ChapterRun(chapter,entry_attack_level=data.entry_attack[chapter-1])
    flow = StageProgression(factory(run.current_stage,stats=run.stats),run)
    store.remember(replace(data,continue_chapter=chapter))
    return flow


def record_clear(store, flow):
    chapter,tick,hp,max_hp,attack = flow.boss_clear_record()
    result = FinalClear(tick,hp,max_hp,attack)
    data = store.data
    if chapter not in data.unlocked:
        raise ValueError('Clear requires an unlocked chapter')
    if chapter in data.cleared:
        # A replay can advance the checkpoint pointer without seeding a new build.
        if chapter < 5 and data.continue_chapter == chapter:
            store.remember(replace(data,continue_chapter=chapter+1))
        return result
    update = dict(cleared=(*data.cleared,chapter),continue_chapter=min(chapter+1,5))
    if chapter < 5:
        update.update(unlocked=(*data.unlocked,chapter+1),entry_attack=(*data.entry_attack,attack))
    else:
        update['final_clear'] = result
    store.remember(replace(data,**update))
    return result
