#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QLineEdit>
#include "game.h"
#include "scoremanager.h"

class MainWindow : public QMainWindow {
    Q_OBJECT
public:
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    void newGame();
    void restartGame();
    void changeGridSize(const QString& size);
    void changePlayerName();

private:
    void createMenuBar();
    QString getPlayerName();
    
    Game* m_game;
    ScoreManager* m_scoreManager;
    QString m_playerName;
    QString m_gridSize;
};

#endif
