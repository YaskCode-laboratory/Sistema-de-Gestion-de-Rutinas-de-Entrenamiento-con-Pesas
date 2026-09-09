from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, RadioField, FloatField, SelectField
from wtforms.validators import ValidationError, DataRequired, EqualTo, NumberRange
import sqlalchemy as sa
from app import db
from app.models import Usuario, Entrenador

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
        entrenador = db.session.scalar(sa.select(Entrenador).where(Entrenador.codigo_entrenador == codigo.data))
        if entrenador is None:
            raise ValidationError("Código inválido. No se encontró ningún entrenador asociado al codigo")

class ClientProfileForm(FlaskForm):
    peso = FloatField('Peso actual (kg)', validators=[DataRequired(), NumberRange(min=30.0, max=300.0, message="Ingrese un peso válido.")])
    objetivo = SelectField('Meta de entrenamiento', choices=[('Hipertrofia', 'Ganar Músculo (Hipertrofia)'), ('Fuerza', 'Ganar Fuerza')], validators=[DataRequired()])
    nivel_experiencia = SelectField('Nivel de Experiencia', choices=[('Principiante', 'Principiante'), ('Intermedio', 'Intermedio'), ('Avanzado', 'Avanzado')], validators=[DataRequired()])
    submit = SubmitField('Finalizar Registro')