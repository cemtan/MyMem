#ifndef SCOREMANAGER_H
#define SCOREMANAGER_H

#include <QObject>
#include <QVariantList>
#include <QVariantMap>
#include <QJsonDocument>
#include <QJsonObject>
#include <QFile>

class ScoreManager : public QObject {
    Q_OBJECT
public:
    explicit ScoreManager(QObject *parent = nullptr);
    
    void addScore(const QString& playerName, int moves, int matched, const QString& gridSize);
    QVariantList getTopScores(const QString& gridSize);
    
private:
    QVariantMap loadScores();
    void saveScores(const QVariantMap& data);
    
    QString m_scoresFile;
    QVariantMap m_leaderboard;
};

#endif
