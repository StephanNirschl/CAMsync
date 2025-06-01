import sqlite3
from datetime import datetime
import os

def log_project_event(db_path, project_name, username, action):
    """
    Loggt ein Ereignis (Download/Upload) in der Tabelle 'project_logs'.
    Erstellt die Tabelle bei Bedarf.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS project_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    c.execute(
        "INSERT INTO project_logs (project_name, username, action, timestamp) VALUES (?, ?, ?, ?)",
        (project_name, username, action, datetime.now().isoformat())
    )

    conn.commit()
    conn.close()

def get_project_log_summary(project_name, db_path):
    import os
    import sqlite3
    from datetime import datetime

    if not os.path.exists(db_path):
        return ""

    # 🔧 Projektname bereinigen
    project_name = project_name.split("__LOCKED")[0].split("__locked")[0]

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("""
        SELECT username, action, timestamp 
        FROM project_log 
        WHERE project_name = ? 
        ORDER BY timestamp DESC
        LIMIT 5
    """, (project_name,))
    entries = c.fetchall()
    conn.close()

    if not entries:
        return "Keine Aktionen gefunden."

    lines = []
    for user, action, ts in entries:
        time_str = datetime.fromisoformat(ts).strftime("%Y-%m-%d %H:%M")
        lines.append(f"{action.upper()} durch {user} am {time_str}")

    return "\n".join(lines)

def log_project_action(project_name, username, action, db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    #print(f"LOGGING: {project_name=} {username=} {action=}")
    #print(f"[LOGGING] db_path: {db_path}")

    
    # Tabelle erstellen, falls sie noch nicht existiert
    c.execute("""
        CREATE TABLE IF NOT EXISTS project_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    # Aktion eintragen
    c.execute("""
        INSERT INTO project_log (project_name, username, action, timestamp)
        VALUES (?, ?, ?, ?)
    """, (project_name, username, action, datetime.now().isoformat()))

    conn.commit()
    conn.close()