from tkinter import *
from tkinter import messagebox
import socket
import jsonpickle

IP = '127.0.0.1'
PORT = 4000

EXAMPLE_TESTS = [
    {"id": 1, "title": "HTTP Status Codes", "description": "Test your knowledge on HTTP codes."}
]

EXAMPLE_QUESTIONS = {
    1: [
        {
            "question": "Что означает статус код 200?",
            "options": ["Bad Request", "OK", "Not Found", "Forbidden"],
            "answer": 1
        },
        {
            "question": "Что означает статус код 404?",
            "options": ["OK", "Created", "Not Found", "Unauthorized"],
            "answer": 2
        }
    ]
}

class StatusCodeTester:
    def __init__(self, root):
        self.root = root
        self.root.title("StatusCode Tester")
        self.root.geometry("600x400")
        self.root.configure(bg='#f0f0f0')

        self.button_font = ('Arial', 10)
        self.label_font = ('Arial', 10)
        self.header_font = ('Arial', 14, 'bold')

        self.current_user = None
        self.current_test = None
        self.current_question_index = 0
        self.correct_answers = 0

        self.start_screen()

    def clear_widgets(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def start_screen(self):
        self.clear_widgets()
        Label(self.root, text="StatusCode Tester", font=self.header_font, bg='#f0f0f0').pack(pady=20)

        Label(self.root, text="Username:", font=self.label_font, bg='#f0f0f0').pack()
        self.username_entry = Entry(self.root)
        self.username_entry.pack()

        Label(self.root, text="Password:", font=self.label_font, bg='#f0f0f0').pack()
        self.password_entry = Entry(self.root, show="*")
        self.password_entry.pack()

        Button(self.root, text="Login", font=self.button_font, command=self.login).pack(pady=10)
        Button(self.root, text="Register", font=self.button_font, command=self.register_screen).pack()

    def register_screen(self):
        self.clear_widgets()
        Label(self.root, text="Register account", font=self.header_font, bg='#f0f0f0').pack(pady=10)

        fields = [
            ("Username:", "reg_username"),
            ("Email:", "reg_email"),
            ("Password:", "reg_password"),
            ("Confirm password:", "reg_confirm_password")
        ]

        self.register_entries = {}

        for label, name in fields:
            Label(self.root, text=label, font=self.label_font, bg='#f0f0f0').pack()
            entry = Entry(self.root)
            if "password" in name:
                entry.config(show="*")
            entry.pack()
            self.register_entries[name] = entry

        Button(self.root, text="Register", font=self.button_font, command=self.register).pack(pady=10)
        Button(self.root, text="Back", font=self.button_font, command=self.start_screen).pack()

    def main_menu(self):
        self.clear_widgets()
        Label(self.root, text=f"Welcome, {self.current_user}!", font=self.header_font, bg='#f0f0f0').pack(pady=20)

        Label(self.root, text="Available Tests:", font=self.label_font, bg='#f0f0f0').pack(pady=10)

        for test in EXAMPLE_TESTS:
            Button(self.root, text=test['title'], font=self.button_font,
                   command=lambda t=test: self.start_test(t)).pack(pady=5)

        Button(self.root, text="Logout", font=self.button_font, command=self.logout).pack(pady=10)

    def start_test(self, test):
        self.current_test = test
        self.current_question_index = 0
        self.correct_answers = 0
        self.show_question()

    def show_question(self):
        self.clear_widgets()
        questions = EXAMPLE_QUESTIONS[self.current_test["id"]]

        if self.current_question_index >= len(questions):
            self.show_result()
            return

        q = questions[self.current_question_index]

        Label(self.root, text=f"{self.current_test['title']} - Question {self.current_question_index + 1}",
              font=self.header_font, bg='#f0f0f0').pack(pady=10)

        Label(self.root, text=q["question"], font=self.label_font, bg='#f0f0f0').pack(pady=5)

        self.selected_option = IntVar(value=-1)

        for i, option in enumerate(q["options"]):
            Radiobutton(self.root, text=option, variable=self.selected_option, value=i,
                        bg='#f0f0f0').pack(anchor='w', padx=20)

        Button(self.root, text="Submit", command=self.check_answer).pack(pady=10)

    def check_answer(self):
        selected = self.selected_option.get()
        if selected == -1:
            messagebox.showwarning("Warning", "Please select an answer.")
            return

        questions = EXAMPLE_QUESTIONS[self.current_test["id"]]
        correct_index = questions[self.current_question_index]["answer"]

        if selected == correct_index:
            self.correct_answers += 1

        self.current_question_index += 1
        self.show_question()

    def show_result(self):
        self.clear_widgets()
        total = len(EXAMPLE_QUESTIONS[self.current_test["id"]])
        result_text = f"You answered {self.correct_answers} out of {total} questions correctly."

        Label(self.root, text="Test Completed", font=self.header_font, bg='#f0f0f0').pack(pady=20)
        Label(self.root, text=result_text, font=self.label_font, bg='#f0f0f0').pack(pady=10)

        Button(self.root, text="Back to Menu", font=self.button_font, command=self.main_menu).pack(pady=10)

    def send_request(self, data):
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((IP, PORT))
            client.send(jsonpickle.encode(data).encode('utf-8'))

            response = client.recv(4096).decode('utf-8')
            client.close()

            if response:
                return jsonpickle.decode(response)
            return {"error": "Empty response from server"}
        except ConnectionRefusedError:
            messagebox.showerror("Error", "No connection")
            return {"error": "Connection refused"}
        except Exception:
            messagebox.showerror("Error", "Connection error")
            return {"error": "Error with server"}

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Enter username and password")
            return

        response = self.send_request({
            "action": "login",
            "username": username,
            "password": password
        })

        if response.get("message") == "Login successful":
            self.current_user = username
            self.main_menu()
        else:
            messagebox.showerror("Error", response.get("message", "Login failed"))

    def register(self):
        if self.register_entries["reg_password"].get() != self.register_entries["reg_confirm_password"].get():
            messagebox.showerror("Error", "Passwords do not match")
            return

        data = {
            "action": "register",
            "username": self.register_entries["reg_username"].get(),
            "email": self.register_entries["reg_email"].get(),
            "password": self.register_entries["reg_password"].get()
        }

        response = self.send_request(data)

        if response.get("message") == "Registration successful":
            messagebox.showinfo("Success", "Registration successful")
            self.start_screen()
        else:
            messagebox.showerror("Error", response.get("message", "Registration failed"))

    def logout(self):
        self.current_user = None
        self.start_screen()


root = Tk()
app = StatusCodeTester(root)

root.mainloop()