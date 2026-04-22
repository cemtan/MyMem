#!/usr/bin/env python3

import sys
import json
import random
import os
from pathlib import Path
from datetime import datetime

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QInputDialog, QMessageBox
from PyQt5.QtCore import Qt, QRect, QTimer, QPoint
from PyQt5.QtGui import QPainter, QColor, QFont, QPixmap, QPen, QBrush
from PIL import Image, ImageFilter, ImageDraw

class Card:
    def __init__(self, card_id, pair_id, icon):
        self.id = card_id
        self.pair_id = pair_id
        self.icon = icon
        self.is_flipped = False
        self.is_matched = False
        self.rect = QRect()
        self.hover = False

SELECTED_ICONS = [
    '🦁', '🐯', '🐻', '🐼', '🍎', '🍊', '⚽', '🏀',
    '🎵', '🎸', '🚗', '✈️', '☀️', '❄️', '⌚', '💻',
    '🌲', '🌸', '🎮', '🎯', '📱', '🎬', '🧩', '🎭'
]

class ScoreManager:
    """Skor sistemi (adım sayısına göre sıralı)"""
    def __init__(self):
        self.scores_file = Path('/tmp/memory_game/scores_steps.json')
        self.leaderboard = self.load_scores()
    
    def load_scores(self):
        """Önceki skorları yükle"""
        if self.scores_file.exists():
            try:
                with open(self.scores_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Adım sayısına göre sırala (az adım = üstte)
                    return sorted(data, key=lambda x: x['moves'])[:10]
            except:
                return []
        return []
    
    def add_score(self, player_name, score, moves, matched_pairs):
        """Yeni skoru ekle"""
        entry = {
            'name': player_name,
            'moves': moves,
            'matched': matched_pairs,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
        
        self.leaderboard.append(entry)
        # Adım sayısına göre sırala
        self.leaderboard = sorted(self.leaderboard, key=lambda x: x['moves'])[:10]
        
        # Kaydet
        try:
            with open(self.scores_file, 'w', encoding='utf-8') as f:
                json.dump(self.leaderboard, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Skor kaydında hata: {e}")
        
        return self.leaderboard
    
    def get_top_scores(self):
        """Top 10'u döndür"""
        return self.leaderboard

class GameWidget(QWidget):
    def __init__(self, player_name, score_manager):
        super().__init__()
        
        self.player_name = player_name
        self.score_manager = score_manager
        
        self.cards = []
        self.first_flipped = -1
        self.second_flipped = -1
        self.score = 0
        self.moves = 0
        self.matched_pairs = 0
        self.game_active = True
        self.game_finished = False
        
        # Arka plan
        self.background_image = None
        self.blurred_background = None
        self.load_or_create_background()
        
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_match)
        
        self.reset_btn_rect = QRect()
        self.reset_btn_hover = False
        
        self.initialize_cards()
        self.setMinimumSize(1400, 900)

    def load_or_create_background(self):
        """Modern Office-style arka plan"""
        try:
            img = Image.new('RGB', (1200, 900), color=(242, 244, 246))
            
            # Çok hafif gradient
            for y in range(900):
                ratio = y / 900
                r = int(242 - ratio * 5)
                g = int(244 - ratio * 5)
                b = int(246 - ratio * 3)
                for x in range(1200):
                    img.putpixel((x, y), (r, g, b))
            
            bg_path = Path('/tmp/memory_game/background_office.png')
            img.save(str(bg_path))
            
            self.background_image = QPixmap(str(bg_path))
            self.blurred_background = self.background_image.copy()
            
        except Exception as e:
            pixmap = QPixmap(1200, 900)
            painter = QPainter(pixmap)
            painter.fillRect(0, 0, 1200, 900, QColor(242, 244, 246))
            painter.end()
            self.background_image = pixmap
            self.blurred_background = pixmap.copy()

    def initialize_cards(self):
        self.cards = []
        icons = SELECTED_ICONS * 2
        random.shuffle(icons)
        
        for i in range(48):
            icon = icons[i]
            pair_id = SELECTED_ICONS.index(icon)
            card = Card(i, pair_id, icon)
            self.cards.append(card)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Arka plan (sağ taraf)
        bg_x = 250
        if self.blurred_background:
            painter.drawPixmap(bg_x, 0, self.width() - bg_x, self.height(), self.blurred_background)
        else:
            painter.fillRect(bg_x, 0, self.width() - bg_x, self.height(), QColor(242, 244, 246))
        
        # SOL PANEL - Modern Office Style
        self.draw_modern_sidebar(painter, bg_x)
        
        # Kartlar (sağ taraf) - Modern tasarım
        cols, rows = 8, 6
        game_width = self.width() - bg_x
        card_w = (game_width - 30) // cols - 4
        card_h = (self.height() - 100) // rows - 4
        start_y = 70
        start_x = bg_x
        
        for i, card in enumerate(self.cards):
            row, col = i // cols, i % cols
            x = start_x + 15 + col * (card_w + 4)
            y = start_y + row * (card_h + 4)
            
            card.rect = QRect(x, y, card_w, card_h)
            
            # Modern kart tasarımı (gölge + gradient)
            if card.is_matched:
                # Başarılı - yeşil gölge
                painter.fillRect(card.rect.adjusted(0, 2, 2, 2), QColor(100, 120, 150, 40))
                painter.fillRect(card.rect, QColor(76, 175, 80))
                border_color = QColor(56, 142, 60)
            elif card.is_flipped:
                # Açılmış - mavi gölge
                painter.fillRect(card.rect.adjusted(0, 2, 2, 2), QColor(33, 150, 243, 80))
                painter.fillRect(card.rect, QColor(25, 118, 210))
                border_color = QColor(13, 71, 161)
            else:
                # Kapalı - gri gölge
                painter.fillRect(card.rect.adjusted(0, 2, 2, 2), QColor(0, 0, 0, 50))
                painter.fillRect(card.rect, QColor(224, 224, 224))
                border_color = QColor(158, 158, 158)
            
            # Border (ince)
            painter.setPen(QPen(border_color, 1))
            painter.drawRoundedRect(card.rect, 6, 6)
            
            # İcon
            if card.is_flipped or card.is_matched:
                painter.setFont(QFont("Arial", 48))
                painter.setPen(Qt.white if card.is_flipped or card.is_matched else QColor(100, 100, 100))
                painter.drawText(card.rect, Qt.AlignCenter, card.icon)
        
        # Üst Panel - Modern Office Style
        self.draw_top_panel(painter, bg_x)

    def draw_modern_sidebar(self, painter, width):
        """Modern Office-style sidebar"""
        # Arka plan - beyaz
        painter.fillRect(0, 0, width, self.height(), QColor(255, 255, 255))
        
        # Alt sınır - hafif gri
        painter.setPen(QPen(QColor(229, 229, 229), 1))
        painter.drawLine(width - 1, 0, width - 1, self.height())
        
        # Başlık
        painter.setPen(QColor(25, 103, 210))
        painter.setFont(QFont("Segoe UI", 16, QFont.Bold))
        painter.drawText(15, 35, "🏆 Sıralama")
        
        # Alt çizgi
        painter.setPen(QPen(QColor(229, 229, 229), 1))
        painter.drawLine(15, 45, width - 15, 45)
        
        # Başlık satırı
        painter.setPen(QColor(100, 100, 100))
        painter.setFont(QFont("Segoe UI", 9, QFont.Normal))
        painter.drawText(15, 65, "Sıra")
        painter.drawText(50, 65, "Oyuncu")
        painter.drawText(200, 65, "Adımlar")
        
        # Skor listesi
        scores = self.score_manager.get_top_scores()
        y_pos = 85
        
        painter.setFont(QFont("Segoe UI", 10, QFont.Normal))
        
        for rank, entry in enumerate(scores[:10], 1):
            # Arka plan - hover
            if rank % 2 == 0:
                painter.fillRect(10, y_pos - 12, width - 20, 20, QColor(245, 245, 245))
            
            # Medal resimleri
            medals = ['🥇', '🥈', '🥉']
            medal = medals[rank - 1] if rank <= 3 else f"{rank}."
            
            painter.setPen(QColor(33, 33, 33))
            painter.drawText(15, y_pos, medal)
            
            # Oyuncu adı (kısalt)
            name = entry['name'][:15]
            painter.drawText(50, y_pos, name)
            
            # Adım sayısı
            painter.setPen(QColor(25, 103, 210))
            painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
            painter.drawText(200, y_pos, str(entry['moves']))
            
            painter.setFont(QFont("Segoe UI", 10, QFont.Normal))
            painter.setPen(QColor(33, 33, 33))
            
            y_pos += 25

    def draw_top_panel(self, painter, start_x):
        """Modern Office-style üst panel"""
        panel_height = 70
        
        # Arka plan - hafif mavi
        painter.fillRect(start_x, 0, self.width() - start_x, panel_height, QColor(245, 248, 255))
        
        # Alt sınır
        painter.setPen(QPen(QColor(229, 229, 229), 1))
        painter.drawLine(start_x, panel_height - 1, self.width(), panel_height - 1)
        
        # Oyuncu adı - başlık
        painter.setPen(QColor(25, 103, 210))
        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        painter.drawText(start_x + 15, 20, f"👤 {self.player_name}")
        
        # Adımlar - sayı
        painter.setPen(QColor(100, 100, 100))
        painter.setFont(QFont("Segoe UI", 10, QFont.Normal))
        painter.drawText(start_x + 15, 45, f"Adımlar:")
        
        painter.setPen(QColor(25, 103, 210))
        painter.setFont(QFont("Segoe UI", 14, QFont.Bold))
        painter.drawText(start_x + 100, 45, str(self.moves))
        
        # Eşleştirmeler - sayı
        painter.setPen(QColor(100, 100, 100))
        painter.setFont(QFont("Segoe UI", 10, QFont.Normal))
        painter.drawText(start_x + 200, 45, f"Eşleştirmeler:")
        
        painter.setPen(QColor(25, 103, 210))
        painter.setFont(QFont("Segoe UI", 14, QFont.Bold))
        painter.drawText(start_x + 330, 45, f"{self.matched_pairs}/24")
        
        # Reset Butonu - Modern Office Style
        self.draw_reset_button(painter)

    def draw_reset_button(self, painter):
        """Modern Office-style reset butonu"""
        self.reset_btn_rect = QRect(self.width() - 180, 12, 160, 46)
        
        # Gölge
        painter.fillRect(self.reset_btn_rect.adjusted(0, 2, 2, 2), QColor(0, 0, 0, 30))
        
        # Arka plan - hover kontrolü
        if self.reset_btn_hover:
            painter.fillRect(self.reset_btn_rect, QColor(41, 128, 185))  # Daha koyu mavi
        else:
            painter.fillRect(self.reset_btn_rect, QColor(52, 152, 219))  # Mavi
        
        # Border
        painter.setPen(QPen(QColor(25, 103, 210), 1))
        painter.drawRoundedRect(self.reset_btn_rect, 4, 4)
        
        # Yazı
        painter.setPen(Qt.white)
        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        painter.drawText(self.reset_btn_rect, Qt.AlignCenter, "↻  Yeniden Başlat")

    def mousePressEvent(self, event):
        if self.reset_btn_rect.contains(event.pos()):
            self.reset_game()
            return
        
        if not self.game_active or (self.first_flipped != -1 and self.second_flipped != -1):
            return
        
        for i, card in enumerate(self.cards):
            if card.rect.contains(event.pos()) and not card.is_flipped and not card.is_matched:
                card.is_flipped = True
                
                if self.first_flipped == -1:
                    self.first_flipped = i
                elif self.second_flipped == -1:
                    self.second_flipped = i
                    self.moves += 1
                    self.game_active = False
                    self.check_timer.start(1000)
                
                self.update()
                return

    def mouseMoveEvent(self, event):
        """Hover efekti"""
        hover = self.reset_btn_rect.contains(event.pos())
        if hover != self.reset_btn_hover:
            self.reset_btn_hover = hover
            self.setCursor(Qt.PointingHandCursor if hover else Qt.ArrowCursor)
            self.update()

    def check_match(self):
        self.check_timer.stop()
        
        first_card = self.cards[self.first_flipped]
        second_card = self.cards[self.second_flipped]
        
        if first_card.pair_id == second_card.pair_id:
            first_card.is_matched = True
            second_card.is_matched = True
            self.matched_pairs += 1
            
            if self.matched_pairs == 24:
                self.game_active = False
                self.save_and_show_result()
        else:
            first_card.is_flipped = False
            second_card.is_flipped = False
        
        self.first_flipped = -1
        self.second_flipped = -1
        self.game_active = True
        
        self.update()

    def save_and_show_result(self):
        """Skoru kaydet ve sonuç göster"""
        self.score_manager.add_score(self.player_name, 0, self.moves, self.matched_pairs)
        
        result_text = f"""
Tebrikler {self.player_name}!

🎯 Toplam Adımlar: {self.moves}
✨ Eşleştirmeler: {self.matched_pairs}/24

📊 Sıralamaya Kaydedildi!
"""
        
        parent = self.parent()
        if parent:
            parent.show_completion(result_text)

    def reset_game(self):
        self.moves = 0
        self.matched_pairs = 0
        self.game_active = True
        self.game_finished = False
        self.first_flipped = -1
        self.second_flipped = -1
        
        self.initialize_cards()
        self.update()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Oyuncu adını sor
        self.player_name = self.get_player_name()
        if not self.player_name:
            sys.exit(0)
        
        self.setWindowTitle(f"📋 Modern Eşleştirme - {self.player_name}")
        self.setGeometry(50, 50, 1400, 900)
        self.setStyleSheet("QMainWindow { background-color: #f5f5f5; }")
        
        # Skor yöneticisi
        self.score_manager = ScoreManager()
        
        # Oyun widget'ı
        game_widget = GameWidget(self.player_name, self.score_manager)
        game_widget.setParent(self)
        self.setCentralWidget(game_widget)
        
        self.game_widget = game_widget

    def get_player_name(self):
        """Oyuncu adını sor"""
        name, ok = QInputDialog.getText(
            None,
            "🎮 Hoş Geldiniz",
            "Adınızı girin:",
            text="Oyuncu"
        )
        
        if ok and name.strip():
            return name.strip()
        return None

    def show_completion(self, message):
        """Oyun tamamlanma mesajı"""
        QMessageBox.information(self, "✅ Oyun Bitti!", message)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
