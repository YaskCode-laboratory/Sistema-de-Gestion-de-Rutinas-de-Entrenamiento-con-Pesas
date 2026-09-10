from functools import wraps
from flask import abort, flash, current_app
from flask_login import current_user

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
