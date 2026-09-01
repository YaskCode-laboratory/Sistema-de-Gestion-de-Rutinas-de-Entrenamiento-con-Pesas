from flask import render_template, flash, redirect, url_for
from app import app
from app.forms import LoginForm
from app.forms import SignupForm

@app.route('/')
def home():
    return render_template('base.html')
    #return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for user {}'.format(form.username.data))
        return redirect(url_for('home'))
    return render_template('access.html', form=form)



@app.route("/signup", methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        flash('Registro exitoso!')
        return redirect(url_for('login'))
    return render_template('access.html', method='signup', form=form)