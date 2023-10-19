import json
import subprocess
import requests
import webbrowser
from PyQt5 import QtWidgets

from PyQt5.QtGui import QColor, QIcon, QPalette


from instruction_ui import Ui_Dialog
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QDialog, QDialogButtonBox, QFileDialog, QLineEdit, QMainWindow, QMenu, QVBoxLayout, QPushButton,
    QRadioButton,
    QButtonGroup, QComboBox, QMessageBox, QDialog, QAction
)


def check_for_updates(repository_url, current_version):
    try:
        response = requests.get(repository_url + '/releases/latest')
        response.raise_for_status()

        latest_release = response.json()
        latest_version = latest_release['tag_name']

        if latest_version != current_version:
            return latest_version
        else:
            return None  # У вас уже установлена последняя версия
    except requests.exceptions.RequestException:
        return None  # Ошибка при обращении к GitHub

# Укажите URL вашего репозитория на GitHub
repository_url = 'https://github.com/GigaBlyate/SeeKer.git'

# Укажите текущую версию вашей программы
current_version = '1.0.0'

latest_version = check_for_updates(repository_url, current_version)

if latest_version:
    print(f'Доступна новая версия: {latest_version}. Пожалуйста, обновитесь.')
else:
    print('У вас установлена последняя версия.')

Form, Window = uic.loadUiType("main_window.ui")
app = QApplication([])

parts_list = []  # Изменено: объявление списка parts_list
components_list = []  # Изменено: объявление списка components_list

def save_theme_state(filename, state):
    with open(filename, 'w') as file:
        json.dump(state, file)

def load_theme_state(filename):
    try:
        with open(filename, 'r') as file:
            state = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        state = None
    return state

# Путь к файлу, в котором будет храниться состояние темы
theme_state_file = 'theme_state.json'

# Попытка загрузить состояние темы
theme_state = load_theme_state(theme_state_file)

if theme_state is not None:
    # Применяем состояние темы
    if theme_state.get('dark_theme_enabled', False):
        app.setStyleSheet(open("styles.qss", "r").read())
        dark_theme_enabled = True


class InstructionWindow(QMainWindow, Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)


# Функция для загрузки списка из JSON-файла или создания нового списка
def load_or_create_list(filename, default_value):
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = default_value
    return data


# Функция для сохранения списка в JSON-файл
def save_list(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file)


class AddSiteDialog(QDialog):
    def __init__(self, parts_list, components_list):
        super().__init__()
        self.setWindowTitle("Добавить сайт")
        self.setWindowIcon(QIcon("iconka.ico"))
        self.setFixedSize(400, 260)
        self.parts_list = parts_list
        self.components_list = components_list
        self.layout = QVBoxLayout()

        self.site_name_input = QLineEdit()
        self.site_name_input.setPlaceholderText("Название сайта")
        self.layout.addWidget(self.site_name_input)

        self.site_link_input = QLineEdit()
        self.site_link_input.setPlaceholderText("Ссылка")
        self.layout.addWidget(self.site_link_input)

        self.radio_group = QButtonGroup()

        self.radio_parts = QRadioButton("Запчасти")
        self.radio_parts.setChecked(True)
        self.radio_group.addButton(self.radio_parts)
        self.layout.addWidget(self.radio_parts)

        self.radio_components = QRadioButton("Комплектующие")
        self.radio_group.addButton(self.radio_components)
        self.layout.addWidget(self.radio_components)

        self.add_button = QPushButton("Добавить")
        self.add_button.clicked.connect(self.add_site)
        self.layout.addWidget(self.add_button)

        self.setLayout(self.layout)

    def add_site(self):
        site_name = self.site_name_input.text()
        site_link = self.site_link_input.text()

        if not site_name or not site_link:
            QMessageBox.critical(self, "Ошибка", "Заполните оба поля: Название сайта и Ссылка")
            return

        if self.radio_parts.isChecked():
            self.parts_list.append({"name": site_name, "link": site_link})
            save_list("parts.json", self.parts_list)
        else:
            self.components_list.append({"name": site_name, "link": site_link})
            save_list("components.json", self.components_list)

        self.accept()


class DeleteSiteDialog(QDialog):
    site_deleted = pyqtSignal()  # Новый сигнал

    def __init__(self, parts_list, components_list):
        super().__init__()
        self.setWindowTitle("Удалить сайт")
        self.setWindowIcon(QIcon("iconka.ico"))
        self.setFixedSize(400, 260)
        self.parts_list = parts_list
        self.components_list = components_list
        self.layout = QVBoxLayout()

        self.radio_group = QButtonGroup()
        self.radio_parts = QRadioButton("Запчасти")
        self.radio_parts.setChecked(True)
        self.radio_group.addButton(self.radio_parts)
        self.layout.addWidget(self.radio_parts)

        self.radio_components = QRadioButton("Комплектующие")
        self.radio_group.addButton(self.radio_components)
        self.layout.addWidget(self.radio_components)

        self.site_name_input = QComboBox()
        self.layout.addWidget(self.site_name_input)

        self.delete_button = QPushButton("Удалить")
        self.delete_button.clicked.connect(self.delete_site_slot)  # Переименованный метод
        self.layout.addWidget(self.delete_button)

        self.setLayout(self.layout)

        self.radio_parts.toggled.connect(self.update_combobox)
        self.radio_components.toggled.connect(self.update_combobox)

        # Инициализируем список при создании
        self.update_combobox()


    def delete_site_slot(self):
        selected_site_name = self.site_name_input.currentText()
        if self.radio_parts.isChecked():
            self.parts_list = [item for item in self.parts_list if item["name"] != selected_site_name]
            save_list("parts.json", self.parts_list)
        else:
            self.components_list = [item for item in self.components_list if item["name"] != selected_site_name]
            save_list("components.json", self.components_list)

        self.site_deleted.emit()
        self.accept()

    def update_combobox(self):
        selected_list = self.parts_list if self.radio_parts.isChecked() else self.components_list
        site_names = [item["name"] for item in selected_list]
        self.site_name_input.clear()
        self.site_name_input.addItems(site_names)


def update_site_name_combobox(self):
    self.site_name_input.clear()
    selected_list = parts_list if self.radio_parts.isChecked() else components_list
    self.site_name_input.addItems([item["name"] for item in selected_list])


def open_delete_site_dialog():
    delete_site_dialog = DeleteSiteDialog(parts_list, components_list)
    result = delete_site_dialog.exec_()
    if result == QDialog.Accepted:
        update_combobox()  # Обновляем список сайтов


def show_error_message(message):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setText(message)
    msg.setWindowTitle("Ошибка")
    msg.exec_()



# Показать содержимое списков
def open_file_dialog():
    file_path, _ = QFileDialog.getOpenFileName(None, "Выберите файл", "", "JSON Files (*.json)")

    if file_path:
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)

            # Извлекаем названия сайтов и ссылки
            content = "\n".join(f"{item['name']}: {item['link']}" for item in data)

            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Содержимое файла")
            msg.setFixedSize(500, 350)
            msg.setText(content)
            msg.exec_()
        except Exception as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText(f"Произошла ошибка при чтении файла: {str(e)}")
            msg.exec_()


# Инициализация списков и вызов функции для обновления QComboBox
parts_list = load_or_create_list("parts.json", [])
components_list = load_or_create_list("components.json", [])

window = Window()
form = Form()
form.setupUi(window)


def show_instruction():
    instruction_window = QDialog()
    ui = Ui_Dialog()
    ui.setupUi(instruction_window)
    instruction_window.exec_()


def open_add_site_dialog():
    add_site_dialog = AddSiteDialog(parts_list, components_list)
    if add_site_dialog.exec_():
        update_combobox()  # Обновляем список сайтов


# Создайте функцию-обработчик для кнопки "Калькулятор"
def open_calculator():
    subprocess.Popen(["calc.exe"])  # Замените "calc.exe" на путь к калькулятору на вашей системе


# В вашем главном окне
def update_combobox():
    form.site_name_input.clear()
    selected_list = parts_list if form.radio_parts.isChecked() else components_list
    form.site_name_input.addItems([item["name"] for item in selected_list])


def search_on_websites(query, websites):
    for website in websites:
        search_url = f"{website['link']}?q={query}"
        webbrowser.open(search_url)


# Поиск по всем сайтам
def on_search_all_button_clicked():
    query = form.lineEdit.text()

    if not query:
        show_error_message("Введите запрос перед выполнением поиска.")
    else:
        selected_list = parts_list if form.radio_parts.isChecked() else components_list
        for item in selected_list:
            site_url = f"{item['link']}{query}"
            webbrowser.open(site_url)


def on_search_single_button_clicked():
    query = form.lineEdit.text()
    selected_site = form.site_name_input.currentText()

    if not query:
        show_error_message("Введите запрос перед выполнением поиска.")
    elif not selected_site:
        show_error_message("Выберите сайт для поиска.")
    else:
        selected_list = parts_list if form.radio_parts.isChecked() else components_list
        for item in selected_list:
            if item['name'] == selected_site:
                site_url = f"{item['link']}{query}"
                webbrowser.open(site_url)


def show_error_message(message):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setText(message)
    msg.setWindowTitle("Ошибка")
    msg.exec_()

dark_theme_enabled = False  # Флаг для отслеживания состояния темной темы

def toggle_theme():
    global dark_theme_enabled

    dark_theme_enabled = not dark_theme_enabled

    if dark_theme_enabled:
        app.setStyleSheet(open("styles.qss", "r").read())
    else:
        app.setStyleSheet("")

    # Применяем состояние темы ко всем открытым окнам
    for widget in QApplication.topLevelWidgets():
        widget.setStyleSheet(app.styleSheet())

    # Сохраняем состояние темы
    theme_state = {'dark_theme_enabled': dark_theme_enabled}
    save_theme_state(theme_state_file, theme_state)


# Подключите функцию-обработчик к событию "toggled" RadioButton
form.radio_parts.toggled.connect(update_combobox)
form.radio_components.toggled.connect(update_combobox)
form.delete_site_button.clicked.connect(open_delete_site_dialog)
form.search_all_button.clicked.connect(on_search_all_button_clicked)
form.search_select_site.clicked.connect(on_search_single_button_clicked)
form.action_2.triggered.connect(open_file_dialog)
form.action.triggered.connect(show_instruction)
form.action_4.triggered.connect(toggle_theme)
form.add_site_button.clicked.connect(open_add_site_dialog)
form.delete_site_button.clicked.connect(open_delete_site_dialog)
form.calculatorButton.clicked.connect(open_calculator)



# Также вызовите эту функцию при запуске приложения, чтобы инициализировать начальное состояние ComboBox
update_combobox()

window.setFixedSize(488, 330)

window.show()
app.exec_()
