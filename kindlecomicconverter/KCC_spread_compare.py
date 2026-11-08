"""Compare original images with a spread-only layout preview for queued books."""

from collections import defaultdict
from contextlib import ExitStack
from copy import copy
from pathlib import Path
from shutil import rmtree

from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6.QtCore import QSignalBlocker, QTimer, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QComboBox, QDialog, QHBoxLayout, QLabel, QMessageBox, QScrollArea, QVBoxLayout, QWidget

from . import comic2ebook, image


CARD_WIDTH = 320
THUMB_HEIGHT = 148


def output_groups(pages, spread_indices):
    """Anchor each resulting page to the source of its first piece in reading order."""
    groups = defaultdict(list)
    joined_from_previous = set()
    index = 0
    while index < len(pages):
        first = pages[index]
        if index in spread_indices:
            second = pages[index + 1]
            groups[first[0]].append((first, second))
            if first[0] != second[0]:
                joined_from_previous.add(second[0])
            index += 2
        else:
            groups[first[0]].append((first,))
            index += 1
    return groups, joined_from_previous


def preview_page(pieces, righttoleft):
    """Crop or join source pieces using the same composition as conversion."""
    images = []
    for path, box in pieces:
        with Image.open(path) as original:
            images.append(original.crop(box))
    if len(images) == 1:
        return images[0]
    left, right = image.spread_visual_order(*images, righttoleft)
    return image.join_spread(left, right)


def add_thumbnail(layout, page, caption, width):
    thumb = page.convert('RGB')
    thumb.thumbnail((width, THUMB_HEIGHT), Image.Resampling.LANCZOS)
    label = QLabel()
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setPixmap(QPixmap.fromImage(ImageQt(thumb)))
    title = QLabel(caption)
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    column = QVBoxLayout()
    column.addWidget(label)
    column.addWidget(title)
    layout.addLayout(column)


def comparison_panel(sources, groups, joined_from_previous, split_sources, righttoleft, notice=None):
    panel = QWidget()
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(0, 0, 0, 0)
    if notice:
        warning = QLabel(notice)
        warning.setWordWrap(True)
        layout.addWidget(warning)

    def make_row(title):
        layout.addWidget(QLabel(title))
        scroll = QScrollArea()
        # The comparison always reads as a left-to-right strip of source columns.
        # Reading direction changes the generated pages, not the scroll position.
        scroll.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        strip = QWidget()
        strip.setFixedSize(CARD_WIDTH * len(sources), 200)
        scroll.setWidget(strip)
        layout.addWidget(scroll)
        return scroll, strip

    before, before_strip = make_row('BEFORE  ·  Original images')
    after, after_strip = make_row('AFTER  ·  Spread layout')
    before.horizontalScrollBar().valueChanged.connect(after.horizontalScrollBar().setValue)
    after.horizontalScrollBar().valueChanged.connect(before.horizontalScrollBar().setValue)
    rendered = set()
    output_offsets = {}
    next_page = 1
    for source in sources:
        output_offsets[source] = next_page
        next_page += len(groups[source])

    def card(strip, index, title):
        widget = QWidget(strip)
        widget.setGeometry(index * CARD_WIDTH, 0, CARD_WIDTH, 200)
        box = QVBoxLayout(widget)
        box.setContentsMargins(8, 2, 8, 2)
        box.addWidget(QLabel(title))
        row = QHBoxLayout()
        box.addLayout(row)
        widget.show()
        return row

    def draw_visible():
        # Decode only visible columns so opening the comparison stays lightweight.
        left = before.horizontalScrollBar().value()
        first = left // CARD_WIDTH
        last = min(len(sources), (left + before.viewport().width()) // CARD_WIDTH + 1)
        for index in range(first, last):
            if index in rendered:
                continue
            rendered.add(index)
            source = sources[index]
            top = card(before_strip, index, f'Source {index + 1}')
            try:
                with Image.open(source) as original:
                    add_thumbnail(top, original, 'Original', CARD_WIDTH - 20)
            except OSError:
                top.addWidget(QLabel('Could not load this image.'))
            title = f'From source {index + 1}'
            if source in joined_from_previous:
                title += '  ·  Joined to previous'
            bottom = card(after_strip, index, title)
            # Show separate output pages in CBZ file order from left to right.
            # Virtual page bounds already account for reading direction.
            pieces_list = groups[source]
            if not pieces_list:
                bottom.addWidget(QLabel('No separate page'))
                continue
            width = (CARD_WIDTH - 24) // len(pieces_list)
            for page_number, pieces in enumerate(pieces_list, output_offsets[source]):
                caption = 'Joined' if len(pieces) == 2 else 'Split' if source in split_sources else 'Whole'
                try:
                    add_thumbnail(bottom, preview_page(pieces, righttoleft), f'{page_number} · {caption}', width)
                except OSError:
                    bottom.addWidget(QLabel('Could not load this preview.'))

    timer = QTimer(panel)
    timer.setSingleShot(True)
    timer.timeout.connect(draw_visible)
    before.horizontalScrollBar().valueChanged.connect(lambda _: timer.start(40))
    before.horizontalScrollBar().rangeChanged.connect(lambda *_: timer.start(40))
    timer.start(0)
    return panel


def prepare_book(source, options, split_default, cleanup):
    label_path = source.with_name(source.name + '.json')
    data = comic2ebook.read_spread_labels(label_path) if label_path.is_file() else None
    notice = None
    if data is not None and data.get('righttoleft', options.righttoleft) != options.righttoleft:
        direction = 'RTL' if options.righttoleft else 'LTR'
        notice = f'Showing {direction} without saved joins. The labels use the other direction. Run Label Spreads again to apply joins in {direction}.'
        data = None
    split = data.get('split_before_labeling', False) if data is not None else split_default
    # The profile is used only if the source needs PDF extraction.
    extraction_options = copy(options)
    extraction_options.tempdir = False
    workdir = comic2ebook.getWorkFolder(str(source), extraction_options)
    cleanup.callback(rmtree, workdir, True)
    path = Path(workdir, 'OEBPS', 'Images')
    comic2ebook.removeNonImages(path)
    comic2ebook.sanitizeTree(path, extraction_options)
    comic2ebook.flattenTree(path)
    sources_and_boxes = list(comic2ebook.spread_label_pages(path, options.righttoleft, split))
    sources = [file for file, _ in sources_and_boxes]
    pages = [(file, box) for file, boxes in sources_and_boxes for box in boxes]
    if data is not None:
        comic2ebook.validate_spread_labels(data, sources_and_boxes, options.righttoleft)
    spreads = set(data['spreads']) if data is not None else set()
    groups, joined = output_groups(pages, spreads)
    split_sources = {file for file, boxes in sources_and_boxes if len(boxes) > 1}
    return sources, groups, joined, split_sources, notice


def show_comparison(window, sources, options, split_default):
    try:
        options = comic2ebook.checkOptions(copy(options))
    except UserWarning as error:
        QMessageBox.warning(window, 'Compare Before / After', str(error))
        return
    dialog = QDialog(window)
    direction = 'RTL' if options.righttoleft else 'LTR'
    dialog.setWindowTitle(f'Before and after — spread layout · {direction}')
    dialog.resize(1120, 560)
    layout = QVBoxLayout(dialog)
    picker = QComboBox()
    for index, source in enumerate(sources, 1):
        picker.addItem(f'{index}/{len(sources)}  {source.name}')
        picker.setItemData(index - 1, str(source), Qt.ItemDataRole.ToolTipRole)
    layout.addWidget(picker)
    layout.addWidget(QLabel(f'{direction} page output · Scroll either row to move both. The lower row shows output pages in numbered file order.'))
    panel = None
    cache = {}
    displayed = None

    with ExitStack() as cleanup:
        def select_book(index):
            nonlocal panel, displayed
            try:
                if index not in cache:
                    # Cache extracted sources for this dialog only. Each book uses its own sidecar.
                    cache[index] = prepare_book(sources[index], options, split_default, cleanup)
                originals, groups, joined, split_sources, notice = cache[index]
                new_panel = comparison_panel(originals, groups, joined, split_sources, options.righttoleft, notice)
                if panel is not None:
                    layout.removeWidget(panel)
                    panel.deleteLater()
                panel = new_panel
                layout.addWidget(panel)
                displayed = index
            except (OSError, RuntimeError, ValueError, UserWarning) as error:
                QMessageBox.warning(dialog, 'Compare Before / After', str(error))
                if displayed is None:
                    dialog.reject()
                else:
                    with QSignalBlocker(picker):
                        picker.setCurrentIndex(displayed)

        picker.currentIndexChanged.connect(select_book)
        QTimer.singleShot(0, lambda: select_book(picker.currentIndex()))
        dialog.exec()
