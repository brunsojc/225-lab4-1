from flask import Flask, request, render_template_string
import sqlite3
import os
import unittest

app = Flask(__name__)

# Configuration
class Config:
    TESTING = False
    DEBUG = False
    DATABASE = '/nfs/demo.db'

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True

app.config.from_object(DevelopmentConfig)  # Change to TestingConfig for testing environment

# Database file path
DATABASE = app.config['DATABASE']

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row  # This enables name-based access to columns
    return db

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL
            );
        ''')
        db.commit()

def update_contact(contact_id, name, phone):
    db = get_db()
    db.execute('UPDATE contacts SET name = ?, phone = ? WHERE id = ?', (name, phone, contact_id))
    db.commit()

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ''  # Message indicating the result of the operation
    if request.method == 'POST':
        # Check if it's a delete action
        if request.form.get('action') == 'delete':
            contact_id = request.form.get('contact_id')
            db = get_db()
            db.execute('DELETE FROM contacts WHERE id = ?', (contact_id,))
            db.commit()
            message = 'Contact deleted successfully.'
        elif request.form.get('action') == 'edit':
            contact_id = request.form.get('contact_id')
            name = request.form.get('name')
            phone = request.form.get('phone')
            if name and phone:
                update_contact(contact_id, name, phone)
                message = 'Contact updated successfully.'
            else:
                message = 'Missing name or phone number.'
        else:
            name = request.form.get('name')
            phone = request.form.get('phone')
            if name and phone:
                db = get_db()
                db.execute('INSERT INTO contacts (name, phone) VALUES (?, ?)', (name, phone))
                db.commit()
                message = 'Contact added successfully.'
            else:
                message = 'Missing name or phone number.'

    # Always display the contacts table
    db = get_db()
    contacts = db.execute('SELECT * FROM contacts').fetchall()

    # Display the HTML form along with the contacts table
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Contacts</title>
            <style>
                table {
                    border-collapse: collapse;
                    width: 50%;
                }
                th, td {
                    border: 1px solid #dddddd;
                    text-align: left;
                    padding: 8px;
                }
                th {
                    background-color: #f2f2f2;
                }
                input[type="submit"] {
                    background-color: #4CAF50;
                    color: white;
                    padding: 8px 20px;
                    border: none;
                    cursor: pointer;
                    border-radius: 4px;
                }
                input[type="submit"]:hover {
                    background-color: #45a049;
                }
            </style>
        </head>
        <body>
            <h2>Add Contact</h2>
            <form method="POST" action="/">
                <label for="name">Name:</label><br>
                <input type="text" id="name" name="name" required><br>
                <label for="phone">Phone Number:</label><br>
                <input type="text" id="phone" name="phone" pattern="[0-9]{3}-[0-9]{3}-[0-9]{4}" required title="Phone number must be in the format xxx-xxx-xxxx"><br><br>
                <input type="submit" value="Submit">
            </form>
            <p>{{ message }}</p>
            {% if contacts %}
                <table border="1">
                    <tr>
                        <th>Name</th>
                        <th>Phone Number</th>
                        <th>Edit</th>
                        <th>Delete</th>
                    </tr>
                    {% for contact in contacts %}
                        <tr>
                            <td>{{ contact['name'] }}</td>
                            <td>{{ contact['phone'] }}</td>
                            <td>
                                <form method="POST" action="/">
                                    <input type="hidden" name="contact_id" value="{{ contact['id'] }}">
                                    <input type="hidden" name="name" value="{{ contact['name'] }}">
                                    <input type="hidden" name="phone" value="{{ contact['phone'] }}">
                                    <input type="hidden" name="action" value="edit">
                                    <input type="submit" value="Edit">
                                </form>
                            </td>
                            <td>
                                <form method="POST" action="/">
                                    <input type="hidden" name="contact_id" value="{{ contact['id'] }}">
                                    <input type="hidden" name="action" value="delete">
                                    <input type="submit" value="Delete">
                                </form>
                            </td>
                        </tr>
                    {% endfor %}
                </table>
            {% else %}
                <p>No contacts found.</p>
            {% endif %}
        </body>
        </html>
    ''', message=message, contacts=contacts)

# Static code testing
@app.cli.command('test')
def test():
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner().run(tests)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    init_db()  # Initialize the database and table
    app.run(debug=True, host='0.0.0.0', port=port)
