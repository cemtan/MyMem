#ifndef GAME_H
#define GAME_H

#include <QWidget>
#include <QVector>
#include <QTimer>
#include <QMouseEvent>
#include <QPaintEvent>
#include <QPainter>
#include <QColor>
#include <QFont>
#include <QRect>
#include <QString>
#include <QStringList>

class ScoreManager;

struct Card {
    int id;
    int pairId;
    QString icon;
    bool isFlipped = false;
    bool isMatched = false;
    QRect rect;
};

class Game : public QWidget {
    Q_OBJECT
public:
    explicit Game(const QString& playerName, const QString& gridSize,
                  ScoreManager* scoreManager, QWidget *parent = nullptr);
    ~Game();
    void setPlayerName(const QString& name);

private slots:
    void checkMatch();
    void resetGame();

protected:
    void mousePressEvent(QMouseEvent *event) override;
    void paintEvent(QPaintEvent *event) override;

private:
    void initCards();
    void flipCard(int index);
    void drawCard(QPainter* p, const Card& c);

    QVector<Card> m_cards;
    QString m_playerName;
    QString m_gridSize;
    ScoreManager* m_scoreManager;
    
    int m_rows = 6, m_cols = 8;
    int m_totalPairs = 24, m_matchedPairs = 0;
    int m_moves = 0;
    int m_firstFlipped = -1, m_secondFlipped = -1;
    bool m_gameActive = true;
    QTimer* m_checkTimer;
    QRect m_resetBtnRect;
};

#endif
