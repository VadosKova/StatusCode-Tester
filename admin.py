from tkinter import *
from tkinter import messagebox, simpledialog
import socket
import jsonpickle

IP = '127.0.0.1'
PORT = 4000

def send_request(data):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((IP, PORT))
        s.send(jsonpickle.encode(data).encode('utf-8'))
        response = s.recv(8192).decode('utf-8')
        return jsonpickle.decode(response)

class AdminPanel:
    def __init__(self, root):
        self.root = root
        self.root.title("Admin Panel")
        self.username = None
        self.current_test_id = None
        self.current_question_id = None
        self.login_screen()

    def clear_widgets(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def login_screen(self):
        self.clear_widgets()
        Label(self.root, text="Admin Authorization", font=('Arial', 18)).pack(pady=10)
        Label(self.root, text="Username").pack()
        self.username_entry = Entry(self.root)
        self.username_entry.pack()
        Label(self.root, text="Password").pack()
        self.password_entry = Entry(self.root, show='*')
        self.password_entry.pack()
        Button(self.root, text="Login", command=self.login).pack(pady=10)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        res = send_request({
            "action": "login",
            "username": username,
            "password": password
        })

        if res.get("message") == "Admin login successful" and res.get("is_admin"):
            self.username = username
            self.main_menu()
        elif res.get("message") == "Login successful":
            messagebox.showerror("Access denied", "You are not an admin")
        else:
            messagebox.showerror("Error", res.get("message", "Unknown error"))

    def main_menu(self):
        self.clear_widgets()
        Label(self.root, text=f"Welcome, {self.username}", font=('Arial', 16)).pack(pady=10)

        Button(self.root, text="Add Test", command=self.add_test).pack(pady=5)
        Button(self.root, text="Edit/Delete Tests", command=self.edit_tests).pack(pady=5)
        Button(self.root, text="View Statistics", command=self.view_statistics).pack(pady=5)
        Button(self.root, text="Logout", command=self.login_screen).pack(pady=10)

    def add_test(self):
        title = simpledialog.askstring("Test Title", "Enter title:")
        if not title:
            return
        description = simpledialog.askstring("Description", "Enter description:")
        if not description:
            return

        res = send_request({
            "action": "admin_add_test",
            "username": self.username,
            "title": title,
            "description": description
        })

        if res.get("message") == "Test added":
            messagebox.showinfo("Success", "Test added")
            test_id = res.get("test_id")
            if test_id:
                self.edit_test({"id": test_id, "title": title, "description": description})

    def edit_tests(self):
        self.clear_widgets()
        Label(self.root, text="Edit/Delete Tests", font=('Arial', 16)).pack(pady=10)

        res = send_request({
            "action": "get_tests",
            "username": self.username
        })

        if "tests" not in res:
            messagebox.showerror("Error", "Failed to load tests")
            self.main_menu()
            return

        if "error" in res:
            messagebox.showerror("Error", res["error"])
            self.main_menu()
            return

        tests = res.get("tests", [])

        if not tests:
            Label(self.root, text="No tests available").pack()
        else:
            for test in tests:
                frame = Frame(self.root)
                frame.pack(fill='x', pady=2)

                Label(frame, text=f"{test['title']} - {test.get('description', '')}",
                      anchor='w').pack(side=LEFT, fill='x', expand=True)

                Button(frame, text="Edit",
                       command=lambda t=test: self.edit_test(t)).pack(side=LEFT, padx=5)
                Button(frame, text="Delete",
                       command=lambda t=test: self.delete_test(t['id'])).pack(side=LEFT)

        Button(self.root, text="Back", command=self.main_menu).pack(pady=10)

    def edit_test(self, test):
        self.clear_widgets()
        self.current_test_id = test["id"]

        test_frame = Frame(self.root)
        test_frame.pack(pady=10)

        Label(test_frame, text="Test Details", font=('Arial', 14)).pack()

        Label(test_frame, text="Title:").pack()
        self.test_title_entry = Entry(test_frame, width=50)
        self.test_title_entry.insert(0, test["title"])
        self.test_title_entry.pack()

        Label(test_frame, text="Description:").pack()
        self.test_desc_entry = Entry(test_frame, width=50)
        self.test_desc_entry.insert(0, test.get("description", ""))
        self.test_desc_entry.pack()

        btn_frame = Frame(test_frame)
        btn_frame.pack(pady=10)

        Button(btn_frame, text="Save Changes", command=self.save_test_changes).pack(side=LEFT, padx=5)
        Button(btn_frame, text="Manage Questions", command=lambda: self.edit_test_questions(test["id"])).pack(side=LEFT, padx=5)
        Button(btn_frame, text="Back", command=self.edit_tests).pack(side=LEFT, padx=5)

        questions_frame = Frame(self.root)
        questions_frame.pack(pady=10)

        Label(questions_frame, text="Questions in this test:", font=('Arial', 12)).pack()

        res = send_request({
            "action": "get_test_data",
            "username": self.username,
            "test_id": test["id"]
        })

        if "questions" in res:
            questions = res["questions"]
            if not questions:
                Label(questions_frame, text="No questions yet").pack()
            else:
                for q in questions:
                    q_frame = Frame(questions_frame)
                    q_frame.pack(fill='x', pady=2)

                    Label(q_frame, text=q["text"], anchor='w').pack(side=LEFT, fill='x', expand=True)
                    Button(q_frame, text="Edit", command=lambda q=q: self.edit_question(q)).pack(side=LEFT, padx=2)

        Button(self.root, text="Add New Question", command=self.add_question).pack(pady=5)

    def save_test_changes(self):
        new_title = self.test_title_entry.get()
        new_desc = self.test_desc_entry.get()

        if not new_title:
            messagebox.showerror("Error", "Title cannot be empty")
            return

        res = send_request({
            "action": "admin_edit_test",
            "username": self.username,
            "test_id": self.current_test_id,
            "title": new_title,
            "description": new_desc
        })

        if res.get("message") == "Test updated":
            messagebox.showinfo("Success", "Test updated successfully")
        else:
            messagebox.showerror("Error", res.get("message", "Failed to update test"))

    def edit_test_questions(self, test_id):
        self.clear_widgets()
        self.current_test_id = test_id

        Label(self.root, text="Manage Questions", font=('Arial', 14)).pack(pady=10)

        res = send_request({
            "action": "get_test_data",
            "username": self.username,
            "test_id": test_id
        })

        if "questions" not in res:
            messagebox.showerror("Error", "Failed to load questions")
            self.edit_tests()
            return

        test_data = res.get("questions", [])

        if not test_data:
            Label(self.root, text="No questions in this test").pack()
        else:
            for i, question in enumerate(test_data):
                Button(self.root, text=f"Q{i + 1}: {question['text']}", command=lambda q=question: self.edit_question(q), width=60, anchor='w').pack(pady=2)

        Button(self.root, text="Add Question", command=self.add_question).pack(pady=5)
        Button(self.root, text="Back", command=lambda: self.edit_test({
            "id": self.current_test_id,
            "title": "",
            "description": ""
        })).pack()

    def add_question(self):
        self.clear_widgets()

        Label(self.root, text="Add New Question", font=('Arial', 14)).pack(pady=10)

        Label(self.root, text="Question Text:").pack()
        self.question_text = Text(self.root, height=3, width=50)
        self.question_text.pack(pady=5)

        Label(self.root, text="Answers (select correct with checkbox)").pack()

        self.answer_entries = []
        self.correct_var = IntVar(value=0)

        for i in range(4):
            frame = Frame(self.root)
            frame.pack(fill=X)

            rb = Radiobutton(frame, variable=self.correct_var, value=i)
            rb.pack(side=LEFT)

            entry = Entry(frame, width=50)
            entry.pack(side=LEFT, padx=5)
            self.answer_entries.append(entry)

        btn_frame = Frame(self.root)
        btn_frame.pack(pady=10)

        Button(btn_frame, text="Save Question", command=self.save_question).pack(side=LEFT, padx=5)
        Button(btn_frame, text="Cancel", command=lambda: self.edit_test_questions(self.current_test_id)).pack(side=LEFT)

    def save_question(self):
        question_text = self.question_text.get("1.0", END).strip()
        if not question_text:
            messagebox.showerror("Error", "Question text cannot be empty")
            return

        answers = [entry.get().strip() for entry in self.answer_entries]
        if any(not answer for answer in answers):
            messagebox.showerror("Error", "All answers must be filled")
            return

        question_res = send_request({
            "action": "admin_add_question",
            "username": self.username,
            "test_id": self.current_test_id,
            "question_text": question_text
        })

        if question_res.get("status") != "success":
            error_msg = question_res.get("message", "Unknown error")
            messagebox.showerror("Error", f"Failed to add question: {error_msg}")
            return

        question_id = question_res["question_id"]
        failed_answers = []

        for i, answer_text in enumerate(answers):
            is_correct = (i == self.correct_var.get())
            answer_res = send_request({
                "action": "admin_add_answer",
                "username": self.username,
                "question_id": question_id,
                "answer_text": answer_text,
                "is_correct": is_correct
            })

            if answer_res.get("status") != "success":
                failed_answers.append(answer_text)

        if not failed_answers:
            messagebox.showinfo("Success", "Question and answers added successfully!")
            self.edit_test_questions(self.current_test_id)
        else:
            send_request({
                "action": "admin_delete_question",
                "username": self.username,
                "question_id": question_id
            })
            messagebox.showerror("Error",f"Failed to add answers: {', '.join(failed_answers)}\nQuestion was not saved.")

    def edit_question(self, question):
        self.clear_widgets()
        self.current_question_id = question['id']
        self.correct_answer = IntVar(value=-1)

        Label(self.root, text="Edit Question", font=('Arial', 14, 'bold')).pack(pady=10)

        Label(self.root, text="Question Text:", font=('Arial', 10)).pack()
        self.question_entry = Text(self.root, height=3, width=60, font=('Arial', 10))
        self.question_entry.insert(END, question['text'])
        self.question_entry.pack(pady=5)

        Label(self.root, text="Answers (select correct one):", font=('Arial', 10)).pack()

        self.answer_entries = []
        self.answer_ids = []

        for i, answer in enumerate(question['answers']):
            frame = Frame(self.root)
            frame.pack(fill=X, pady=2)

            Radiobutton(frame, variable=self.correct_answer, value=i, command=lambda idx=i: self._highlight_correct(idx)).pack(side=LEFT)

            entry = Entry(frame, width=60, font=('Arial', 10))
            entry.insert(0, answer['text'])
            entry.pack(side=LEFT, padx=5)
            self.answer_entries.append(entry)
            self.answer_ids.append(answer['id'])

            if answer.get('is_correct', False):
                self.correct_answer.set(i)
                entry.config(bg='#e6f7e6')

        btn_frame = Frame(self.root)
        btn_frame.pack(pady=10)

        Button(btn_frame, text="Update Question", command=self._update_question, bg='#4CAF50', fg='white', font=('Arial', 10)).pack(side=LEFT, padx=5)
        Button(btn_frame, text="Cancel", command=lambda: self.edit_test_questions(self.current_test_id), bg='#f44336', fg='white', font=('Arial', 10)).pack(side=LEFT)

    def _highlight_correct(self, idx):
        for i, entry in enumerate(self.answer_entries):
            entry.config(bg='white')
        self.answer_entries[idx].config(bg='#e6f7e6')

    def _update_question(self):
        question_text = self.question_entry.get("1.0", END).strip()
        if not question_text:
            messagebox.showerror("Error", "Question text cannot be empty!")
            return

        answers = [entry.get().strip() for entry in self.answer_entries]
        if any(not answer for answer in answers):
            messagebox.showerror("Error", "All answers must be filled!")
            return

        if len(set(answers)) != len(answers):
            messagebox.showerror("Error", "Answers must be unique!")
            return

        if self.correct_answer.get() == -1:
            messagebox.showerror("Error", "Please select the correct answer!")
            return

        res = send_request({
            "action": "admin_edit_question",
            "username": self.username,
            "question_id": self.current_question_id,
            "question_text": question_text
        })

        if res.get("message") != "Question updated":
            messagebox.showerror("Error", "Failed to update question!")
            return

        success = True
        for i, answer_id in enumerate(self.answer_ids):
            res = send_request({
                "action": "admin_edit_answer",
                "username": self.username,
                "answer_id": answer_id,
                "answer_text": answers[i],
                "is_correct": (i == self.correct_answer.get())
            })

            if res.get("message") != "Answer updated":
                success = False
                break

        if success:
            messagebox.showinfo("Success", "Question and answers updated successfully!")
            self.edit_test_questions(self.current_test_id)
        else:
            messagebox.showerror("Error", "Failed to update some answers!")

    def delete_test(self, test_id):
        if messagebox.askyesno("Confirm", "Are you sure?"):
            res = send_request({
                "action": "admin_delete_test",
                "username": self.username,
                "test_id": test_id
            })

            if res.get("message") == "Test deleted":
                messagebox.showinfo("Success", "Test deleted")
                self.edit_tests()
            else:
                error_msg = res.get("message", "Unknown error")
                messagebox.showerror("Error", f"Failed to delete test: {error_msg}")

    def view_statistics(self):
        self.clear_widgets()
        Label(self.root, text="Statistics", font=('Arial', 16)).pack(pady=10)

        stats = send_request({
            "action": "admin_get_statistics",
            "username": self.username
        }).get("statistics", [])

        text = Text(self.root, width=100, height=20)
        scrollbar = Scrollbar(self.root, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)

        for stat in stats:
            line = f"{stat['date']} | {stat['username']} | {stat['test']} | {stat['question']} | {stat['answer']} | {'Correct' if stat['correct'] else 'Wrong'}\n"
            text.insert(END, line)

        text.pack(side=LEFT, fill=BOTH)
        scrollbar.pack(side=RIGHT, fill=Y)

        Button(self.root, text="Back", command=self.main_menu).pack(pady=10)


root = Tk()
app = AdminPanel(root)

root.mainloop()