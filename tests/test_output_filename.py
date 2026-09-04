import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from kindlecomicconverter import comic2ebook


class GetOutputFilenameTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def get_output(self, source, *, profile="KoC", no_kepub=False, wanted_name=None, tome_number=""):
        # checkOptions sets folder_output for every run; only the FOLDER
        # format turns it on, and these cases are all EPUB.
        options = SimpleNamespace(
            profile=profile,
            format="EPUB",
            noKepub=no_kepub,
            output=wanted_name,
            folder_output=False,
        )
        with patch.object(comic2ebook, "options", options, create=True):
            return Path(comic2ebook.getOutputFilename(str(source), wanted_name, ".epub", tome_number))

    def test_kobo_epub_preserves_source_filename(self):
        cases = (
            ("One Piece - Chapter 4.cbz", False, "", "One Piece - Chapter 4.kepub.epub"),
            ("Vol.01 Ch.001 - Shinmen Takezo.cbz", False, "", "Vol.01 Ch.001 - Shinmen Takezo.kepub.epub"),
            ("One Piece - Chapter 4.cbz", True, "", "One Piece - Chapter 4.epub"),
            ("One Piece - Chapter 4.cbz", False, " 2", "One Piece - Chapter 4 2.kepub.epub"),
        )

        for source_name, no_kepub, tome_number, expected_name in cases:
            with self.subTest(source_name=source_name, no_kepub=no_kepub, tome_number=tome_number):
                source = self.root / source_name
                source.touch()
                output = self.get_output(source, no_kepub=no_kepub, tome_number=tome_number)

                self.assertEqual(output.name, expected_name)

    def test_non_kobo_filename_is_unchanged(self):
        source = self.root / "One Piece - Chapter 4.cbz"
        source.touch()

        output = self.get_output(source, profile="KV")

        self.assertEqual(output, source.with_suffix(".epub"))

    def test_explicit_output_file_is_unchanged(self):
        source = self.root / "One Piece - Chapter 4.cbz"
        source.touch()
        wanted_output = self.root / "Custom Kobo Name.kepub.epub"

        output = self.get_output(source, wanted_name=str(wanted_output))

        self.assertEqual(output, wanted_output)

    def test_explicit_output_directory_preserves_source_filename(self):
        source = self.root / "One Piece - Chapter 4.cbz"
        source.touch()
        output_directory = self.root / "output"
        output_directory.mkdir()

        output = self.get_output(source, wanted_name=str(output_directory))

        self.assertEqual(output, output_directory / "One Piece - Chapter 4.kepub.epub")

    def test_directory_source_behavior_is_unchanged(self):
        source = self.root / "One Piece - Chapter 4"
        source.mkdir()

        output = self.get_output(source)

        self.assertEqual(output, source.with_name("One Piece - Chapter 4.kepub.epub"))

    def test_existing_output_keeps_collision_suffix_behavior(self):
        source = self.root / "One Piece - Chapter 4.cbz"
        source.touch()
        existing_output = source.with_name("One Piece - Chapter 4.epub")
        existing_output.touch()

        output = self.get_output(source, no_kepub=True)

        self.assertEqual(output, source.with_name("One Piece - Chapter 4_kcc0.epub"))


if __name__ == "__main__":
    unittest.main()
