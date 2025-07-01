from PySide6.QtWidgets import QListWidget
from PySide6.QtGui import QPainter, QFont
from PySide6.QtCore import Qt, QRect


class JobListWidget(QListWidget):
    def paintEvent(self, event):
        if not self.model() or self.model().rowCount() == 0:
            p = QPainter(self.viewport())
            p.setPen(Qt.GlobalColor.gray)
            
            rect = self.viewport().rect()
            
            # Draw book emoji - centered at top
            emoji_font = QFont()
            emoji_font.setPointSize(36)
            p.setFont(emoji_font)
            emoji_rect = QRect(0, rect.height()//2 - 80, rect.width(), 50)
            p.drawText(emoji_rect, Qt.AlignmentFlag.AlignCenter, "📚")
            
            # Draw main title text - centered in middle
            title_font = QFont()
            title_font.setPointSize(14)
            title_font.setBold(True)
            p.setFont(title_font)
            title_rect = QRect(0, rect.height()//2 - 20, rect.width(), 25)
            p.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, "Drag & Drop Files Here")
            
            # Draw description text - directly below title
            desc_font = QFont()
            desc_font.setPointSize(10)
            p.setFont(desc_font)
            desc_rect = QRect(20, rect.height()//2 + 5, rect.width() - 40, 60)
            p.drawText(desc_rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, 
                      "Supports folders (with JPG, PNG, or GIF files in them), CBZ, CBR, ZIP, RAR, 7Z, PDF files")
        else:
            super().paintEvent(event) 