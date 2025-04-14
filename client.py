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