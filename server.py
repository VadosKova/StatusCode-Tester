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

    except Exception:
        error_response = {"error": "Error with client"}
        client.send(jsonpickle.encode(error_response).encode('utf-8'))
    finally:
        client.close()