import socket
import jsonpickle
import pyodbc

class User:
    def __init__(self, username=None, email=None, password=None):
        self.username = username
        self.email = email
        self.password = password

        self.connection_string = ('DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=StatusTester;Trusted_Connection=yes')
        self.conn = pyodbc.connect(self.connection_string)
        self.cursor = self.conn.cursor()

    def is_admin(self):
        self.cursor.execute('SELECT IsAdmin FROM Users WHERE Username = ?', (self.username,))
        result = self.cursor.fetchone()
        return result and result[0] == 1

    def register_user(self):
        self.cursor.execute('INSERT INTO Users (Username, Email, Password) VALUES (?, ?, ?)',(self.username, self.email, self.password))
        self.conn.commit()

    def check_login(self, input_password):
        self.cursor.execute('SELECT Password FROM Users WHERE Username = ?', (self.username,))
        result = self.cursor.fetchone()
        if result:
            return result[0] == input_password
        return False

    def check_username_exists(self):
        self.cursor.execute('SELECT * FROM Users WHERE Username = ?', (self.username,))
        return self.cursor.fetchone() is not None

    def get_available_tests(self):
        self.cursor.execute('SELECT ID, Title, Description FROM Tests')
        return self.cursor.fetchall()

    def get_test_questions_and_answers(self, test_id):
        self.cursor.execute('SELECT ID, QuestionText FROM Questions WHERE TestID = ?', (test_id,))
        questions = self.cursor.fetchall()
        question_data = []

        for q in questions:
            q_id, q_text = q
            self.cursor.execute('SELECT ID, AnswerText FROM Answers WHERE QuestionID = ?', (q_id,))
            answers = self.cursor.fetchall()
            answer_list = [{"id": a[0], "text": a[1]} for a in answers]
            question_data.append({"id": q_id, "text": q_text, "answers": answer_list})

        return question_data

    def save_test_result(self, test_id, score, answers):
        self.cursor.execute('SELECT ID FROM Users WHERE Username = ?', (self.username,))
        user_id = self.cursor.fetchone()[0]

        self.cursor.execute('INSERT INTO Results (UserId, TestId, Score, DateTaken) VALUES (?, ?, ?, GETDATE())',(user_id, test_id, score))
        self.conn.commit()

        self.cursor.execute('SELECT TOP 1 ID FROM Results WHERE UserId = ? ORDER BY DateTaken DESC', (user_id,))
        result_id = self.cursor.fetchone()[0]

        for a in answers:
            self.cursor.execute('INSERT INTO AnswerLogs (ResultId, UserId, QuestionId, AnswerId, IsCorrect) VALUES (?, ?, ?, ?, ?)', (result_id, user_id, a['question_id'], a['answer_id'], a['is_correct']))
        self.conn.commit()

    def get_user_results(self):
        self.cursor.execute('SELECT ID FROM Users WHERE Username = ?', (self.username,))
        user_row = self.cursor.fetchone()

        if not user_row:
            return []

        user_id = user_row[0]

        self.cursor.execute('SELECT T.Title, R.Score, R.DateTaken FROM Results R JOIN Tests T ON R.TestId = T.ID WHERE R.UserId = ? ORDER BY R.DateTaken DESC', (user_id,))
        return self.cursor.fetchall()

    def admin_add_test(self, title, description):
        self.cursor.execute('INSERT INTO Tests (Title, Description) VALUES (?, ?)', (title, description))
        self.conn.commit()

    def admin_add_question(self, test_id, question_text):
        self.cursor.execute('INSERT INTO Questions (TestID, QuestionText) VALUES (?, ?)', (test_id, question_text))
        self.conn.commit()
        return self.cursor.execute('SELECT SCOPE_IDENTITY()').fetchone()[0]

    def admin_add_answer(self, question_id, answer_text, is_correct):
        self.cursor.execute(
            'INSERT INTO Answers (QuestionID, AnswerText, IsCorrect) VALUES (?, ?, ?)',
            (question_id, answer_text, is_correct)
        )
        self.conn.commit()

    def close_connection(self):
        self.conn.close()

def client_request(client):
    try:
        req = client.recv(4096).decode('utf-8')
        data = jsonpickle.decode(req)
        action = data.get('action')
        res = {"message": "Unknown action"}

        if action == 'register':
            user = User(username=data['username'], email=data['email'], password=data['password'])
            if user.check_username_exists():
                res = {"message": "Username already registered"}
            else:
                user.register_user()
                res = {"message": "Registration successful"}

        elif action == 'login':
            user = User(username=data['username'])
            if user.check_login(data['password']):
                res = {"message": "Login successful"}
            else:
                res = {"message": "Invalid credentials"}

        elif action == 'get_tests':
            user = User(username=data['username'])
            tests = user.get_available_tests()
            res = {"tests": [{"id": t.ID, "title": t.Title, "description": t.Description} for t in tests]}

        elif action == 'get_test_data':
            user = User(username=data['username'])
            test_data = user.get_test_questions_and_answers(data['test_id'])
            res = {"questions": test_data}

        elif action == 'submit_test':
            user = User(username=data['username'])
            test_id = data['test_id']
            answers = data['answers']
            correct_count = sum(1 for a in answers if a['is_correct'])
            total = len(answers)
            score = round((correct_count / total) * 100, 2)
            user.save_test_result(test_id, score, answers)
            res = {"message": "Test submitted", "score": score}

        elif action == 'get_results':
            user = User(username=data['username'])
            results = user.get_user_results()
            res = {
                "results": [
                    {
                        "title": r.Title,
                        "score": r.Score,
                        "date": r.DateTaken.strftime('%Y-%m-%d %H:%M:%S')
                    } for r in results
                ]
            }

        client.send(jsonpickle.encode(res).encode('utf-8'))
    except Exception:
        error_response = {"error": "Error with client"}
        client.send(jsonpickle.encode(error_response).encode('utf-8'))
    finally:
        client.close()


IP = '127.0.0.1'
PORT = 4000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((IP, PORT))
server.listen(2)
print("Сервер запущен...")

while True:
    client, addr = server.accept()
    print(f"Подключение от {addr}")
    client_request(client)