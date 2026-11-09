"""Interactive spread review, including pending suggestions and batch edits."""

from PySide6.QtCore import QEvent, QTimer, Qt
from PySide6.QtGui import QColor, QKeySequence, QPainter, QPen, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QHBoxLayout, QLabel, QListWidget,
    QMessageBox, QSizePolicy, QVBoxLayout, QWidget,
)


class LabelSpreadsDialog(QDialog):
    def __init__(self, available_height, pairs, spreads, load_preview, classify, names, splits, settings=None):
        super().__init__()
        # The caller owns these sets and saves them only after the dialog is accepted.
        # Automatic classifications live separately and never modify either set.
        self.spreads = spreads
        self.splits = splits
        self.load_preview = load_preview
        self.classify = classify
        self.names = names
        self.kinds = {}
        self.pending = iter(pairs)
        self.pairs = list(pairs)
        self.visible_pairs = []
        self.run = None
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
        self.group.addItems(['By filename', 'By operation'])
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
        decision_font = self.decision.font()
        decision_font.setPointSize(decision_font.pointSize() + 4)
        decision_font.setBold(True)
        self.decision.setFont(decision_font)
        preview_column.addWidget(self.decision)
        self.resize(920, self.preview_height + 120)

        controls = QHBoxLayout()
        layout.addLayout(controls)
        self.full_page = QCheckBox('Show full pages')
        self.full_page.setToolTip('Show artwork outside the seam strips. May reveal spoilers.')
        self.full_page.toggled.connect(self.show_pair)
        controls.addWidget(self.full_page)
        self.spread_shift_box = QCheckBox('Spread Shift')
        self.spread_shift_box.setToolTip(
            'Shift the starting page of each spread pair.'
        )
        controls.addWidget(self.spread_shift_box)
        self.spread_shift_box.toggled.connect(self.change_spread_shift)
        controls.addWidget(QLabel('Arrows Browse   ·   Space Toggle   ·   M Merge   ·   Shift-click Range   ·   R Run   ·   U Undo   ·   Enter Save'), 1)
        footer = QHBoxLayout()
        layout.addLayout(footer)
        self.status = QLabel()
        self.counter = QLabel()
        footer.addWidget(self.status, 1)
        footer.addWidget(self.counter)
        self.group.currentIndexChanged.connect(lambda _: self.refresh_list())
        self.files.currentRowChanged.connect(self.show_pair)
        self.files.itemSelectionChanged.connect(self.update_status)

        self.shortcuts = []
        for sequence, action in (
            ('M', lambda: self.mark_selection(merge=True)), ('R', self.toggle_run), ('U', self.undo),
            ('Return', self.save), ('Enter', self.save),
        ):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setAutoRepeat(False)
            shortcut.activated.connect(action)
            self.shortcuts.append(shortcut)

        for widget in (self, self.files, self.files.viewport(), self.group, self.full_page):
            widget.installEventFilter(self)
        self.files.setFocus()

        self.finished_scan = False
        self.reorder_pending = False
        self.scan = QTimer(self)
        self.scan.setInterval(1)
        self.scan.timeout.connect(self.scan_pair)
        self.finished.connect(lambda _: self.scan.stop())
        self.refresh_list()
        self.scan.start()

    def change_spread_shift(self, enabled):
        callback = getattr(self, "shift_changed_callback", None)
        if callback is None:
            return

        try:
            pairs, names, spreads, splits = callback(enabled)
        except Exception as error:
            self.spread_shift_box.blockSignals(True)
            self.spread_shift_box.setChecked(not enabled)
            self.spread_shift_box.blockSignals(False)
            QMessageBox.warning(self, "Spread Shift", str(error))
            return

        self.scan.stop()
        self.pairs = list(pairs)
        self.names = names
        self.spreads = spreads
        self.splits = splits
        self.kinds = {}
        self.pending = iter(self.pairs)
        self.finished_scan = False
        self.reorder_pending = False
        self.last_edit = None
        self.run = None
        self.pixmap = None

        self.refresh_list(start_at_top=True)
        self.scan.start()

        # Commit the alignment only after the viewer has refreshed.
        confirmed = getattr(self, "shift_confirmed_callback", None)
        if confirmed is not None:
            confirmed(enabled)

    def scan_pair(self):
        # Check one pair per timer tick so the reviewer can browse while sorting.
        pair = next(self.pending, None)
        if pair is None:
            self.scan.stop()
            self.finished_scan = True
            if self.group.currentIndex():
                if self.run is None:
                    self.refresh_list(start_at_top=True)
                else:
                    self.reorder_pending = True
            self.update_status()
            return
        try:
            self.kinds[pair] = self.classify(pair)
        except OSError:
            self.kinds[pair] = 'review'
        self.update_row(pair)
        if pair == self.current_pair():
            self.draw_preview()
        self.update_status()

    def eventFilter(self, watched, event):
        # Handle browse and mark keys before focused list and checkbox widgets consume them.
        if event.type() in (QEvent.Type.ShortcutOverride, QEvent.Type.KeyPress):
            key = event.key()
            modifiers = event.modifiers() & ~Qt.KeyboardModifier.KeypadModifier
            if key in (Qt.Key.Key_Space, Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down) and not modifiers:
                if event.type() == QEvent.Type.KeyPress:
                    if key == Qt.Key.Key_Space:
                        if not event.isAutoRepeat():
                            self.mark_selection()
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
        return {
            None: 'Checking', 'split': 'Suggested split', 'full': 'Suggested merge',
            'panel': 'Suggested merge', 'review': 'Needs review',
        }[self.kinds.get(pair)]

    def update_row(self, pair):
        item = self.files.item(self.rows[pair])
        status = self.row_status(pair)
        filename = self.names[pair].split('  ', 1)[-1].split(' + ', 1)[0]
        item.setText(f'{status}  ·  {filename}')
        kind = self.kinds.get(pair)
        detail = {'full': ' · Likely full-page spread', 'panel': ' · Likely panel spread'}.get(kind, '')
        item.setToolTip(f'{self.names[pair]}\n{status}{detail}')

    def refresh_list(self, *, start_at_top=False):
        current = None if start_at_top else self.current_pair()
        selected = set() if start_at_top else {
            self.visible_pairs[index.row()] for index in self.files.selectedIndexes()
        }
        self.run = None
        self.reorder_pending = False
        self.visible_pairs = list(self.pairs)
        if self.group.currentIndex() and self.finished_scan:
            order = {'review': 0, 'full': 1, 'panel': 2, 'split': 3}
            self.visible_pairs.sort(key=lambda pair: order[self.kinds[pair]])
        self.rows = {pair: row for row, pair in enumerate(self.visible_pairs)}
        self.files.blockSignals(True)
        self.files.clear()
        self.files.addItems([''] * len(self.visible_pairs))
        for pair in self.visible_pairs:
            self.update_row(pair)
        row = self.rows.get(current, 0)
        self.files.setCurrentRow(row)
        for pair in selected:
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
            self.preview.setText('No pairs to review.' if self.finished_scan else 'Checking pairs…')
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
        if self.run is not None:
            start, merge = self.run
            count = len(self.run_pairs(start))
            self.status.setText(f'{"Merge" if merge else "Split"} run · {count} pairs · R to apply')
        else:
            count = len(self.files.selectedIndexes())
            pair = self.current_pair()
            status = self.row_status(pair) if pair is not None else ''
            self.status.setText(f'{count} selected · Space to mark' if count > 1 else
                                f'{status}   ·   {len(self.spreads)} confirmed merges · {len(self.splits)} confirmed splits')
        total = len(self.visible_pairs)
        position = max(0, self.files.currentRow() + 1)
        self.counter.setText(f'{position} / {total} pairs')

    def move(self, step):
        row = self.files.currentRow() + step
        if 0 <= row < len(self.visible_pairs):
            self.files.clearSelection()
            self.files.setCurrentRow(row)

    def apply(self, pairs, merge):
        self.last_edit = (self.spreads.copy(), self.splits.copy())
        self.spreads.difference_update(pairs)
        self.splits.difference_update(pairs)
        (self.spreads if merge else self.splits).update(pairs)
        self.update_rows()

    def update_rows(self):
        for pair in self.visible_pairs:
            self.update_row(pair)
        self.draw_preview()
        self.update_status()

    def mark_selection(self, merge=None):
        pair = self.current_pair()
        if pair is None:
            return
        pairs = {self.visible_pairs[index.row()] for index in self.files.selectedIndexes()} or {pair}
        if merge is None:
            suggested_merge = pair not in self.splits and self.kinds.get(pair) in ('full', 'panel')
            merge = pair not in self.spreads and not suggested_merge
        self.apply(pairs, merge)

    def run_pairs(self, start):
        # A keyboard run in operation order stays within its starting category.
        first, last = sorted((start, self.files.currentRow()))
        pairs = self.visible_pairs[first:last + 1]
        if self.group.currentIndex() == 1 and self.finished_scan and not self.reorder_pending:
            operation = {'review': 'review', 'full': 'merge', 'panel': 'merge', 'split': 'split'}
            kind = operation[self.kinds[self.visible_pairs[start]]]
            pairs = [pair for pair in pairs if operation[self.kinds[pair]] == kind]
        return set(pairs)

    def toggle_run(self):
        pair = self.current_pair()
        if pair is None:
            return
        row = self.files.currentRow()
        if self.run is None:
            merge = pair in self.spreads or (pair not in self.splits and self.kinds.get(pair) != 'split')
            self.run = row, merge
        else:
            start, merge = self.run
            self.run = None
            self.apply(self.run_pairs(start), merge)
            if self.reorder_pending:
                self.refresh_list(start_at_top=True)
        self.update_status()

    def undo(self):
        if self.last_edit is None:
            return
        spreads, splits = self.last_edit
        self.last_edit = None
        self.run = None
        self.spreads.clear()
        self.spreads.update(spreads)
        self.splits.clear()
        self.splits.update(splits)
        self.update_rows()

    def save(self):
        # Suggestions stay pending unless the user explicitly accepts them here.
        if self.run is not None:
            self.status.setText('Press R to apply the active run before saving.')
            return
        pending = {
            pair for pair, kind in self.kinds.items()
            if kind in ('full', 'panel') and pair not in self.spreads and pair not in self.splits
        }
        if pending or not self.finished_scan:
            prompt = QMessageBox(self)
            prompt.setWindowTitle('Save spread labels')
            if self.finished_scan:
                prompt.setText(f'{len(self.spreads)} confirmed merges · {len(pending)} pending merge suggestions')
            else:
                prompt.setText('KCC is still checking pairs. Save the decisions you have marked or keep reviewing.')
            confirmed = prompt.addButton('Save confirmed only', QMessageBox.ButtonRole.AcceptRole)
            include = None
            if self.finished_scan:
                include = prompt.addButton('Confirm suggested merges too', QMessageBox.ButtonRole.ActionRole)
            prompt.addButton(QMessageBox.StandardButton.Cancel)
            prompt.setDefaultButton(confirmed)
            prompt.exec()
            if include is not None and prompt.clickedButton() == include:
                self.spreads.update(pending)
            elif prompt.clickedButton() != confirmed:
                return
        self.accept()
