import sqlite3

def init_db():
    conn = sqlite3.connect('notes.db')
    cursor = conn.cursor()

    # создаем таблицу notes с колонками created_at и updated_at
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY, 
            title TEXT, 
            content TEXT, 
            favorite INTEGER DEFAULT 0, 
            category TEXT DEFAULT "General",
            is_pinned INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
# переключение статуса закрепления
def toggle_pin(note_id):
    try:
        conn = sqlite3.connect('notes.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE notes SET is_pinned = NOT is_pinned WHERE id = ?", (note_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()
# функция для добавления новой заметки в базу данных
def add_note_to_db(title, content, category):
    conn = sqlite3.connect('notes.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO notes (title, content, category, created_at, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)', (title, content, category))
    conn.commit()
    conn.close()

# получение всех заметок из базы данных
def get_all_notes():
    conn = sqlite3.connect('notes.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content, favorite, category, is_pinned FROM notes")
    notes = cursor.fetchall()
    conn.close()
    return notes

# получение содержимого заметки по id
def get_note_content(note_id):
    conn = sqlite3.connect('notes.db')
    cursor = conn.cursor()
    cursor.execute('SELECT title, content, category FROM notes WHERE id = ?', (int(note_id),))
    note = cursor.fetchone()
    conn.close()
    return note if note else ("", "", "")  # возвращаем пустой кортеж, если заметка не найдена


# удаление заметки
def delete_note_from_db(note_id):
    conn = sqlite3.connect('notes.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    conn.commit()
    conn.close()

# переключение избранного
def toggle_favorite(note_id):
    conn = sqlite3.connect("notes.db")
    cursor = conn.cursor()

    cursor.execute("UPDATE notes SET favorite = NOT favorite WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()


def update_note_content(note_id, title=None, content=None, category=None):
    conn = sqlite3.connect('notes.db')
    cursor = conn.cursor()

    # формируем список значений для обновления
    updates = []
    params = []

    if title is not None:
        updates.append("title = ?")
        params.append(title)
    if content is not None:
        updates.append("content = ?")
        params.append(content)
    if category is not None:
        updates.append("category = ?")
        params.append(category)

    if updates:
        # обновляем все поля, если они указаны
        params.append(note_id)
        cursor.execute(f"UPDATE notes SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", params)

    conn.commit()
    conn.close()


