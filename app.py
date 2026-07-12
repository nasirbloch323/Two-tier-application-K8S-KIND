import os
from flask import Flask, render_template, request, jsonify
from flask_mysqldb import MySQL
from dotenv import load_dotenv

load_dotenv()  # ✅ Load from .env

app = Flask(__name__)

# ✅ Print for debug
print("✅ DB Config:")
print("Host:", os.environ.get('MYSQL_HOST'))
print("User:", os.environ.get('MYSQL_USER'))
print("Pass:", os.environ.get('MYSQL_PASSWORD'))
print("DB:  ", os.environ.get('MYSQL_DB'))

# ✅ Config from env
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'default_user')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', 'default_password')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'default_db')

mysql = MySQL(app)

def init_db():
    with app.app_context():
        try:
            cur = mysql.connection.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    message TEXT
                );
            ''')
            mysql.connection.commit()
            cur.close()
            print("✅ Table creat or already exists.")
        except Exception as e:
            print("❌ DB init error:", e)

@app.route('/')
def hello():
    try:
        cur = mysql.connection.cursor()
        cur.execute('SELECT message FROM messages')
        messages = cur.fetchall()
        cur.close()
        return render_template('index.html', messages=messages)
    except Exception as e:
        return f"❌ Error loading messages: {e}"

@app.route('/submit', methods=['POST'])
def submit():
    try:
        new_message = request.form.get('new_message')
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO messages (message) VALUES (%s)', [new_message])
        mysql.connection.commit()
        cur.close()
        return jsonify({'message': new_message})
    except Exception as e:
        return f"❌ Error submitting message: {e}"

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)

