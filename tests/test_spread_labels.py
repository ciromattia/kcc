import tempfile
import unittest
from pathlib import Path

from PIL import Image

from kindlecomicconverter import comic2ebook
from kindlecomicconverter.KCC_spread_compare import output_groups, preview_page


class SpreadLabelsTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name)
        self.source = self.path / 'kcc-0001.png'
        page = Image.new('RGB', (320, 240), 'red')
        page.paste('blue', (160, 0, 320, 240))
        page.save(self.source)

    def layout(self):
        return list(comic2ebook.spread_label_pages(self.path, righttoleft=True, split=True))

    def test_old_labels_still_load(self):
        layout = self.layout()
        sidecar = self.path / 'book.json'
        sidecar.write_text('{"spreads": [0]}', encoding='utf-8')
        comic2ebook.validate_spread_labels(comic2ebook.read_spread_labels(sidecar), layout, True)

    def test_changed_image_with_same_dimensions_invalidates_labels(self):
        layout = self.layout()
        labels = {'spreads': [0], 'source_layout': comic2ebook.spread_layout_signature(layout)}
        Image.new('RGB', (320, 240), 'green').save(self.source)
        with self.assertRaisesRegex(UserWarning, 'no longer match'):
            comic2ebook.validate_spread_labels(labels, self.layout(), True)

    def test_rejects_overlapping_out_of_range_and_wrong_direction(self):
        layout = self.layout()
        for labels in ({'spreads': [0, 0]}, {'spreads': [1]}, {'spreads': [0], 'righttoleft': False}):
            with self.subTest(labels=labels), self.assertRaises(UserWarning):
                comic2ebook.validate_spread_labels(labels, layout, True)

    def test_split_only_preview_has_same_page_order_as_conversion(self):
        for righttoleft, expected in ((False, [(255, 0, 0), (0, 0, 255)]),
                                     (True, [(0, 0, 255), (255, 0, 0)])):
            with self.subTest(righttoleft=righttoleft), tempfile.TemporaryDirectory() as workspace:
                source = Path(workspace) / self.source.name
                source.write_bytes(self.source.read_bytes())
                layout = list(comic2ebook.spread_label_pages(workspace, righttoleft, split=True))
                pages = [(file, box) for file, boxes in layout for box in boxes]
                groups, _ = output_groups(pages, set())
                preview = [preview_page(pieces, righttoleft).getpixel((0, 0)) for pieces in groups[source]]
                comic2ebook.split_pages_for_labeling(layout)
                actual = []
                for file in sorted(Path(workspace).glob('*.png')):
                    with Image.open(file) as page:
                        actual.append(page.getpixel((0, 0)))
                self.assertEqual(preview, expected)
                self.assertEqual(actual, expected)

    def test_compare_obeys_reading_direction_for_a_cross_source_join(self):
        second = self.path / 'kcc-0002.png'
        Image.new('RGB', (120, 240), 'green').save(second)
        first_box = (0, 0, 320, 240)
        second_box = (0, 0, 120, 240)
        pieces = ((self.source, first_box), (second, second_box))
        self.assertEqual(preview_page(pieces, False).getpixel((0, 0)), (255, 0, 0))
        self.assertEqual(preview_page(pieces, True).getpixel((0, 0)), (0, 128, 0))

    def test_rtl_preview_rejoins_in_original_visual_order(self):
        pages = [(source, box) for source, boxes in self.layout() for box in boxes]
        groups, joined = output_groups(pages, {0})
        self.assertFalse(joined)
        page = preview_page(groups[self.source][0], True)
        self.assertEqual(page.getpixel((10, 10)), (255, 0, 0))
        self.assertEqual(page.getpixel((310, 10)), (0, 0, 255))


if __name__ == '__main__':
    unittest.main()
