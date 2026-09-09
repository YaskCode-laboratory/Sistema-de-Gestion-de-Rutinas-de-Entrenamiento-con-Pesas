from flask import render_template, flash, redirect, url_for, session
from app import app
from app.forms import LoginForm
from app.forms import SignupForm
from app.forms import TrainerCodeForm
from app.forms import ClientProfileForm
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from app import db
from app.models import Usuario, Entrenador, Cliente
from flask import request
from urllib.parse import urlsplit

@app.route('/')
def home():
    if current_user.is_authenticated:
        return render_template('base.html')
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        usuario = db.session.scalar(sa.select(Usuario).where(Usuario.nombre_usuario == form.username.data.strip())) # .strip() elimina espacios en blanco

        if usuario is None:
            form.username.errors.append("Este usuario no existe")
            return render_template('auth/login.html', form=form), 400
        if not usuario.chequear_contraseña(form.password.data):
            form.password.errors.append("La contraseña es invalida")
            return render_template('auth/login.html', form=form), 400
        login_user(usuario, remember=form.remember_me.data)
        
        flash('Usuario: {}'.format(usuario.nombre_usuario))
        flash('Rol: {}'.format(usuario.tipo))
        if usuario.tipo == 'entrenador':
            flash('Codigo de Entrenador: {}'.format(usuario.codigo_entrenador))
        elif usuario.tipo == 'cliente':
            flash('Entrenador: {}'.format(usuario.entrenador.nombre_usuario))

        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(next_page)
    
    return render_template('auth/login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = SignupForm()
    if form.validate_on_submit():
        if form.role.data == 'entrenador':
            usuario = Entrenador(nombre_usuario=form.username.data.strip())
            usuario.guardar_contraseña(form.password.data)
            usuario.generar_codigo_entrenador()
            db.session.add(usuario)
            db.session.commit()
            flash('Registro exitoso!')
            return redirect(url_for('login'))

        elif form.role.data == 'cliente':
            session['reg_cliente'] = {
            'username': form.username.data,
            'password': form.password.data
            }
            return redirect(url_for('link_trainer'))

    return render_template('auth/signup.html', form=form)

#2do Paso de registro para cliente
@app.route("/signup/link-trainer", methods=['GET', 'POST'])
def link_trainer():
    if 'reg_cliente' not in session:
        return redirect(url_for('signup'))

    form = TrainerCodeForm()
    if form.validate_on_submit():
        entrenador = db.session.scalar(sa.select(Entrenador).where(Entrenador.codigo_entrenador == form.codigo_entrenador.data.strip().upper()))
        session['reg_cliente']['entrenador_id'] = entrenador.id
        session.modified = True  # Signal session modification to Flask
        return redirect(url_for('client_profile'))
    
    return render_template('auth/link_trainer.html', form=form)

#3er y ultimo Paso de registro para cliente
@app.route("/signup/client-profile", methods=['GET', 'POST'])
def client_profile():
    reg_data = session.get('reg_cliente')
    if not reg_data or 'entrenador_id' not in reg_data:
        return redirect(url_for('signup'))

    form = ClientProfileForm()
    if form.validate_on_submit():
        cliente = Cliente(nombre_usuario=reg_data['username'], entrenador_id=reg_data['entrenador_id'], peso=form.peso.data, meta=form.objetivo.data, nivel_experiencia=form.nivel_experiencia.data)
        cliente.guardar_contraseña(reg_data['password'])

        db.session.add(cliente)
        db.session.commit()

        # Clean session after successful registration
        session.pop('reg_cliente')

        flash('Registro exitoso!')
        return redirect(url_for('login'))
    return render_template('auth/client_profile.html', form=form)