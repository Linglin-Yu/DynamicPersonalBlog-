from flask import Flask, render_template, redirect, url_for, request, flash,session
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from datetime import datetime
import random, string, re, json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aas4hfs34dfihu'  
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test1.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
limiter = Limiter(app)



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(30), nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    theme = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    text = db.Column(db.String(600), nullable=False)
    is_public = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


@app.route('/')
def index():
    if "visitor_id" not in session:
        session["visitor_id"] = generate_visitor_id()
    return render_template('index.html',visitor_id=session["visitor_id"],user_id=session.get('user_id'))

def generate_visitor_id():
    characters = string.ascii_letters + string.digits
    id_length = 8
    return 'visitor_' + ''.join(random.choice(characters) for _ in range(id_length))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = username
            return redirect(url_for('index'))
        else:
            flash('Login failed. Check your username and password.', 'danger')
    

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different username.', 'danger')
            return render_template('signup.html')
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route('/submit', methods=['POST'])
@limiter.limit("5 per day")
@limiter.limit("1 per 10 seconds")
def submit():
    if request.method == 'POST':
        theme = request.form['theme']
        title = request.form['title']
        text = request.form['text']
        is_public = 'is_public' in request.form
        if contains_sensitive_words(text):
            flash('Your comment contains sensitive words. Please modify it.', 'danger')
            return redirect(url_for('contact'))
        comment = Comment( theme=theme, title=title,text=text, is_public=is_public)
        db.session.add(comment)
        db.session.commit()
        current_date = datetime.now().strftime('%Y-%m-%d')
        return redirect(url_for('contact', current_date=current_date))

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    comments = Comment.query.order_by(Comment.timestamp.asc()).all()
    current_date = request.args.get('current_date', '') 
    return render_template('contact.html', comments=comments, visitor_id=session["visitor_id"], user_id=session.get('user_id'), current_date=current_date)


@app.route('/skill')
def skill():
    return render_template('skill.html')
@app.route('/project')
def project():
    return render_template('project.html')



def load_js_array(js_file, array_name):
    with open(js_file, 'r', encoding='utf-8') as file:
        content = file.read()
        pattern = re.compile(rf'\b{re.escape(array_name)}\b\s*=\s*\[([^\]]+)\];')
        match = pattern.search(content)
        array_definition = match.group(1).strip()
        array_data = json.loads('[' + array_definition + ']')
        return array_data

def contains_sensitive_words(text):
    bad_words = load_js_array("static/badwords.js","badwords")
    for word in bad_words:
        pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
        if re.search(pattern, text):
            return True
    return False

        
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
