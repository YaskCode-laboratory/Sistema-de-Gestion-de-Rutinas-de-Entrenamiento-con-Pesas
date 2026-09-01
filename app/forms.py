from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, RadioField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(message="Porfavor llene este campo")])
    password = PasswordField('Contraseña', validators=[DataRequired(message="Porfavor llene este campo")])
    remember_me = BooleanField('Recuerdame')
    submit = SubmitField('Iniciar Sesion')

class SignupForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(message="Porfavor llene este campo")])
    password = PasswordField('Contraseña', validators=[DataRequired(message="Porfavor llene este campo")])
    role = RadioField('Rol', choices=[('entrenador', 'Entrenador'), ('cliente', 'Cliente')],  validators=[DataRequired(message="Porfavor seleccione una opcion para continuar")]) #Cumple con RF1
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(message="Porfavor llene este campo")])
    submit = SubmitField('Registrarse')

    