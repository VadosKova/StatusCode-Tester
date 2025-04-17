from tkinter import *
from tkinter import messagebox
import socket
import jsonpickle

IP = '127.0.0.1'
PORT = 4000

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
        self.user_answers = []
        self.tests = []
        self.questions = []

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

        Button(self.root, text="Available Tests", font=self.button_font, command=self.show_tests).pack(pady=10)
        Button(self.root, text="My Results", font=self.button_font, command=self.show_user_results).pack(pady=10)
        Button(self.root, text="Logout", font=self.button_font, command=self.logout).pack(pady=10)

    def show_tests(self):
        self.clear_widgets()
        Label(self.root, text="Available Tests", font=self.header_font, bg='#f0f0f0').pack(pady=20)

        response = self.send_request({
            "action": "get_tests",
            "username": self.current_user
        })

        if response.get("status") == "ok":
            self.tests = response.get("tests", [])
            for test in self.tests:
                Button(self.root, text=test['title'], font=self.button_font, command=lambda t=test: self.start_test(t)).pack(pady=5)
        else:
            messagebox.showerror("Error", response.get("message", "Failed to load tests"))

        Button(self.root, text="Back", font=self.button_font, command=self.main_menu).pack(pady=10)

    def start_test(self, test):
        self.current_test = test
        self.current_question_index = 0
        self.user_answers = []

        response = self.send_request({
            "action": "get_test_data",
            "username": self.current_user,
            "test_id": test["id"]
        })

        if "questions" in response:
            self.questions = response["questions"]
            self.show_question()
        else:
            messagebox.showerror("Error", "Failed to load questions")
            self.show_tests()

    def show_question(self):
        self.clear_widgets()

        if self.current_question_index >= len(self.questions):
            self.submit_test()
            return

        question = self.questions[self.current_question_index]

        Label(self.root, text=f"Question {self.current_question_index + 1} of {len(self.questions)}", font=self.header_font, bg='#f0f0f0').pack(pady=10)

        Label(self.root, text=question["text"], font=self.label_font, bg='#f0f0f0', wraplength=550).pack(pady=10)

        self.selected_answer = IntVar(value=-1)

        for idx, answer in enumerate(question["answers"]):
            Radiobutton(self.root, text=answer["text"], variable=self.selected_answer, value=idx, bg='#f0f0f0', wraplength=550).pack(anchor='w', padx=20)

        Button(self.root, text="Next" if self.current_question_index < len(self.questions) - 1 else "Submit", font=self.button_font, command=self.save_answer).pack(pady=20)

    def save_answer(self):
        selected_idx = self.selected_answer.get()
        if selected_idx == -1:
            messagebox.showwarning("Warning", "Please select an answer")
            return

        question = self.questions[self.current_question_index]
        selected_answer = question["answers"][selected_idx]

        is_correct_res = self.send_request({
            "action": "check_answer",
            "answer_id": selected_answer["id"],
            "username": self.current_user
        })

        is_correct = bool(is_correct_res.get("is_correct"))

        self.user_answers.append({
            "question_id": question["id"],
            "answer_id": selected_answer["id"],
            "is_correct": is_correct
        })

        self.current_question_index += 1
        self.show_question()

    def submit_test(self):
        try:
            test_data = {
                "action": "submit_test",
                "username": self.current_user,
                "test_id": self.current_test["id"],
                "answers": [{
                    "question_id": a['question_id'],
                    "answer_id": a['answer_id']
                } for a in self.user_answers]
            }

            response = self.send_request(test_data)

            if response.get('status') == 'success':
                self.show_test_result(
                    response['score'],
                    response['total_questions'],
                    response['correct_count']
                )
            else:
                messagebox.showerror("Error", response.get('message', 'Failed to submit test results'))
                self.main_menu()

        except Exception as e:
            messagebox.showerror("Error",f"Error submitting test: {str(e)}")
            self.main_menu()

    def show_test_result(self, score, total, correct):
        self.clear_widgets()
        Label(self.root, text="Test Completed", font=self.header_font, bg='#f0f0f0').pack(pady=20)
        Label(self.root, text=f"Your score: {score}%", font=self.label_font, bg='#f0f0f0').pack()
        Label(self.root, text=f"Correct answers: {correct}/{total}", font=self.label_font, bg='#f0f0f0').pack()

        Button(self.root, text="Back to Tests", font=self.button_font, command=self.show_tests).pack(pady=10)

        Button(self.root, text="Main Menu", font=self.button_font, command=self.main_menu).pack()

    def show_user_results(self):
        self.clear_widgets()
        Label(self.root, text="My Results", font=self.header_font, bg='#f0f0f0').pack(pady=20)

        response = self.send_request({
            "action": "get_results",
            "username": self.current_user
        })

        if "results" in response:
            results = response["results"]
            if not results:
                Label(self.root, text="No test results yet", font=self.label_font, bg='#f0f0f0').pack()
            else:
                for result in results:
                    frame = Frame(self.root, bg='#f0f0f0', padx=10, pady=5)
                    frame.pack(fill=X, padx=20, pady=5)

                    Label(frame,
                          text=f"{result['title']} - Score: {result['score']}%",
                          font=self.label_font,
                          bg='#f0f0f0'
                          ).pack(anchor='w')

                    Label(frame,
                          text=f"Date: {result['date']}",
                          font=('Arial', 8),
                          bg='#f0f0f0'
                          ).pack(anchor='w')
        else:
            messagebox.showerror("Error", "Failed to load results")

        Button(self.root,
               text="Back",
               font=self.button_font,
               command=self.main_menu
               ).pack(pady=20)

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