#include "mainwindow.h"
#include <QMenu>
#include <QInputDialog>
#include <QMessageBox>
#include <QAction>
#include <QLineEdit>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , m_game(nullptr)
    , m_scoreManager(new ScoreManager(this))
    , m_gridSize("6x8")
{
    m_playerName = getPlayerName();
    if (m_playerName.isEmpty()) {
        close();
        return;
    }
    
    createMenuBar();
    m_game = new Game(m_playerName, m_gridSize, m_scoreManager, this);
    setCentralWidget(m_game);
    
    setWindowTitle(QString("Modern Eslestirme - %1 - %2").arg(m_playerName).arg(m_gridSize));
}

MainWindow::~MainWindow() {}

QString MainWindow::getPlayerName() {
    bool ok;
    QString name = QInputDialog::getText(this, "Hos Geldiniz", 
                                    "Adinizi girin:", 
                                    QLineEdit::Normal, 
                                    "Oyuncu", 
                                    &ok);
    return ok ? name.trimmed() : QString();
}

void MainWindow::createMenuBar() {
    QMenu* gameMenu = menuBar()->addMenu("Oyun");
    
    QAction* newAct = new QAction("Yeni Oyun", this);
    newAct->setShortcut(QKeySequence("Ctrl+N"));
    connect(newAct, &QAction::triggered, this, &MainWindow::newGame);
    gameMenu->addAction(newAct);
    
    QAction* restartAct = new QAction("Yeniden Baslat", this);
    restartAct->setShortcut(QKeySequence("Ctrl+R"));
    connect(restartAct, &QAction::triggered, this, &MainWindow::restartGame);
    gameMenu->addAction(restartAct);
    
    gameMenu->addSeparator();
    
    QMenu* gridMenu = new QMenu("Kart Adedi", this);
    
    QStringList sizes = {"4x4", "4x6", "5x6", "4x8", "6x8"};
    QStringList labels = {"4x4 (16 kart)", "4x6 (24 kart)", "5x6 (30 kart)", "4x8 (32 kart)", "6x8 (48 kart)"};
    
    for (int i = 0; i < sizes.size(); ++i) {
        QAction* act = new QAction(labels[i], this);
        connect(act, &QAction::triggered, this, [this, &sizes, i]() {
            changeGridSize(sizes[i]);
        });
        gridMenu->addAction(act);
    }
    gameMenu->addMenu(gridMenu);
    
    gameMenu->addSeparator();
    
    QAction* exitAct = new QAction("Cikis", this);
    exitAct->setShortcut(QKeySequence("Ctrl+Q"));
    connect(exitAct, &QAction::triggered, this, &QMainWindow::close);
    gameMenu->addAction(exitAct);
    
    QMenu* playerMenu = menuBar()->addMenu("Oyuncu");
    QAction* nameAct = new QAction("Isim Degistir", this);
    connect(nameAct, &QAction::triggered, this, &MainWindow::changePlayerName);
    playerMenu->addAction(nameAct);
}

void MainWindow::newGame() {
    QString name = QInputDialog::getText(this, "Yeni Oyun", 
                                   "Oyuncu adi:", 
                                   QLineEdit::Normal, 
                                   m_playerName);
    if (!name.trimmed().isEmpty()) {
        m_playerName = name.trimmed();
        restartGame();
    }
}

void MainWindow::restartGame() {
    delete m_game;
    m_game = new Game(m_playerName, m_gridSize, m_scoreManager, this);
    setCentralWidget(m_game);
    setWindowTitle(QString("Modern Eslestirme - %1 - %2").arg(m_playerName).arg(m_gridSize));
}

void MainWindow::changeGridSize(const QString& size) {
    m_gridSize = size;
    restartGame();
}

void MainWindow::changePlayerName() {
    QString name = QInputDialog::getText(this, "Oyuncu", 
                                    "Yeni isminiz:", 
                                    QLineEdit::Normal, 
                                    m_playerName);
    if (!name.trimmed().isEmpty()) {
        m_playerName = name.trimmed();
        setWindowTitle(QString("Modern Eslestirme - %1 - %2").arg(m_playerName).arg(m_gridSize));
        if (m_game) {
            m_game->setPlayerName(m_playerName);
        }
    }
}
