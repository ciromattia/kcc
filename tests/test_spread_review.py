import os
import unittest
from unittest.mock import patch

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QDialog

from kindlecomicconverter.KCC_spread_label import LabelSpreadsDialog, choose_automatic_merges


class SpreadReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        cls.app = QApplication.instance() or QApplication([])

    def make_dialog(self, kinds, spreads=None, splits=None, merge_only=False):
        def alignment(shift):
            pairs = [pair for pair in kinds if pair % 2 == int(shift)]
            return pairs, {pair: f'{pair + 1}–{pair + 2}  page-{pair}' for pair in pairs}

        pairs, names = alignment(False)
        dialog = LabelSpreadsDialog(
            650, pairs, set(spreads or ()), lambda *_: (QPixmap(50, 100), 25),
            kinds.__getitem__, names, set(splits or ()), merge_only=merge_only,
        )
        dialog.shift_changed_callback = alignment
        self.addCleanup(dialog.reject)
        return dialog

    def finish_current_scan(self, dialog):
        while not dialog.finished_scan:
            dialog.scan_pair()

    def test_auto_pairing_suggests_both_alignments_without_overlap(self):
        dialog = self.make_dialog({0: 'panel', 1: 'full', 2: 'split', 3: 'panel', 4: 'review'})
        dialog.pairing_box.setCurrentIndex(2)
        self.finish_current_scan(dialog)
        self.assertEqual(dialog.visible_pairs, [1, 3])
        self.assertFalse(dialog.shift_hint)
        self.assertTrue(dialog.apply({1, 3}, merge=True))
        self.assertEqual(dialog.spreads, {1, 3})
        dialog.pairing_box.setCurrentIndex(0)
        self.assertEqual(dialog.spreads, {1, 3})

    def test_auto_pairing_can_prefer_two_nonoverlapping_joins(self):
        self.assertEqual(choose_automatic_merges({0: 2, 1: 2, 2: 2}), {0, 2})
        self.assertEqual(choose_automatic_merges({0: 1, 1: 2}), {1})

    def test_warns_about_actionable_merge_in_other_alignment(self):
        dialog = self.make_dialog({0: 'split', 1: 'full', 2: 'review'})
        self.finish_current_scan(dialog)
        dialog.scan_pair()
        self.assertEqual(dialog.shift_banner.text(), 'Likely merges found with Spread Shift on')
        self.assertFalse(dialog.shift_banner.isHidden())
        dialog.pairing_box.setCurrentIndex(1)
        self.assertTrue(dialog.shift_banner.isHidden())

    def test_confirmations_survive_switch_and_overlap_does_not_prompt(self):
        dialog = self.make_dialog(
            {0: 'split', 1: 'full', 2: 'review', 3: 'split', 4: 'full', 5: 'full'},
            spreads={4}, splits={0}, merge_only=True,
        )
        self.finish_current_scan(dialog)
        self.assertEqual(dialog.visible_pairs, [0, 4])
        dialog.pairing_box.setCurrentIndex(1)
        self.finish_current_scan(dialog)
        self.assertEqual(dialog.row_status(1), 'Overlaps split')
        self.assertEqual(dialog.row_status(5), 'Overlaps merge')
        self.assertEqual(dialog.visible_pairs, [])
        with patch('kindlecomicconverter.KCC_spread_label.QMessageBox') as prompt:
            dialog.save()
        prompt.assert_not_called()
        self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)
        self.assertEqual(dialog.spreads, {4})
        self.assertEqual(dialog.splits, {0})


if __name__ == '__main__':
    unittest.main()
