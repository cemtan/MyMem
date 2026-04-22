#!/usr/bin/env python3
"""
Hafıza Oyunu - Memory Card Game
Linux KDE uyumlu, modern MSOffice/OnlyOffice tarzında bir hafıza oyunu.
"""

import sys
import json
import random
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QDialog, QLineEdit, QMessageBox,
    QMenuBar, QMenu, QStatusBar, QFrame, QComboBox
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QRect
from PyQt6.QtGui import QAction, QIcon, QFont, QColor, QPalette


# ============== SABITLER ==============
LEADERBOARD_FILE = "leaderboard.json"
MAX_LEADERBOARD = 10
GRID_SIZE = 4  # 4x4 = 16 kart
CARD_PAIRS = 8

# Modern renkler (MSOffice/OnlyOffice tarzı)
COLORS = {
    'primary_bg': '#FAFAFA',
    'secondary_bg': '#F0F0F0',
    'accent': '#0078D4',
    'accent_dark': '#106EBE',
    'success': '#107C10',
    'warning': '#FFB900',
    'text_primary': '#24292F',
    'text_secondary': '#57606A',
    'border': '#D0D7DE',
    'card_back': '#1F6FEB',
    'card_front': '#FFFFFF',
    'card_shadow': 'rgba(0, 0, 0, 0.12)',
}

# Kart ikonları (Unicode emoji ile) - 20 farklı ikon
CARD_ICONS = [
    "🌟",  # Yıldız
    "🎯",  # Hedef
    "🚀",  # Roket
    "💎",  # Elmas
    "🎨",  # Palet
    "🎵",  # Müzik
    "🌈",  # Gökkuşağı
    "🔥",  # Ateş
    "🍀",  # Numarataş
    "🌙",  # Ay
    "⭐",  # Yıldız 2
    "🎲",  # Zar
    "🎭",  # Maske
    "🎪",  # Çadır
    "🌸",  # Çiçek
    "🦋",  # Kelebek
    "🐱",  # Kedi
    "🐕",  # Köpek
    "🎁",  # Hediye
    "🔔",  # Çan
]


# ============== YARDIMCI FONKSİYONLAR ==============
def load_leaderboard():
    """Leaderboard dosyasını yükle."""
    try:
        with open(LEADERBOARD_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_leaderboard(leaderboard):
    """Leaderboard dosyasını kaydet."""
    with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
        json.dump(leaderboard, f, ensure_ascii=False, indent=2)


def add_to_leaderboard(player_name, moves):
    """Skoru leaderboard'a ekle."""
    leaderboard = load_leaderboard()
    leaderboard.append({'name': player_name, 'moves': moves})
    # Hamle sayısına göre sırala (azdan çoğa)
    leaderboard.sort(key=lambda x: x['moves'])
    # En fazla 10 kayıt tut
    leaderboard = leaderboard[:MAX_LEADERBOARD]
    save_leaderboard(leaderboard)
    return leaderboard


# ============== KART WIDGETI ==============
class CardButton(QFrame):
    """Oyun kartı widget'ı."""
    
    clicked_signal = pyqtSignal()
    
    def __init__(self, icon: str, card_id: int, parent=None):
        super().__init__(parent)
        self.icon = icon
        self.card_id = card_id  # Benzersiz kart ID
        self.is_flipped = False
        self.is_matched = False
        self.is_locked = False
        
        self.setup_ui()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def setup_ui(self):
        """Kullanıcı arayüzünü oluştur."""
        self.setFixedSize(90, 120)
        self.setFrameStyle(QFrame.Shape.NoFrame)
        
        # Başlangıçta kart arkası görünür (kapalı)
        self.set_card_back()
        
        # İkon label - ince kenarlı iskambil kağıdı gibi
        self.icon_label = QLabel(self.icon, self)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("""
            font-size: 42px;
            background-color: transparent;
        """)
        self.icon_label.setGeometry(0, 0, 90, 120)
        self.icon_label.hide()  # Başlangıçta gizli
    
    def set_card_back(self):
        """Kart arkasını göster (kapalı) - iskambil kağıdı desenli."""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #1a5fb4, stop:0.5 #1c71d7, stop:1 #1a5fb4);
                border: none;
                border-radius: 6px;
                box-shadow: 2px 2px 4px {COLORS['card_shadow']};
            }}
        """)
    
    def set_card_front(self):
        """Kart önünü göster (açık) - temiz beyaz iskambil kağıdı."""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['card_front']};
                border: none;
                border-radius: 6px;
                box-shadow: 2px 2px 4px {COLORS['card_shadow']};
            }}
        """)
    
    def flip(self, show_icon: bool):
        """Kartı çevir."""
        self.is_flipped = show_icon
        
        if show_icon:
            self.set_card_front()
            self.icon_label.show()
        else:
            self.set_card_back()
            self.icon_label.hide()
    
    def set_matched(self):
        """Kartı eşleşmiş olarak işaretle."""
        self.is_matched = True
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #dafbe1;
                border: none;
                border-radius: 6px;
                box-shadow: 2px 2px 4px {COLORS['card_shadow']};
            }}
        """)
    
    def mousePressEvent(self, event):
        """Kart tıklandığında."""
        if not self.is_locked and not self.is_matched and not self.is_flipped:
            self.clicked_signal.emit()
        super().mousePressEvent(event)
    
    def enterEvent(self, event):
        """Mouse üzerine geldiğinde."""
        if not self.is_matched and not self.is_flipped:
            self.setFixedSize(94, 124)  # Hafif büyüme efekti
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Mouse karttan ayrıldığında."""
        if not self.is_matched and not self.is_flipped:
            self.setFixedSize(90, 120)
        super().leaveEvent(event)


# ============== OYUN AYARLARI DİYALOGU ==============
class GameSettingsDialog(QDialog):
    """Oyun başlangıcında kart sayısı seçimi."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = 4
        self.cols = 4
        self.setup_ui()
    
    def setup_ui(self):
        """UI oluştur."""
        self.setWindowTitle("Oyun Ayarları")
        self.setFixedSize(400, 250)
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Başlık
        title = QLabel("🧠 Oyun Ayarları")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {COLORS['accent']};")
        
        # Kart sayısı seçimi
        size_label = QLabel("Kart Sayısı:")
        size_label.setFont(QFont("Segoe UI", 12))
        
        self.size_combo = QComboBox()
        self.size_combo.setFont(QFont("Segoe UI", 12))
        self.size_combo.addItems(["4x4 (16 kart)", "4x6 (24 kart)", "5x6 (30 kart)", "4x8 (32 kart)"])
        self.size_combo.setCurrentIndex(0)
        self.size_combo.setStyleSheet(f"""
            QComboBox {{
                padding: 8px;
                border: 2px solid {COLORS['border']};
                border-radius: 4px;
                font-size: 14px;
            }}
            QComboBox:focus {{
                border-color: {COLORS['accent']};
            }}
        """)
        
        size_layout = QHBoxLayout()
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.size_combo)
        
        # Açıklama
        desc = QLabel("Kartları eşleştirerek oynayacağınız bu oyunda\nen az hamle ile kazanmaya çalışın!")
        desc.setFont(QFont("Segoe UI", 11))
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        # Başla butonu
        start_btn = QPushButton("🚀 Oyunu Başlat")
        start_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_dark']};
            }}
        """)
        start_btn.clicked.connect(self.accept)
        
        layout.addWidget(title)
        layout.addLayout(size_layout)
        layout.addWidget(desc)
        layout.addStretch()
        layout.addWidget(start_btn)
        
        self.setLayout(layout)
    
    def accept(self):
        """Dialog kabul edildiğinde."""
        index = self.size_combo.currentIndex()
        # (satır, sütun) çiftleri
        sizes = [(4, 4), (4, 6), (5, 6), (4, 8)]
        self.rows, self.cols = sizes[index]
        super().accept()
    
    def get_grid_size(self):
        """Izgara boyutunu döndür."""
        return self.rows, self.cols


# ============== KARŞILAMA DİYALOGU ==============
class WelcomeDialog(QDialog):
    """Oyuncunun adını alan karşılama dialogu."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.player_name = ""
        self.setup_ui()
    
    def setup_ui(self):
        """UI oluştur."""
        self.setWindowTitle("Hafıza Oyunu")
        self.setFixedSize(400, 200)
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Başlık
        title = QLabel("🎮 Hafıza Oyunu'na Hoş Geldiniz!")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {COLORS['accent']};")
        
        # Açıklama
        desc = QLabel("Kartları eşleştirerek oynayacağınız bu oyunda\nen az hamle ile kazanmaya çalışın!")
        desc.setFont(QFont("Segoe UI", 12))
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        # İsim girişi
        name_layout = QHBoxLayout()
        name_label = QLabel("Adınız:")
        name_label.setFont(QFont("Segoe UI", 12))
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Adınızı girin")
        self.name_input.setFont(QFont("Segoe UI", 12))
        self.name_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 8px;
                border: 2px solid {COLORS['border']};
                border-radius: 4px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['accent']};
            }}
        """)
        self.name_input.setText("Oyuncu")
        self.name_input.selectAll()
        
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        
        # Başla butonu
        start_btn = QPushButton("🚀 Oyunu Başlat")
        start_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_dark']};
            }}
        """)
        start_btn.clicked.connect(self.accept)
        
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addLayout(name_layout)
        layout.addWidget(start_btn)
        
        self.setLayout(layout)
        self.name_input.setFocus()
    
    def accept(self):
        """Dialog kabul edildiğinde."""
        name = self.name_input.text().strip()
        self.player_name = name if name else "Oyuncu"
        super().accept()


# ============== LİDER TABLOSU DİYALOGU ==============
class LeaderboardDialog(QDialog):
    """Oyun sonu lider tablosu dialogu."""
    
    def __init__(self, player_name: str, moves: int, parent=None):
        super().__init__(parent)
        self.player_name = player_name
        self.moves = moves
        self.is_new_record = False
        self.setup_ui()
    
    def setup_ui(self):
        """UI oluştur."""
        self.setWindowTitle("🏆 Lider Tablosu")
        self.setFixedSize(500, 550)
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Başarı mesajı
        title = QLabel(f"🎉 Tebrikler {self.player_name}!")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {COLORS['success']};")
        
        # Skor
        score_label = f"Oyunu {self.moves} hamlede tamamladınız!"
        
        # Yeni rekor kontrolü
        leaderboard = load_leaderboard()
        is_top_10 = len(leaderboard) < MAX_LEADERBOARD
        is_new_record = True
        
        for entry in leaderboard:
            if entry['moves'] < self.moves:
                is_top_10 = False
                break
        
        if is_top_10:
            self.is_new_record = True
            score_label += "\n🥇 YENİ REKOR!"
            title.setText("🎉 YENİ REKOR! 🎉")
        
        score = QLabel(score_label)
        score.setFont(QFont("Segoe UI", 14))
        score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        score.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        # Lider tablosu başlığı
        lb_title = QLabel("📊 En İyi Skorlar")
        lb_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        lb_title.setStyleSheet(f"color: {COLORS['accent']};")
        
        # Tablo
        table_widget = QWidget()
        table_layout = QVBoxLayout()
        table_layout.setSpacing(4)
        
        # Başlık satırı
        header = QWidget()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(8, 8, 8, 8)
        
        rank_label = QLabel("#")
        rank_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        rank_label.setFixedWidth(40)
        
        name_label = QLabel("Oyuncu")
        name_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        
        moves_label = QLabel("Hamle")
        moves_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        moves_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        moves_label.setFixedWidth(80)
        
        header_layout.addWidget(rank_label)
        header_layout.addWidget(name_label)
        header_layout.addWidget(moves_label)
        header.setLayout(header_layout)
        header.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['secondary_bg']};
                border-radius: 4px;
            }}
        """)
        table_layout.addWidget(header)
        
        # Skor satırları
        leaderboard = load_leaderboard()
        if not leaderboard:
            empty_label = QLabel("Henüz skor yok!")
            empty_label.setFont(QFont("Segoe UI", 12))
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
            table_layout.addWidget(empty_label)
        else:
            for i, entry in enumerate(leaderboard):
                row = QWidget()
                row_layout = QHBoxLayout()
                row_layout.setContentsMargins(8, 8, 8, 8)
                
                # Renk seçimi
                if i == 0:
                    bg_color = "#FFF8E1"  # Altın
                elif i == 1:
                    bg_color = "#F5F5F5"  # Gümüş
                elif i == 2:
                    bg_color = "#FFECB3"  # Bronz
                else:
                    bg_color = "transparent"
                
                rank = QLabel(str(i + 1))
                rank.setFont(QFont("Segoe UI", 11))
                rank.setFixedWidth(40)
                
                name = QLabel(entry['name'])
                name.setFont(QFont("Segoe UI", 11))
                
                moves = QLabel(str(entry['moves']))
                moves.setFont(QFont("Segoe UI", 11))
                moves.setAlignment(Qt.AlignmentFlag.AlignRight)
                moves.setFixedWidth(80)
                
                row_layout.addWidget(rank)
                row_layout.addWidget(name)
                row_layout.addWidget(moves)
                row.setLayout(row_layout)
                row.setStyleSheet(f"""
                    QWidget {{
                        background-color: {bg_color};
                        border-radius: 4px;
                        padding: 4px;
                    }}
                """)
                table_layout.addWidget(row)
        
        table_widget.setLayout(table_layout)
        
        # Butonlar
        button_layout = QHBoxLayout()
        
        replay_btn = QPushButton("🔄 Tekrar Oyna")
        replay_btn.setFont(QFont("Segoe UI", 12))
        replay_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        replay_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_dark']};
            }}
        """)
        replay_btn.clicked.connect(self.accept)
        
        close_btn = QPushButton("✖ Kapat")
        close_btn.setFont(QFont("Segoe UI", 12))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['secondary_bg']};
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border']};
                padding: 10px 20px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['border']};
            }}
        """)
        close_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(replay_btn)
        button_layout.addWidget(close_btn)
        
        layout.addWidget(title)
        layout.addWidget(score)
        layout.addWidget(lb_title)
        layout.addWidget(table_widget)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)


# ============== ANA PENCERE ==============
class MemoryGameWindow(QMainWindow):
    """Ana oyun penceresi."""
    
    def __init__(self):
        super().__init__()
        self.player_name = "Oyuncu"
        self.moves = 0
        self.first_card = None
        self.second_card = None
        self.is_locked = False
        self.matched_pairs = 0
        self.cards = []
        self.rows = 4
        self.cols = 4
        
        self.setup_ui()
        self.show_welcome()
    
    def setup_ui(self):
        """UI oluştur."""
        self.setWindowTitle("Hafıza Oyunu")
        self.setMinimumSize(1000, 700)
        
        # Ana widget ve layout - yatay bölme
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sol kenar çubuğu (skor tablosu)
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)
        
        # Sağ taraf - oyun alanı
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setSpacing(0)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Menü çubuğu
        self.create_menu_bar()
        
        # Üst bar (oyuncu adı + hamle sayısı)
        top_bar = QWidget()
        top_bar.setFixedHeight(50)
        top_bar.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['primary_bg']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(20, 0, 20, 0)
        
        # Oyuncu adı
        self.player_label = QLabel(f"👤 {self.player_name}")
        self.player_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Medium))
        self.player_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        
        # Hamle sayısı
        self.moves_label = QLabel(f"Hamle: {self.moves}")
        self.moves_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Medium))
        self.moves_label.setStyleSheet(f"color: {COLORS['accent']};")
        
        top_layout.addWidget(self.player_label)
        top_layout.addStretch()
        top_layout.addWidget(self.moves_label)
        
        top_bar.setLayout(top_layout)
        
        # Oyun alanı
        game_area = QWidget()
        game_area.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['secondary_bg']};
            }}
        """)
        game_layout = QVBoxLayout()
        
        # Kart ızgara
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(6)
        self.grid_layout.setContentsMargins(24, 24, 24, 24)
        
        game_layout.addLayout(self.grid_layout)
        game_area.setLayout(game_layout)
        
        right_layout.addWidget(top_bar)
        right_layout.addWidget(game_area, 1)
        
        right_panel.setLayout(right_layout)
        main_layout.addWidget(right_panel, 1)
        
        central_widget.setLayout(main_layout)
        
        # Sidebar leaderboard'ı güncelle
        self.update_sidebar()
    
    def create_sidebar(self):
        """Sol kenar çubuğu oluştur."""
        sidebar = QWidget()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['primary_bg']};
                border-right: 1px solid {COLORS['border']};
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 20, 16, 20)
        
        # Başlık
        title = QLabel("🏆 Lider Tablosu")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['accent']}; padding-bottom: 8px;")
        
        layout.addWidget(title)
        
        # Skor listesi
        self.scores_list = QWidget()
        self.scores_layout = QVBoxLayout()
        self.scores_layout.setSpacing(4)
        self.scores_list.setLayout(self.scores_layout)
        
        layout.addWidget(self.scores_list)
        layout.addStretch()
        
        sidebar.setLayout(layout)
        
        return sidebar
    
    def update_sidebar(self):
        """Sidebar'daki skor listesini güncelle."""
        # Mevcut widget'ları temizle
        while self.scores_layout.count():
            item = self.scores_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Lider tablosunu al
        leaderboard = load_leaderboard()
        
        if not leaderboard:
            empty = QLabel("Henüz skor yok")
            empty.setFont(QFont("Segoe UI", 12))
            empty.setStyleSheet(f"color: {COLORS['text_secondary']}; padding: 8px;")
            self.scores_layout.addWidget(empty)
        else:
            for i, entry in enumerate(leaderboard[:10]):
                score_widget = QWidget()
                score_layout = QHBoxLayout()
                score_layout.setContentsMargins(8, 6, 8, 6)
                
                # Sıra numarası
                rank = QLabel(f"#{i+1}")
                rank.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
                if i == 0:
                    rank.setStyleSheet("color: #e3b341;")  # Altın
                elif i == 1:
                    rank.setStyleSheet("color: #8b8b8b;")  # Gümüş
                elif i == 2:
                    rank.setStyleSheet("color: #cd7f32;")  # Bronz
                else:
                    rank.setStyleSheet(f"color: {COLORS['text_secondary']};")
                rank.setFixedWidth(30)
                
                # İsim
                name = QLabel(entry['name'])
                name.setFont(QFont("Segoe UI", 11))
                name.setStyleSheet(f"color: {COLORS['text_primary']};")
                name.setToolTip(entry['name'])
                
                # Hamle sayısı
                moves = QLabel(f"{entry['moves']}")
                moves.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                moves.setStyleSheet(f"color: {COLORS['accent']};")
                moves.setAlignment(Qt.AlignmentFlag.AlignRight)
                
                score_layout.addWidget(rank)
                score_layout.addWidget(name, 1)
                score_layout.addWidget(moves)
                
                # Arka plan rengi
                if i == 0:
                    bg = "#fff8e1"
                elif i == 1:
                    bg = "#f5f5f5"
                elif i == 2:
                    bg = "#fff3e0"
                else:
                    bg = "transparent"
                
                score_widget.setStyleSheet(f"""
                    QWidget {{
                        background-color: {bg};
                        border-radius: 4px;
                    }}
                """)
                score_widget.setLayout(score_layout)
                self.scores_layout.addWidget(score_widget)
    
    def create_menu_bar(self):
        """Menü çubuğu oluştur."""
        menubar = self.menuBar()
        menubar.setStyleSheet(f"""
            QMenuBar {{
                background-color: {COLORS['primary_bg']};
                color: {COLORS['text_primary']};
                border-bottom: 1px solid {COLORS['border']};
                padding: 4px;
            }}
            QMenuBar::item {{
                padding: 6px 12px;
                border-radius: 4px;
            }}
            QMenuBar::item:selected {{
                background-color: {COLORS['secondary_bg']};
            }}
            QMenu {{
                background-color: {COLORS['primary_bg']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 24px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {COLORS['accent']};
                color: white;
            }}
        """)
        
        # Oyun menüsü
        game_menu = menubar.addMenu("🎮 Oyun")
        
        new_game_action = QAction("🆕 Yeni Oyun", self)
        new_game_action.setShortcut("Ctrl+N")
        new_game_action.triggered.connect(self.show_welcome)
        game_menu.addAction(new_game_action)
        
        restart_action = QAction("🔄 Yeniden Başlat", self)
        restart_action.setShortcut("Ctrl+R")
        restart_action.triggered.connect(self.restart_game)
        game_menu.addAction(restart_action)
        
        game_menu.addSeparator()
        
        # Kart adedi seçimi
        grid_menu = QMenu("📊 Kart Adedi", self)
        
        for label, (rows, cols) in [("4x4 (16 kart)", (4, 4)), ("4x6 (24 kart)", (4, 6)), 
                                     ("5x6 (30 kart)", (5, 6)), ("4x8 (32 kart)", (4, 8))]:
            action = QAction(label, self)
            action.triggered.connect(lambda checked, r=rows, c=cols: self.set_grid_size(r, c))
            grid_menu.addAction(action)
        
        game_menu.addMenu(grid_menu)
        
        game_menu.addSeparator()
        
        exit_action = QAction("✖ Çıkış", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        game_menu.addAction(exit_action)
        
        # Oyuncu menüsü
        player_menu = menubar.addMenu("👤 Oyuncu")
        
        change_name_action = QAction("📝 İsim Değiştir", self)
        change_name_action.setShortcut("Ctrl+I")
        change_name_action.triggered.connect(self.change_player_name)
        player_menu.addAction(change_name_action)
        
        # Yardım menüsü
        help_menu = menubar.addMenu("❓ Yardım")
        
        about_action = QAction("ℹ️ Hakkında", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def set_grid_size(self, rows, cols):
        """Kart adedini değiştir ve yeni oyun başlat."""
        self.rows = rows
        self.cols = cols
        self.start_new_game()
    
    def change_player_name(self):
        """Oyuncu ismini değiştir."""
        dialog = WelcomeDialog(self)
        if dialog.exec():
            self.player_name = dialog.player_name
            self.player_label.setText(f"👤 {self.player_name}")
    
    def show_welcome(self):
        """Karşılama dialogunu göster."""
        # Önce oyun ayarlarını göster
        settings_dialog = GameSettingsDialog(self)
        if settings_dialog.exec():
            self.rows, self.cols = settings_dialog.get_grid_size()
            
            # Sonra isim gir
            welcome_dialog = WelcomeDialog(self)
            if welcome_dialog.exec():
                self.player_name = welcome_dialog.player_name
                self.player_label.setText(f"👤 {self.player_name}")
                self.start_new_game()
    
    def start_new_game(self):
        """Yeni oyun başlat."""
        # Temizle
        for i in range(self.grid_layout.count()):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        self.cards = []
        self.moves = 0
        self.first_card = None
        self.second_card = None
        self.is_locked = False
        self.matched_pairs = 0
        
        self.update_moves()
        
        # Toplam kart sayısı
        total_cards = self.rows * self.cols
        num_pairs = total_cards // 2
        
        # İkonları seç ve karıştır
        selected_icons = CARD_ICONS[:num_pairs] * 2  # Gerekli kadar ikon
        random.shuffle(selected_icons)
        
        # Izgaraya yerleştir
        index = 0
        for row in range(self.rows):
            for col in range(self.cols):
                card = CardButton(selected_icons[index], index)  # Benzersiz ID
                card.clicked_signal.connect(lambda c=card: self.on_card_click(c))
                self.grid_layout.addWidget(card, row, col)
                self.cards.append(card)
                index += 1
    
    def on_card_click(self, card: CardButton):
        """Kart tıklandığında."""
        if self.is_locked:
            return
        
        if card.is_flipped or card.is_matched:
            return
        
        if card == self.first_card:
            return
        
        # Kartı çevir
        card.flip(True)
        
        if self.first_card is None:
            # İlk kart
            self.first_card = card
        else:
            # İkinci kart
            self.second_card = card
            self.moves += 1
            self.update_moves()
            
            # Eşleşme kontrolü
            self.is_locked = True
            QTimer.singleShot(1000, self.check_match)
    
    def check_match(self):
        """Kartları kontrol et."""
        if self.first_card.icon == self.second_card.icon:
            # Eşleşme var
            self.first_card.set_matched()
            self.second_card.set_matched()
            self.matched_pairs += 1
            
            # Toplam çift sayısı
            total_pairs = (self.rows * self.cols) // 2
            
            if self.matched_pairs == total_pairs:
                # Oyun bitti
                QTimer.singleShot(500, self.game_over)
        else:
            # Eşleşme yok
            self.first_card.flip(False)
            self.second_card.flip(False)
        
        self.first_card = None
        self.second_card = None
        self.is_locked = False
    
    def update_moves(self):
        """Hamle sayısını güncelle."""
        self.moves_label.setText(f"Hamle: {self.moves}")
    
    def game_over(self):
        """Oyun bitti."""
        # Skoru kaydet
        add_to_leaderboard(self.player_name, self.moves)
        
        # Sidebar'ı güncelle
        self.update_sidebar()
        
        # Lider tablosu dialog
        dialog = LeaderboardDialog(self.player_name, self.moves, self)
        if dialog.exec():
            self.start_new_game()
    
    def restart_game(self):
        """Oyunu yeniden başlat."""
        reply = QMessageBox.question(
            self,
            "Yeniden Başlat",
            "Oyunu yeniden başlatmak istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.start_new_game()
    
    def show_about(self):
        """Hakkında dialogunu göster."""
        QMessageBox.about(
            self,
            "Hakkında - Hafıza Oyunu",
            f"""🧠 Hafıza Oyunu v1.0

Bir kart eşleştirme oyunu.

Nasıl Oynanır:
• 16 kart (8 çift) var
• Kartlara tıklayarak çevirin
• Aynı ikonlu kartları eşleştirin
• En az hamlede kazanmaya çalışın!

Tasarım: MSOffice/OnlyOffice tarzı modern arayüz
Platform: Linux KDE uyumlu
"""
        )


# ============== UYGULAMA BAŞLANGICI ==============
def main():
    app = QApplication(sys.argv)
    
    # Uygulama stili
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    
    # Palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(COLORS['primary_bg']))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.ColorRole.Base, QColor(COLORS['primary_bg']))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(COLORS['secondary_bg']))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(COLORS['primary_bg']))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.ColorRole.Text, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.ColorRole.Button, QColor(COLORS['secondary_bg']))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.Link, QColor(COLORS['accent']))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(COLORS['accent']))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    app.setPalette(palette)
    
    window = MemoryGameWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()