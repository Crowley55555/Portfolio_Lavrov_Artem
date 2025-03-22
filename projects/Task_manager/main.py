import tkinter as tk

def add_task():
    task = task_entry.get()
    if task:
        task_listBox.insert(tk.END, task)
        task_entry.delete(0, tk.END)

def delete_task():
    selected_task = task_listBox.curselection()
    if selected_task:
        deleted_task = task_listBox.get(selected_task)
        deleted_task_listBox.insert(tk.END, deleted_task)  # Добавление удаленной задачи в список
        task_listBox.delete(selected_task)

def completed_task():
    selected_task = task_listBox.curselection()
    if selected_task:
        task = task_listBox.get(selected_task)  # Получаем текст задачи
        completed_tasks_listBox.insert(tk.END, task)  # Добавляем в список выполненных задач
        task_listBox.delete(selected_task)  # Удаляем задачу из списка задач

root = tk.Tk()
root.geometry("500x800")
root.title("task list")
root.configure(background="SlateGray4")

text1 = tk.Label(root, text="Введите задачу", bg="white")
text1.pack(pady=5)

task_entry = tk.Entry(root, width=30, bg="pink")
task_entry.pack(pady=5, padx=5)

add_task_button = tk.Button(root, text="Добавить задачу", bg="yellow", command=add_task)
add_task_button.pack(pady=5)

delete_button = tk.Button(root, text="Удалить задачу", bg="red", command=delete_task)
delete_button.pack(pady=5)

mark_button = tk.Button(root, text="Отметить выполненную задачу", bg="green", command=completed_task)
mark_button.pack(pady=5)

text2 = tk.Label(root, text="Список задач", bg="yellow")
text2.pack(pady=5)

task_listBox = tk.Listbox(root, height=10, width=100, bg="dark turquoise")
task_listBox.pack(pady=5, padx=5)

text3 = tk.Label(root, text="Выполненные задачи", bg="green")
text3.pack(pady=5)
completed_tasks_listBox = tk.Listbox(root, height=10, width=100, bg="dark turquoise")
completed_tasks_listBox.pack(pady=5, padx=5)

text4 = tk.Label(root, text="Удаленные задачи", bg="red")
text4.pack(pady=5)
deleted_task_listBox = tk.Listbox(root, height=10, width=100, bg="dark turquoise")
deleted_task_listBox.pack(pady=5, padx=5)


root.mainloop()