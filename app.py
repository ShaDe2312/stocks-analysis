from flask import Flask, render_template, url_for, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from flask_mysqldb import MySQL
from matplotlib import pyplot as plt
import pandas_datareader as pdr
import pandas
import pandas_ta as ta
import os
from io import BytesIO
from matplotlib.figure import Figure
import base64

app = Flask(__name__)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:bisaf49000@localhost/stocks'
app.config['SECRET_KEY'] = 'thisisasecretkey'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'bisaf49000'
app.config['MYSQL_DB'] = 'stocks'
mysql = MySQL(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)


class RegisterForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                'That username already exists. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')


@app.route('/')
def home():
    return redirect('landing')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
    return render_template('login2.html', form=form)


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('landing'))


@ app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register2.html', form=form)


@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':
        stockname = request.form.get("search_param")
        df = pdr.get_data_yahoo(stockname)
        print(df.to_string)
        dir = 'static/dynamic'
        for f in os.listdir(dir):
            os.remove(os.path.join(dir, f))

        fig = Figure()
        ax = fig.subplots()
        sma10 = df.ta.sma()
        ax.plot(sma10, label='SMA')
        ax.plot(df['Close'], label='Close')
        ax.legend()
        buf = BytesIO()
        fig.savefig(buf, format="png")
        img1data = base64.b64encode(buf.getbuffer()).decode("ascii")


        fig1 = Figure()
        ax1 = fig1.subplots()
        ema10_ohlc4 = df.ta.ema(close=df.ta.ohlc4(), length=10, suffix="OHLC4")
        ax1.plot(ema10_ohlc4, label='EMA')
        ax1.plot(df['Close'], label='Close')
        ax1.legend()
        buf = BytesIO()
        fig1.savefig(buf, format="png")
        img2data = base64.b64encode(buf.getbuffer()).decode("ascii")



        fig2 = Figure()
        ax2 = fig2.subplots()
        donchiandf = df.ta.donchian(lower_length=10, upper_length=15)
        ax2.plot(donchiandf['DCL_10_15'], label='Low')
        ax2.plot(donchiandf['DCM_10_15'], label='Medium')
        ax2.plot(donchiandf['DCU_10_15'], label='High')
        ax2.legend()
        buf = BytesIO()
        fig2.savefig(buf, format="png")
        img3data = base64.b64encode(buf.getbuffer()).decode("ascii")

        fig3 = Figure()
        ax3 = fig3.subplots()
        ebsw = ta.ebsw(df['Close'] , fillna=True)
        ax3.plot(ebsw, label='EBSW')
        ax3.legend()
        buf = BytesIO()
        fig3.savefig(buf, format="png")
        img4data = base64.b64encode(buf.getbuffer()).decode("ascii")
 

        data = [("SMA (10)", f"data:image/png;base64,{img1data}"),("EMA (10)", f"data:image/png;base64,{img2data}"),("Doncian Channel", f"data:image/png;base64,{img3data}"),("EBSW", f"data:image/png;base64,{img4data}")]
        return render_template('dashboard.html',data=data)

@app.route('/message', methods=['GET', 'POST'])
@login_required
def message():
    return render_template('message.html')

@app.route('/blog', methods=['GET', 'POST'])
@login_required
def blog():
    cur = mysql.connection.cursor() 
    cur.execute("SELECT username,comment FROM comments WHERE blog_id='1' ")
    data = cur.fetchall()
    print(data)
    return render_template('blog.html', data=data)

@app.route('/comment', methods=['GET', 'POST'])
@login_required
def comment():
    if request.method == 'POST':
        cur = mysql.connection.cursor() 
        print(current_user.username,request.form.get("comment"), request.form.get("comment_id"),request.form.get("blog_id")) #
        cur.execute("INSERT INTO honours.comments VALUES('%s','%s','%s','%s') " %(current_user.username,request.form.get("comment"), request.form.get("comment_id"), request.form.get("blog_id")))
        mysql.connection.commit()
        return redirect(url_for('blog'));        

@app.route('/insert', methods=['GET','POST'])
@login_required
def insert():
    if request.method== "POST":
        name = request.form['user-name']
        message = request.form['user-message']
        image = request.form['message-image']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO product_review (username, feedback, product_image) VALUES (%s, %s, %s)", (name, message, image))
        mysql.connection.commit()
        return redirect(url_for('insert'))

    cur = mysql.connection.cursor() 
    cur.execute("SELECT username,feedback,product_image FROM product_review");
    data = cur.fetchall()
    print(data)
    return render_template('review.html', data=data);

@app.route('/preferences', methods=['GET','POST'])
@login_required
def preferences():
    if request.method== "POST":
        s1 = request.form.get('stock1')
        s2 = request.form.get('stock2')
        s3 = request.form.get('stock3')
        cur = mysql.connection.cursor()
        cur.execute("UPDATE stock_prefs SET stock1='%s', stock2='%s', stock3='%s' WHERE username = '%s' " %(s1, s2, s3, current_user.username ))
        mysql.connection.commit()
        return redirect(url_for('prefstocks'))
    return render_template('preferences.html')    

@app.route('/prefstocks', methods=['GET', 'POST'])
def prefstocks():
    cur = mysql.connection.cursor() 
    cur.execute("SELECT stock1,stock2,stock3 FROM stock_prefs WHERE username= '%s'" %(current_user.username));
    data = cur.fetchone()
    print(data)
    finaldata = []
    for stock in data:
        graphs = calculator(pdr.get_data_yahoo(stock))
        finaldata.append(graphs)

    return render_template('prefstocks.html' , data=finaldata)

def calculator(df):
        
        fig = Figure()
        ax = fig.subplots()
        sma10 = df.ta.sma()
        ax.plot(sma10, label='SMA')
        ax.plot(df['Close'], label='Close')
        ax.legend()
        buf = BytesIO()
        fig.savefig(buf, format="png")
        img1data = base64.b64encode(buf.getbuffer()).decode("ascii")


        fig1 = Figure()
        ax1 = fig1.subplots()
        ema10_ohlc4 = df.ta.ema(close=df.ta.ohlc4(), length=10, suffix="OHLC4")
        ax1.plot(ema10_ohlc4, label='EMA')
        ax1.plot(df['Close'], label='Close')
        ax1.legend()
        buf = BytesIO()
        fig1.savefig(buf, format="png")
        img2data = base64.b64encode(buf.getbuffer()).decode("ascii")



        fig2 = Figure()
        ax2 = fig2.subplots()
        donchiandf = df.ta.donchian(lower_length=10, upper_length=15)
        ax2.plot(donchiandf['DCL_10_15'], label='Low')
        ax2.plot(donchiandf['DCM_10_15'], label='Medium')
        ax2.plot(donchiandf['DCU_10_15'], label='High')
        ax2.legend()
        buf = BytesIO()
        fig2.savefig(buf, format="png")
        img3data = base64.b64encode(buf.getbuffer()).decode("ascii")

        fig3 = Figure()
        ax3 = fig3.subplots()
        ebsw = ta.ebsw(df['Close'] , fillna=True)
        ax3.plot(ebsw, label='EBSW')
        ax3.legend()
        buf = BytesIO()
        fig3.savefig(buf, format="png")
        img4data = base64.b64encode(buf.getbuffer()).decode("ascii")
 

        data = [("SMA (10)", f"data:image/png;base64,{img1data}"),("EMA (10)", f"data:image/png;base64,{img2data}"),("Doncian Channel", f"data:image/png;base64,{img3data}"),("EBSW", f"data:image/png;base64,{img4data}")]
        return data;

@app.route('/landing', methods=['GET', 'POST'])
def landing():
    return render_template('landing.html')

if __name__ == "__main__":
    app.run(debug=True)

