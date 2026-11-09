"""Interactive spread review, including pending suggestions and batch edits."""

from PySide6.QtCore import QEvent, QTimer, Qt
from PySide6.QtGui import QBrush, QColor, QKeySequence, QPainter, QPen, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QHBoxLayout, QLabel, QListWidget,
    QMessageBox, QSizePolicy, QVBoxLayout, QWidget,
)


def choose_automatic_merges(candidates):
    """Choose the highest-scoring set of adjacent pairs without reusing pages."""
    pairs = sorted(candidates)
    scores = [0] * (len(pairs) + 1)
    take = [False] * len(pairs)
    following = [0] * len(pairs)
    for index in range(len(pairs) - 1, -1, -1):
        pair = pairs[index]
        next_index = index + 1
        if next_index < len(pairs) and pairs[next_index] == pair + 1:
            next_index += 1
        following[index] = next_index
        join_score = candidates[pair] + scores[next_index]
        take[index] = join_score >= scores[index + 1]
        scores[index] = join_score if take[index] else scores[index + 1]

    chosen = set()
    index = 0
    while index < len(pairs):
        if take[index]:
            chosen.add(pairs[index])
            index = following[index]
        else:
            index += 1
    return chosen


class LabelSpreadsDialog(QDialog):
    def __init__(self, available_height, pairs, spreads, load_preview, classify, names, splits, settings=None,
                 *, merge_only=False, spread_shift=False):
        super().__init__()
        # The caller owns these sets and saves them only after the dialog is accepted.
        # Automatic classifications live separately and never modify either set.
        self.spreads = spreads
        self.splits = splits
        self.load_preview = load_preview
        self.classify = classify
        self.names = names
        self.merge_only = merge_only
        self.manual_shift = spread_shift
        self.kinds = {}
        self.alternate_pending = iter(())
        self.shift_hint = False
        self.pending = iter(pairs)
        self.pairs = list(pairs)
        self.visible_pairs = []
        self.active_range = None
        self.last_edit = None
        self.preview_height = max(100, int(available_height * 0.68))
        self.preview_width = 680
        self.pixmap = None
        self.seam = 0

        layout = QVBoxLayout(self)
        body = QHBoxLayout()
        layout.addLayout(body)
        sidebar_widget = QWidget()
        sidebar_widget.setFixedWidth(218)
        sidebar = QVBoxLayout(sidebar_widget)
        sidebar.setContentsMargins(0, 0, 0, 0)
        body.addWidget(sidebar_widget)
        self.group = QComboBox()
        self.group.addItems(['Sort by filename', 'Sort by operation'])
        if settings is not None:
            self.group.setCurrentIndex(int(settings.value('spreadReviewByOperation', False, type=bool)))
            self.group.currentIndexChanged.connect(
                lambda index: settings.setValue('spreadReviewByOperation', index == 1)
            )
        sidebar.addWidget(self.group)
        self.files = QListWidget()
        self.files.setUniformItemSizes(True)
        self.files.setStyleSheet("""
            QListWidget::item:selected {
                background-color: #0067c5;
                color: white;
            }
        """)
        self.files.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.files.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.files.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        sidebar.addWidget(self.files)
        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.preview.setMinimumSize(220, 200)
        preview_column = QVBoxLayout()
        body.addLayout(preview_column, 1)
        preview_column.addWidget(self.preview, 1)
        self.decision = QLabel()
        self.decision.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.decision.setToolTip('Backspace clears the confirmation on this pair or the selected range.')
        decision_font = self.decision.font()
        decision_font.setPointSize(decision_font.pointSize() + 4)
        decision_font.setBold(True)
        self.decision.setFont(decision_font)
        preview_column.addWidget(self.decision)
        shortcut_hint = QLabel(
            'Arrows Browse   ·   Space Toggle   ·   M Merge   ·   R Select a range   ·   U Undo   ·   Enter Save'
        )
        shortcut_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shortcut_hint.setWordWrap(True)
        preview_column.addWidget(shortcut_hint)
        self.resize(920, self.preview_height + 120)

        self.shift_banner = QLabel()
        self.shift_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.shift_banner.setWordWrap(True)
        banner_font = self.shift_banner.font()
        banner_font.setPointSize(banner_font.pointSize() + 4)
        banner_font.setBold(True)
        self.shift_banner.setFont(banner_font)
        self.shift_banner.setStyleSheet(
            'background-color: rgba(176, 132, 64, 55);'
            'border: 1px solid rgba(176, 132, 64, 130);'
            'border-radius: 5px; padding: 8px;'
        )
        self.shift_banner.hide()
        layout.insertWidget(0, self.shift_banner)
        controls = QHBoxLayout()
        layout.insertLayout(1, controls)
        self.full_page = QCheckBox('Show full pages')
        self.full_page.setToolTip('Show artwork outside the seam strips. May reveal spoilers.')
        self.full_page.toggled.connect(self.show_pair)
        controls.addWidget(self.full_page)
        self.pairing_box = QComboBox()
        self.pairing_box.addItems(['Spread Shift off', 'Spread Shift on', 'Auto pairing'])
        self.pairing_box.setCurrentIndex(int(spread_shift))
        self.pairing_box.setToolTip(
            'Auto pairing suggests non-overlapping merges from both alignments. '
            'The manual views let you inspect either alignment.'
        )
        controls.addWidget(self.pairing_box)
        self.pairing_box.currentIndexChanged.connect(self.change_pairing)
        controls.addStretch(1)
        footer = QHBoxLayout()
        layout.addLayout(footer)
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.counter = QLabel()
        footer.addWidget(self.status, 1)
        footer.addWidget(self.counter)
        self.group.currentIndexChanged.connect(lambda _: self.refresh_list())
        self.files.currentRowChanged.connect(self.show_pair)
        self.files.itemSelectionChanged.connect(self.update_status)

        self.shortcuts = []
        for sequence, action in (
            ('M', lambda: self.mark_selection(merge=True)), ('R', self.toggle_range), ('U', self.undo),
            ('Return', self.save), ('Enter', self.save),
        ):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setAutoRepeat(False)
            shortcut.activated.connect(action)
            self.shortcuts.append(shortcut)

        for widget in (self, self.files, self.files.viewport(), self.group, self.full_page, self.pairing_box):
            widget.installEventFilter(self)
        self.files.setFocus()

        self.finished_scan = False
        self.keep_scan_position = False
        self.reorder_pending = False
        self.scan = QTimer(self)
        self.scan.setInterval(1)
        self.scan.timeout.connect(self.scan_pair)
        self.finished.connect(lambda _: self.scan.stop())
        self.refresh_list()
        self.scan.start()

    def automatic_pairing(self):
        return self.pairing_box.currentIndex() == 2

    def change_pairing(self, mode):
        callback = getattr(self, 'shift_changed_callback', None)
        if callback is None:
            return
        if mode == 2:
            # Pair IDs are the same virtual page indices in either alignment.
            off, off_names = callback(False)
            on, on_names = callback(True)
            pairs, names = sorted([*off, *on]), {**off_names, **on_names}
        else:
            self.manual_shift = bool(mode)
            pairs, names = callback(self.manual_shift)

        self.scan.stop()
        self.shift_hint = False
        self.pairs = list(pairs)
        self.names = names
        # Pair IDs are stable across alignments. Reuse completed classifications
        # when switching back and scan only the pairs that are still unknown.
        remaining = [pair for pair in self.pairs if pair not in self.kinds]
        self.pending = iter(remaining)
        self.finished_scan = not remaining
        self.keep_scan_position = True
        self.reorder_pending = False

        self.refresh_list()
        if remaining:
            self.scan.start()
        else:
            self.check_other_alignment()
            self.update_status()

    def check_other_alignment(self):
        # Share the existing timer and cache. After the visible list is ready,
        # the alternate scan stops as soon as it finds an actionable suggestion.
        self.scan.stop()
        self.shift_hint = False
        callback = getattr(self, 'shift_changed_callback', None)
        if callback is None or self.automatic_pairing():
            return
        other_pairs, _ = callback(not self.manual_shift)
        self.shift_hint = any(self.row_status(pair) == 'Suggested merge' for pair in other_pairs)
        if not self.shift_hint:
            remaining = [pair for pair in other_pairs if self.row_status(pair) == 'Checking']
            self.alternate_pending = iter(remaining)
            if remaining:
                self.scan.start()

    def classify_pair(self, pair):
        try:
            self.kinds[pair] = self.classify(pair)
        except OSError:
            self.kinds[pair] = 'review'

    def scan_other_alignment(self):
        pair = next(self.alternate_pending, None)
        if pair is None:
            self.scan.stop()
            return
        self.classify_pair(pair)
        if self.row_status(pair) == 'Suggested merge':
            self.shift_hint = True
            self.scan.stop()
            self.update_status()

    def scan_pair(self):
        # Check one pair per timer tick so the reviewer can browse while sorting.
        if self.finished_scan:
            self.scan_other_alignment()
            return
        pair = next(self.pending, None)
        if pair is None:
            self.scan.stop()
            self.finished_scan = True
            if self.group.currentIndex() or self.merge_only or self.automatic_pairing():
                if self.active_range is None:
                    self.refresh_list(start_at_top=bool(self.group.currentIndex()) and not self.keep_scan_position)
                else:
                    self.reorder_pending = True
            self.check_other_alignment()
            self.update_status()
            return
        self.classify_pair(pair)
        if pair in self.rows:
            self.update_row(pair)
        if pair == self.current_pair():
            self.draw_preview()
        self.update_status()

    def eventFilter(self, watched, event):
        # Handle browse and mark keys before focused list and checkbox widgets consume them.
        if event.type() in (QEvent.Type.ShortcutOverride, QEvent.Type.KeyPress):
            key = event.key()
            modifiers = event.modifiers() & ~Qt.KeyboardModifier.KeypadModifier
            if key in (Qt.Key.Key_Space, Qt.Key.Key_Backspace, Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down) and not modifiers:
                if event.type() == QEvent.Type.KeyPress:
                    if key == Qt.Key.Key_Space:
                        if not event.isAutoRepeat():
                            self.mark_selection()
                    elif key == Qt.Key.Key_Backspace:
                        if not event.isAutoRepeat():
                            self.clear_confirmation()
                    else:
                        self.move(-1 if key in (Qt.Key.Key_Left, Qt.Key.Key_Up) else 1)
                event.accept()
                return True
        return super().eventFilter(watched, event)

    def current_pair(self):
        row = self.files.currentRow()
        return self.visible_pairs[row] if 0 <= row < len(self.visible_pairs) else None

    def row_status(self, pair):
        if pair in self.spreads:
            return 'Merged'
        if pair in self.splits:
            return 'Split'
        if self.overlaps_merge(pair):
            return 'Overlaps merge'
        # An adjacent split marks a different seam. Show the overlap without
        # blocking a join that preserves the confirmed split boundary.
        if pair - 1 in self.splits or pair + 1 in self.splits:
            return 'Overlaps split'
        return {
            None: 'Checking', 'split': 'Suggested split', 'full': 'Suggested merge',
            'panel': 'Suggested merge', 'review': 'Needs review',
        }[self.kinds.get(pair)]

    def operation_group(self, pair):
        status = self.row_status(pair)
        if status == 'Needs review':
            return 0
        if status in ('Merged', 'Suggested merge'):
            return 1
        if status in ('Split', 'Suggested split'):
            return 2
        if status in ('Overlaps merge', 'Overlaps split'):
            return 3
        return 4

    def update_row(self, pair):
        item = self.files.item(self.rows[pair])
        status = self.row_status(pair)
        filename = self.names[pair].split('  ', 1)[-1].split(' + ', 1)[0]
        item.setText(f'{status}  ·  {filename}')
        if status in ('Overlaps merge', 'Overlaps split'):
            item.setBackground(QBrush(QColor(190, 70, 70, 36)))
        elif status in ('Merged', 'Split'):
            item.setBackground(QBrush(QColor(55, 145, 90, 36)))
        else:
            item.setBackground(QBrush())
        kind = self.kinds.get(pair)
        detail = {'full': ' · Likely full-page spread', 'panel': ' · Likely panel spread'}.get(kind, '')
        item.setToolTip(f'{self.names[pair]}\n{status}{detail}')

    def selected_pairs(self):
        return {self.visible_pairs[index.row()] for index in self.files.selectedIndexes()}

    def review_pairs(self):
        # Keep the list stable while checking pairs or selecting a range.
        # In merge-only review, an unmarked pair is already separate.
        if self.automatic_pairing():
            confirmed = self.spreads | self.splits
            candidates = {
                pair: 2 if self.kinds[pair] == 'full' else 1
                for pair in self.pairs if self.row_status(pair) == 'Suggested merge'
            } if self.finished_scan else {}
            suggested = choose_automatic_merges(candidates)
            return [pair for pair in self.pairs if pair in confirmed or pair in suggested]
        if not self.merge_only or not self.finished_scan:
            return list(self.pairs)
        return [pair for pair in self.pairs if self.row_status(pair) in ('Suggested merge', 'Merged', 'Split')]

    def refresh_list(self, *, start_at_top=False):
        current = None if start_at_top else self.current_pair()
        selected = set() if start_at_top else self.selected_pairs()
        self.active_range = None
        self.reorder_pending = False
        self.visible_pairs = self.review_pairs()
        if self.group.currentIndex():
            self.operation_groups = {pair: self.operation_group(pair) for pair in self.visible_pairs}
            self.visible_pairs.sort(key=self.operation_groups.__getitem__)
        self.rows = {pair: row for row, pair in enumerate(self.visible_pairs)}
        self.files.blockSignals(True)
        self.files.clear()
        self.files.addItems([''] * len(self.visible_pairs))
        for pair in self.visible_pairs:
            self.update_row(pair)
        if current is not None and current not in self.rows and self.visible_pairs:
            current = min(self.visible_pairs, key=lambda pair: abs(pair - current))
        row = self.rows.get(current, 0)
        self.files.setCurrentRow(row)
        for pair in selected.intersection(self.rows):
            self.files.item(self.rows[pair]).setSelected(True)
        self.files.blockSignals(False)
        self.show_pair(row)

    def show_pair(self, _row):
        pair = self.current_pair()
        self.pixmap = None
        if pair is not None:
            try:
                pixmap, seam = self.load_preview(pair, self.full_page.isChecked())
                width = max(220, min(self.preview_width, self.width() - 250))
                self.pixmap = pixmap.scaled(width, self.preview_height, Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation)
                self.seam = round(seam * self.pixmap.width() / pixmap.width())
            except OSError:
                self.preview.setText('Could not load this pair.')
                self.decision.clear()
                self.update_status()
                return
        self.draw_preview()
        self.update_status()

    def draw_preview(self):
        if self.pixmap is None:
            self.preview.setText('No pairs need review.' if self.finished_scan else 'Checking pairs…')
            self.decision.clear()
            return
        pair = self.current_pair()
        split = pair in self.splits or (pair not in self.spreads and self.kinds.get(pair) == 'split')
        pixmap = self.pixmap
        if split:
            pixmap = pixmap.copy()
            painter = QPainter(pixmap)
            painter.setPen(QPen(QColor('#f23838'), 3, Qt.PenStyle.DashLine))
            painter.drawLine(self.seam, 0, self.seam, pixmap.height())
            painter.end()
        self.preview.setPixmap(pixmap)
        if pair in self.spreads:
            decision = 'Merged'
        elif pair in self.splits:
            decision = 'Split'
        else:
            decision = self.row_status(pair)
        self.decision.setText(decision)

    def update_status(self):
        if self.active_range is not None:
            start, merge = self.active_range
            count = len(self.range_pairs(start))
            self.status.setText(f'{"Merge" if merge else "Split"} range · {count} pairs · R to apply')
        else:
            pair = self.current_pair()
            status = self.row_status(pair) if pair is not None else ''
            count = len(self.selected_pairs())
            if count > 1:
                status = f'{count} pairs selected'
            self.status.setText(f'{status}   ·   {len(self.spreads)} confirmed merges · {len(self.splits)} confirmed splits')
        if self.shift_hint:
            other = 'off' if self.manual_shift else 'on'
            self.shift_banner.setText(f'Likely merges found with Spread Shift {other}')
        self.shift_banner.setVisible(self.shift_hint)
        total = len(self.visible_pairs)
        position = max(0, self.files.currentRow() + 1)
        self.counter.setText(f'{position} / {total} pairs')

    def move(self, step):
        row = self.files.currentRow() + step
        if 0 <= row < len(self.visible_pairs):
            self.files.clearSelection()
            self.files.setCurrentRow(row)

    def overlaps_merge(self, pair):
        # A pair is identified by its first page. An adjacent pair shares one page.
        return pair - 1 in self.spreads or pair + 1 in self.spreads

    def apply(self, pairs, merge):
        if merge and any(self.overlaps_merge(pair) or pair + 1 in pairs for pair in pairs):
            self.status.setText('A page is already in a confirmed merge. Switch alignment and split that pair first.')
            return False
        self.last_edit = (self.spreads.copy(), self.splits.copy())
        self.spreads.difference_update(pairs)
        self.splits.difference_update(pairs)
        if merge is not None:
            (self.spreads if merge else self.splits).update(pairs)
        self.update_rows()
        return True

    def update_rows(self):
        if self.finished_scan:
            self.check_other_alignment()
        if self.active_range is None and set(self.visible_pairs) != set(self.review_pairs()):
            self.refresh_list()
            return
        for pair in self.visible_pairs:
            self.update_row(pair)
        self.draw_preview()
        self.update_status()

    def mark_selection(self, merge=None):
        pair = self.current_pair()
        if pair is None:
            return
        if merge is None:
            suggested_merge = pair not in self.splits and self.kinds.get(pair) in ('full', 'panel')
            merge = pair not in self.spreads and not suggested_merge
        self.apply(self.selected_pairs() or {pair}, merge)

    def range_pairs(self, start):
        # A range in operation order stays within its starting category.
        first, last = sorted((start, self.files.currentRow()))
        pairs = self.visible_pairs[first:last + 1]
        if self.group.currentIndex() == 1 and self.finished_scan and not self.reorder_pending:
            kind = self.operation_groups[self.visible_pairs[start]]
            pairs = [pair for pair in pairs if self.operation_groups[pair] == kind]
        return set(pairs)

    def toggle_range(self):
        pair = self.current_pair()
        if pair is None:
            return
        row = self.files.currentRow()
        if self.active_range is None:
            merge = pair in self.spreads or (pair not in self.splits and self.kinds.get(pair) != 'split')
            self.active_range = row, merge
        else:
            start, merge = self.active_range
            self.active_range = None
            if not self.apply(self.range_pairs(start), merge):
                return
            if self.reorder_pending:
                self.refresh_list(start_at_top=not self.keep_scan_position)
        self.update_status()

    def clear_confirmation(self):
        # Clearing uses the same undo snapshot as an explicit merge or split.
        pair = self.current_pair()
        if pair is None:
            return
        pairs = self.selected_pairs() or {pair}
        if self.active_range is not None:
            start, _ = self.active_range
            pairs = self.range_pairs(start)
            self.active_range = None
        if pairs.intersection(self.spreads | self.splits):
            self.apply(pairs, merge=None)
        if self.reorder_pending:
            self.refresh_list(start_at_top=not self.keep_scan_position)
        self.update_status()

    def undo(self):
        if self.last_edit is None:
            return
        spreads, splits = self.last_edit
        self.last_edit = None
        self.active_range = None
        self.spreads.clear()
        self.spreads.update(spreads)
        self.splits.clear()
        self.splits.update(splits)
        self.update_rows()

    def save(self):
        # Suggestions stay pending unless the user explicitly accepts them here.
        if self.active_range is not None:
            self.status.setText('Press R to apply the selected range before saving.')
            return
        # Hidden pairs and overlaps are not actionable suggestions in this view.
        pending = {pair for pair in self.visible_pairs if self.row_status(pair) == 'Suggested merge'}
        if pending or not self.finished_scan:
            prompt = QMessageBox(self)
            prompt.setWindowTitle('Save spread labels')
            if self.finished_scan:
                prompt.setText(
                    f'{len(self.spreads)} confirmed merges saved across both alignments. '
                    f'{len(pending)} suggested merges still pending in this view.'
                )
            else:
                prompt.setText('KCC is still checking pairs. Save the decisions you have marked or keep reviewing.')
            confirmed = prompt.addButton('Save confirmed only', QMessageBox.ButtonRole.AcceptRole)
            include = None
            if self.finished_scan:
                include = prompt.addButton('Confirm suggestions in this view', QMessageBox.ButtonRole.ActionRole)
            prompt.addButton(QMessageBox.StandardButton.Cancel)
            prompt.setDefaultButton(confirmed)
            prompt.exec()
            if include is not None and prompt.clickedButton() == include:
                self.spreads.update(pending)
            elif prompt.clickedButton() != confirmed:
                return
        self.accept()
