<<<<<<< HEAD

import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector

# Подключение к БД

def connect_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="mydb"
        )
        return conn
    except Exception as e:
        messagebox.showerror("Ошибка подключения", str(e))
        return None


class ClientApp:

    def __init__(self, root):

        self.root = root
        self.root.title("Управление клиентами фитнес-клуба")
        self.root.geometry("800x500")

        self.selected_id = None

        # Поля ввода
        
        input_frame = tk.Frame(root)
        input_frame.pack(pady=10)

        tk.Label(input_frame, text="Фамилия").grid(row=0, column=0)
        self.entry_surname = tk.Entry(input_frame, width=20)
        self.entry_surname.grid(row=0, column=1)

        tk.Label(input_frame, text="Имя").grid(row=0, column=2)
        self.entry_name = tk.Entry(input_frame, width=20)
        self.entry_name.grid(row=0, column=3)

        tk.Label(input_frame, text="Отчество").grid(row=0, column=4)
        self.entry_middle = tk.Entry(input_frame, width=20)
        self.entry_middle.grid(row=0, column=5)

        tk.Label(input_frame, text="Телефон").grid(row=1, column=0)
        self.entry_phone = tk.Entry(input_frame, width=20)
        self.entry_phone.grid(row=1, column=1)

        tk.Label(input_frame, text="Email").grid(row=1, column=2)
        self.entry_email = tk.Entry(input_frame, width=20)
        self.entry_email.grid(row=1, column=3)

        # Поиск


        search_frame = tk.Frame(root)
        search_frame.pack()

        tk.Label(search_frame, text="Поиск").pack(side=tk.LEFT)

        self.search_entry = tk.Entry(search_frame, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)

        tk.Button(
            search_frame,
            text="🔍 Найти",
            command=self.search_client
        ).pack(side=tk.LEFT)

  
        # Кнопки
  
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="➕ Добавить",
            width=15,
            command=self.add_client
        ).grid(row=0, column=0, padx=5)

        tk.Button(
            btn_frame,
            text="✏ Обновить",
            width=15,
            command=self.update_client
        ).grid(row=0, column=1, padx=5)

        tk.Button(
            btn_frame,
            text="🗑 Удалить",
            width=15,
            command=self.delete_client
        ).grid(row=0, column=2, padx=5)

        tk.Button(
            btn_frame,
            text="🧹 Очистить",
            width=15,
            command=self.clear_fields
        ).grid(row=0, column=3, padx=5)

        tk.Button(
            btn_frame,
            text="🔄 Показать всех",
            width=15,
            command=self.load_data
        ).grid(row=0, column=4, padx=5)

        # Таблица

        self.tree = ttk.Treeview(
            root,
            columns=(
                "id",
                "фамилия",
                "имя",
                "отчество",
                "телефон",
                "email"
            ),
            show="headings"
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("фамилия", text="Фамилия")
        self.tree.heading("имя", text="Имя")
        self.tree.heading("отчество", text="Отчество")
        self.tree.heading("телефон", text="Телефон")
        self.tree.heading("email", text="Email")

        self.tree.column("id", width=50)

        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind(
            "<<TreeviewSelect>>",
            self.select_record
        )

        self.load_data()

    # SELECT

    def load_data(self):

        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = connect_db()

        if conn:

            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                id_клиента,
                фамилия,
                имя,
                отчество,
                телефон,
                email
                FROM Клиенты
            """)

            rows = cursor.fetchall()

            for row in rows:
                self.tree.insert("", tk.END, values=row)

            conn.close()


    # INSERT

    def add_client(self):

        if not self.entry_surname.get():
            messagebox.showwarning(
                "Ошибка",
                "Введите фамилию"
            )
            return

        conn = connect_db()

        if conn:

            cursor = conn.cursor()

            query = """
            INSERT INTO Клиенты
            (
                фамилия,
                имя,
                отчество,
                телефон,
                email
            )
            VALUES (%s,%s,%s,%s,%s)
            """

            cursor.execute(
                query,
                (
                    self.entry_surname.get(),
                    self.entry_name.get(),
                    self.entry_middle.get(),
                    self.entry_phone.get(),
                    self.entry_email.get()
                )
            )

            conn.commit()
            conn.close()

            messagebox.showinfo(
                "Успех",
                "Клиент добавлен"
            )

            self.load_data()
            self.clear_fields()


    # UPDATE

    def update_client(self):

        if not self.selected_id:
            return

        conn = connect_db()

        if conn:

            cursor = conn.cursor()

            query = """
            UPDATE Клиенты
            SET
                фамилия=%s,
                имя=%s,
                отчество=%s,
                телефон=%s,
                email=%s
            WHERE id_клиента=%s
            """

            cursor.execute(
                query,
                (
                    self.entry_surname.get(),
                    self.entry_name.get(),
                    self.entry_middle.get(),
                    self.entry_phone.get(),
                    self.entry_email.get(),
                    self.selected_id
                )
            )

            conn.commit()
            conn.close()

            self.load_data()

            messagebox.showinfo(
                "Успех",
                "Запись обновлена"
            )


    # DELETE

    def delete_client(self):

        if not self.selected_id:
            return

        answer = messagebox.askyesno(
            "Удаление",
            "Удалить клиента?"
        )

        if not answer:
            return

        conn = connect_db()

        if conn:

            cursor = conn.cursor()

            cursor.execute(
                """
                DELETE FROM Клиенты
                WHERE id_клиента=%s
                """,
                (self.selected_id,)
            )

            conn.commit()
            conn.close()

            self.load_data()
            self.clear_fields()

    # Поиск

    def search_client(self):

        keyword = self.search_entry.get().strip()

        if keyword == "":
            self.load_data()
            return

        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = connect_db()

        if conn:

            cursor = conn.cursor()

            query = """
            SELECT
                id_клиента,
                фамилия,
                имя,
                отчество,
                телефон,
                email
            FROM Клиенты
            WHERE фамилия LIKE %s
               OR имя LIKE %s
               OR телефон LIKE %s
               OR email LIKE %s
            """

            search = f"%{keyword}%"

            cursor.execute(
                query,
                (
                    search,
                    search,
                    search,
                    search
                )
            )

            rows = cursor.fetchall()

            for row in rows:
                self.tree.insert(
                    "",
                    tk.END,
                    values=row
                )

            conn.close()


    # Выбор строки

    def select_record(self, event):

        selected = self.tree.selection()

        if not selected:
            return

        values = self.tree.item(
            selected[0]
        )["values"]

        self.selected_id = values[0]

        self.clear_fields()

        self.entry_surname.insert(0, values[1])
        self.entry_name.insert(0, values[2])

        if values[3]:
            self.entry_middle.insert(0, values[3])

        if values[4]:
            self.entry_phone.insert(0, values[4])

        if values[5]:
            self.entry_email.insert(0, values[5])


    # Очистка

    def clear_fields(self):

        self.entry_surname.delete(0, tk.END)
        self.entry_name.delete(0, tk.END)
        self.entry_middle.delete(0, tk.END)
        self.entry_phone.delete(0, tk.END)
        self.entry_email.delete(0, tk.END)


root = tk.Tk()

app = ClientApp(root)

=======

import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector

# Подключение к БД

def connect_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="mydb"
        )
        return conn
    except Exception as e:
        messagebox.showerror("Ошибка подключения", str(e))
        return None


class ClientApp:

    def __init__(self, root):

        self.root = root
        self.root.title("Управление клиентами фитнес-клуба")
        self.root.geometry("800x500")

        self.selected_id = None

        # Поля ввода
        
        input_frame = tk.Frame(root)
        input_frame.pack(pady=10)

        tk.Label(input_frame, text="Фамилия").grid(row=0, column=0)
        self.entry_surname = tk.Entry(input_frame, width=20)
        self.entry_surname.grid(row=0, column=1)

        tk.Label(input_frame, text="Имя").grid(row=0, column=2)
        self.entry_name = tk.Entry(input_frame, width=20)
        self.entry_name.grid(row=0, column=3)

        tk.Label(input_frame, text="Отчество").grid(row=0, column=4)
        self.entry_middle = tk.Entry(input_frame, width=20)
        self.entry_middle.grid(row=0, column=5)

        tk.Label(input_frame, text="Телефон").grid(row=1, column=0)
        self.entry_phone = tk.Entry(input_frame, width=20)
        self.entry_phone.grid(row=1, column=1)

        tk.Label(input_frame, text="Email").grid(row=1, column=2)
        self.entry_email = tk.Entry(input_frame, width=20)
        self.entry_email.grid(row=1, column=3)

        # Поиск


        search_frame = tk.Frame(root)
        search_frame.pack()

        tk.Label(search_frame, text="Поиск").pack(side=tk.LEFT)

        self.search_entry = tk.Entry(search_frame, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)

        tk.Button(
            search_frame,
            text="🔍 Найти",
            command=self.search_client
        ).pack(side=tk.LEFT)

  
        # Кнопки
  
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="➕ Добавить",
            width=15,
            command=self.add_client
        ).grid(row=0, column=0, padx=5)

        tk.Button(
            btn_frame,
            text="✏ Обновить",
            width=15,
            command=self.update_client
        ).grid(row=0, column=1, padx=5)

        tk.Button(
            btn_frame,
            text="🗑 Удалить",
            width=15,
            command=self.delete_client
        ).grid(row=0, column=2, padx=5)

        tk.Button(
            btn_frame,
            text="🧹 Очистить",
            width=15,
            command=self.clear_fields
        ).grid(row=0, column=3, padx=5)

        tk.Button(
            btn_frame,
            text="🔄 Показать всех",
            width=15,
            command=self.load_data
        ).grid(row=0, column=4, padx=5)

        # Таблица

        self.tree = ttk.Treeview(
            root,
            columns=(
                "id",
                "фамилия",
                "имя",
                "отчество",
                "телефон",
                "email"
            ),
            show="headings"
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("фамилия", text="Фамилия")
        self.tree.heading("имя", text="Имя")
        self.tree.heading("отчество", text="Отчество")
        self.tree.heading("телефон", text="Телефон")
        self.tree.heading("email", text="Email")

        self.tree.column("id", width=50)

        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind(
            "<<TreeviewSelect>>",
            self.select_record
        )

        self.load_data()

    # SELECT

    def load_data(self):

        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = connect_db()

        if conn:

            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                id_клиента,
                фамилия,
                имя,
                отчество,
                телефон,
                email
                FROM Клиенты
            """)

            rows = cursor.fetchall()

            for row in rows:
                self.tree.insert("", tk.END, values=row)

            conn.close()


    # INSERT

    def add_client(self):

        if not self.entry_surname.get():
            messagebox.showwarning(
                "Ошибка",
                "Введите фамилию"
            )
            return

        conn = connect_db()

        if conn:

            cursor = conn.cursor()

            query = """
            INSERT INTO Клиенты
            (
                фамилия,
                имя,
                отчество,
                телефон,
                email
            )
            VALUES (%s,%s,%s,%s,%s)
            """

            cursor.execute(
                query,
                (
                    self.entry_surname.get(),
                    self.entry_name.get(),
                    self.entry_middle.get(),
                    self.entry_phone.get(),
                    self.entry_email.get()
                )
            )

            conn.commit()
            conn.close()

            messagebox.showinfo(
                "Успех",
                "Клиент добавлен"
            )

            self.load_data()
            self.clear_fields()


    # UPDATE

    def update_client(self):

        if not self.selected_id:
            return

        conn = connect_db()

        if conn:

            cursor = conn.cursor()

            query = """
            UPDATE Клиенты
            SET
                фамилия=%s,
                имя=%s,
                отчество=%s,
                телефон=%s,
                email=%s
            WHERE id_клиента=%s
            """

            cursor.execute(
                query,
                (
                    self.entry_surname.get(),
                    self.entry_name.get(),
                    self.entry_middle.get(),
                    self.entry_phone.get(),
                    self.entry_email.get(),
                    self.selected_id
                )
            )

            conn.commit()
            conn.close()

            self.load_data()

            messagebox.showinfo(
                "Успех",
                "Запись обновлена"
            )


    # DELETE

    def delete_client(self):

        if not self.selected_id:
            return

        answer = messagebox.askyesno(
            "Удаление",
            "Удалить клиента?"
        )

        if not answer:
            return

        conn = connect_db()

        if conn:

            cursor = conn.cursor()

            cursor.execute(
                """
                DELETE FROM Клиенты
                WHERE id_клиента=%s
                """,
                (self.selected_id,)
            )

            conn.commit()
            conn.close()

            self.load_data()
            self.clear_fields()

    # Поиск

    def search_client(self):

        keyword = self.search_entry.get().strip()

        if keyword == "":
            self.load_data()
            return

        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = connect_db()

        if conn:

            cursor = conn.cursor()

            query = """
            SELECT
                id_клиента,
                фамилия,
                имя,
                отчество,
                телефон,
                email
            FROM Клиенты
            WHERE фамилия LIKE %s
               OR имя LIKE %s
               OR телефон LIKE %s
               OR email LIKE %s
            """

            search = f"%{keyword}%"

            cursor.execute(
                query,
                (
                    search,
                    search,
                    search,
                    search
                )
            )

            rows = cursor.fetchall()

            for row in rows:
                self.tree.insert(
                    "",
                    tk.END,
                    values=row
                )

            conn.close()


    # Выбор строки

    def select_record(self, event):

        selected = self.tree.selection()

        if not selected:
            return

        values = self.tree.item(
            selected[0]
        )["values"]

        self.selected_id = values[0]

        self.clear_fields()

        self.entry_surname.insert(0, values[1])
        self.entry_name.insert(0, values[2])

        if values[3]:
            self.entry_middle.insert(0, values[3])

        if values[4]:
            self.entry_phone.insert(0, values[4])

        if values[5]:
            self.entry_email.insert(0, values[5])


    # Очистка

    def clear_fields(self):

        self.entry_surname.delete(0, tk.END)
        self.entry_name.delete(0, tk.END)
        self.entry_middle.delete(0, tk.END)
        self.entry_phone.delete(0, tk.END)
        self.entry_email.delete(0, tk.END)


root = tk.Tk()

app = ClientApp(root)

>>>>>>> 3b4f349933548da8251d14636178f1a05d9906f0
root.mainloop()