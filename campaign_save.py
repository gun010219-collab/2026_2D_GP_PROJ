"""Translate verified progression receipts into chapter checkpoints."""
from dataclasses import replace

from chapter_run import ChapterRun
from save_manager import FinalClear, within
from stage_progression import StageProgression
from upgrades import ChapterBuild


def start_chapter(store, chapter, factory, *, new_game=False):
    data = store.data
    if not within(chapter,1,len(data.unlocked)):
        raise ValueError('Chapter is locked')
    if new_game:
        if chapter != 1:
            raise ValueError('New game must start in Chapter 1')
        data = replace(data,entry_builds=(ChapterBuild(),)+(None,)*(len(data.unlocked)-1))
    run = ChapterRun(chapter,entry_build=data.entry_builds[chapter-1])
    flow = StageProgression(factory(run.current_stage,stats=run.stats),run)
    store.remember(replace(data,continue_chapter=chapter))
    return flow


def record_clear(store, flow):
    chapter,tick,hp,max_hp,attack = flow.boss_clear_record()
    result = FinalClear(tick,hp,max_hp,attack)
    data = store.data
    if chapter not in data.unlocked:
        raise ValueError('Clear requires an unlocked chapter')
    first_clear = chapter not in data.cleared
    update = {}
    if first_clear:
        update.update(cleared=(*data.cleared,chapter),continue_chapter=min(chapter+1,5))
    if chapter < 5:
        builds = data.entry_builds
        if first_clear:
            update.update(unlocked=(*data.unlocked,chapter+1),entry_builds=(*builds,flow.run.build))
        elif builds[chapter] is None:
            update['entry_builds'] = builds[:chapter]+(flow.run.build,)+builds[chapter+1:]
        if data.continue_chapter == chapter:
            update['continue_chapter'] = chapter+1
    elif first_clear:
        update['final_clear'] = result
    if update:
        store.remember(replace(data,**update))
    return result
