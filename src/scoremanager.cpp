#include "scoremanager.h"
#include <QJsonDocument>
#include <QJsonObject>

ScoreManager::ScoreManager(QObject *parent)
    : QObject(parent)
    , m_scoresFile("/tmp/memory_game/scores_steps.json")
{
    m_leaderboard = loadScores();
}

QVariantMap ScoreManager::loadScores() {
    QFile file(m_scoresFile);
    if (!file.open(QIODevice::ReadOnly)) {
        return QVariantMap();
    }
    
    QByteArray data = file.readAll();
    file.close();
    
    QJsonParseError error;
    QJsonDocument doc = QJsonDocument::fromJson(data, &error);
    
    if (error.error != QJsonParseError::NoError) {
        return QVariantMap();
    }
    
    return doc.object().toVariantMap();
}

void ScoreManager::saveScores(const QVariantMap& data) {
    QFile file(m_scoresFile);
    if (!file.open(QIODevice::WriteOnly)) {
        return;
    }
    
    QJsonDocument doc = QJsonObject::fromVariantMap(data);
    file.write(doc.toJson());
    file.close();
}

void ScoreManager::addScore(const QString& playerName, int moves, int matched, const QString& gridSize) {
    QVariantList scores = m_leaderboard[gridSize].toList();
    
    QVariantMap entry;
    entry["name"] = playerName;
    entry["moves"] = moves;
    entry["matched"] = matched;
    entry["date"] = QDateTime::currentDateTime().toString("yyyy-MM-dd HH:mm");
    
    scores.append(entry);
    m_leaderboard[gridSize] = scores;
    saveScores(m_leaderboard);
}

QVariantList ScoreManager::getTopScores(const QString& gridSize) {
    if (!m_leaderboard.contains(gridSize)) {
        return QVariantList();
    }
    return m_leaderboard[gridSize].toList();
}
