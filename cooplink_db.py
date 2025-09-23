import sqlite3

# Create CoopLink database
db = sqlite3.connect("cooplink.db")
cursor = db.cursor()

# -------------------------
# Core Tables
# -------------------------

# List of all projects CoopLink manages
cursor.execute("""
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,       -- Project name (e.g., Campus Suite, Orphanage App)
    description TEXT,
    db_path TEXT NOT NULL,           -- Path to that project’s SQLite DB
    status TEXT DEFAULT 'active',    -- active / inactive / archived
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Registered modules/features inside each project
cursor.execute("""
CREATE TABLE IF NOT EXISTS project_modules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    module_name TEXT,                -- e.g., User Management, Printing, Map
    description TEXT,
    status TEXT DEFAULT 'enabled',
    FOREIGN KEY (project_id) REFERENCES projects(id)
)
""")

# Store bug/error reports from each project
cursor.execute("""
CREATE TABLE IF NOT EXISTS error_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    module_id INTEGER,
    error_message TEXT,
    severity TEXT,                   -- info / warning / critical
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (module_id) REFERENCES project_modules(id)
)
""")

# General system monitoring per project
cursor.execute("""
CREATE TABLE IF NOT EXISTS monitoring (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    active_users INTEGER,
    uptime REAL,                     -- % uptime
    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
)
""")

# Analytics across projects
cursor.execute("""
CREATE TABLE IF NOT EXISTS analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    metric_name TEXT,                -- e.g., "print_jobs", "events_created"
    metric_value REAL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
)
""")

# System settings for CoopLink itself
cursor.execute("""
CREATE TABLE IF NOT EXISTS cooplink_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE,
    value TEXT
)
""")

# Save and close
db.commit()
db.close()