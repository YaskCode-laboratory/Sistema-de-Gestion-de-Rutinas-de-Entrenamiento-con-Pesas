from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, RadioField, FloatField, SelectField, IntegerField
from wtforms.validators import ValidationError, DataRequired, EqualTo, NumberRange
import sqlalchemy as sa
from app import db
from app.models import Usuario, Entrenador, Ejercicio, Rutina
from flask_login import current_user

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(message="Porfavor llene este campo")])
    password = PasswordField('Contraseña', validators=[DataRequired(message="Porfavor llene este campo")])
    remember_me = BooleanField('Recuerdame')
    submit = SubmitField('Iniciar Sesion')
    
class SignupForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(message="Porfavor llene este campo")])
    password = PasswordField('Contraseña', validators=[DataRequired(message="Porfavor llene este campo")])
    role = RadioField('Rol', choices=[('entrenador', 'Entrenador'), ('cliente', 'Cliente')],  validators=[DataRequired(message="Porfavor seleccione una opcion para continuar")]) #Cumple con RF1
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(message="Porfavor llene este campo"), EqualTo('password')])
    submit = SubmitField('Registrarse')

    def validate_username(self, username):
        usuario = db.session.scalar(sa.select(Usuario).where(Usuario.nombre_usuario == username.data.strip()))
        if usuario is not None:
            raise ValidationError("Este usuario ya exite, porfavor utilice otro nombre de usuario")

class TrainerCodeForm(FlaskForm):
    codigo_entrenador = StringField('Codigo Entrenador', validators=[DataRequired(message="Porfavor llene este campo")])
    submit = SubmitField('Verificar Código')

    def validate_codigo_entrenador(self, codigo):
        entrenador = db.session.scalar(sa.select(Entrenador).where(Entrenador.codigo_entrenador == codigo.data.strip().upper()))
        if entrenador is None:
            raise ValidationError("Código inválido. No se encontró ningún entrenador asociado al codigo")

class ClientProfileForm(FlaskForm):
    peso = FloatField('Peso actual (kg)', validators=[DataRequired(message="Por favor ingrese su peso actual."), NumberRange(min=30.0, max=300.0, message="Ingrese un peso válido.")])
    peso_objetivo = FloatField('Peso objetivo / Meta (kg)', validators=[DataRequired(message="Indica tu peso meta a alcanzar."), NumberRange(min=30.0, max=300.0, message="Ingrese un peso objetivo válido.")])
    objetivo = SelectField('Meta de entrenamiento', choices=[('Hipertrofia', 'Ganar Músculo (Hipertrofia)'), ('Fuerza', 'Ganar Fuerza')], validators=[DataRequired()])
    dias_semana_meta = SelectField('Meta de Días de Entrenamiento Semanales', choices=[('2', '2 días por semana'), ('3', '3 días por semana'), ('4', '4 días por semana'), ('5', '5 días por semana'), ('6', '6 días por semana')], default='4', validators=[DataRequired()])
    nivel_experiencia = SelectField('Nivel de Experiencia', choices=[('Principiante', 'Principiante'), ('Intermedio', 'Intermedio'), ('Avanzado', 'Avanzado')], validators=[DataRequired()])
    submit = SubmitField('Finalizar Registro')

class ActualizarPesoForm(FlaskForm):
    nuevo_peso = FloatField('Nuevo Peso Corporal (kg)', validators=[DataRequired(message="Por favor ingrese su nuevo peso."), NumberRange(min=30.0, max=300.0, message="Ingrese un peso válido.")])
    submit = SubmitField('Registrar Peso')

class ExerciseForm(FlaskForm):
    nombre = StringField('Nombre del Ejercicio', validators=[DataRequired(message="Por favor ingrese un nombre")])
    grupo_muscular = SelectField('Grupo Muscular', choices=[ ('Pecho', 'Pecho'), ('Espalda', 'Espalda'), ('Piernas', 'Piernas'), ('Hombros', 'Hombros'), ('Brazos', 'Brazos'), ('Core', 'Core')], validators=[DataRequired()]) 
    patron_movimiento = SelectField('Patrón de Movimiento', choices=[('Empuje', 'Empuje (Push)'), ('Tracción', 'Tracción (Pull)'), ('Sentadilla', 'Sentadilla (Squat)'), ('Bisagra de Cadera', 'Bisagra de Cadera (Hinge)'), ('Aislamiento / Core', 'Aislamiento / Core')], validators=[DataRequired()])                
    submit = SubmitField('Guardar Ejercicio')

    def validate_nombre(self, nombre):                                                                                                                                                                       
        nombre_limpio = nombre.data.strip().lower()                                                                                                                                                          
        # Busca si ya existe en el sistema (NULL) o en los propios de este entrenador                                                                                                                        
        ejercicio = db.session.scalar(                                                                                                                                                                       
            sa.select(Ejercicio).where(                                                                                                                                                                      
                sa.func.lower(Ejercicio.nombre) == nombre_limpio,                                                                                                                                            
                sa.or_(                                                                                                                                                                                      
                    Ejercicio.entrenador_id.is_(None),                                                                                                                                                       
                    Ejercicio.entrenador_id == current_user.id                                                                                                                                               
                )
            )
        )
        if ejercicio is not None:
            raise ValidationError("Ya existe un ejercicio con este nombre en tu catálogo.")

class RoutineForm(FlaskForm):
    nombre = StringField('Nombre de la Rutina', validators=[DataRequired(message="Por favor ingrese un nombre")])
    objetivo = SelectField('Meta Objetivo', choices=[('Hipertrofia', 'Ganar Músculo (Hipertrofia)'), ('Fuerza', 'Ganar Fuerza')], validators=[DataRequired()])
    nivel = SelectField('Nivel de Experiencia', choices=[('Principiante', 'Principiante'), ('Intermedio', 'Intermedio'), ('Avanzado', 'Avanzado')], validators=[DataRequired()])
    submit = SubmitField('Guardar Rutina')

    def validate_nombre(self, nombre):
        nombre_limpio = nombre.data.strip().lower()
        rutina_existente = db.session.scalar(sa.select(Rutina).where(sa.func.lower(Rutina.nombre) == nombre_limpio, Rutina.entrenador_id == current_user.id))
        if rutina_existente is not None:
            raise ValidationError('Ya tienes una rutina registrada con este nombre.')

class SessionForm(FlaskForm):
    nombre = StringField('Nombre de la Sesion', validators=[DataRequired(message="Por favor ingrese un nombre")])
    dia = SelectField('Dia de la semana', choices=[('1', 'Lunes'), ('2', 'Martes'), ('3', 'Miércoles'), ('4', 'Jueves'), ('5', 'Viernes'), ('6', 'Sábado'), ('7', 'Domingo')])
    submit = SubmitField('Añadir Sesion')

class PrescriptionForm(FlaskForm):
    ejercicio_id = SelectField('Ejercicio', coerce=int, validators=[DataRequired(message='Seleccione un ejercicio')])
    series = IntegerField('Series', validators=[DataRequired(message='Indique las series'), NumberRange(min=1, max=20)], default=3)
    repeticiones = StringField('Repeticiones', validators=[DataRequired(message='Indique las repeticiones')])
    descanso_segundos = IntegerField('Descanso (segundos)', default=90)
    intensidad = StringField('Intensidad (Opcional)')
    notas = StringField('Notas o Instrucciones (Opcional)')
    submit = SubmitField("Añadir Ejercicio")