from PySide6.QtWidgets import QListWidget
from PySide6.QtGui import QPainter, QFont, QFontMetrics
from PySide6.QtCore import Qt, QRect


class JobListWidget(QListWidget):
    def paintEvent(self, event):
        if not self.model() or self.model().rowCount() == 0:
            p = QPainter(self.viewport())
            p.setPen(Qt.GlobalColor.gray)
            
            rect = self.viewport().rect()
            
            # Calculate dimensions for proper centering
            emoji_height = 50
            title_height = 25
            desc_height = 40  # Approximate height for description text
            gap_emoji_title = 15  # Gap between emoji and title
            gap_title_desc = 2    # Small gap between title and description (like new line)
            
            # Total height of the entire block
            total_height = emoji_height + gap_emoji_title + title_height + gap_title_desc + desc_height
            
            # Starting Y position to center the entire block
            start_y = (rect.height() - total_height) // 2
            
            # Draw book emoji - centered horizontally, positioned at calculated Y
            emoji_font = QFont()
            emoji_font.setPointSize(36)
            p.setFont(emoji_font)
            emoji_rect = QRect(0, start_y, rect.width(), emoji_height)
            p.drawText(emoji_rect, Qt.AlignmentFlag.AlignCenter, "📚")
            
            # Draw main title text - centered horizontally, right below emoji
            title_font = QFont()
            title_font.setPointSize(14)
            title_font.setBold(True)
            p.setFont(title_font)
            title_y = start_y + emoji_height + gap_emoji_title
            title_rect = QRect(0, title_y, rect.width(), title_height)
            p.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, "Drag & Drop Files Here")
            
            # Draw description text - centered horizontally, right below title (like new line)
            desc_font = QFont()
            desc_font.setPointSize(10)
            p.setFont(desc_font)
            desc_y = title_y + title_height + gap_title_desc
            desc_rect = QRect(20, desc_y, rect.width() - 40, desc_height)
            p.drawText(desc_rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, 
                      "Supports folders (with JPG, PNG, or GIF files in them), CBZ, CBR, ZIP, RAR, 7Z, PDF files")
        else:
            super().paintEvent(event) 