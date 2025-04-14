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