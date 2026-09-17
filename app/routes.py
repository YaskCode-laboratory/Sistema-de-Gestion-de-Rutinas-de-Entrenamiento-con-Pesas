from flask import render_template, flash, redirect, url_for, session
from app import app
from app.forms import LoginForm
from app.forms import SignupForm
from app.forms import TrainerCodeForm
from app.forms import ClientProfileForm
from app.forms import ExerciseForm
from app.forms import RoutineForm
from app.forms import SessionForm
from app.forms import PrescriptionForm
from flask_login import current_user, login_user, logout_user, login_required
from app.utils import role_required
import sqlalchemy as sa
from app import db
from app.models import Usuario, Entrenador, Cliente, Ejercicio, Rutina, Sesion, PrescripcionEjercicioSesion
from flask import request
from urllib.parse import urlsplit

@app.route('/')
def home():
    if current_user.is_authenticated:
        if current_user.tipo == 'entrenador':
            return redirect(url_for('clientes'))
        elif current_user.tipo == 'cliente':
            return redirect(url_for('perfil'))
    else:
        return redirect(url_for('login'))

@app.route('/clientes')
@role_required('entrenador')
def clientes():
    return render_template('trainer/clientes.html')

@app.route('/trainer/ejercicios', methods=['GET', 'POST'])
@role_required('entrenador')
def ejercicios():
    form = ExerciseForm()                                                                                                                                                                                    
                                                                                                                                                                                                                
    if request.method == 'POST':                                                                                                                                                                             
        # 1. Caso: ¿Se presionó el botón de Eliminar?                                                                                                                                                        
        delete_id = request.form.get('delete_id')                                                                                                                                                            
        if delete_id:                                                                                                                                                                                        
            ejercicio = db.session.get(Ejercicio, int(delete_id))                                                                                                                                            
            if ejercicio and ejercicio.entrenador_id == current_user.id:                                                                                                                                     
                db.session.delete(ejercicio)                                                                                                                                                                 
                db.session.commit()                                                                                                                                                                          
                flash(f'Ejercicio "{ejercicio.nombre}" eliminado.', 'success')                                                                                                                               
            else:                                                                                                                                                                                            
                flash("No puedes eliminar un ejercicio base del sistema.", "danger")                                                                                                                         
            return redirect(url_for('ejercicios'))                                                                                                                                                           
                                                                                                                                                                                                                
        # 2. Caso: ¿Se envió el formulario de Crear nuevo ejercicio?                                                                                                                                         
        if form.validate_on_submit():                                                                                                                                                                        
            nuevo = Ejercicio(                                                                                                                                                                               
                nombre=form.nombre.data.strip(),                                                                                                                                                             
                grupo_muscular=form.grupo_muscular.data,
                patron_movimiento=form.patron_movimiento.data,                                                                                                                                                     
                entrenador_id=current_user.id                                                                                                                                                                
            )                                                                                                                                                                                                
            db.session.add(nuevo)                                                                                                                                                                            
            db.session.commit()                                                                                                                                                                              
            flash(f'Ejercicio "{nuevo.nombre}" agregado.', 'success')                                                                                                                                        
            return redirect(url_for('ejercicios'))                                                                                                                                                           
                                                                                                                                                                                                                
    # 3. Caso GET: Consultar y listar                                                                                                                                                                        
    query = sa.select(Ejercicio).where(                                                                                                                                                                      
        sa.or_(                                                                                                                                                                                              
            Ejercicio.entrenador_id.is_(None),                                                                                                                                                               
            Ejercicio.entrenador_id == current_user.id                                                                                                                                                       
        )                                                                                                                                                                                                    
    ).order_by(Ejercicio.grupo_muscular, Ejercicio.nombre)                                                                                                                                                   
                                                                                                                                                                                                                
    lista = db.session.scalars(query).all()                                                                                                                                                                  
    return render_template('trainer/ejercicios.html', form=form, ejercicios=lista)      

@app.route('/trainer/rutinas', methods=['GET', 'POST'])
@role_required('entrenador')
def rutinas():
    form = RoutineForm()

    if request.method == 'POST':
        # Caso 1: ¿Se presionó el botón de Eliminar rutina?
        delete_id = request.form.get('delete_id')
        if delete_id:
            rutina = db.session.get(Rutina, int(delete_id))
            if rutina and rutina.entrenador_id == current_user.id:
                db.session.delete(rutina)
                db.session.commit()
                flash(f'Rutina "{rutina.nombre}" eliminada correctamente.', 'success')
            else:
                flash('No tienes permiso para eliminar esta rutina.', 'danger')
            return redirect(url_for('rutinas'))

        # Caso 2: Crear nueva rutina
        if form.validate_on_submit():
            nueva_rutina = Rutina(
                nombre=form.nombre.data.strip(),
                meta=form.objetivo.data,
                nivel=form.nivel.data,
                entrenador_id=current_user.id
            )
            db.session.add(nueva_rutina)
            db.session.commit()
            flash(f'Rutina "{nueva_rutina.nombre}" creada con éxito.', 'success')
            return redirect(url_for('rutinas'))

    query = sa.select(Rutina).where(Rutina.entrenador_id == current_user.id).order_by(Rutina.nombre)
    mis_rutinas = db.session.scalars(query).all()
    return render_template('trainer/rutinas.html', form=form, rutinas=mis_rutinas)

@app.route('/trainer/rutinas/<int:rutina_id>') # Muestra formularios de creacion de rutina
@role_required('entrenador')
def detalle_rutina(rutina_id):

    # 1. Buscar rutina y validar que sea del usuario actual
    rutina = db.session.get(Rutina, rutina_id)
    if not rutina:
        flash('Rutina no encontrada.', 'danger')
        return redirect(url_for('rutinas'))
    if rutina.entrenador_id != current_user.id:
        flash('No tienes permiso para ver esta rutina')
        return redirect(url_for('rutinas'))

    # 2. Instanciar los dos formularios (para los datos de la sesion de entrenamiento y otro para los datos de los ejercicios de esa sesion)
    session_form = SessionForm() 
    prescription_form = PrescriptionForm()

    # 3. Poblar las opciones del Select del form con los ejercicios disponibles en la base de datos (por defecto del sistema y propios del entrenador)
    ejercicios = db.session.scalars(sa.select(Ejercicio).where(sa.or_(Ejercicio.entrenador_id.is_(None), Ejercicio.entrenador_id == current_user.id)).order_by(Ejercicio.grupo_muscular, Ejercicio.nombre)).all()
    prescription_form.ejercicio_id.choices = [(e.id, f'{e.nombre} ({e.grupo_muscular})') for e in ejercicios]

    # 4. Renderizar la plantilla
    return render_template('/trainer/detalle_rutina.html', rutina=rutina, session_form=session_form, prescription_form=prescription_form)

@app.route('/trainer/rutinas/<int:rutina_id>/sesiones/agregar-sesion', methods=['POST']) # Ruta para agregar sesion
@role_required('entrenador')
def agregar_sesion(rutina_id):
    rutina = db.session.get(Rutina, rutina_id)
    if not rutina or rutina.entrenador_id != current_user.id:
        flash("No tienes permiso para modificar esta rutina.", 'danger')
        return redirect(url_for('rutinas'))

    form = SessionForm()
    if form.validate_on_submit():
        nueva_sesion = Sesion(nombre=form.nombre.data.strip(), dia=int(form.dia.data), rutina_id=rutina_id)
        db.session.add(nueva_sesion)
        db.session.commit()
        flash(f'Sesión "{nueva_sesion.nombre}" agregada con éxito.', 'success')
    else:
        for error in form.nombre.errors:
            flash(error, 'danger')

    return redirect(url_for('detalle_rutina', rutina_id=rutina_id))

@app.route('/trainer/rutinas/<int:rutina_id>/sesiones/<int:sesion_id>/eliminar', methods=['POST']) # Ruta para agregar sesion
@role_required('entrenador')
def eliminar_sesion(rutina_id, sesion_id):
    sesion = db.session.get(Sesion, sesion_id)
    if sesion and sesion.rutina.entrenador_id == current_user.id:
        db.session.delete(sesion)
        db.session.commit()
    else:
        flash('No tienes permiso para eliminar esta sesión.', 'danger')

    return redirect(url_for('detalle_rutina', rutina_id=rutina_id))

@app.route('/trainer/rutinas/<int:rutina_id>/sesiones/<int:sesion_id>/agregar-ejercicios', methods=['POST'])
@role_required('entrenador')
def agregar_prescripcion_ejercicio(rutina_id, sesion_id):
    # 1. Validar que la sesion exista y pertenzca a una rutina del entrenador
    sesion = db.session.get(Sesion, sesion_id)
    if not sesion or sesion.rutina.entrenador_id != current_user.id:
        flash('No tienes permiso para modifar esta sesion.', 'danger')
        return redirect(url_for('rutinas'))

    form = PrescriptionForm()

    #Carga los ejercicios de la base de datos para verificar que el que eligio es valido
    ejercicios = db.session.scalars(sa.select(Ejercicio).where(sa.or_(Ejercicio.entrenador_id.is_(None), Ejercicio.entrenador_id == current_user.id)).order_by(Ejercicio.grupo_muscular, Ejercicio.nombre)).all()
    form.ejercicio_id.choices = [(e.id, f'{e.nombre} ({e.grupo_muscular})') for e in ejercicios]

    # 2. Si es valido guardar en la base de datos
    if form.validate_on_submit():
        prescripcion = PrescripcionEjercicioSesion(sesion_id=sesion.id, ejercicio_id=form.ejercicio_id.data, series=form.series.data, repeticiones=form.repeticiones.data.strip(), descanso_segundos=form.descanso_segundos.data, intensidad=form.intensidad.data.strip() if form.intensidad.data else None, notas=form.notas.data.strip() if form.notas.data else None)
        db.session.add(prescripcion)
        db.session.commit()
        flash(f'Ejercicio agregado a la sesión "{sesion.nombre}".', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en {field}: {error}', 'danger')
    return redirect(url_for('detalle_rutina', rutina_id=rutina_id))
    
@app.route('/trainer/prescripciones/<int:prescripcion_id>/eliminar', methods=['POST'])
@role_required('entrenador')
def eliminar_prescripcion(prescripcion_id):
    prescripcion = db.session.get(PrescripcionEjercicioSesion, prescripcion_id)
    
    # Verificamos que exista y que la rutina sea del entrenador en sesión
    if prescripcion and prescripcion.sesion.rutina.entrenador_id == current_user.id:
        rutina_id = prescripcion.sesion.rutina_id  # Guardamos el ID para saber a dónde redirigir
        db.session.delete(prescripcion)
        db.session.commit()
        flash('Ejercicio eliminado de la sesión.', 'success')
        return redirect(url_for('detalle_rutina', rutina_id=rutina_id))
    else:
        flash('No tienes permiso para eliminar este ejercicio.', 'danger')
        return redirect(url_for('rutinas'))

@app.route('/trainer/clientes/<int:cliente_id>/asignar-rutina', methods=['GET', 'POST'])
@role_required('entrenador')
def asignar_rutina(cliente_id):
    cliente = db.session.get(Cliente, cliente_id)
    if not cliente or cliente.entrenador_id != current_user.id:
        flash('Cliente no encontrado o no tienes permiso para gestionarlo.', 'danger')
        return redirect(url_for('clientes'))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'desasignar':
            cliente.rutina_id = None
            db.session.commit()
            flash(f'Se ha desvinculado la rutina de {cliente.nombre_usuario}.', 'info')
            return redirect(url_for('clientes'))

        rutina_id = request.form.get('rutina_id', type=int)
        rutina = db.session.get(Rutina, rutina_id) if rutina_id else None

        if not rutina or rutina.entrenador_id != current_user.id:
            flash('La rutina seleccionada no es válida.', 'danger')
            return redirect(url_for('asignar_rutina', cliente_id=cliente.id))

        cliente.rutina_id = rutina.id
        db.session.commit()
        flash(f'¡Rutina "{rutina.nombre}" asignada exitosamente a {cliente.nombre_usuario}!', 'success')
        return redirect(url_for('clientes'))

    # GET: Filtrado de rutinas compatibles con meta y nivel del cliente (CU08 / RF12)
    query_compatibles = sa.select(Rutina).where(
        Rutina.entrenador_id == current_user.id,
        sa.func.lower(Rutina.meta) == cliente.meta.lower(),
        sa.func.lower(Rutina.nivel) == cliente.nivel_experiencia.lower()
    ).order_by(Rutina.nombre)
    rutinas_compatibles = db.session.scalars(query_compatibles).all()

    # Rutinas con objetivos o niveles diferentes (para ofrecerlas como alternativa opcional)
    query_otras = sa.select(Rutina).where(
        Rutina.entrenador_id == current_user.id,
        sa.or_(
            sa.func.lower(Rutina.meta) != cliente.meta.lower(),
            sa.func.lower(Rutina.nivel) != cliente.nivel_experiencia.lower()
        )
    ).order_by(Rutina.nombre)
    otras_rutinas = db.session.scalars(query_otras).all()

    return render_template(
        'trainer/asignar_rutina.html',
        cliente=cliente,
        rutinas_compatibles=rutinas_compatibles,
        otras_rutinas=otras_rutinas
    )
    

@app.route('/perfil')
@role_required('cliente')
def perfil():
    return render_template('cliente/profile.html')

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