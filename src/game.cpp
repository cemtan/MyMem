#include "game.h"
#include "scoremanager.h"
#include <QMessageBox>
#include <QRandomGenerator>

const QStringList ICONS = {
    "🦁", "🐯", "🐻", "🐼", "🍎", "🍊", "⚽", "🏀",
    "🎵", "🎸", "🚗", "✈️", "☀️", "❄️", "⌚", "💻",
    "🌲", "🌸", "🎮", "🎯", "📱", "🎬", "🧩", "🎭"
};

Game::Game(const QString& playerName, const QString& gridSize, 
           ScoreManager* scoreManager, QWidget *parent)
    : QWidget(parent)
    , m_playerName(playerName)
    , m_gridSize(gridSize)
    , m_scoreManager(scoreManager)
{
    if (gridSize == "4x4") { m_rows = 4; m_cols = 4; }
    else if (gridSize == "4x6") { m_rows = 4; m_cols = 6; }
    else if (gridSize == "5x6") { m_rows = 5; m_cols = 6; }
    else if (gridSize == "4x8") { m_rows = 4; m_cols = 8; }
    else { m_rows = 6; m_cols = 8; }
    
    m_totalPairs = (m_rows * m_cols) / 2;
    m_checkTimer = new QTimer(this);
    connect(m_checkTimer, &QTimer::timeout, this, &Game::checkMatch);
    initCards();
    setMinimumSize(1400, 900);
}

Game::~Game() {}

void Game::initCards() {
    m_cards.clear();
    m_moves = 0;
    m_matchedPairs = 0;
    m_firstFlipped = -1;
    m_secondFlipped = -1;
    m_gameActive = true;
    
    QStringList icons = ICONS.mid(0, m_totalPairs);
    icons += icons;
    for (int i = icons.size() - 1; i > 0; --i) {
        int j = QRandomGenerator::global()->bounded(i + 1);
        icons.swapItemsAt(i, j);
    }
    
    for (int i = 0; i < m_rows * m_cols; ++i) {
        Card card;
        card.id = i;
        card.pairId = ICONS.indexOf(icons[i]);
        card.icon = icons[i];
        m_cards.append(card);
    }
}

void Game::setPlayerName(const QString& name) {
    m_playerName = name;
    update();
}

void Game::mousePressEvent(QMouseEvent *event) {
    QPoint pos = event->pos();
    
    if (m_resetBtnRect.contains(pos)) {
        resetGame();
        return;
    }
    
    if (!m_gameActive) return;
    
    for (int i = 0; i < m_cards.size(); ++i) {
        if (m_cards[i].rect.contains(pos) && 
            !m_cards[i].isFlipped && !m_cards[i].isMatched) {
            flipCard(i);
            break;
        }
    }
}

void Game::flipCard(int index) {
    m_cards[index].isFlipped = true;
    
    if (m_firstFlipped == -1) {
        m_firstFlipped = index;
    } else {
        m_secondFlipped = index;
        m_moves++;
        m_gameActive = false;
        m_checkTimer->start(1000);
    }
    update();
}

void Game::checkMatch() {
    m_checkTimer->stop();
    
    Card& c1 = m_cards[m_firstFlipped];
    Card& c2 = m_cards[m_secondFlipped];
    
    if (c1.pairId == c2.pairId) {
        c1.isMatched = true;
        c2.isMatched = true;
        m_matchedPairs++;
        
        if (m_matchedPairs == m_totalPairs) {
            m_gameActive = false;
            m_scoreManager->addScore(m_playerName, m_moves, m_matchedPairs, m_gridSize);
            QMessageBox::information(this, "Oyun Bitti!",
                QString("Tebrikler %1!\n\nAdimlar: %2\nEslesmeler: %3/%4")
                    .arg(m_playerName).arg(m_moves).arg(m_matchedPairs).arg(m_totalPairs));
        }
    } else {
        c1.isFlipped = false;
        c2.isFlipped = false;
    }
    
    m_firstFlipped = -1;
    m_secondFlipped = -1;
    m_gameActive = true;
    update();
}

void Game::resetGame() {
    initCards();
    update();
}

void Game::paintEvent(QPaintEvent *) {
    QPainter painter(this);
    painter.setRenderHint(QPainter::Antialiasing);
    
    painter.fillRect(rect(), QColor(245, 248, 255));
    
    // Sol panel (skorlar)
    int w = 250;
    painter.fillRect(0, 0, w, height(), Qt::white);
    
    QPen linePen(QColor(229, 229, 229), 1);
    painter.setPen(linePen);
    painter.drawLine(w, 0, w, height());
    
    QFont titleFont("Segoe UI", 14, QFont::Bold);
    painter.setFont(titleFont);
    painter.setPen(QColor(25, 103, 210));
    painter.drawText(15, 30, QString("Siralaman (%1)").arg(m_gridSize));
    painter.setPen(linePen);
    painter.drawLine(15, 40, w - 15, 40);
    
    // Skorlar
    auto scores = m_scoreManager->getTopScores(m_gridSize);
    QFont scoreFont("Segoe UI", 10);
    QStringList medals = {"1.", "2.", "3."};
    
    for (int i = 0; i < qMin(10, scores.size()); ++i) {
        int y = 60 + i * 20;
        if (i % 2 == 1) painter.fillRect(10, y - 14, w - 20, 18, QColor(245, 245, 245));
        painter.setFont(scoreFont);
        painter.setPen(QColor(33, 33, 33));
        QString name = scores[i].toMap()["name"].toString();
        if (name.length() > 14) name = name.left(14);
        painter.drawText(15, y, medals.value(i < 3 ? i : 0));
        painter.drawText(40, y, name);
        painter.setPen(QColor(25, 103, 210));
        painter.drawText(180, y, QString::number(scores[i].toMap()["moves"].toInt()));
    }
    
    // Üst panel
    painter.fillRect(250, 0, width() - 250, 70, QColor(245, 248, 255));
    painter.setPen(linePen);
    painter.drawLine(250, 69, width(), 69);
    
    QFont infoFont("Segoe UI", 12, QFont::Bold);
    painter.setFont(infoFont);
    painter.setPen(QColor(25, 103, 210));
    painter.drawText(265, 25, QString("Oyuncu: %1").arg(m_playerName));
    painter.setPen(QColor(100, 100, 100));
    painter.drawText(265, 50, "Adimlar:");
    painter.setPen(QColor(25, 103, 210));
    painter.drawText(340, 50, QString::number(m_moves));
    painter.setPen(QColor(100, 100, 100));
    painter.drawText(420, 50, "Eslesmeler:");
    painter.setPen(QColor(25, 103, 210));
    painter.drawText(530, 50, QString("%1/%2").arg(m_matchedPairs).arg(m_totalPairs));
    
    // Kartlar
    int cardW = (width() - 270) / m_cols - 4;
    int cardH = (height() - 80) / m_rows - 4;
    int startX = 260, startY = 75;
    
    for (int i = 0; i < m_cards.size(); ++i) {
        int row = i / m_cols, col = i % m_cols;
        m_cards[i].rect = QRect(startX + col * (cardW + 4), startY + row * (cardH + 4), cardW, cardH);
        drawCard(&painter, m_cards[i]);
    }
    
    // Reset butonu
    m_resetBtnRect = QRect(width() - 170, 12, 155, 46);
    QColor bg(52, 152, 219);
    painter.fillRect(m_resetBtnRect, bg);
    painter.drawRoundedRect(m_resetBtnRect, 4, 4);
    painter.setPen(Qt::white);
    QFont btnFont("Segoe UI", 11, QFont::Bold);
    painter.setFont(btnFont);
    painter.drawText(m_resetBtnRect, Qt::AlignCenter, "Yeniden");
}

void Game::drawCard(QPainter* painter, const Card& card) {
    QRect r = card.rect;
    
    if (card.isMatched) {
        painter->fillRect(r, QColor(76, 175, 80));
    } else if (card.isFlipped) {
        painter->fillRect(r, QColor(25, 118, 210));
    } else {
        painter->fillRect(r, QColor(224, 224, 224));
    }
    
    painter->setPen(QPen(card.isMatched ? QColor(56, 142, 60) : 
                       card.isFlipped ? QColor(13, 71, 161) : 
                       QColor(158, 158, 158), 1));
    painter->drawRoundedRect(r, 6, 6);
    
    if (card.isFlipped || card.isMatched) {
        painter->setPen(Qt::white);
        QFont iconFont("Segoe UI Emoji", qMin(r.width(), r.height()) / 2);
        painter->setFont(iconFont);
        painter->drawText(r, Qt::AlignCenter, card.icon);
    }
}
