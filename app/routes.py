from flask import render_template, flash, redirect, url_for, session, request
from app import app
from app.forms import LoginForm
from app.forms import SignupForm
from app.forms import TrainerCodeForm
from app.forms import ClientProfileForm
from app.forms import ExerciseForm
from app.forms import RoutineForm
from app.forms import SessionForm
from app.forms import PrescriptionForm
from app.forms import ActualizarPesoForm
from flask_login import current_user, login_user, logout_user, login_required
from app.utils import role_required, registrar_log
import sqlalchemy as sa
from app import db
from app.models import Usuario, Entrenador, Cliente, Ejercicio, Rutina, Sesion, PrescripcionEjercicioSesion, RegistroSesionEntrenamiento, RegistroEjercicioSesion, RegistroSerie, RegistroPesoCorporal, Recomendacion
from urllib.parse import urlsplit
from datetime import date, datetime, timedelta

@app.route('/')
def home():
    if current_user.is_authenticated:
        if current_user.tipo == 'entrenador':
            return redirect(url_for('clientes'))
        elif current_user.tipo == 'cliente':
            return redirect(url_for('perfil'))
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
        registrar_log('Login', usuario=usuario.nombre_usuario)

        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(next_page)
    
    return render_template('auth/login.html', form=form)

@app.route('/logout')
def logout():
    nombre = current_user.nombre_usuario if current_user.is_authenticated else 'Anonimo'
    logout_user()
    registrar_log('Logout', usuario=nombre)
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
            registrar_log('Registro: Entrenador', usuario=usuario.nombre_usuario)
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
        cliente = Cliente(
            nombre_usuario=reg_data['username'],
            entrenador_id=reg_data['entrenador_id'],
            peso=form.peso.data,
            peso_objetivo=form.peso_objetivo.data,
            dias_semana_meta=int(form.dias_semana_meta.data),
            meta=form.objetivo.data,
            nivel_experiencia=form.nivel_experiencia.data
        )
        cliente.guardar_contraseña(reg_data['password'])

        db.session.add(cliente)
        db.session.flush() # Obtiene el ID generado para el cliente

        # Registro histórico inicial del peso (RF 11 & CU 13)
        primer_peso = RegistroPesoCorporal(
            cliente_id=cliente.id,
            peso=form.peso.data,
            fecha=date.today()
        )
        db.session.add(primer_peso)
        db.session.commit()
        registrar_log('Registro: Cliente', usuario=cliente.nombre_usuario)

        # Clean session after successful registration
        session.pop('reg_cliente')

        flash('Registro exitoso!')
        return redirect(url_for('login'))
    return render_template('auth/client_profile.html', form=form)

@app.route('/clientes')
@role_required('entrenador')
def clientes():
    registrar_log('Consulta: Mis Clientes')
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
                nombre_ej = ejercicio.nombre
                db.session.delete(ejercicio)                                                                                                                                                                 
                db.session.commit()
                registrar_log(f'Eliminación: Ejercicio "{nombre_ej}"')
                flash(f'Ejercicio "{nombre_ej}" eliminado.', 'success')                                                                                                                               
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
            registrar_log(f'Registro: Ejercicio "{nuevo.nombre}"')
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
    registrar_log('Consulta: Librería de Ejercicios')
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
                nombre_rutina = rutina.nombre
                db.session.delete(rutina)
                db.session.commit()
                registrar_log(f'Eliminación: Rutina "{nombre_rutina}"')
                flash(f'Rutina "{nombre_rutina}" eliminada correctamente.', 'success')
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
            registrar_log(f'Registro: Rutina "{nueva_rutina.nombre}"')
            flash(f'Rutina "{nueva_rutina.nombre}" creada con éxito.', 'success')
            return redirect(url_for('rutinas'))

    query = sa.select(Rutina).where(Rutina.entrenador_id == current_user.id).order_by(Rutina.nombre)
    mis_rutinas = db.session.scalars(query).all()
    registrar_log('Consulta: Mis Rutinas')
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

    # 4. Registrar log y renderizar la plantilla
    registrar_log(f'Consulta: Detalle Rutina "{rutina.nombre}"')
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
        registrar_log(f'Registro: Sesión "{nueva_sesion.nombre}" en Rutina "{rutina.nombre}"')
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
        nombre_sesion = sesion.nombre
        rutina_nombre = sesion.rutina.nombre
        db.session.delete(sesion)
        db.session.commit()
        registrar_log(f'Eliminación: Sesión "{nombre_sesion}" de Rutina "{rutina_nombre}"')
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
        registrar_log(f'Registro: Prescripción en Sesión "{sesion.nombre}"')
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
        nombre_sesion = prescripcion.sesion.nombre
        db.session.delete(prescripcion)
        db.session.commit()
        registrar_log(f'Eliminación: Prescripción de Sesión "{nombre_sesion}"')
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
            registrar_log(f'Eliminación: Desasignar Rutina de Cliente {cliente.nombre_usuario}')
            flash(f'Se ha desvinculado la rutina de {cliente.nombre_usuario}.', 'info')
            return redirect(url_for('clientes'))

        rutina_id = request.form.get('rutina_id', type=int)
        rutina = db.session.get(Rutina, rutina_id) if rutina_id else None

        if not rutina or rutina.entrenador_id != current_user.id:
            flash('La rutina seleccionada no es válida.', 'danger')
            return redirect(url_for('asignar_rutina', cliente_id=cliente.id))

        cliente.rutina_id = rutina.id
        db.session.commit()
        registrar_log(f'Registro: Asignación de Rutina "{rutina.nombre}" a Cliente {cliente.nombre_usuario}')
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

    registrar_log(f'Consulta: Asignar Rutina a Cliente {cliente.nombre_usuario}')
    return render_template(
        'trainer/asignar_rutina.html',
        cliente=cliente,
        rutinas_compatibles=rutinas_compatibles,
        otras_rutinas=otras_rutinas
    )    

@app.route('/perfil')
@role_required('cliente')
def perfil():
    registrar_log('Consulta: Mi Perfil')
    return render_template('cliente/profile.html')

@app.route('/cliente/mi-rutina')
@role_required('cliente')
def mi_rutina():
    registrar_log('Consulta: Mi Rutina')
    return render_template('cliente/mi_rutina.html')

@app.route('/cliente/mi-progreso', methods=['GET', 'POST'])
@role_required('cliente')
def mi_progreso():
    cliente = current_user
    form = ActualizarPesoForm()

    if form.validate_on_submit():
        nuevo_peso = form.nuevo_peso.data
        cliente.peso = nuevo_peso
        reg_peso = RegistroPesoCorporal(
            cliente_id=cliente.id,
            peso=nuevo_peso,
            fecha=date.today()
        )
        db.session.add(reg_peso)
        db.session.commit()
        flash(f'¡Nuevo peso corporal ({nuevo_peso} kg) registrado exitosamente!', 'success')
        return redirect(url_for('mi_progreso'))

    # 1. Trazabilidad de Peso Corporal
    historial_pesos = db.session.scalars(
        sa.select(RegistroPesoCorporal)
        .where(RegistroPesoCorporal.cliente_id == cliente.id)
        .order_by(RegistroPesoCorporal.fecha.desc(), RegistroPesoCorporal.id.desc())
    ).all()

    # Peso inicial (el registro más antiguo del historial)
    peso_inicial = historial_pesos[-1].peso if historial_pesos else cliente.peso
    peso_actual = cliente.peso
    peso_objetivo = cliente.peso_objetivo if cliente.peso_objetivo else cliente.peso

    # 2. Evaluación de la Meta de Peso (Semáforo con colores)
    quiere_subir = peso_objetivo > peso_inicial
    quiere_bajar = peso_objetivo < peso_inicial

    meta_peso_alcanzada = False
    progreso_peso_pct = 0.0

    if peso_inicial == peso_objetivo:
        meta_peso_alcanzada = abs(peso_actual - peso_objetivo) <= 0.5
        estado_peso = 'alcanzada' if meta_peso_alcanzada else 'en_progreso'
        color_peso = 'success' if meta_peso_alcanzada else 'warning'
        mensaje_peso = "¡Meta de mantenimiento alcanzada!" if meta_peso_alcanzada else "Manteniéndote cerca de tu objetivo."
        progreso_peso_pct = 100.0 if meta_peso_alcanzada else 80.0
    elif quiere_subir:
        delta_total = peso_objetivo - peso_inicial
        delta_logrado = peso_actual - peso_inicial
        if peso_actual >= peso_objetivo:
            meta_peso_alcanzada = True
            estado_peso = 'alcanzada'
            color_peso = 'success'
            mensaje_peso = f"¡Meta Alcanzada! Lograste tu objetivo de {peso_objetivo} kg."
            progreso_peso_pct = 100.0
        elif delta_logrado > 0:
            estado_peso = 'en_progreso'
            color_peso = 'warning'
            progreso_peso_pct = min(99.0, max(5.0, round((delta_logrado / delta_total) * 100, 1)))
            mensaje_peso = f"¡En camino! Has ganado {round(delta_logrado, 1)} kg de tu meta de +{round(delta_total, 1)} kg."
        else:
            estado_peso = 'no_alcanzada'
            color_peso = 'danger'
            progreso_peso_pct = 0.0
            mensaje_peso = f"Meta no alcanzada aún. Tu peso actual ({peso_actual} kg) está por debajo de tu punto de inicio ({peso_inicial} kg)."
    else:
        delta_total = peso_inicial - peso_objetivo
        delta_logrado = peso_inicial - peso_actual
        if peso_actual <= peso_objetivo:
            meta_peso_alcanzada = True
            estado_peso = 'alcanzada'
            color_peso = 'success'
            mensaje_peso = f"¡Meta Alcanzada! Has logrado bajar a {peso_actual} kg (objetivo: {peso_objetivo} kg)."
            progreso_peso_pct = 100.0
        elif delta_logrado > 0:
            estado_peso = 'en_progreso'
            color_peso = 'warning'
            progreso_peso_pct = min(99.0, max(5.0, round((delta_logrado / delta_total) * 100, 1)))
            mensaje_peso = f"¡En camino! Has bajado {round(delta_logrado, 1)} kg de tu meta de -{round(delta_total, 1)} kg."
        else:
            estado_peso = 'no_alcanzada'
            color_peso = 'danger'
            progreso_peso_pct = 0.0
            mensaje_peso = f"Meta no alcanzada aún. Tu peso actual ({peso_actual} kg) está por encima de tu punto de inicio ({peso_inicial} kg)."

    # 3. Evaluación de la Meta Semanal de Entrenamientos (inferida de las sesiones de la rutina)
    if cliente.rutina_asignada and cliente.rutina_asignada.sesiones:
        dias_meta = len(cliente.rutina_asignada.sesiones)
        nombre_rutina = cliente.rutina_asignada.nombre
    else:
        dias_meta = 0
        nombre_rutina = None

    inicio_semana = date.today() - timedelta(days=date.today().weekday())
    registros_semana = db.session.scalars(
        sa.select(RegistroSesionEntrenamiento).where(
            RegistroSesionEntrenamiento.cliente_id == cliente.id,
            RegistroSesionEntrenamiento.fecha >= inicio_semana
        )
    ).all()
    sesiones_completadas_semana = len(registros_semana)

    if dias_meta > 0:
        if sesiones_completadas_semana >= dias_meta:
            estado_semana = 'alcanzada'
            color_semana = 'success'
            mensaje_semana = f"¡Plan semanal cumplido! Has completado {sesiones_completadas_semana} de {dias_meta} sesiones de tu rutina '{nombre_rutina}'."
            progreso_semana_pct = 100.0
        elif sesiones_completadas_semana > 0:
            estado_semana = 'en_progreso'
            color_semana = 'warning'
            progreso_semana_pct = min(99.0, round((sesiones_completadas_semana / dias_meta) * 100, 1))
            mensaje_semana = f"En progreso: Llevas {sesiones_completadas_semana} de {dias_meta} sesiones de tu rutina '{nombre_rutina}' esta semana."
        else:
            estado_semana = 'no_alcanzada'
            color_semana = 'danger'
            progreso_semana_pct = 0.0
            mensaje_semana = f"Aún no has registrado sesiones esta semana (Rutina '{nombre_rutina}': {dias_meta} días)."
    else:
        estado_semana = 'en_progreso'
        color_semana = 'secondary'
        mensaje_semana = "Aún no tienes una rutina asignada para calcular los días de entrenamiento semanal."
        progreso_semana_pct = 0.0

    # 4. Evaluación de la Meta según Modalidad (Fuerza vs Hipertrofia)
    es_meta_fuerza = (cliente.meta or '').lower() == 'fuerza'
    es_meta_hipertrofia = (cliente.meta or '').lower() == 'hipertrofia'

    # Calcular incremento y sobrecarga progresiva en los ejercicios
    entrenamientos_cronologicos = db.session.scalars(
        sa.select(RegistroSesionEntrenamiento)
        .where(RegistroSesionEntrenamiento.cliente_id == cliente.id)
        .order_by(RegistroSesionEntrenamiento.fecha.asc(), RegistroSesionEntrenamiento.id.asc())
    ).all()

    progreso_ejercicios = {}
    for s in entrenamientos_cronologicos:
        for reg_ej in s.registros_ejercicios:
            nombre = reg_ej.ejercicio.nombre
            pesos_sesion = [sr.peso_usado for sr in reg_ej.series if sr.peso_usado is not None]
            if not pesos_sesion:
                continue
            max_sesion = max(pesos_sesion)
            if nombre not in progreso_ejercicios:
                progreso_ejercicios[nombre] = {
                    'nombre': nombre,
                    'grupo_muscular': reg_ej.ejercicio.grupo_muscular or 'General',
                    'primera_carga': max_sesion,
                    'max_carga': max_sesion,
                    'ultima_carga': max_sesion,
                    'primera_fecha': s.fecha,
                    'ultima_fecha': s.fecha,
                    'total_series': len(reg_ej.series)
                }
            else:
                if max_sesion > progreso_ejercicios[nombre]['max_carga']:
                    progreso_ejercicios[nombre]['max_carga'] = max_sesion
                progreso_ejercicios[nombre]['ultima_carga'] = max_sesion
                progreso_ejercicios[nombre]['ultima_fecha'] = s.fecha
                progreso_ejercicios[nombre]['total_series'] += len(reg_ej.series)

    lista_progresos_ejercicios = []
    for ej, info in progreso_ejercicios.items():
        delta = round(info['max_carga'] - info['primera_carga'], 1)
        pct = round((delta / info['primera_carga'] * 100), 1) if info['primera_carga'] > 0 else 0.0
        info['delta'] = delta
        info['pct'] = pct
        if delta > 0:
            info['color'] = 'success'
            info['estado'] = f"+{delta} kg (+{pct}%)"
        elif delta == 0:
            info['color'] = 'warning'
            info['estado'] = "Carga base"
        else:
            info['color'] = 'danger'
            info['estado'] = f"{delta} kg"
        lista_progresos_ejercicios.append(info)

    total_ejercicios_trackeados = len(lista_progresos_ejercicios)
    ejercicios_con_sobrecarga = sum(1 for e in lista_progresos_ejercicios if e['delta'] > 0)
    total_kg_ganados = round(sum(e['delta'] for e in lista_progresos_ejercicios if e['delta'] > 0), 1)

    if total_ejercicios_trackeados > 0:
        if ejercicios_con_sobrecarga > 0:
            progreso_ejercicios_pct = round((ejercicios_con_sobrecarga / total_ejercicios_trackeados) * 100, 1)
            if ejercicios_con_sobrecarga == total_ejercicios_trackeados:
                estado_ejercicios = 'alcanzada'
                color_ejercicios = 'success'
                mensaje_ejercicios = f"¡Sobrecarga progresiva óptima! Has incrementado peso en todos tus ejercicios (+{total_kg_ganados} kg en total)."
            else:
                estado_ejercicios = 'en_progreso'
                color_ejercicios = 'warning'
                mensaje_ejercicios = f"En progreso: Has incrementado carga en {ejercicios_con_sobrecarga} de {total_ejercicios_trackeados} ejercicios (+{total_kg_ganados} kg ganados)."
        else:
            progreso_ejercicios_pct = 50.0
            estado_ejercicios = 'en_progreso'
            color_ejercicios = 'warning'
            mensaje_ejercicios = f"Cargas base registradas en {total_ejercicios_trackeados} ejercicio(s). En tu próxima sesión busca la sobrecarga progresiva (+1.25 kg a +2.5 kg)."
    else:
        progreso_ejercicios_pct = 0.0
        estado_ejercicios = 'no_alcanzada'
        color_ejercicios = 'secondary'
        mensaje_ejercicios = "Aún no has registrado sesiones para medir la sobrecarga de peso en los ejercicios."

    # 5. Total general de entrenamientos y recomendaciones (IA)
    entrenamientos = db.session.scalars(
        sa.select(RegistroSesionEntrenamiento)
        .where(RegistroSesionEntrenamiento.cliente_id == cliente.id)
        .order_by(RegistroSesionEntrenamiento.fecha.desc())
    ).all()

    total_sesiones = len(entrenamientos)
    total_minutos = sum(e.duracion_minutos for e in entrenamientos)

    recomendaciones = db.session.scalars(
        sa.select(Recomendacion)
        .where(Recomendacion.cliente_id == cliente.id)
        .order_by(Recomendacion.fecha.desc())
    ).all()

    registrar_log('Consulta: Mi Progreso y Metas')
    return render_template(
        'cliente/progreso.html',
        form=form,
        cliente=cliente,
        peso_inicial=peso_inicial,
        peso_actual=peso_actual,
        peso_objetivo=peso_objetivo,
        estado_peso=estado_peso,
        color_peso=color_peso,
        mensaje_peso=mensaje_peso,
        progreso_peso_pct=progreso_peso_pct,
        meta_peso_alcanzada=meta_peso_alcanzada,
        dias_meta=dias_meta,
        sesiones_semana=sesiones_completadas_semana,
        estado_semana=estado_semana,
        color_semana=color_semana,
        mensaje_semana=mensaje_semana,
        progreso_semana_pct=progreso_semana_pct,
        total_sesiones=total_sesiones,
        total_minutos=total_minutos,
        historial_pesos=historial_pesos,
        recomendaciones=recomendaciones,
        entrenamientos=entrenamientos,
        es_meta_fuerza=es_meta_fuerza,
        es_meta_hipertrofia=es_meta_hipertrofia,
        lista_progresos_ejercicios=lista_progresos_ejercicios,
        total_ejercicios_trackeados=total_ejercicios_trackeados,
        ejercicios_con_sobrecarga=ejercicios_con_sobrecarga,
        total_kg_ganados=total_kg_ganados,
        estado_ejercicios=estado_ejercicios,
        color_ejercicios=color_ejercicios,
        mensaje_ejercicios=mensaje_ejercicios,
        progreso_ejercicios_pct=progreso_ejercicios_pct
    )

@app.route('/cliente/entrenamiento-hoy')
@role_required('cliente')
def entrenamiento_hoy():
    if not current_user.rutina_asignada:
        flash('Aún no tienes una rutina de entrenamiento asignada.', 'warning')
        return redirect(url_for('perfil'))

    dia_hoy = date.today().isoweekday() # 1=Lunes ... 7=Domingo
    dia_param = request.args.get('dia', type=int)

    # 1. Sesiones de la rutina ordenadas cronológicamente
    sesiones_ordenadas = sorted(current_user.rutina_asignada.sesiones, key=lambda s: s.dia)

    # 2. Buscar qué sesiones ya completó el alumno esta semana
    inicio_semana = date.today() - timedelta(days=date.today().weekday())
    registros_semana = db.session.scalars(
        sa.select(RegistroSesionEntrenamiento).where(
            RegistroSesionEntrenamiento.cliente_id == current_user.id,
            RegistroSesionEntrenamiento.fecha >= inicio_semana
        )
    ).all()
    completadas_ids = {r.sesion_id for r in registros_semana}

    # 3. La siguiente sesión pendiente según la filosofía 3DMJ (retomar donde quedó)
    proxima_sesion = next((s for s in sesiones_ordenadas if s.id not in completadas_ids), None)

    # 4. ¿Qué sesión mostramos en pantalla?
    if dia_param:
        # Si el usuario hizo clic en entrenar la sesión sugerida en día de descanso
        sesion_a_mostrar = next((s for s in sesiones_ordenadas if s.dia == dia_param), None)
        es_dia_descanso = False
    elif proxima_pendiente := proxima_sesion:
        if proxima_pendiente.dia == dia_hoy:
            # Hoy coincide exactamente con la sesión que le toca: entra directo
            sesion_a_mostrar = proxima_pendiente
            es_dia_descanso = False
        else:
            # Hoy no coincide (es día de descanso o día desfasado)
            sesion_a_mostrar = None
            es_dia_descanso = True
    else:
        # Ya completó todas las sesiones de la semana
        sesion_a_mostrar = None
        es_dia_descanso = True

    # Control de tiempo en el servidor (Cero JavaScript)
    if sesion_a_mostrar:
        if not session.get('inicio_entrenamiento') or session.get('sesion_activa_id') != sesion_a_mostrar.id:
            session['inicio_entrenamiento'] = datetime.now().isoformat()
            session['sesion_activa_id'] = sesion_a_mostrar.id
        hora_inicio_dt = datetime.fromisoformat(session['inicio_entrenamiento'])
        hora_inicio_str = hora_inicio_dt.strftime('%I:%M %p')
    else:
        session.pop('inicio_entrenamiento', None)
        session.pop('sesion_activa_id', None)
        hora_inicio_str = None

    registrar_log('Consulta: Entrenamiento del Día')
    return render_template(
        'cliente/entrenamiento_hoy.html',
        sesion=sesion_a_mostrar,
        proxima_sesion=proxima_sesion,
        es_dia_descanso=es_dia_descanso,
        dia_hoy=dia_hoy,
        rutina=current_user.rutina_asignada,
        completadas_ids=completadas_ids,
        hora_inicio_str=hora_inicio_str
    )

@app.route('/cliente/sesiones/<int:sesion_id>/guardar-entrenamiento', methods=['POST'])
@role_required('cliente')
def guardar_entrenamiento(sesion_id):
    sesion = db.session.get(Sesion, sesion_id)
    if not sesion or sesion.rutina_id != current_user.rutina_id:
        flash('Sesión de entrenamiento no válida.', 'danger')
        return redirect(url_for('perfil'))

    # 1. Calcular duración en el servidor (Python puro)
    inicio_iso = session.pop('inicio_entrenamiento', None)
    session.pop('sesion_activa_id', None)
    if inicio_iso:
        hora_inicio = datetime.fromisoformat(inicio_iso)
        segundos = (datetime.now() - hora_inicio).total_seconds()
        duracion_minutos = max(1, round(segundos / 60))
    else:
        duracion_minutos = request.form.get('duracion_minutos', default=45, type=int)

    estado_animo = request.form.get('estado_animo', 'Normal').strip()

    # 2. Crear cabecera: RegistroSesionEntrenamiento
    registro_sesion = RegistroSesionEntrenamiento(
        cliente_id=current_user.id,
        sesion_id=sesion.id,
        fecha=date.today(),
        duracion_minutos=duracion_minutos,
        estado_animo=estado_animo
    )
    db.session.add(registro_sesion)

    # 3. Guardar ejercicios y sus series
    for p in sesion.prescripciones:
        notas = request.form.get(f'notas_{p.ejercicio_id}', '').strip()
        reg_ejercicio = RegistroEjercicioSesion(
            registro_sesion=registro_sesion,
            ejercicio_id=p.ejercicio_id,
            notas_adicionales=notas if notas else None
        )
        db.session.add(reg_ejercicio)

        # Guardar cada serie completada
        for s_idx in range(1, p.series + 1):
            peso_val = request.form.get(f'peso_{p.ejercicio_id}_{s_idx}', type=float)
            reps_val = request.form.get(f'reps_{p.ejercicio_id}_{s_idx}', type=int)

            # Si el usuario llenó los datos de la serie, la registramos
            if peso_val is not None and reps_val is not None:
                serie = RegistroSerie(
                    registro_ejercicio=reg_ejercicio,
                    numero_serie=s_idx,
                    peso_usado=peso_val,
                    repeticiones_logradas=reps_val
                )
                db.session.add(serie)

    db.session.commit()
    registrar_log(f'Registro: Entrenamiento completado "{sesion.nombre}" (Duración: {duracion_minutos} min)')
    flash(f'¡Entrenamiento "{sesion.nombre}" guardado con éxito! Duración registrada: {duracion_minutos} min.', 'success')
    return redirect(url_for('perfil'))

@app.route('/trainer/clientes/<int:cliente_id>/entrenamientos')
@role_required('entrenador')
def ver_entrenamientos_cliente(cliente_id):
    # 1. Obtener cliente y verificar autorización 
    cliente = db.session.get(Cliente, cliente_id)
    if not cliente or cliente.entrenador_id != current_user.id:
        flash('Cliente no encontrado o no autorizado', 'danger')
        return redirect(url_for('clientes'))

    # 2. Consultar a la base de datos el historial de entrenamientos ordenados por fecha descendente
    registros = db.session.scalars(sa.select(RegistroSesionEntrenamiento).where(RegistroSesionEntrenamiento.cliente_id == cliente.id).order_by(RegistroSesionEntrenamiento.fecha.desc(), RegistroSesionEntrenamiento.id.desc())).all()

    # 3. Historial de recomendaciones de IA generadas para este cliente
    recomendaciones_ia = db.session.scalars(
        sa.select(Recomendacion)
        .where(Recomendacion.cliente_id == cliente.id)
        .order_by(Recomendacion.fecha.desc())
    ).all()

    # 4. Registrar log y renderizar la vista de historial del cliente
    registrar_log(f'Consulta: Historial Entrenamientos de Cliente {cliente.nombre_usuario}')
    return render_template(
        'trainer/historial_cliente.html',
        cliente=cliente,
        registros=registros,
        recomendaciones_ia=recomendaciones_ia
    )

@app.route('/cliente/progreso')
@role_required('cliente')
def progreso():
    return redirect(url_for('mi_progreso'))

@app.route('/cliente/recomendaciones/<int:rec_id>/marcar-leida', methods=['POST'])
@role_required('cliente')
def marcar_recomendacion_leida(rec_id):
    rec = db.session.get(Recomendacion, rec_id)
    if rec and rec.cliente_id == current_user.id:
        rec.leido = True
        db.session.commit()
        flash('Recomendación marcada como leída.', 'info')
    return redirect(url_for('mi_progreso'))

@app.route('/cliente/generar-recomendacion-ia', methods=['POST'])
@role_required('cliente')
def generar_recomendacion_ia_cliente():
    from app.ai_service import generar_recomendacion_ia
    titulo, mensaje = generar_recomendacion_ia(current_user.id)
    if not titulo:
        flash(mensaje, 'warning')
        return redirect(url_for('mi_progreso'))

    titulo_final = titulo if titulo.startswith("🤖") else f"🤖 {titulo}"
    nueva_rec = Recomendacion(
        cliente_id=current_user.id,
        entrenador_id=current_user.entrenador_id,
        titulo=titulo_final,
        mensaje=mensaje,
        fecha=datetime.now(),
        leido=False
    )
    db.session.add(nueva_rec)
    db.session.commit()
    registrar_log(f'Registro: Recomendación IA generada para {current_user.nombre_usuario}')
    flash('¡Análisis de Inteligencia Artificial generado con éxito y agregado a tus recomendaciones!', 'success')
    return redirect(url_for('mi_progreso'))

@app.route('/trainer/clientes/<int:cliente_id>/recomendaciones/generar-ia', methods=['POST'])
@role_required('entrenador')
def generar_recomendacion_ia_trainer(cliente_id):
    cliente = db.session.get(Cliente, cliente_id)
    if not cliente or cliente.entrenador_id != current_user.id:
        flash('Operación no permitida o cliente no válido.', 'danger')
        return redirect(url_for('clientes'))

    from app.ai_service import generar_recomendacion_ia
    titulo, mensaje = generar_recomendacion_ia(cliente.id)
    if not titulo:
        flash(mensaje, 'warning')
        return redirect(url_for('ver_entrenamientos_cliente', cliente_id=cliente.id))

    titulo_limpio = titulo[2:].strip() if titulo.startswith("🤖") else titulo
    titulo_final = f"🤖 {titulo_limpio} (Supervisado por Entrenador)"
    nueva_rec = Recomendacion(
        cliente_id=cliente.id,
        entrenador_id=current_user.id,
        titulo=titulo_final,
        mensaje=mensaje,
        fecha=datetime.now(),
        leido=False
    )
    db.session.add(nueva_rec)
    db.session.commit()
    registrar_log(f'Registro: Recomendación IA supervisada para {cliente.nombre_usuario}')
    flash(f'¡Análisis de IA generado y enviado como recomendación a {cliente.nombre_usuario}!', 'success')
    return redirect(url_for('ver_entrenamientos_cliente', cliente_id=cliente.id))