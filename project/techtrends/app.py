import sqlite3

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
from datetime import datetime
import threading, logging, sys

class Counter(object):
    def __init__(self):
        self.value = 0
        self._lock = threading.Lock()

    def increment(self):
        with self._lock:
            self.value += 1

    def decrement(self):
        with self._lock:
            self.value -= 1

    def getValue(self):
        v = -1
        with self._lock:
            v = self.value
        return v

c = Counter()

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    c.increment()
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
#    c.decrement()
    return post

def get_post_count():
    connection = get_db_connection()
    post_count = connection.execute('SELECT count(*) FROM posts').fetchone()
    connection.close()
#    c.decrement()
    return post_count[0]

def get_timestamp():
    dateTimeObj = datetime.now()
    return dateTimeObj.strftime("%d/%b/%Y, %H:%M:%S")

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
#    c.decrement()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      app.logger.info('A non-existing article is accessed and a 404 page is returned!')
      return render_template('404.html'), 404
    else:
      app.logger.info('Article "{}" retrieved!'.format(post['title']))
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('The "About Us" page is retrieved!')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
 #           c.decrement()
            app.logger.info('Article "{}" created!'.format(title))
            return redirect(url_for('index'))

    return render_template('create.html')

@app.route('/healthz')
def healthcheck():
    response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
        )
    return response

@app.route('/metrics')
def metrics():
    response = app.response_class(     
            response=json.dumps({"status":"success", "data":{"db_connection_count": c.getValue(), "post_count": get_post_count()}}),
            status=200,
            mimetype='application/json'
        )
    return response

# start the application on port 3111
if __name__ == "__main__":
    stdout_handler = logging.StreamHandler(sys.stdout)
    stderr_handler = logging.StreamHandler(sys.stderr)
    handlers = [stdout_handler, stderr_handler]
#    logging.getLogger('werkzeug').setLevel(logging.DEBUG)
#    logging.getLogger('werkzeug').addHandler(stdout_handler)
#    logging.getLogger('werkzeug').addHandler(stderr_handler)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.basicConfig(level=logging.DEBUG, formatter=formatter, handlers=handlers)
#    app.logger.setLevel(logging.DEBUG)
#    app.logger.addHandler(stdout_handler)
#    app.logger.addHandler(stderr_handler)
    app.run(host='0.0.0.0', port='3111')

