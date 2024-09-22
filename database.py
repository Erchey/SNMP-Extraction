import sqlite3

def store_data_in_db(db_path, data, uptime, in_traffic, out_traffic):

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS DataMonitor(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        total_traf INTEGER,
                        uptime INTEGER,
                        in_traf INTEGER,
                        out_traf INTEGER
                        )''')
    
    cursor.execute('''
        INSERT INTO DataMonitor (total_traf, uptime, in_traf, out_traf)
        VALUES (?, ?, ?, ?)
    ''', (data, uptime, in_traffic, out_traffic))

    connection.commit()
    connection.close()
    print(f"Stored data: {data} and uptime: {uptime} in the database.")