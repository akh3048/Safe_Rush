# -*- coding: utf-8 -*-
"""SQLite 저장소: 랭킹과 설정"""
import os
import sqlite3
import datetime

from .utils import user_data_dir


class Database:
    def __init__(self, path=None):
        if path is None:
            folder = user_data_dir()
            path = os.path.join(folder, "safe_rush.db") if folder else ":memory:"
        try:
            self.conn = sqlite3.connect(path)
        except sqlite3.Error:
            self.conn = sqlite3.connect(":memory:")   # 저장이 안 되는 환경에서도 게임은 돌아가게
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS ranking ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " difficulty TEXT NOT NULL,"
            " initials TEXT NOT NULL,"
            " time_ms INTEGER NOT NULL,"
            " skips INTEGER NOT NULL DEFAULT 0,"
            " created_at TEXT NOT NULL)"
        )
        self.conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        if self.get_setting("migrated_hard") != "1":      # 예전 '챌린지' 기록은 새 이름인 '어려움'으로 옮겨요 (한 번만)
            self.conn.execute("UPDATE ranking SET difficulty='hard' WHERE difficulty='challenge'")
            self.set_setting("migrated_hard", "1")
        self.conn.commit()

    # ---- 설정
    def get_setting(self, key, default=None):
        row = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    def set_setting(self, key, value):
        self.conn.execute("INSERT OR REPLACE INTO settings(key, value) VALUES (?, ?)", (key, str(value)))
        self.conn.commit()

    # ---- 랭킹 (기록은 밀리초 정수로 저장해서 소수 오차를 피해요)
    def add_record(self, difficulty, initials, time_ms, skips):
        cur = self.conn.execute(
            "INSERT INTO ranking(difficulty, initials, time_ms, skips, created_at) VALUES (?, ?, ?, ?, ?)",
            (difficulty, initials, int(time_ms), int(skips), datetime.datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        self.conn.commit()
        return cur.lastrowid

    def top(self, difficulty, limit=10):
        """[(id, initials, time_ms, skips, created_at), ...]  빠른 기록 순, 같으면 먼저 달성한 기록이 위"""
        return self.conn.execute(
            "SELECT id, initials, time_ms, skips, created_at FROM ranking"
            " WHERE difficulty=? ORDER BY time_ms ASC, id ASC LIMIT ?",
            (difficulty, limit),
        ).fetchall()

    def rank_of(self, rec_id, difficulty):
        rows = self.conn.execute(
            "SELECT id FROM ranking WHERE difficulty=? ORDER BY time_ms ASC, id ASC", (difficulty,)
        ).fetchall()
        for i, (rid,) in enumerate(rows):
            if rid == rec_id:
                return i + 1
        return None

    def count(self, difficulty):
        return self.conn.execute("SELECT COUNT(*) FROM ranking WHERE difficulty=?", (difficulty,)).fetchone()[0]
