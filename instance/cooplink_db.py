import sqlite3

# Create CoopLink database
db = sqlite3.connect("C:\Github_repo\Cooplink\instance\cooplink.db")
cursor = db.cursor()

# -------------------------
# Core Tables
# -------------------------



# Store bug/error reports from each project
cursor.execute("""
DROP TABLE IF EXISTS sqlite_sequence""")

print("changes saved successfully!")




# Save and close
db.commit()
db.close()