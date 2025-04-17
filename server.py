import socket
import jsonpickle
import pyodbc
import logging

class User:
    def __init__(self, username=None, email=None, password=None):
        self.username = username
        self.email = email
        self.password = password

        self.connection_string = ('DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=StatusTester;Trusted_Connection=yes')
        self.conn = pyodbc.connect(self.connection_string)
        self.cursor = self.conn.cursor()

    def is_admin(self):
        self.cursor.execute('SELECT IsAdmin FROM Users WHERE LOWER(Username) = LOWER(?)', (self.username,))
        result = self.cursor.fetchone()
        return result and result[0] == 1

    def register_user(self):
        self.cursor.execute('INSERT INTO Users (Username, Email, Password) VALUES (?, ?, ?)',(self.username, self.email, self.password))
        self.conn.commit()

    def check_login(self, input_password):
        self.cursor.execute('SELECT Password FROM Users WHERE LOWER(Username) = LOWER(?)', (self.username,))
        result = self.cursor.fetchone()
        if result:
            return result[0] == input_password
        return False

    def check_username_exists(self):
        self.cursor.execute('SELECT * FROM Users WHERE LOWER(Username) = LOWER(?)', (self.username,))
        return self.cursor.fetchone() is not None

    def get_tests(self):
        self.cursor.execute("SELECT ID, Title FROM Tests")
        return [{"id": row[0], "title": row[1]} for row in self.cursor.fetchall()]

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

    def is_answer_correct(self, answer_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT IsCorrect FROM Answers WHERE Id = ?", (answer_id,))
        result = cursor.fetchone()
        return {"is_correct": bool(result[0])} if result else {"is_correct": False}

    def save_test_result(self, test_id, answers):
        result_template = {
            "status": "error",
            "message": "Unknown error",
            "score": 0,
            "correct_count": 0,
            "total_questions": 0
        }

        try:
            self.conn.autocommit = False

            self.cursor.execute('SELECT ID FROM Users WHERE Username = ?', (self.username,))
            user_row = self.cursor.fetchone()
            if not user_row:
                result_template["message"] = "User not found"
                return result_template
            user_id = user_row[0]

            self.cursor.execute('SELECT 1 FROM Tests WHERE ID = ?', (test_id,))
            if not self.cursor.fetchone():
                result_template["message"] = "Test not found"
                return result_template

            correct_count = 0
            validated_answers = []

            for answer in answers:
                if not all(k in answer for k in ['question_id', 'answer_id']):
                    result_template["message"] = f"Invalid answer format: {answer}"
                    return result_template

                self.cursor.execute('SELECT 1 FROM Questions WHERE ID = ?', (answer['question_id'],))
                if not self.cursor.fetchone():
                    result_template["message"] = f"Question {answer['question_id']} not found"
                    return result_template

                self.cursor.execute('''
                        SELECT IsCorrect FROM Answers 
                        WHERE ID = ? AND QuestionID = ?
                    ''', (answer['answer_id'], answer['question_id']))

                result = self.cursor.fetchone()
                if not result:
                    result_template[
                        "message"] = f"Answer {answer['answer_id']} not found or does not belong to question {answer['question_id']}"
                    return result_template

                is_correct = bool(result[0])
                if is_correct:
                    correct_count += 1
                answer['is_correct'] = is_correct
                validated_answers.append(answer)

            total = len(validated_answers)
            if total == 0:
                result_template["message"] = "No valid answers provided"
                return result_template

            score = round((correct_count / total) * 100, 2)

            self.cursor.execute('INSERT INTO Results (UserId, TestId, Score) OUTPUT INSERTED.ID VALUES (?, ?, ?)', (user_id, test_id, score))

            result_id = self.cursor.fetchone()[0]

            for answer in validated_answers:
                self.cursor.execute('''INSERT INTO AnswerLogs 
                        (ResultId, UserId, QuestionId, AnswerId, IsCorrect)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                    result_id,
                    user_id,
                    answer['question_id'],
                    answer['answer_id'],
                    int(answer['is_correct'])
                ))

            self.conn.commit()

            return {
                "status": "success",
                "message": "Test results saved successfully",
                "score": score,
                "correct_count": correct_count,
                "total_questions": total
            }

        except pyodbc.Error as e:
            self.conn.rollback()
            logging.error(f"Database error in save_test_result: {str(e)}")
            result_template["message"] = f"Database error: {str(e)}"
            return result_template
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Unexpected error in save_test_result: {str(e)}")
            result_template["message"] = f"Unexpected error: {str(e)}"
            return result_template
        finally:
            self.conn.autocommit = True

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
        try:
            self.conn.autocommit = False
            self.cursor.execute('INSERT INTO Questions (TestID, QuestionText) OUTPUT INSERTED.ID VALUES (?, ?)',(test_id, question_text))
            question_id_row = self.cursor.fetchone()
            self.conn.commit()
            if question_id_row:
                return {"status": "success", "question_id": int(question_id_row[0])}
            else:
                return {"status": "error", "message": "Failed to retrieve inserted question ID."}
        except Exception as e:
            self.conn.rollback()
            return {"status": "error", "message": str(e)}
        finally:
            self.conn.autocommit = True

    def admin_add_answer(self, question_id, answer_text, is_correct):
        try:
            self.cursor.execute('INSERT INTO Answers (QuestionID, AnswerText, IsCorrect) VALUES (?, ?, ?)',(question_id, answer_text, 1 if is_correct else 0))
            self.conn.commit()
            return {"status": "success"}
        except Exception as e:
            self.conn.rollback()
            return {"status": "error", "message": str(e)}

    def admin_get_statistics(self):
        self.cursor.execute('SELECT U.Username, T.Title, R.Score, R.DateTaken, Q.QuestionText, A.AnswerText, L.IsCorrect FROM AnswerLogs L JOIN Results R ON L.ResultId = R.ID JOIN Users U ON L.UserId = U.ID JOIN Questions Q ON L.QuestionId = Q.ID JOIN Answers A ON L.AnswerId = A.ID JOIN Tests T ON R.TestId = T.ID ORDER BY R.DateTaken DESC')
        return self.cursor.fetchall()

    def admin_edit_test(self, test_id, title, description):
        self.cursor.execute('UPDATE Tests SET Title = ?, Description = ? WHERE ID = ?', (title, description, test_id))
        self.conn.commit()

    def admin_edit_question(self, question_id, question_text):
        self.cursor.execute('UPDATE Questions SET QuestionText = ? WHERE ID = ?', (question_text, question_id))
        self.conn.commit()

    def admin_edit_answer(self, answer_id, answer_text, is_correct):
        self.cursor.execute('UPDATE Answers SET AnswerText = ?, IsCorrect = ? WHERE ID = ?',(answer_text, is_correct, answer_id))
        self.conn.commit()

    def admin_delete_test(self, test_id):
        try:
            self.cursor.execute('SELECT ID FROM Tests WHERE ID = ?', (test_id,))
            if not self.cursor.fetchone():
                return False
            self.conn.autocommit = False

            self.cursor.execute('DELETE FROM AnswerLogs WHERE ResultId IN (SELECT ID FROM Results WHERE TestId = ?)', (test_id,))

            self.cursor.execute('DELETE FROM Results WHERE TestId = ?', (test_id,))

            self.cursor.execute('DELETE FROM Answers WHERE QuestionID IN (SELECT ID FROM Questions WHERE TestID = ?)', (test_id,))

            self.cursor.execute('DELETE FROM Questions WHERE TestID = ?', (test_id,))

            self.cursor.execute('DELETE FROM Tests WHERE ID = ?', (test_id,))

            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"Error deleting test: {str(e)}")
            return False
        finally:
            self.conn.autocommit = True

    def admin_delete_question(self, question_id):
        try:
            self.conn.autocommit = False
            self.cursor.execute('DELETE FROM Answers WHERE QuestionID = ?', (question_id,))
            self.cursor.execute('DELETE FROM Questions WHERE ID = ?', (question_id,))
            self.conn.commit()
            return {"status": "success"}
        except Exception as e:
            self.conn.rollback()
            return {"status": "error", "message": str(e)}
        finally:
            self.conn.autocommit = True

    def close_connection(self):
        self.conn.close()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def client_request(client):
    try:
        req = client.recv(4096).decode('utf-8')
        data = jsonpickle.decode(req)
        action = data.get('action')
        res = {"message": "Unknown action"}

        user = User(username=data.get('username'))

        if action == 'register':
            user = User(username=data['username'], email=data['email'], password=data['password'])
            if user.check_username_exists():
                res = {"message": "Username already registered"}
            else:
                user.register_user()
                res = {"message": "Registration successful"}

        elif action == 'login':
            if user.check_login(data['password']):
                is_admin = user.is_admin()
                if is_admin:
                    res = {"message": "Admin login successful", "is_admin": True}
                else:
                    res = {"message": "Login successful", "is_admin": False}
            else:
                res = {"message": "Invalid credentials"}

        elif action == 'get_tests':
            tests = user.get_tests()
            res = {"status": "ok", "tests": tests}

        elif action == 'get_test_data':
            user = User(username=data['username'])
            test_data = user.get_test_questions_and_answers(data['test_id'])
            res = {"questions": test_data}

        elif action == 'submit_test':
            try:
                user = User(username=data['username'])
                test_id = data['test_id']
                answers = data['answers']
                logging.info(
                    f"Received submit_test request: username={data['username']}, test_id={test_id}, answers={answers}")

                if not isinstance(answers, list):
                    raise ValueError("Answers should be a list")

                for answer in answers:
                    if not isinstance(answer, dict) or not all(k in answer for k in ['question_id', 'answer_id']):
                        raise ValueError(f"Invalid answer format: {answer}")

                result = user.save_test_result(test_id, answers)

                if result.get('status') == 'success':
                    res = {
                        "status": "success",
                        "message": "Test submitted",
                        "score": result['score'],
                        "correct_count": result['correct_count'],
                        "total_questions": result['total_questions']
                    }
                else:
                    res = {
                        "status": "error",
                        "message": result.get('message', 'Failed to save test results')
                    }

            except Exception as e:
                logging.error(f"Error in submit_test: {str(e)}")
                res = {
                    "status": "error",
                    "message": f"Error submitting test: {str(e)}"
                }

        elif action == 'get_questions':
            user = User(username=data['username'])
            test_id = data['test_id']
            questions = user.get_test_questions_and_answers(test_id)

            for q in questions:
                correct_index = next((i for i, a in enumerate(q['answers']) if user.is_answer_correct(a['id'])), -1)
                q['correct_index'] = correct_index
            res = {"questions": questions}

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

        elif action == 'check_answer':
            user = User(username=data.get('username'))
            res = user.is_answer_correct(data['answer_id'])

        elif action == 'admin_add_test':
            if user.is_admin():
                user.admin_add_test(data['title'], data['description'])
                res = {"message": "Test added"}
            else:
                res = {"message": "Unauthorized"}

        elif action == 'admin_add_question':
            if user.is_admin():
                res = user.admin_add_question(data['test_id'], data['question_text'])
            else:
                res = {"status": "error", "message": "Unauthorized"}

        elif action == 'admin_add_answer':
            if user.is_admin():
                res = user.admin_add_answer(
                    data['question_id'],
                    data['answer_text'],
                    bool(data['is_correct'])
                )
            else:
                res = {"status": "error", "message": "Unauthorized"}

        elif action == 'admin_get_statistics':
            if user.is_admin():
                stats = user.admin_get_statistics()
                res = {
                    "statistics": [
                        {
                            "username": s.Username,
                            "test": s.Title,
                            "score": s.Score,
                            "date": s.DateTaken.strftime('%Y-%m-%d %H:%M:%S'),
                            "question": s.QuestionText,
                            "answer": s.AnswerText,
                            "correct": bool(s.IsCorrect)
                        } for s in stats
                    ]
                }
            else:
                res = {"message": "Unauthorized"}

        elif action == 'admin_edit_test':
            if user.is_admin():
                user.admin_edit_test(data['test_id'], data['title'], data['description'])
                res = {"message": "Test updated"}
            else:
                res = {"message": "Unauthorized"}

        elif action == 'admin_edit_question':
            if user.is_admin():
                user.admin_edit_question(data['question_id'], data['question_text'])
                res = {"message": "Question updated"}
            else:
                res = {"message": "Unauthorized"}

        elif action == 'admin_edit_answer':
            if user.is_admin():
                user.admin_edit_answer(data['answer_id'], data['answer_text'], data['is_correct'])
                res = {"message": "Answer updated"}
            else:
                res = {"message": "Unauthorized"}

        elif action == 'admin_delete_test':
            if user.is_admin():
                user.admin_delete_test(data['test_id'])
                res = {"message": "Test deleted"}
            else:
                res = {"message": "Unauthorized"}

        elif action == 'admin_delete_question':
            if user.is_admin():
                res = user.admin_delete_question(data['question_id'])
            else:
                res = {"status": "error", "message": "Unauthorized"}

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