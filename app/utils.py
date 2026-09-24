from functools import wraps
from flask import abort, flash, current_app
from flask_login import current_user
from datetime import datetime
import os

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return current_app.login_manager.unauthorized()   
            if current_user.tipo not in roles:
                flash("No tienes permisos para acceder a esta sección.", "danger")
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def registrar_log(actividad, usuario=None):
    """
    Registro de actividad para el archivo plano de auditoría (.txt)
    con el formato exigido por la cátedra: FECHA, USUARIO, ACTIVIDAD
    Actividades base: Login, Consulta, Registro, Eliminación, Logout.
    """
    try: 
        from flask import has_app_context, current_app
        log_path = None
        if has_app_context():
            log_path = current_app.config.get('AUDITORIA_LOG_FILE')
        if not log_path:
            from config import Config
            log_path = getattr(Config, 'AUDITORIA_LOG_FILE', None)
        if not log_path:
            basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            log_path = os.path.join(basedir, 'auditoria_log.txt')

        fecha_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if usuario is None:
            if has_app_context() and current_user and getattr(current_user, 'is_authenticated', False):
                usuario = getattr(current_user, 'nombre_usuario', str(current_user))
            else:
                usuario = 'Anonimo'

        linea = f"{fecha_str}, {usuario}, {actividad}\n"

        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(linea)
    except Exception as e:
        print(f"Error registrando actividad en log de auditoría: {e}")

