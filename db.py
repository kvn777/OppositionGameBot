import sqlite3

class Database:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def set(self, table, values):
        # create request to insert data
        query = "INSERT OR IGNORE INTO {} ({}) VALUES ({})".format(
            table,
            ', '.join(values.keys()), 
            ', '.join('?'*len(values))
        )
        # execute request
        self.cursor.execute(query, tuple(values.values()))
        self.conn.commit()

    def get(self, table, where=None):
        # create request to select data
        query = "SELECT * FROM {}".format(table)
        if where:
            query += " WHERE {}".format(where)
        # execute request
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        if rows is None:
            return None
        return rows
    
    def get_by_id(self, table, id):
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM {table} WHERE id=?", (id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return row
    
    def del_by_id(self, table, id):
        cursor = self.conn.cursor()
        cursor.execute(f"DELETE FROM {table} WHERE id=?", (id,))
        self.conn.commit()

    def __del__(self):
        # close connection
        self.conn.close()

    def create_game_tables(self, game_id=None):
        if game_id:
            self.cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS game_{game_id} (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    role TEXT NULL,
                    mc INTEGER NULL,
                    round INTEGER NULL
                )
            ''')

            # save changes to database
            self.conn.commit() 

    def create_tables(self):
        # create request to create tables
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                lang CHAR(2) NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                cause_name TEXT NOT NULL
            )
        ''')

        # save changes to database
        self.conn.commit()        