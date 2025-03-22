
import telebot
from telebot import types
from datetime import datetime
import json
import os
import calendar
import io

# Инициализация бота
bot = telebot.TeleBot("8159160029:AAFqOA0ec8ZlCkZgYBUIjbZ_jA2K007AqdA")

# Глобальные переменные
user_tasks = {}  # Текущие задачи
completed_tasks = {}  # Выполненные задачи
user_data = {}
user_states = {}  # Состояния пользователей
languages = {"en": "English", "ru": "Русский"}
current_language = "ru"

# Класс задачи
class Task:
    def __init__(self, description, deadline, category="Общее", status=False):
        self.description = description
        self.deadline = deadline
        self.status = status
        self.category = category

    def __str__(self):
        return f"Описание: {self.description}, Срок: {self.deadline}, Статус: {'✅ Выполнено' if self.status else '❌ Не выполнено'}, Категория: {self.category}"

# ==================== УТИЛИТЫ ДЛЯ СЕРИАЛИЗАЦИИ ====================
def task_to_dict(task):
    """Преобразует объект Task в словарь"""
    return {
        "description": task.description,
        "deadline": task.deadline,
        "status": task.status,
        "category": task.category,
    }

def dict_to_task(data):
    """Преобразует словарь обратно в объект Task"""
    return Task(
        description=data.get("description", ""),
        deadline=data.get("deadline", ""),
        status=data.get("status", False),
        category=data.get("category", "Общее"),
    )

# Сохранение данных в файл
def save_data():
    """Сохраняет данные в файл data.json"""
    data = {
        "tasks": {user_id: [task_to_dict(task) for task in tasks] for user_id, tasks in user_tasks.items()},
        "completed": {user_id: [task_to_dict(task) for task in tasks] for user_id, tasks in completed_tasks.items()},
    }
    file: io.TextIOWrapper
    with open("data.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# Загрузка данных из файла
def load_data():
    """Загружает данные из файла data.json"""
    global user_tasks, completed_tasks
    try:
        if os.path.exists("data.json"):
            with open("data.json", "r", encoding="utf-8") as file:
                data = json.load(file)
                print("Загруженные данные:", data)  # Отладочная информация
                user_tasks = {
                    int(user_id): [dict_to_task(task_data) for task_data in tasks]
                    for user_id, tasks in data.get("tasks", {}).items()
                }
                completed_tasks = {
                    int(user_id): [dict_to_task(task_data) for task_data in tasks]
                    for user_id, tasks in data.get("completed", {}).items()
                }
    except Exception as e:
        print(f"Ошибка при загрузке данных: {e}")
        user_tasks = {}
        completed_tasks = {}

load_data()

# ==================== ЛОКАЛИЗАЦИЯ ====================
lang_texts = {
    "ru": {
        "start_message": "Добро пожаловать в Task Manager Bot! Выберите действие:",
        "task_added": "✅ Задача добавлена! Срок: {}",
        "no_tasks": "❌ Нет текущих задач.",
        "task_marked_completed": "✅ Задача отмечена выполненной!",
        "invalid_task": "❌ Неверный номер задачи.",
        "input_error": "❌ Ошибка ввода.",
        "task_deleted": "❌ Задача удалена.",
        "choose_language": "Выберите язык:",
        "language_set": "Язык установлен: {}",
        "enter_description": "Введите описание задачи:",
        "choose_date": "Выберите дату выполнения:",
        "confirm_date": "Подтвердить дату",
        "export_tasks": "Все задачи экспортированы в файл tasks.txt",
        "search_results": "Результаты поиска:",
        "no_search_results": "❌ Ничего не найдено.",
        "progress_bar": "Прогресс выполнения задач: {}%",
        "category_added": "Категория '{}' добавлена к задаче.",
    },
    "en": {
        "start_message": "Welcome to Task Manager Bot! Choose an action:",
        "task_added": "✅ Task added! Deadline: {}",
        "no_tasks": "❌ No current tasks.",
        "task_marked_completed": "✅ Task marked as completed!",
        "invalid_task": "❌ Invalid task number.",
        "input_error": "❌ Input error.",
        "task_deleted": "❌ Task deleted.",
        "choose_language": "Choose language:",
        "language_set": "Language set: {}",
        "enter_description": "Enter task description:",
        "choose_date": "Choose the deadline:",
        "confirm_date": "Confirm date",
        "export_tasks": "All tasks exported to tasks.txt",
        "search_results": "Search results:",
        "no_search_results": "❌ Nothing found.",
        "progress_bar": "Task completion progress: {}%",
        "category_added": "Category '{}' added to the task.",
    },
}

def get_text(key):
    return lang_texts[current_language][key]

# ==================== УТИЛИТЫ ====================
def get_user_data(user_id):
    if user_id not in user_tasks:
        user_tasks[user_id] = []
    if user_id not in completed_tasks:
        completed_tasks[user_id] = []

def set_user_state(user_id, state):
    user_states[user_id] = state

def get_user_state(user_id):
    return user_states.get(user_id, None)

# Функция для сравнения клавиатур
def is_keyboard_changed(old_keyboard, new_keyboard):
    if not old_keyboard or not new_keyboard:
        return True  # Если одна из клавиатур пуста, считаем, что она изменилась
    return old_keyboard.to_json() != new_keyboard.to_json()

# Корректировка дня для текущего месяца
def adjust_day(year, month, day):
    """Корректирует день в зависимости от месяца и года"""
    _, last_day = calendar.monthrange(year, month)  # Получаем последний день месяца
    return min(day, last_day)

# ==================== ОСНОВНАЯ КЛАВИАТУРА ====================
def create_main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        "Добавить задачу", "Отметить выполненную", "Показать текущие",
        "Удалить задачу", "Редактировать задачу", "Сортировать задачи",
        "Экспорт задач", "Просмотр выполненных", "Поиск задач",
        "Выбрать язык", "Статистика"
    ]
    for btn in buttons:
        keyboard.add(types.KeyboardButton(btn))
    return keyboard

# ==================== КЛАВИАТУРА ДЛЯ ВЫБОРА ДАТЫ ====================
def create_date_keyboard(user_id):
    keyboard = types.InlineKeyboardMarkup(row_width=4)
    year = user_data[user_id].get("year", datetime.now().year)
    month = user_data[user_id].get("month", datetime.now().month)
    day = user_data[user_id].get("day", datetime.now().day)

    # Строка с годом
    keyboard.row(
        types.InlineKeyboardButton("Год:", callback_data=f"ignore_{user_id}"),
        types.InlineKeyboardButton("<<", callback_data=f"prev_year_{user_id}"),
        types.InlineKeyboardButton(str(year), callback_data=f"ignore_{user_id}"),
        types.InlineKeyboardButton(">>", callback_data=f"next_year_{user_id}")
    )

    # Строка с месяцем
    keyboard.row(
        types.InlineKeyboardButton("Месяц:", callback_data=f"ignore_{user_id}"),
        types.InlineKeyboardButton("<<", callback_data=f"prev_month_{user_id}"),
        types.InlineKeyboardButton(str(month), callback_data=f"ignore_{user_id}"),
        types.InlineKeyboardButton(">>", callback_data=f"next_month_{user_id}")
    )

    # Строка с днями
    days_row = [types.InlineKeyboardButton(str(day), callback_data=f"ignore_{user_id}")]
    for d in range(1, adjust_day(year, month, 31) + 1):
        days_row.append(types.InlineKeyboardButton(str(d), callback_data=f"select_day_{user_id}_{d}"))
    keyboard.row(*days_row)

    # Кнопка подтверждения
    keyboard.add(types.InlineKeyboardButton(get_text("confirm_date"), callback_data=f"confirm_date_{user_id}"))

    return keyboard

# ==================== КОМАНДА /start ====================
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    get_user_data(user_id)
    bot.send_message(user_id, get_text("start_message"), reply_markup=create_main_keyboard())

# ==================== ДОБАВЛЕНИЕ ЗАДАЧИ ====================
@bot.message_handler(func=lambda msg: msg.text == "Добавить задачу")
def add_task(message):
    user_id = message.from_user.id
    if get_user_state(user_id) != "adding_task":
        set_user_state(user_id, "adding_task")
        msg = bot.send_message(user_id, get_text("enter_description"))
        bot.register_next_step_handler(msg, process_description_step, user_id)
    else:
        bot.send_message(user_id, "❌ Вы уже добавляете задачу. Завершите текущее действие.")

def process_description_step(message, user_id):
    if not message.text.strip():
        bot.send_message(user_id, "❌ Сообщение не должно быть пустым.", reply_markup=create_main_keyboard())
        set_user_state(user_id, None)
        return
    description = message.text
    user_data[user_id] = {"description": description}
    bot.send_message(user_id, get_text("choose_date"), reply_markup=create_date_keyboard(user_id))

@bot.callback_query_handler(func=lambda call: call.data.startswith(("prev_year", "next_year", "prev_month", "next_month", "select_day")))
def handle_date_selection(call):
    user_id = call.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {}

    # Инициализация данных, если их нет
    now = datetime.now()
    user_data[user_id].setdefault("year", now.year)
    user_data[user_id].setdefault("month", now.month)
    user_data[user_id].setdefault("day", now.day)

    data = call.data.split("_")
    action = data[0]
    if action in ["prev_year", "next_year", "prev_month", "next_month"]:
        # Обработка изменения даты
        if action == "prev_year":
            user_data[user_id]["year"] -= 1
        elif action == "next_year":
            user_data[user_id]["year"] += 1
        elif action == "prev_month":
            user_data[user_id]["month"] = max(1, user_data[user_id]["month"] - 1)
        elif action == "next_month":
            user_data[user_id]["month"] = min(12, user_data[user_id]["month"] + 1)

        # Корректировка дня для текущего месяца
        user_data[user_id]["day"] = adjust_day(
            user_data[user_id]["year"],
            user_data[user_id]["month"],
            user_data[user_id]["day"]
        )

        # Создаем новую клавиатуру
        new_keyboard = create_date_keyboard(user_id)

        # Получаем старую клавиатуру
        old_keyboard = call.message.reply_markup

        # Проверяем, изменилась ли клавиатура
        if is_keyboard_changed(old_keyboard, new_keyboard):
            bot.edit_message_reply_markup(
                chat_id=user_id,
                message_id=call.message.message_id,
                reply_markup=new_keyboard,
            )
    elif action == "select_day":
        user_data[user_id]["day"] = int(data[2])
        new_keyboard = create_date_keyboard(user_id)
        bot.edit_message_reply_markup(
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=new_keyboard,
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_date"))
def confirm_date_selection(call):
    user_id = call.from_user.id
    year = user_data[user_id]["year"]
    month = user_data[user_id]["month"]
    day = user_data[user_id]["day"]

    # Проверка корректности даты
    try:
        deadline = f"{day:02d}-{month:02d}-{year}"
        datetime.strptime(deadline, "%d-%m-%Y")  # Проверка формата даты
    except ValueError:
        bot.send_message(user_id, "❌ Некорректная дата. Пожалуйста, выберите другую дату.")
        return

    # Добавление задачи
    if "description" not in user_data[user_id]:
        bot.send_message(user_id, "❌ Описание задачи отсутствует. Попробуйте начать заново.")
        return

    description = user_data[user_id]["description"]
    user_tasks[user_id].append(Task(description, deadline))
    bot.send_message(user_id, get_text("task_added").format(deadline), reply_markup=create_main_keyboard())
    save_data()
    set_user_state(user_id, None)

    # Удаляем сообщение с выбором даты
    bot.delete_message(chat_id=user_id, message_id=call.message.message_id)

# ==================== УДАЛЕНИЕ ЗАДАЧИ ====================
@bot.message_handler(func=lambda msg: msg.text == "Удалить задачу")
def delete_task(message):
    user_id = message.from_user.id
    get_user_data(user_id)
    if not user_tasks[user_id]:
        bot.send_message(user_id, get_text("no_tasks"), reply_markup=create_main_keyboard())
        return
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for idx, task in enumerate(user_tasks[user_id]):
        keyboard.add(types.KeyboardButton(f"Задача {idx + 1}"))
    keyboard.add(types.KeyboardButton("Отмена"))
    msg = bot.send_message(user_id, "Выберите задачу для удаления:", reply_markup=keyboard)
    bot.register_next_step_handler(msg, process_delete_task, user_id)

def process_delete_task(message, user_id):
    if message.text == "Отмена":
        bot.send_message(user_id, "Действие отменено.", reply_markup=create_main_keyboard())
        return
    try:
        task_index = int(message.text.split()[1]) - 1
        if not (0 <= task_index < len(user_tasks[user_id])):
            raise ValueError
        del user_tasks[user_id][task_index]
        bot.send_message(user_id, get_text("task_deleted"), reply_markup=create_main_keyboard())
        save_data()
    except (ValueError, IndexError):
        bot.send_message(user_id, get_text("invalid_task"), reply_markup=create_main_keyboard())

# ==================== РЕДАКТИРОВАНИЕ ЗАДАЧИ ====================
@bot.message_handler(func=lambda msg: msg.text == "Редактировать задачу")
def edit_task(message):
    user_id = message.from_user.id
    get_user_data(user_id)
    if not user_tasks[user_id]:
        bot.send_message(user_id, get_text("no_tasks"), reply_markup=create_main_keyboard())
        return
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for idx, task in enumerate(user_tasks[user_id]):
        keyboard.add(types.KeyboardButton(f"Задача {idx + 1}"))
    keyboard.add(types.KeyboardButton("Отмена"))
    msg = bot.send_message(user_id, "Выберите задачу для редактирования:", reply_markup=keyboard)
    bot.register_next_step_handler(msg, process_edit_task, user_id)

def process_edit_task(message, user_id):
    if message.text == "Отмена":
        bot.send_message(user_id, "Действие отменено.", reply_markup=create_main_keyboard())
        return
    try:
        task_index = int(message.text.split()[1]) - 1
        if not (0 <= task_index < len(user_tasks[user_id])):
            raise ValueError
        task = user_tasks[user_id][task_index]
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton("Изменить описание"), types.KeyboardButton("Изменить дедлайн"))
        keyboard.add(types.KeyboardButton("Отмена"))
        msg = bot.send_message(user_id, f"Редактирование задачи:\n{task}", reply_markup=keyboard)
        bot.register_next_step_handler(msg, process_edit_choice, user_id, task_index)
    except (ValueError, IndexError):
        bot.send_message(user_id, get_text("invalid_task"), reply_markup=create_main_keyboard())

def process_edit_choice(message, user_id, task_index):
    if message.text == "Отмена":
        bot.send_message(user_id, "Действие отменено.", reply_markup=create_main_keyboard())
        return
    if message.text == "Изменить описание":
        msg = bot.send_message(user_id, "Введите новое описание:")
        bot.register_next_step_handler(msg, process_edit_description, user_id, task_index)
    elif message.text == "Изменить дедлайн":
        user_data[user_id] = {"task_index": task_index}
        bot.send_message(user_id, get_text("choose_date"), reply_markup=create_date_keyboard(user_id))

def process_edit_description(message, user_id, task_index):
    if not message.text.strip():
        bot.send_message(user_id, "❌ Сообщение не должно быть пустым.", reply_markup=create_main_keyboard())
        return
    new_description = message.text
    user_tasks[user_id][task_index].description = new_description
    bot.send_message(user_id, "Описание успешно изменено!", reply_markup=create_main_keyboard())
    save_data()

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_date"))
def confirm_edit_deadline(call):
    user_id = call.from_user.id
    task_index = user_data[user_id]["task_index"]
    year, month, day = user_data[user_id]["year"], user_data[user_id]["month"], user_data[user_id]["day"]
    new_deadline = f"{day:02d}-{month:02d}-{year}"
    user_tasks[user_id][task_index].deadline = new_deadline
    bot.send_message(user_id, "Дедлайн успешно изменен!", reply_markup=create_main_keyboard())
    save_data()

# ==================== СОРТИРОВКА ЗАДАЧ ====================
@bot.message_handler(func=lambda msg: msg.text == "Сортировать задачи")
def sort_tasks(message):
    user_id = message.from_user.id
    get_user_data(user_id)
    sorted_tasks = sorted(user_tasks[user_id], key=lambda t: (t.status, datetime.strptime(t.deadline, "%d-%m-%Y")))
    tasks_text = "\n".join([f"{idx + 1}. {task}" for idx, task in enumerate(sorted_tasks)])
    bot.send_message(user_id, f"=== ОТСОРТИРОВАННЫЕ ЗАДАЧИ ===\n{tasks_text}", reply_markup=create_main_keyboard())

# ==================== ЭКСПОРТ ЗАДАЧ ====================
@bot.message_handler(func=lambda msg: msg.text == "Экспорт задач")
def export_tasks(message):
    user_id = message.from_user.id
    get_user_data(user_id)
    with open("tasks.txt", "w", encoding="utf-8") as file:
        for idx, task in enumerate(user_tasks[user_id]):
            file.write(f"{idx + 1}. {task}\n")
    if os.path.getsize("tasks.txt") > 50 * 1024:  # 50 KB
        bot.send_message(user_id, "❌ Размер файла слишком большой. Попробуйте удалить некоторые задачи.")
        os.remove("tasks.txt")
        return
    with open("tasks.txt", "rb") as file:
        bot.send_document(user_id, file, caption=get_text("export_tasks"))
    os.remove("tasks.txt")

# ==================== ПРОСМОТР ВЫПОЛНЕННЫХ ЗАДАЧ ====================
@bot.message_handler(func=lambda msg: msg.text == "Просмотр выполненных")
def view_completed_tasks(message):
    user_id = message.from_user.id
    get_user_data(user_id)
    tasks = [task for task in completed_tasks[user_id]]
    if not tasks:
        bot.send_message(user_id, get_text("no_tasks"), reply_markup=create_main_keyboard())
    else:
        tasks_text = "\n".join([f"{idx + 1}. {task}" for idx, task in enumerate(tasks)])
        bot.send_message(user_id, f"=== ВЫПОЛНЕННЫЕ ЗАДАЧИ ===\n{tasks_text}", reply_markup=create_main_keyboard())

# ==================== ПОИСК ЗАДАЧ ====================
@bot.message_handler(func=lambda msg: msg.text == "Поиск задач")
def search_tasks(message):
    user_id = message.from_user.id
    get_user_data(user_id)
    msg = bot.send_message(user_id, "Введите слово или дату для поиска:")
    bot.register_next_step_handler(msg, process_search, user_id)

def process_search(message, user_id):
    query = message.text.lower()
    results = [task for task in user_tasks[user_id] if query in task.description.lower() or query in task.deadline]
    if not results:
        bot.send_message(user_id, get_text("no_search_results"), reply_markup=create_main_keyboard())
    else:
        results_text = "\n".join([f"{idx + 1}. {task}" for idx, task in enumerate(results)])
        bot.send_message(user_id, f"{get_text('search_results')}\n{results_text}", reply_markup=create_main_keyboard())

# ==================== ВЫБОР ЯЗЫКА ====================
@bot.message_handler(func=lambda msg: msg.text == "Выбрать язык")
def choose_language(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for lang_code, lang_name in languages.items():
        keyboard.add(types.KeyboardButton(lang_code))
    msg = bot.send_message(message.from_user.id, get_text("choose_language"), reply_markup=keyboard)
    bot.register_next_step_handler(msg, set_language)

def set_language(message):
    global current_language
    lang_code = message.text
    if lang_code not in languages:
        bot.send_message(message.from_user.id, "❌ Язык не поддерживается.", reply_markup=create_main_keyboard())
        return
    current_language = lang_code
    bot.send_message(message.from_user.id, get_text("language_set").format(languages[lang_code]), reply_markup=create_main_keyboard())

# ==================== СТАТИСТИКА ====================
@bot.message_handler(func=lambda msg: msg.text == "Статистика")
def show_progress(message):
    user_id = message.from_user.id
    get_user_data(user_id)
    total = len(user_tasks[user_id])
    completed = sum(1 for task in user_tasks[user_id] if task.status)
    progress = (completed / total) * 100 if total > 0 else 0
    bot.send_message(user_id, get_text("progress_bar").format(progress), reply_markup=create_main_keyboard())

# ==================== ЗАПУСК БОТА ====================
if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling(none_stop=True)
