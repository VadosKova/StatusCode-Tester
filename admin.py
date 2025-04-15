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

        if res.get("message") == "Admin login successful":
            self.username = username
            self.main_menu()
        else:
            messagebox.showerror("Error", res.get("message", "Unknown error"))

    def main_menu(self):
        self.clear_widgets()
        Label(self.root, text=f"Welcome, {self.username}", font=('Arial', 16)).pack(pady=10)

        Button(self.root, text="Add Test", command=self.add_test).pack(pady=5)
        Button(self.root, text="Edit/Delete Tests", command=self.edit_tests).pack(pady=5)
        Button(self.root, text="View Statistics", command=self.view_stats).pack(pady=5)
        Button(self.root, text="Logout", command=self.login_screen).pack(pady=10)

    def add_test(self):
        title = simpledialog.askstring("Test Title", "Enter title:")
        description = simpledialog.askstring("Description", "Enter description:")
        if title and description:
            res = send_request({
                "action": "admin_add_test",
                "username": self.username,
                "title": title,
                "description": description
            })
            if res.get("message") == "Test added":
                messagebox.showinfo("Success", "Test added")

    def edit_tests(self):
        self.clear_widgets()
        Label(self.root, text="Edit/Delete Tests", font=('Arial', 16)).pack(pady=10)
        tests = send_request({
            "action": "get_tests",
            "username": self.username
        }).get("tests", [])

        for test in tests:
            frame = Frame(self.root)
            frame.pack(fill='x', pady=2)

            Label(frame, text=f"{test['title']} - {test['description']}", anchor='w').pack(side=LEFT, fill='x', expand=True)

            Button(frame, text="Edit", command=lambda t=test: self.edit_test(t)).pack(side=LEFT, padx=5)
            Button(frame, text="Delete", command=lambda t=test: self.delete_test(t['id'])).pack(side=LEFT)

        Button(self.root, text="Back", command=self.main_menu).pack(pady=10)

    def edit_test(self, test):
        new_title = simpledialog.askstring("Edit Title", "Enter new title:", initialvalue=test["title"])
        new_description = simpledialog.askstring("Edit Description", "Enter new description:", initialvalue=test["description"])
        if new_title and new_description:
            res = send_request({
                "action": "admin_edit_test",
                "username": self.username,
                "test_id": test["id"],
                "title": new_title,
                "description": new_description
            })
            if res.get("message") == "Test updated":
                messagebox.showinfo("Success", "Test updated")
        self.edit_test_questions(test["id"])

    def edit_test_questions(self, test_id):
        self.clear_widgets()
        Label(self.root, text="Edit Questions", font=('Arial', 14)).pack(pady=10)
        test_data = send_request({
            "action": "get_test_data",
            "username": self.username,
            "test_id": test_id
        }).get("questions", [])

        for question in test_data:
            q_frame = Frame(self.root)
            q_frame.pack(fill='x', pady=2)

            Label(q_frame, text=f"Q: {question['text']}", anchor='w').pack(side=LEFT, expand=True)
            Button(q_frame, text="Edit", command=lambda q=question: self.edit_question(q)).pack(side=LEFT, padx=2)

            for answer in question['answers']:
                a_frame = Frame(self.root)
                a_frame.pack(fill='x', padx=20)
                Label(a_frame, text=f"A: {answer['text']}", anchor='w').pack(side=LEFT, expand=True)
                Button(a_frame, text="Edit", command=lambda a=answer: self.edit_answer(a)).pack(side=LEFT, padx=2)

        Button(self.root, text="Add Question", command=lambda: self.add_question(test_id)).pack(pady=5)
        Button(self.root, text="Back", command=self.edit_tests).pack(pady=5)

    def add_question(self, test_id):
        q_text = simpledialog.askstring("New Question", "Enter question text:")
        if q_text:
            res = send_request({
                "action": "admin_add_question",
                "username": self.username,
                "test_id": test_id,
                "question_text": q_text
            })
            q_id = res.get("question_id")
            if q_id:
                for _ in range(4):
                    a_text = simpledialog.askstring("Answer", "Enter answer text:")
                    is_correct = messagebox.askyesno("Correct?", f"Is this the correct answer: {a_text}?")
                    send_request({
                        "action": "admin_add_answer",
                        "username": self.username,
                        "question_id": q_id,
                        "answer_text": a_text,
                        "is_correct": is_correct
                    })
                messagebox.showinfo("Success", "Question and answers added")
                self.edit_test_questions(test_id)

    def edit_question(self, question):
        new_text = simpledialog.askstring("Edit Question", "Enter new question text:", initialvalue=question['text'])
        if new_text:
            send_request({
                "action": "admin_edit_question",
                "username": self.username,
                "question_id": question["id"],
                "question_text": new_text
            })
            messagebox.showinfo("Success", "Question updated")
            self.edit_test_questions(question['id'])

    def edit_answer(self, answer):
        new_text = simpledialog.askstring("Edit Answer", "Enter new answer text:", initialvalue=answer['text'])
        is_correct = messagebox.askyesno("Correct?", f"Is this the correct answer?")
        send_request({
            "action": "admin_edit_answer",
            "username": self.username,
            "answer_id": answer["id"],
            "answer_text": new_text,
            "is_correct": is_correct
        })
        messagebox.showinfo("Success", "Answer updated")
        self.edit_tests()

    def delete_test(self, test_id):
        if messagebox.askyesno("Confirm", "Are you sure?"):
            send_request({
                "action": "admin_delete_test",
                "username": self.username,
                "test_id": test_id
            })
            messagebox.showinfo("Deleted", "Test deleted")
            self.edit_tests()

    def view_statistics(self):
        self.clear_widgets()
        Label(self.root, text="Statistics", font=('Arial', 16)).pack(pady=10)
        res = send_request({
            "action": "admin_get_statistics",
            "username": self.username
        })

        stats = res.get("statistics", [])
        for stat in stats:
            Label(
                self.root,
                text=f"{stat['date']} | {stat['username']} | {stat['test']} | {stat['question']} | {stat['answer']} | {'Correct' if stat['correct'] else 'Wrong'}"
            ).pack(anchor='w', padx=10)

        Button(self.root, text="Back", command=self.main_menu).pack(pady=10)


root = Tk()
app = AdminPanel(root)

root.mainloop()