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