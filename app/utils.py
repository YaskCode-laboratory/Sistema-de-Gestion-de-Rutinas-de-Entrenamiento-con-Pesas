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

def render_markdown(text: str):
    """
    Convierte sintaxis básica de Markdown (encabezados, negrita, cursiva, listas, saltos)
    en HTML seguro y estilizado con clases de Bootstrap.
    """
    import re
    from markupsafe import Markup, escape

    if not text:
        return Markup("")

    escaped = str(escape(text))
    lineas = escaped.split('\n')
    html_lineas = []
    en_lista_desordenada = False
    en_lista_ordenada = False

    for linea in lineas:
        l = linea.strip()

        # Encabezados ###
        if l.startswith('### '):
            if en_lista_desordenada:
                html_lineas.append('</ul>')
                en_lista_desordenada = False
            if en_lista_ordenada:
                html_lineas.append('</ol>')
                en_lista_ordenada = False
            contenido = l[4:].strip()
            contenido = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', contenido)
            html_lineas.append(f'<h6 class="fw-bold text-primary mt-3 mb-2">{contenido}</h6>')
            continue

        # Encabezados ##
        elif l.startswith('## '):
            if en_lista_desordenada:
                html_lineas.append('</ul>')
                en_lista_desordenada = False
            if en_lista_ordenada:
                html_lineas.append('</ol>')
                en_lista_ordenada = False
            contenido = l[3:].strip()
            contenido = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', contenido)
            html_lineas.append(f'<h5 class="fw-bold text-dark mt-3 mb-2">{contenido}</h5>')
            continue

        # Listas desordenadas: - o • o *
        elif re.match(r'^[-•\*]\s+(.+)', l):
            if en_lista_ordenada:
                html_lineas.append('</ol>')
                en_lista_ordenada = False
            if not en_lista_desordenada:
                html_lineas.append('<ul class="mb-2 ps-3">')
                en_lista_desordenada = True
            m = re.match(r'^[-•\*]\s+(.+)', l)
            contenido = m.group(1)
            contenido = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', contenido)
            contenido = re.sub(r'\*(.+?)\*', r'<em>\1</em>', contenido)
            html_lineas.append(f'<li class="mb-1">{contenido}</li>')
            continue

        # Listas ordenadas: 1. 2. etc.
        elif re.match(r'^\d+\.\s+(.+)', l):
            if en_lista_desordenada:
                html_lineas.append('</ul>')
                en_lista_desordenada = False
            if not en_lista_ordenada:
                html_lineas.append('<ol class="mb-2 ps-3">')
                en_lista_ordenada = True
            m = re.match(r'^\d+\.\s+(.+)', l)
            contenido = m.group(1)
            contenido = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', contenido)
            contenido = re.sub(r'\*(.+?)\*', r'<em>\1</em>', contenido)
            html_lineas.append(f'<li class="mb-1">{contenido}</li>')
            continue

        else:
            if en_lista_desordenada:
                html_lineas.append('</ul>')
                en_lista_desordenada = False
            if en_lista_ordenada:
                html_lineas.append('</ol>')
                en_lista_ordenada = False

            if not l:
                html_lineas.append('<div class="my-1"></div>')
            else:
                contenido = l
                contenido = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', contenido)
                contenido = re.sub(r'\*(.+?)\*', r'<em>\1</em>', contenido)
                html_lineas.append(f'<p class="mb-1">{contenido}</p>')

    if en_lista_desordenada:
        html_lineas.append('</ul>')
    if en_lista_ordenada:
        html_lineas.append('</ol>')

    return Markup("\n".join(html_lineas))


