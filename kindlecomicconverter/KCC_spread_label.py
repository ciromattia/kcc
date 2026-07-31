import os

from PySide6.QtCore import (Qt)
from PySide6.QtGui import (QKeyEvent, QPixmap)
from PySide6.QtWidgets import (QDialogButtonBox, QHBoxLayout, QLabel, QDialog)

class CustomDialog(QDialog):
    def __init__(self, available_height, images, spreads):
        super().__init__()
        self.index = 0
        self.images = images 
        self.spreads = spreads
        self.index2page = {i: os.path.basename(image) for i, image in enumerate(images)}

        self.setWindowTitle("TODO: Filename goes here")
        # self.setGeometry(APP.primaryScreen().availableGeometry())
        # self.setMaximumSize(APP.primaryScreen().availableSize())
        self.available_height = available_height

        QBtn = (
            QDialogButtonBox.Yes | QDialogButtonBox.No
        )

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        layout = QHBoxLayout()
        self.setLayout(layout)
        
        label = QLabel()
        label2 = QLabel()
        self.label = label
        self.label2 = label2
        layout.addWidget(label)
        layout.addWidget(label2)
        label2.setText("not a spread")

        buttonLabel = QLabel("Press Yes to save labels to file.\nUse arrows to change index.\nUse space bar to confirm spreads.")
        layout.addWidget(buttonLabel)
        layout.addWidget(self.buttonBox)
        # print(label.size())
        # print(label.maximumSize())
        # l, t, r, b = layout.getContentsMargins()
        
        #label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        pixmap = QPixmap(images[0]).scaledToHeight(self.available_height * 0.9)
        label.setPixmap(pixmap)
        #label.setScaledContents(True)
        
        #label2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # pixmap2 = QPixmap(images[0]).scaledToHeight(self.frameGeometry().height() - t - b - t - b)
        # label2.setPixmap(pixmap2)
        #label2.setScaledContents(True)
        #self.resize(pixmap2.width(), pixmap2.height())
    def keyReleaseEvent(self, event):
        # t = 20
        # b = 20
        if isinstance(event, QKeyEvent):
            if event.key() == Qt.Key.Key_Left:
                self.index = max(0, self.index - 1)
                if self.index2page[self.index] in self.spreads:
                    self.label2.setText('spread')
                else:
                    self.label2.setText('not a spread')
                pixmap = QPixmap(self.images[self.index]).scaledToHeight(self.available_height * 0.9)
                self.label.setPixmap(pixmap)
                # pixmap2 = QPixmap(images[self.index]).scaledToHeight(self.frameGeometry().height() - t - b - t - b)
                # self.label2.setPixmap(pixmap2)
            elif event.key() == Qt.Key.Key_Right:
                self.index = min(self.index + 1, len(self.images) - 1)
                if self.index2page[self.index] in self.spreads:
                    self.label2.setText('spread')
                else:
                    self.label2.setText('not a spread')
                
                pixmap = QPixmap(self.images[self.index]).scaledToHeight(self.available_height * 0.9)
                self.label.setPixmap(pixmap)
                # pixmap2 = QPixmap(images[self.index]).scaledToHeight(self.frameGeometry().height() - t - b - t - b)
                # self.label2.setPixmap(pixmap2)
            elif event.key() == Qt.Key.Key_Space:
                self.spreads.append(os.path.basename(self.images[self.index]))
                self.label2.setText('spread')
            else:
                super().keyReleaseEvent(event)
        else:
            super().keyReleaseEvent(event)