"""PDF values, all build combinations, immutable options and payload validation."""
from dataclasses import FrozenInstanceError, replace
from itertools import product
import unittest

from upgrades import (ChapterBuild, DerivedStats, UpgradeKind, UPGRADE_VALUES,
                      UpgradeOffer, UpgradeOption, UpgradeReceipt)


def offer(build=ChapterBuild()):
    return UpgradeOffer('run', 'offer', 1, 1, 'stage', build)


class UpgradeDataTests(unittest.TestCase):
    def test_exact_three_types_and_value_tables_are_read_only(self):
        self.assertEqual(tuple(k.value for k in UpgradeKind), ('attack', 'hp', 'move'))
        self.assertEqual(tuple(UPGRADE_VALUES.values()), ((1,2,3),(3,4,5,6),(18,15,12)))
        with self.assertRaises(TypeError):
            UPGRADE_VALUES[UpgradeKind.ATTACK] = (99,)

    def test_default_and_maximum_build_stats(self):
        self.assertEqual(ChapterBuild().stats, DerivedStats(1,3,18))
        self.assertEqual(ChapterBuild(2,3,2).stats, DerivedStats(3,6,12))

    def test_every_one_of_36_builds_has_exact_deterministic_stats(self):
        for attack,hp,move in product(range(3),range(4),range(3)):
            b=ChapterBuild(attack,hp,move)
            expected=DerivedStats((1,2,3)[attack],(3,4,5,6)[hp],(18,15,12)[move])
            self.assertEqual(b.stats,expected)
            self.assertEqual(b.stats,ChapterBuild(attack,hp,move).stats)

    def test_bad_levels_bool_negative_float_string_and_over_cap_rejected(self):
        for field,cap in (('attack_level',2),('hp_level',3),('move_level',2)):
            for bad in (True,False,-1,cap+1,1.0,'1',None,[],float('nan')):
                with self.subTest(field=field,bad=bad), self.assertRaises(ValueError):
                    ChapterBuild(**{field:bad})

    def test_build_and_stats_are_frozen_and_have_no_mutable_container(self):
        for obj,field in ((ChapterBuild(),'hp_level'),(ChapterBuild().stats,'max_hp')):
            with self.assertRaises((FrozenInstanceError,AttributeError)):
                setattr(obj,field,100)
            self.assertFalse(hasattr(obj,'__dict__'))

    def test_invalid_derived_values_never_become_custom_upgrade_effects(self):
        for index in range(3):
            for bad in (True,False,0,-1,99,1.5,None):
                values=[1,3,18]
                values[index]=bad
                with self.assertRaises(ValueError):
                    DerivedStats(*values)

    def test_same_kind_grows_one_level_using_table_not_accumulated_values(self):
        b=ChapterBuild()
        first=b.upgraded('attack')
        second=first.upgraded(UpgradeKind.ATTACK)
        self.assertEqual((b.stats.attack_damage,first.stats.attack_damage,second.stats.attack_damage),(1,2,3))
        with self.assertRaises(ValueError):
            second.upgraded('attack')
        self.assertEqual(second,ChapterBuild(2,0,0))

    def test_unknown_effects_are_not_silently_mapped_to_a_card(self):
        for bad in ('parry','critical','speed',True,1,None,[],{}):
            with self.assertRaises(ValueError):
                ChapterBuild().upgraded(bad)

    def test_offer_always_has_three_cards_in_fixed_order_with_next_values(self):
        options=offer(ChapterBuild(1,2,1)).options
        self.assertEqual([x.kind.value for x in options],['attack','hp','move'])
        self.assertEqual([(x.current_level,x.next_level,x.current_value,x.next_value,x.enabled) for x in options],
                         [(1,2,2,3,True),(2,3,5,6,True),(1,2,15,12,True)])

    def test_max_cards_stay_present_without_fictitious_next_levels(self):
        options=offer(ChapterBuild(2,3,2)).options
        self.assertEqual(len(options),3)
        for option in options:
            self.assertTrue(option.is_max)
            self.assertFalse(option.enabled)
            self.assertIsNone(option.next_level)
            self.assertIsNone(option.next_value)

    def test_option_and_offer_are_immutable(self):
        o=offer()
        with self.assertRaises(FrozenInstanceError):
            o.before_build=ChapterBuild(1)
        with self.assertRaises(FrozenInstanceError):
            o.options[0].current_level=2

    def test_invalid_option_and_offer_scope_payloads(self):
        for kind,level in (('unknown',0),('attack',3),('hp',True),('move',-1)):
            with self.assertRaises(ValueError):
                UpgradeOption(kind,level)
        for fields in ({'run_id':''},{'offer_id':' '},{'stage_instance_id':None},
                       {'chapter':True},{'chapter':0},{'chapter':6},{'stage':True},
                       {'stage':0},{'stage':5},{'stage':6}):
            with self.assertRaises(ValueError):
                replace(offer(),**fields)
        with self.assertRaises(TypeError):
            replace(offer(),before_build=None)

    def test_receipt_connects_exactly_one_before_and_after_step(self):
        o=offer()
        receipt=UpgradeReceipt(o,'hp',ChapterBuild(0,1,0))
        self.assertEqual(receipt.run_id,o.run_id)
        self.assertEqual(receipt.before_build,ChapterBuild())
        with self.assertRaises(FrozenInstanceError):
            receipt.kind=UpgradeKind.ATTACK
        for after in (ChapterBuild(),ChapterBuild(0,2,0),ChapterBuild(1,1,0),None):
            with self.assertRaises(ValueError):
                UpgradeReceipt(o,'hp',after)


if __name__=='__main__':
    unittest.main()
