#!/usr/bin/env python3

import sys
import json
import random
import os
from pathlib import Path
from datetime import datetime

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QInputDialog, QMessageBox, QMenu, QAction
from PyQt5.QtCore import Qt, QRect, QTimer, QPoint
from PyQt5.QtGui import QPainter, QColor, QFont, QPixmap, QPen, QBrush
from PIL import Image, ImageFilter, ImageDraw

# ============== KART SINIFI ==============
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

# ============== SKOR YÖNETİCİSİ ==============
class ScoreManager:
    """Skor sistemi - her kart adedi için ayrı skor"""
    def __init__(self):
        self.scores_file = Path('/tmp/memory_game/scores_steps.json')
        self.leaderboard = self.load_scores()
    
    def load_scores(self):
        if self.scores_file.exists():
            try:
                with open(self.scores_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Eski liste formatını yeni dict formatına çevir
                    if isinstance(data, list):
                        return {'4x4': [], '4x6': [], '5x6': [], '4x8': [], '6x8': []}
                    return data
            except:
                return {'4x4': [], '4x6': [], '5x6': [], '4x8': [], '6x8': []}
        return {'4x4': [], '4x6': [], '5x6': [], '4x8': [], '6x8': []}
    
    def add_score(self, player_name, score, moves, matched_pairs, grid_size):
        if grid_size not in self.leaderboard:
            self.leaderboard[grid_size] = []
        
        entry = {
            'name': player_name,
            'moves': moves,
            'matched': matched_pairs,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
        
        self.leaderboard[grid_size].append(entry)
        self.leaderboard[grid_size] = sorted(self.leaderboard[grid_size], key=lambda x: x['moves'])[:10]
        
        try:
            with open(self.scores_file, 'w', encoding='utf-8') as f:
                json.dump(self.leaderboard, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Skor kaydında hata: {e}")
        
        return self.leaderboard[grid_size]
    
    def get_top_scores(self, grid_size='6x8'):
        return self.leaderboard.get(grid_size, [])


class GameWidget(QWidget):
    def __init__(self, player_name, score_manager, grid_size='6x8'):
        super().__init__()
        
        self.player_name = player_name
        self.score_manager = score_manager
        self.grid_size = grid_size
        
        self.rows, self.cols = self.parse_grid(grid_size)
        self.total_pairs = (self.rows * self.cols) // 2
        
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
    
    def parse_grid(self, grid_size):
        sizes = {'4x4': (4, 4), '4x6': (4, 6), '5x6': (5, 6), '4x8': (4, 8), '6x8': (6, 8)}
        return sizes.get(grid_size, (6, 8))
    
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
        total_cards = self.rows * self.cols
        needed_pairs = total_cards // 2
        icons = SELECTED_ICONS[:needed_pairs] * 2
        random.shuffle(icons)
        
        self.total_pairs = needed_pairs
        
        for i in range(total_cards):
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
        cols = self.cols
        rows = self.rows
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
        painter.drawText(15, 35, f"🏆 Sıralama ({self.grid_size})")
        
        # Alt çizgi
        painter.setPen(QPen(QColor(229, 229, 229), 1))
        painter.drawLine(15, 45, width - 15, 45)
        
        # Başlık satırı
        painter.setPen(QColor(100, 100, 100))
        painter.setFont(QFont("Segoe UI", 9, QFont.Normal))
        painter.drawText(15, 65, "Sıra")
        painter.drawText(50, 65, "Oyuncu")
        painter.drawText(200, 65, "Adımlar")
        
        # Skor listesi - grid boyutuna göre
        scores = self.score_manager.get_top_scores(self.grid_size)
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
        painter.drawText(start_x + 330, 45, f"{self.matched_pairs}/{self.total_pairs}")
        
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
            
            if self.matched_pairs == self.total_pairs:
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
        self.score_manager.add_score(self.player_name, 0, self.moves, self.matched_pairs, self.grid_size)
        
        result_text = f"""
Tebrikler {self.player_name}!

🎯 Toplam Adımlar: {self.moves}
✨ Eşleştirmeler: {self.matched_pairs}/{self.total_pairs}

📊 {self.grid_size} Sıralamaya Kaydedildi!
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
        
        # Varsayılan grid boyutu
        self.grid_size = '6x8'
        
        # Oyuncu adını sor
        self.player_name = self.get_player_name()
        if not self.player_name:
            sys.exit(0)
        
        self.setWindowTitle(f"📋 Modern Eşleştirme - {self.player_name} - {self.grid_size}")
        self.setGeometry(50, 50, 1400, 900)
        self.setStyleSheet("QMainWindow { background-color: #f5f5f5; }")
        
        # Skor yöneticisi
        self.score_manager = ScoreManager()
        
        # Menü çubuğu oluştur
        self.create_menu_bar()
        
        # Oyun widget'ı
        self.game_widget = GameWidget(self.player_name, self.score_manager, self.grid_size)
        self.game_widget.setParent(self)
        self.setCentralWidget(self.game_widget)
    
    def create_menu_bar(self):
        """Menü çubuğu oluştur"""
        menubar = self.menuBar()
        menubar.setStyleSheet("QMenuBar { background-color: #f5f5f5; }")
        
        # Oyun menüsü
        game_menu = menubar.addMenu("🎮 Oyun")
        
        # Yeni oyun
        new_action = QAction("🆕 Yeni Oyun", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_game)
        game_menu.addAction(new_action)
        
        # Yeniden başlat
        restart_action = QAction("🔄 Yeniden Başlat", self)
        restart_action.setShortcut("Ctrl+R")
        restart_action.triggered.connect(self.restart_game)
        game_menu.addAction(restart_action)
        
        game_menu.addSeparator()
        
        # Kart adedi alt menüsü
        grid_menu = QMenu("📊 Kart Adedi", self)
        
        for label, size in [("4x4 (16 kart)", "4x4"), ("4x6 (24 kart)", "4x6"),
                          ("5x6 (30 kart)", "5x6"), ("4x8 (32 kart)", "4x8"),
                          ("6x8 (48 kart)", "6x8")]:
            action = QAction(label, self)
            action.triggered.connect(lambda checked, s=size: self.change_grid_size(s))
            grid_menu.addAction(action)
        
        game_menu.addMenu(grid_menu)
        
        game_menu.addSeparator()
        
        # Çıkış
        exit_action = QAction("✖ Çıkış", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        game_menu.addAction(exit_action)
        
        # Oyuncu menüsü
        player_menu = menubar.addMenu("👤 Oyuncu")
        
        name_action = QAction("📝 İsim Değiştir", self)
        name_action.triggered.connect(self.change_name)
        player_menu.addAction(name_action)
    
    def new_game(self):
        """Yeni oyun"""
        name, ok = QInputDialog.getText(self, "🆕 Yeni Oyun", "Oyuncu adı:", text=self.player_name)
        if ok and name.strip():
            self.player_name = name.strip()
            self.restart_game()
    
    def restart_game(self):
        """Oyunu yeniden başlat"""
        self.game_widget = GameWidget(self.player_name, self.score_manager, self.grid_size)
        self.setCentralWidget(self.game_widget)
        self.setWindowTitle(f"📋 Modern Eşleştirme - {self.player_name} - {self.grid_size}")
    
    def change_grid_size(self, grid_size):
        """Grid boyutunu değiştir"""
        self.grid_size = grid_size
        self.restart_game()
    
    def change_name(self):
        """İsim değiştir"""
        name, ok = QInputDialog.getText(self, "👤 Oyuncu", "Yeni isminiz:", text=self.player_name)
        if ok and name.strip():
            self.player_name = name.strip()
            self.setWindowTitle(f"📋 Modern Eşleştirme - {self.player_name} - {self.grid_size}")
    
    def get_player_name(self):
        """Oyuncu adını sor"""
        name, ok = QInputDialog.getText(None, "🎮 Hoş Geldiniz", "Adınızı girin:", text="Oyuncu")
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
