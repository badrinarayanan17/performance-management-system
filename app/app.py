from flask import flash
from flask import Flask,render_template,request,redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from models import User
import models
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import io
from app import User
from werkzeug.security import generate_password_hash, check_password_hash
import matplotlib.pyplot as plt
from flask import make_response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import os




app = Flask(__name__)
app.secret_key = 'my_secret_key'
os.urandom(24)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:badri119@localhost:5432/performance_db'
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
    
class User(db.Model, UserMixin):
    __tablename__ = "register"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
   
    def __init__(self, email, password):
        self.email = email
        self.set_password(password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
@app.route("/")
def main():
    results = db.session.query(models.sentiment_analysis).all()
    return render_template('index.html',results = results)

@app.route("/counts")
def counts():
    results = db.session.query(models.sentiment_analysis_counts).all()
    return render_template('counts.html',results = results)

@app.route('/sentiment_counts_image')
def sentiment_counts_image():
    # Query the database for the sentiment counts
    positive_counts = db.session.query(models.sentiment_analysis_counts.email_id, models.sentiment_analysis_counts.positive_count).all()
    negative_counts = db.session.query(models.sentiment_analysis_counts.email_id, models.sentiment_analysis_counts.negative_count).all()

    # Create a dictionary to store the counts for each employee
    positive_dict = {}
    negative_dict = {}

    for email_id, count in positive_counts:
        positive_dict[email_id] = count
    
    for email_id, count in negative_counts:
        negative_dict[email_id] = count

    # Create a bar chart of the sentiment counts
    fig = Figure()
    ax = fig.add_subplot(111)
    fig,ax = plt.subplots(figsize = (11,6))
    ax.bar(list(positive_dict.keys()), list(positive_dict.values()), label='Positive')
    ax.bar(list(negative_dict.keys()), list(negative_dict.values()), bottom=list(positive_dict.values()), label='Negative')
    ax.set_xlabel('Performer')
    ax.set_ylabel('Sentiment Count')
    ax.set_title('Sentiment Counts ')
    ax.legend()


    # Convert the plot to a PNG image
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)

    # Return the image as a response
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = db.session.query(User).filter_by(email=email).first()
        if user:
            flash('Email address already exists', 'error')
        else:
            new_user = models.User(email=email, password_hash=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            flash('You have successfully registered', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    if '_flashes' in session:
        session['_flashes'] = []
    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    email = current_user.email
    sentiment_counts = db.session.query(models.sentiment_analysis_counts).filter_by(email_id=email).first()
    if sentiment_counts:
        positive_count = sentiment_counts.positive_count
        negative_count = sentiment_counts.negative_count
    else:
        positive_count = 0
        negative_count = 0
    return render_template('dashboard.html', positive_count=positive_count, negative_count=negative_count)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
    
    