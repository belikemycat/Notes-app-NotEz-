import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QTextEdit, QPushButton, QListWidget, \
    QComboBox, QMenu, QLabel, QMessageBox, QHBoxLayout, QDialog, QDialogButtonBox
from PyQt5.QtCore import Qt, QPoint
from db import init_db, add_note_to_db, get_all_notes, get_note_content, delete_note_from_db, update_note_content, \
    toggle_favorite, toggle_pin
from PyQt5.QtGui import QIcon,QFont


class NoteEditor(QWidget):
    #Экран для редактирования/создания заметок
    def __init__(self, note_id=None, on_save_callback=None, is_dark_theme=False):
        super().__init__()
        self.note_id = note_id
        self.on_save_callback = on_save_callback  # Callback для обновления списка заметок
        self.is_dark_theme = is_dark_theme  # сохранение темы
        self.setWindowTitle("Edit the note")
        self.setFixedSize(400, 300)  # размер окна приложения

        # поле для заголовка заметки
        self.title_input = QLineEdit(self)
        self.title_input.setPlaceholderText("Title")

        # поле для контента заметки
        self.content_input = QTextEdit(self)

        # поле для выбора категории при создании/редактировании
        self.category_input = QComboBox(self)
        self.category_input.addItems(["All", "Work", "Ideas", "Favorite"])  # категории

        # кнопка сохранения заметки
        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.save_note)

        # создаем layout
        layout = QVBoxLayout()
        layout.addWidget(self.title_input)
        layout.addWidget(self.content_input)
        layout.addWidget(QLabel("Category:"))  # добавляем метку для поля категории
        layout.addWidget(self.category_input)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

        if self.note_id:
            self.load_note()

        self.apply_theme()  # применяем тему при инициализации

    def apply_theme(self):
        # применяем тему к редактору заметок
        if self.is_dark_theme:
            self.setStyleSheet("background-color: #444444; color: white;")
            self.title_input.setStyleSheet("background-color: #555555; color: white;")
            self.content_input.setStyleSheet("background-color: #555555; color: white;")
            self.save_button.setStyleSheet("background-color: #555555; color: white;")
        else:
            self.setStyleSheet("background-color: white; color: black;")
            self.title_input.setStyleSheet("background-color: white; color: black;")
            self.content_input.setStyleSheet("background-color: white; color: black;")
            self.save_button.setStyleSheet("background-color: #DDDDDD; color: black;")

    def load_note(self):
        # Загружаем данные заметки по её ID
        title, content, category = get_note_content(self.note_id)
        self.title_input.setText(title)
        self.content_input.setPlainText(content)  # устанавливаем контент
        self.category_input.setCurrentText(category)  # устанавливаем категорию

    def save_note(self):
        # сохранение заметки
        title = self.title_input.text().strip()
        content = self.content_input.toPlainText().strip()
        category = self.category_input.currentText()  # получаем выбранную категорию

        # если есть звездочка то добавляем в избранное
        if '⭐' in title:
            category = "Favorite"

        if not title:
            QMessageBox.warning(self, "Error", "Name the note!")
            return

        try:
            if self.note_id:
                # обновляем существующую заметку
                update_note_content(self.note_id, title, content, category)  # обновляем с новой категорией
            else:
                # создаем новую заметку
                add_note_to_db(title, content, category)  # создаем с выбранной категорией

            if self.on_save_callback:
                self.on_save_callback()  # Вызываем callback для обновления списка заметок
            self.close()  # Закрываем редактор заметок
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save the note :( : {e}")


class CategoryDialog(QDialog):
    # диалог для выбора категории

    def __init__(self, categories, on_select_callback, is_dark_theme=False):
        super().__init__()
        self.setWindowTitle("Choose the category")
        self.setFixedSize(200, 150)

        self.on_select_callback = on_select_callback
        self.is_dark_theme = is_dark_theme  # добавляем переменную для темы

        layout = QVBoxLayout()

        self.category_list = QListWidget(self)
        self.category_list.addItems(categories)
        self.category_list.itemClicked.connect(self.select_category)

        layout.addWidget(self.category_list)

        self.setLayout(layout)
        self.apply_theme()  # применяем тему при инициализации

    def apply_theme(self):
        if self.is_dark_theme:
            self.setStyleSheet("background-color: #444444; color: white;")
            self.category_list.setStyleSheet("background-color: #555555; color: white;")
        else:
            self.setStyleSheet("background-color: white; color: black;")
            self.category_list.setStyleSheet("background-color: white; color: black;")

    def select_category(self, item):
        # выбор категории и закрытие диалога
        selected_category = item.text()
        self.on_select_callback(selected_category)  # вызываем callback с выбранной категорией
        self.close()


class NotesApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NotEZ")
        self.setFixedSize(600, 400)  # Размер окна

        # Список заметок
        self.notes_list = QListWidget(self)
        self.notes_list.itemClicked.connect(self.open_note_editor)
        self.notes_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.notes_list.customContextMenuRequested.connect(self.show_context_menu)

        # поле для поиска заметок
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Search a note...")
        self.search_input.textChanged.connect(self.filter_notes)  # подключаем сигнал для поиска

        # кнопка создания новой заметки
        self.new_note_button = QPushButton("➕ New Note", self)
        self.new_note_button.clicked.connect(self.create_new_note)

        # эмодзи для переключения темы
        self.theme_toggle_button = QPushButton("🌙", self)  # Начнем с темной темы
        self.theme_toggle_button.clicked.connect(self.toggle_theme)

        # Кнопка для выбора категории
        self.category_button = QPushButton("⚙️", self)  # Шестеренка
        self.category_button.clicked.connect(self.open_category_dialog)

        # Создаем layout
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.new_note_button)
        bottom_layout.addWidget(self.search_input)  # Добавляем поле поиска
        bottom_layout.addWidget(self.theme_toggle_button)  # Добавляем кнопку для переключения темы
        bottom_layout.addWidget(self.category_button)  # Добавляем кнопку для выбора категории

        layout = QVBoxLayout()
        layout.addWidget(self.notes_list)
        layout.addLayout(bottom_layout)

        self.setLayout(layout)

        self.is_dark_theme = False  # переменная для отслеживания темы
        self.apply_theme()

        init_db()  # инициализируем базу данных
        self.load_notes()

    def apply_theme(self):
        if self.is_dark_theme:
            self.setStyleSheet("background-color: #2E2E2E; color: white;")
            self.notes_list.setStyleSheet("background-color: #444444; color: white;")
            self.search_input.setStyleSheet("background-color: #555555; color: white;")
            self.new_note_button.setStyleSheet("background-color: #444444; color: white;")
            self.theme_toggle_button.setStyleSheet("background-color: #444444; color: white;")
            self.category_button.setStyleSheet("background-color: #444444; color: white;")
            self.theme_toggle_button.setText("☀️")  # Изменяем эмодзи на солнце
        else:
            self.setStyleSheet("background-color: white; color: black;")
            self.notes_list.setStyleSheet("background-color: white; color: black;")
            self.search_input.setStyleSheet("background-color: white; color: black;")
            self.new_note_button.setStyleSheet("background-color: #DDDDDD; color: black;")
            self.theme_toggle_button.setStyleSheet("background-color: #DDDDDD; color: black;")
            self.category_button.setStyleSheet("background-color: #DDDDDD; color: black;")
            self.theme_toggle_button.setText("🌙")  # изменяем эмодзи на луну

    def toggle_theme(self):
        # переключение темы
        self.is_dark_theme = not self.is_dark_theme
        self.apply_theme()

        # если редактор открыт, обновляем его
        if hasattr(self, 'note_editor') and self.note_editor.isVisible():
            self.note_editor.is_dark_theme = self.is_dark_theme  # сохраняем состояние темы
            self.note_editor.apply_theme()  # применяем тему к редактору

    def load_notes(self, category_filter=None):
        # загружаем заметки из базы данных с фильтром по категории
        self.notes_list.clear()
        self.all_notes = get_all_notes()

        # фильтруем заметки по категории, если она задана
        if category_filter and category_filter != "All":
            self.all_notes = [note for note in self.all_notes if
                              note[4] == category_filter]  # применяем фильтр по категории

        # разделяем заметки на закреплённые и обычные
        pinned_notes = [note for note in self.all_notes if note[5]]  # проверяем is_pinned
        regular_notes = [note for note in self.all_notes if not note[5]]

        # добавляем закреплённые заметки сначала
        for note in pinned_notes:
            note_id, title, content, favorite, category, is_pinned = note
            note_text = f"{note_id}: {title} 📌"  # Добавляем эмодзи закрепления
            self.notes_list.addItem(note_text)

        # затем обычные заметки
        for note in regular_notes:
            note_id, title, content, favorite, category, is_pinned = note
            note_text = f"{note_id}: {title} {'⭐' if favorite else ''}"
            self.notes_list.addItem(note_text)

    def filter_notes(self):
        search_text = self.search_input.text().lower()
        self.notes_list.clear()

        print("All notes:", self.all_notes)  # отладочное сообщение

        if not self.all_notes:
            return

        for note in self.all_notes:
            try:
                note_id, title, content, favorite, category , is_pinned = note
                if search_text in title.lower() or search_text in content.lower():
                    note_text = f"{note_id}: {title} {'⭐' if favorite else ''}"
                    self.notes_list.addItem(note_text)
            except Exception as e:
                print("Error:", e)  # отладочное сообщение

    def open_note_editor(self, item):
        try:
            note_id = int(item.text().split(":")[0])  # получаем ID заметки
            self.note_editor = NoteEditor(note_id, self.load_notes, self.is_dark_theme)  # Передаем состояние темы
            self.note_editor.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Can not open the note: {e}")

    def create_new_note(self):
        self.note_editor = NoteEditor(on_save_callback=self.load_notes)  # передаем callback
        self.note_editor.show()

    def show_context_menu(self, pos):
        # для правой мыши функции
        menu = QMenu(self)
        delete_action = menu.addAction("Delete the note")
        toggle_favorite_action = menu.addAction("Favorite")
        toggle_pin_action = menu.addAction("Pin/Unpin")  # добавлено действие

        action = menu.exec_(self.notes_list.mapToGlobal(pos))

        if action == delete_action:
            self.delete_note()
        elif action == toggle_favorite_action:
            self.toggle_favorite()
        elif action == toggle_pin_action:
            self.toggle_pin()  # обработчик для закрепления

    def toggle_pin(self):
        # переключатель закрепа
        current_item = self.notes_list.currentItem()
        if current_item:
            note_id = int(current_item.text().split(":")[0])  # получаем ID заметки
            try:
                toggle_pin(note_id)  # переключаем статус в базе данных
                self.load_notes()  # обновляем список заметок
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Can not pin the note: {e}")

    def delete_note(self):
        # удаление заметки
        current_item = self.notes_list.currentItem()
        if current_item:
            note_id = int(current_item.text().split(":")[0])  # Получаем ID заметки
            delete_note_from_db(note_id)
            self.load_notes()  # Обновляем список заметок

    def toggle_favorite(self):
        # переключение статуса избранного
        current_item = self.notes_list.currentItem()
        if current_item:
            note_id = int(current_item.text().split(":")[0])  # Получаем ID заметки
            toggle_favorite(note_id)
            self.load_notes()  # Обновляем список заметок

    def open_category_dialog(self):
        dialog = CategoryDialog(["All", "Work", "Ideas", "Favorite"], self.select_category, self.is_dark_theme)
        dialog.exec_()

    def select_category(self, category):
        # выбирает категорию и загружает заметки для этой категории
        self.load_notes(category_filter=category)  # Загружаем заметки с фильтром


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("notez_icon.jpg"))  #icon
    font = QFont("Verdana", 10)   #font
    app.setFont(font)
    window = NotesApp()
    window.show()
    sys.exit(app.exec_())
