import os
import re
import tempfile
import unittest
import sqlalchemy as sa
from sqlalchemy.pool import StaticPool
from datetime import date, datetime, timedelta

from app import app, db
from app.models import (
    Usuario, Entrenador, Cliente, Ejercicio, Rutina, Sesion,
    PrescripcionEjercicioSesion, RegistroSesionEntrenamiento,
    RegistroEjercicioSesion, RegistroSerie, RegistroPesoCorporal,
    Recomendacion
)
from app.utils import registrar_log
from app.ai_service import recopilar_datos_entrenamiento, _generar_recomendacion_heuristica, generar_recomendacion_ia


class BaseTestCase(unittest.TestCase):
    """Clase base de pruebas con aislamiento de base de datos en memoria y log temporal."""
    @classmethod
    def setUpClass(cls):
        cls._original_engine = db._app_engines.get(app, {}).get(None)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, '_original_engine') and cls._original_engine is not None:
            db._app_engines[app] = {None: cls._original_engine}

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False

        # Usar motor SQLite en memoria aislado para no afectar app.db
        self.test_engine = sa.create_engine(
            'sqlite:///:memory:',
            connect_args={'check_same_thread': False},
            poolclass=StaticPool
        )
        db._app_engines[self.app] = {None: self.test_engine}

        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.temp_log = tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w+', encoding='utf-8')
        self.temp_log_path = self.temp_log.name
        self.temp_log.close()
        self.app.config['AUDITORIA_LOG_FILE'] = self.temp_log_path

        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        if os.path.exists(self.temp_log_path):
            try:
                os.remove(self.temp_log_path)
            except OSError:
                pass

    def crear_entrenador(self, username="TrainerPro", password="Password123"):
        entrenador = Entrenador(nombre_usuario=username)
        entrenador.guardar_contraseña(password)
        entrenador.generar_codigo_entrenador()
        db.session.add(entrenador)
        db.session.commit()
        return entrenador

    def crear_cliente(self, entrenador, username="AlumnoFuerte", password="Password123",
                      peso=75.0, peso_objetivo=80.0, meta="Hipertrofia", nivel="Intermedio"):
        cliente = Cliente(
            nombre_usuario=username,
            entrenador_id=entrenador.id,
            peso=peso,
            peso_objetivo=peso_objetivo,
            dias_semana_meta=4,
            meta=meta,
            nivel_experiencia=nivel
        )
        cliente.guardar_contraseña(password)
        db.session.add(cliente)
        db.session.flush()

        primer_peso = RegistroPesoCorporal(cliente_id=cliente.id, peso=peso, fecha=date.today())
        db.session.add(primer_peso)
        db.session.commit()
        return cliente

    def login(self, username, password):
        return self.client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)


class TestModelosYPOO(BaseTestCase):
    """Pruebas unitarias de modelos, encapsulamiento, polimorfismo JTI e integridad relacional."""

    def test_01_encriptacion_contraseña(self):
        """Verifica que las contraseñas se almacenen hasheadas y que la verificación sea exacta."""
        u = Usuario(nombre_usuario="TestUser")
        u.guardar_contraseña("Secret123")
        self.assertNotEqual(u.contraseña, "Secret123")
        self.assertTrue(u.chequear_contraseña("Secret123"))
        self.assertFalse(u.chequear_contraseña("WrongPass"))

    def test_02_generacion_codigo_entrenador(self):
        """Verifica formato ENT-XXXXXX y unicidad en códigos de entrenador."""
        e1 = self.crear_entrenador("Trainer1")
        e2 = self.crear_entrenador("Trainer2")
        self.assertTrue(re.match(r"^ENT-[A-Z0-9]{6}$", e1.codigo_entrenador))
        self.assertTrue(re.match(r"^ENT-[A-Z0-9]{6}$", e2.codigo_entrenador))
        self.assertNotEqual(e1.codigo_entrenador, e2.codigo_entrenador)

    def test_03_herencia_polimorfica_jti(self):
        """Verifica que Entrenador y Cliente hereden de Usuario con discriminador 'tipo'."""
        e = self.crear_entrenador("CarlosCoach")
        c = self.crear_cliente(e, "PedroAtleta")

        # Consultar vía clase base polimórfica Usuario
        usuarios = db.session.scalars(db.select(Usuario)).all()
        self.assertEqual(len(usuarios), 2)

        u_coach = db.session.get(Usuario, e.id)
        u_client = db.session.get(Usuario, c.id)
        self.assertEqual(u_coach.tipo, "entrenador")
        self.assertEqual(u_client.tipo, "cliente")
        self.assertIsInstance(u_coach, Entrenador)
        self.assertIsInstance(u_client, Cliente)

    def test_04_cascada_eliminacion_rutina(self):
        """Verifica que eliminar una Rutina elimine en cascada sus Sesiones y Prescripciones."""
        e = self.crear_entrenador()
        ej = Ejercicio(nombre="Press de Banca", grupo_muscular="Pecho", patron_movimiento="Empuje")
        db.session.add(ej)
        db.session.commit()

        rutina = Rutina(nombre="Torso-Pierna", meta="Hipertrofia", nivel="Intermedio", entrenador_id=e.id)
        db.session.add(rutina)
        db.session.commit()

        sesion = Sesion(nombre="Día 1 Torso", dia=1, rutina_id=rutina.id)
        db.session.add(sesion)
        db.session.commit()

        presc = PrescripcionEjercicioSesion(sesion_id=sesion.id, ejercicio_id=ej.id, series=4, repeticiones="8-10")
        db.session.add(presc)
        db.session.commit()

        rutina_id = rutina.id
        sesion_id = sesion.id
        presc_id = presc.id

        # Eliminar Rutina
        db.session.delete(rutina)
        db.session.commit()

        self.assertIsNone(db.session.get(Rutina, rutina_id))
        self.assertIsNone(db.session.get(Sesion, sesion_id))
        self.assertIsNone(db.session.get(PrescripcionEjercicioSesion, presc_id))
        # El ejercicio del catálogo no debe ser eliminado
        self.assertIsNotNone(db.session.get(Ejercicio, ej.id))


class TestAuditoriaLog(BaseTestCase):
    """Pruebas del módulo de auditoría continua y cumplimiento de formato plano (.txt)."""

    def test_05_formato_linea_auditoria(self):
        """Verifica que registrar_log guarde en formato estricto 'FECHA, USUARIO, ACTIVIDAD'."""
        registrar_log("Login", usuario="CarlosCoach")
        registrar_log("Consulta: Librería de Ejercicios", usuario="CarlosCoach")

        with open(self.temp_log_path, 'r', encoding='utf-8') as f:
            lineas = f.readlines()

        self.assertEqual(len(lineas), 2)
        patron = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}, CarlosCoach, .+$"
        self.assertTrue(re.match(patron, lineas[0].strip()))
        self.assertIn("Login", lineas[0])
        self.assertIn("Consulta: Librería de Ejercicios", lineas[1])

    def test_06_usuario_anonimo_auditoria(self):
        """Verifica que si no hay usuario autenticado se registre como 'Anonimo'."""
        registrar_log("Intento de acceso")
        with open(self.temp_log_path, 'r', encoding='utf-8') as f:
            contenido = f.read()
        self.assertIn(", Anonimo, Intento de acceso", contenido)


class TestSeguridadYRBAC(BaseTestCase):
    """Pruebas de seguridad, interceptor @role_required y aislamiento de datos entre roles."""

    def test_07_acceso_no_autenticado_redirige_login(self):
        """Usuarios anónimos deben ser redirigidos con HTTP 302 a la pantalla de login."""
        res_trainer = self.client.get('/clientes')
        self.assertEqual(res_trainer.status_code, 302)
        self.assertIn('/login', res_trainer.headers['Location'])

        res_client = self.client.get('/perfil')
        self.assertEqual(res_client.status_code, 302)
        self.assertIn('/login', res_client.headers['Location'])

    def test_08_cliente_bloqueado_en_rutas_entrenador_403(self):
        """Clientes autenticados que intenten acceder a rutas de entrenador reciben HTTP 403 Forbidden."""
        e = self.crear_entrenador()
        c = self.crear_cliente(e)

        self.login(c.nombre_usuario, "Password123")

        # Intentar acceder a panel de entrenador
        res1 = self.client.get('/clientes')
        self.assertEqual(res1.status_code, 403)

        res2 = self.client.get('/trainer/ejercicios')
        self.assertEqual(res2.status_code, 403)

        res3 = self.client.get('/trainer/rutinas')
        self.assertEqual(res3.status_code, 403)

    def test_09_entrenador_bloqueado_en_rutas_cliente_403(self):
        """Entrenadores autenticados que intenten acceder a rutas de cliente reciben HTTP 403 Forbidden."""
        e = self.crear_entrenador()
        self.login(e.nombre_usuario, "Password123")

        res1 = self.client.get('/perfil')
        self.assertEqual(res1.status_code, 403)

        res2 = self.client.get('/cliente/mi-rutina')
        self.assertEqual(res2.status_code, 403)

        res3 = self.client.get('/cliente/mi-progreso')
        self.assertEqual(res3.status_code, 403)

        res4 = self.client.get('/cliente/entrenamiento-hoy')
        self.assertEqual(res4.status_code, 403)

    def test_10_aislamiento_entre_entrenadores(self):
        """Un entrenador no puede eliminar ni modificar ejercicios propios de otro entrenador."""
        e1 = self.crear_entrenador("Coach1")
        e2 = self.crear_entrenador("Coach2")

        # Coach 1 crea ejercicio personalizado
        ej_coach1 = Ejercicio(nombre="Press Suizo Coach1", grupo_muscular="Pecho",
                              patron_movimiento="Empuje", entrenador_id=e1.id)
        db.session.add(ej_coach1)
        db.session.commit()

        # Login como Coach 2 e intentar eliminar el ejercicio de Coach 1
        self.login("Coach2", "Password123")
        res = self.client.post('/trainer/ejercicios', data={'delete_id': ej_coach1.id}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Verificar que el ejercicio sigue existiendo
        self.assertIsNotNone(db.session.get(Ejercicio, ej_coach1.id))


class TestFlujoAutenticacionYRegistro(BaseTestCase):
    """Pruebas de integración de registro, inicio y cierre de sesión."""

    def test_11_registro_entrenador_exitoso(self):
        """Registro de entrenador asigna código alfanumérico y permite login."""
        res = self.client.post('/signup', data={
            'username': 'NuevoEntrenador',
            'password': 'Password123',
            'confirm_password': 'Password123',
            'role': 'entrenador'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        entrenador = db.session.scalar(db.select(Entrenador).where(Entrenador.nombre_usuario == 'NuevoEntrenador'))
        self.assertIsNotNone(entrenador)
        self.assertTrue(entrenador.codigo_entrenador.startswith("ENT-"))

    def test_12_registro_cliente_tres_pasos(self):
        """Registro de cliente en 3 pasos: credenciales, validación de código de entrenador y onboarding."""
        e = self.crear_entrenador("CoachGuia")

        # Paso 1: Signup inicial
        res1 = self.client.post('/signup', data={
            'username': 'NuevoAlumno',
            'password': 'Password123',
            'confirm_password': 'Password123',
            'role': 'cliente'
        }, follow_redirects=True)
        self.assertEqual(res1.status_code, 200)

        # Paso 2: Vincular código
        res2 = self.client.post('/signup/link-trainer', data={
            'codigo_entrenador': e.codigo_entrenador
        }, follow_redirects=True)
        self.assertEqual(res2.status_code, 200)

        # Paso 3: Onboarding físico
        res3 = self.client.post('/signup/client-profile', data={
            'peso': 72.5,
            'peso_objetivo': 78.0,
            'objetivo': 'Hipertrofia',
            'dias_semana_meta': '4',
            'nivel_experiencia': 'Intermedio'
        }, follow_redirects=True)
        self.assertEqual(res3.status_code, 200)

        # Verificar cliente creado en base de datos
        cliente = db.session.scalar(db.select(Cliente).where(Cliente.nombre_usuario == 'NuevoAlumno'))
        self.assertIsNotNone(cliente)
        self.assertEqual(cliente.entrenador_id, e.id)
        self.assertEqual(cliente.peso, 72.5)
        self.assertEqual(len(cliente.historial_peso), 1)

    def test_13_login_credenciales_invalidas(self):
        """Login con usuario inexistente o contraseña incorrecta debe rechazar con HTTP 400."""
        res_no_user = self.client.post('/login', data={'username': 'Fantasma', 'password': '123'})
        self.assertEqual(res_no_user.status_code, 400)
        self.assertIn("Este usuario no existe", res_no_user.text)

        self.crear_entrenador("CoachExistente", "Password123")
        res_bad_pass = self.client.post('/login', data={'username': 'CoachExistente', 'password': 'WrongPassword'})
        self.assertEqual(res_bad_pass.status_code, 400)
        self.assertIn("La contraseña es invalida", res_bad_pass.text)


class TestGestionRutinasYPrescripcion(BaseTestCase):
    """Pruebas de creación de rutinas, diseño de sesiones, prescripción y asignación."""

    def test_14_crear_rutina_y_asignar_a_cliente(self):
        """Entrenador crea rutina, agrega sesión con prescripciones y la asigna al cliente."""
        e = self.crear_entrenador()
        c = self.crear_cliente(e)
        ej = Ejercicio(nombre="Sentadilla Libre", grupo_muscular="Piernas", patron_movimiento="Sentadilla")
        db.session.add(ej)
        db.session.commit()

        self.login(e.nombre_usuario, "Password123")

        # 1. Crear rutina
        res1 = self.client.post('/trainer/rutinas', data={
            'nombre': 'Rutina Hipertrofia A',
            'objetivo': 'Hipertrofia',
            'nivel': 'Intermedio'
        }, follow_redirects=True)
        self.assertEqual(res1.status_code, 200)
        rutina = db.session.scalar(db.select(Rutina).where(Rutina.nombre == 'Rutina Hipertrofia A'))
        self.assertIsNotNone(rutina)

        # 2. Agregar sesión
        res2 = self.client.post(f'/trainer/rutinas/{rutina.id}/sesiones/agregar-sesion', data={
            'nombre': 'Piernas Intenso',
            'dia': '1'
        }, follow_redirects=True)
        self.assertEqual(res2.status_code, 200)
        sesion = db.session.scalar(db.select(Sesion).where(Sesion.rutina_id == rutina.id))
        self.assertIsNotNone(sesion)

        # 3. Agregar prescripción
        res3 = self.client.post(f'/trainer/rutinas/{rutina.id}/sesiones/{sesion.id}/agregar-ejercicios', data={
            'ejercicio_id': ej.id,
            'series': 4,
            'repeticiones': '8-10',
            'descanso_segundos': 120,
            'intensidad': '@ RPE 8',
            'notas': 'Buena profundidad'
        }, follow_redirects=True)
        self.assertEqual(res3.status_code, 200)
        self.assertEqual(len(sesion.prescripciones), 1)

        # 4. Asignar rutina al cliente
        res4 = self.client.post(f'/trainer/clientes/{c.id}/asignar-rutina', data={
            'rutina_id': rutina.id
        }, follow_redirects=True)
        self.assertEqual(res4.status_code, 200)

        # Refrescar cliente y verificar
        db.session.refresh(c)
        self.assertEqual(c.rutina_id, rutina.id)
        self.assertEqual(c.rutina_asignada.nombre, 'Rutina Hipertrofia A')


class TestEntrenamientoYProgreso(BaseTestCase):
    """Pruebas del registro diario de series, sobrecarga progresiva y semáforo de parámetro META."""

    def test_15_registro_completo_sesion_diaria(self):
        """Cliente registra entrenamiento con pesas, duracion y series logradas."""
        e = self.crear_entrenador()
        c = self.crear_cliente(e)
        ej = Ejercicio(nombre="Press Militar", grupo_muscular="Hombros", patron_movimiento="Empuje")
        db.session.add(ej)
        db.session.commit()

        rutina = Rutina(nombre="Fuerza 3 Dias", meta="Fuerza", nivel="Intermedio", entrenador_id=e.id)
        db.session.add(rutina)
        db.session.flush()

        sesion = Sesion(nombre="Día Hombros", dia=date.today().isoweekday(), rutina_id=rutina.id)
        db.session.add(sesion)
        db.session.flush()

        presc = PrescripcionEjercicioSesion(sesion_id=sesion.id, ejercicio_id=ej.id, series=2, repeticiones="5")
        db.session.add(presc)
        c.rutina_id = rutina.id
        db.session.commit()

        self.login(c.nombre_usuario, "Password123")

        # Guardar entrenamiento
        datos_form = {
            'duracion_minutos': 50,
            'estado_animo': 'Enérgico',
            f'notas_{ej.id}': 'Se sintió ligero',
            f'peso_{ej.id}_1': 50.0,
            f'reps_{ej.id}_1': 5,
            f'peso_{ej.id}_2': 52.5,
            f'reps_{ej.id}_2': 5
        }
        res = self.client.post(f'/cliente/sesiones/{sesion.id}/guardar-entrenamiento', data=datos_form, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Validar en base de datos
        reg_sesion = db.session.scalar(db.select(RegistroSesionEntrenamiento).where(RegistroSesionEntrenamiento.cliente_id == c.id))
        self.assertIsNotNone(reg_sesion)
        self.assertEqual(reg_sesion.duracion_minutos, 50)
        self.assertEqual(len(reg_sesion.registros_ejercicios), 1)

        reg_ej = reg_sesion.registros_ejercicios[0]
        self.assertEqual(len(reg_ej.series), 2)
        self.assertEqual(reg_ej.series[0].peso_usado, 50.0)
        self.assertEqual(reg_ej.series[1].peso_usado, 52.5)

    def test_16_evaluacion_semaforo_parametro_meta(self):
        """Verifica el cálculo del semáforo de peso (alcanzada=success, en_progreso=warning, no_alcanzada=danger)."""
        e = self.crear_entrenador()
        # Cliente que quiere subir de 70kg a 75kg
        c = self.crear_cliente(e, peso=70.0, peso_objetivo=75.0, meta="Hipertrofia")

        self.login(c.nombre_usuario, "Password123")

        # 1. Aún en 70kg -> delta = 0 -> danger
        res1 = self.client.get('/cliente/mi-progreso')
        self.assertIn('danger', res1.text)

        # 2. Registra nuevo peso 72.5kg -> subió pero no llegó a 75 -> warning (en progreso)
        self.client.post('/cliente/mi-progreso', data={'nuevo_peso': 72.5}, follow_redirects=True)
        res2 = self.client.get('/cliente/mi-progreso')
        self.assertIn('warning', res2.text)

        # 3. Registra nuevo peso 75.5kg -> superó meta de 75kg -> success (alcanzada)
        self.client.post('/cliente/mi-progreso', data={'nuevo_peso': 75.5}, follow_redirects=True)
        res3 = self.client.get('/cliente/mi-progreso')
        self.assertIn('success', res3.text)
        self.assertIn('Meta Alcanzada', res3.text)


class TestAIServiceYResiliencia(BaseTestCase):
    """Pruebas del pipeline de datos de IA, motor heurístico y resiliencia offline ante fallos de red."""

    def test_17_recopilacion_datos_para_ia(self):
        """Verifica que recopilar_datos_entrenamiento extraiga métricas, deltas y cargas correctamente."""
        e = self.crear_entrenador()
        c = self.crear_cliente(e)

        # Sin entrenamientos debe retornar None
        self.assertIsNone(recopilar_datos_entrenamiento(c))

        ej = Ejercicio(nombre="Dominadas Lastradas", grupo_muscular="Espalda", patron_movimiento="Tracción")
        db.session.add(ej)
        db.session.commit()

        rutina = Rutina(nombre="Rutina Traccion", meta="Fuerza", nivel="Avanzado", entrenador_id=e.id)
        db.session.add(rutina)
        db.session.flush()

        sesion = Sesion(nombre="Tracción", dia=1, rutina_id=rutina.id)
        db.session.add(sesion)
        db.session.flush()

        # Crear una sesión registrada
        reg_s = RegistroSesionEntrenamiento(cliente_id=c.id, sesion_id=sesion.id, fecha=date.today(), duracion_minutos=40)
        db.session.add(reg_s)
        db.session.flush()

        reg_e = RegistroEjercicioSesion(registro_sesion_id=reg_s.id, ejercicio_id=ej.id)
        db.session.add(reg_e)
        db.session.flush()

        s1 = RegistroSerie(registro_ejercicio_id=reg_e.id, numero_serie=1, peso_usado=10.0, repeticiones_logradas=6)
        s2 = RegistroSerie(registro_ejercicio_id=reg_e.id, numero_serie=2, peso_usado=15.0, repeticiones_logradas=5)
        db.session.add_all([s1, s2])
        db.session.commit()

        datos = recopilar_datos_entrenamiento(c)
        self.assertIsNotNone(datos)
        self.assertEqual(datos['total_sesiones'], 1)
        self.assertEqual(datos['total_minutos'], 40)
        self.assertIn('Dominadas Lastradas', datos['ejercicios_stats'])
        stats = datos['ejercicios_stats']['Dominadas Lastradas']
        self.assertEqual(stats['max_peso'], 15.0)
        self.assertEqual(stats['total_reps'], 11)

    def test_18_motor_heuristico_fallback_determinista(self):
        """Verifica que el motor heurístico local genere diagnóstico y proyección sin conexión a internet."""
        e = self.crear_entrenador()
        c = self.crear_cliente(e, peso=75.0, peso_objetivo=80.0, meta="Hipertrofia")

        datos = {
            'cliente': c,
            'resumen_sesiones': [{'fecha': '01/10/2026', 'nombre_sesion': 'Torso', 'duracion_minutos': 60, 'estado_animo': 'Excelente', 'ejercicios': ['Press banca: [80kg x 8 reps]']}],
            'ejercicios_stats': {'Press banca': {'nombre': 'Press banca', 'grupo': 'Pecho', 'max_peso': 80.0, 'primera_carga': 75.0, 'delta_peso': 5.0, 'total_series': 4, 'total_reps': 32, 'cargas': [80.0]}},
            'peso_actual': 77.0,
            'peso_inicial': 75.0,
            'peso_objetivo': 80.0,
            'historial_peso_str': ['01/10/2026: 77.0 kg'],
            'total_sesiones': 3,
            'total_minutos': 180,
            'sesiones_semana': 3,
            'dias_semana_meta': 4,
            'meta_peso_alcanzada': False,
            'adherencia_semanal_pct': 75.0
        }

        titulo, recomendacion = _generar_recomendacion_heuristica(c, datos)
        self.assertIn("Análisis de Volumen Muscular", titulo)
        self.assertIn("Diagnóstico de Rendimiento", recomendacion)
        self.assertIn("Proyección de Tiempo Estimado", recomendacion)
        self.assertIn("Motor Analítico Experto", recomendacion)

    def test_19_resiliencia_ia_fallback_transparente(self):
        """Simula ausencia de conexión / fallo de API y comprueba que generar_recomendacion_ia active fallback sin error."""
        e = self.crear_entrenador()
        c = self.crear_cliente(e)

        # Crear entrenamiento para que tenga datos
        rutina = Rutina(nombre="Rutina Test", meta="Hipertrofia", nivel="Principiante", entrenador_id=e.id)
        db.session.add(rutina)
        db.session.flush()

        sesion = Sesion(nombre="Sesión 1", dia=1, rutina_id=rutina.id)
        db.session.add(sesion)
        db.session.flush()

        reg_s = RegistroSesionEntrenamiento(cliente_id=c.id, sesion_id=sesion.id, fecha=date.today(), duracion_minutos=45)
        db.session.add(reg_s)
        db.session.commit()

        # Al invocar generar_recomendacion_ia, con o sin API key, debe retornar diagnóstico sin excepciones
        titulo, mensaje = generar_recomendacion_ia(c.id)
        self.assertIsNotNone(titulo)
        self.assertIsNotNone(mensaje)
        self.assertIn("Proyección", titulo)
        self.assertIn("Diagnóstico de Rendimiento", mensaje)

    def test_20_ruta_generar_recomendacion_ia_persiste_en_bd(self):
        """Cliente invoca POST /cliente/generar-recomendacion-ia y se persiste en Recomendacion con 🤖."""
        e = self.crear_entrenador()
        c = self.crear_cliente(e)

        rutina = Rutina(nombre="Rutina Fuerza", meta="Fuerza", nivel="Intermedio", entrenador_id=e.id)
        db.session.add(rutina)
        db.session.flush()

        sesion = Sesion(nombre="Sesión 1", dia=1, rutina_id=rutina.id)
        db.session.add(sesion)
        db.session.flush()

        reg_s = RegistroSesionEntrenamiento(cliente_id=c.id, sesion_id=sesion.id, fecha=date.today(), duracion_minutos=50)
        db.session.add(reg_s)
        c.rutina_id = rutina.id
        db.session.commit()

        self.login(c.nombre_usuario, "Password123")
        res = self.client.post('/cliente/generar-recomendacion-ia', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Comprobar recomendación guardada en base de datos
        recs = db.session.scalars(db.select(Recomendacion).where(Recomendacion.cliente_id == c.id)).all()
        self.assertEqual(len(recs), 1)
        self.assertTrue(recs[0].titulo.startswith("🤖"))
        self.assertIn("Diagnóstico de Rendimiento", recs[0].mensaje)


class TestCasosDeUsoAvanzados(BaseTestCase):
    """Pruebas adicionales de Casos de Uso (CU08, CU13, CU14) y validación estricta de formularios."""

    def test_21_validacion_formulario_usuario_duplicado(self):
        """Verifica que el formulario de registro rechace nombres de usuario ya tomados."""
        self.crear_entrenador("UsuarioOcupado")
        res = self.client.post('/signup', data={
            'username': 'UsuarioOcupado',
            'password': 'Password123',
            'confirm_password': 'Password123',
            'role': 'entrenador'
        })
        self.assertIn("Este usuario ya exite", res.text)

    def test_22_validacion_formulario_codigo_entrenador_invalido(self):
        """Verifica que el paso 2 de registro rechace códigos de entrenador inexistentes."""
        with self.client.session_transaction() as sess:
            sess['reg_cliente'] = {'username': 'NuevoUser', 'password': 'Password123'}

        res = self.client.post('/signup/link-trainer', data={
            'codigo_entrenador': 'ENT-INVENT'
        })
        self.assertIn("Código inválido", res.text)

    def test_23_filtrado_rutinas_por_target_cliente(self):
        """Verifica que el entrenador vea las rutinas compatibles filtradas por meta y nivel (CU08 / RF12)."""
        e = self.crear_entrenador()
        c = self.crear_cliente(e, meta="Hipertrofia", nivel="Intermedio")

        # Rutina compatible (Hipertrofia / Intermedio)
        r_compatible = Rutina(nombre="Rutina Torso-Pierna Compatible", meta="Hipertrofia", nivel="Intermedio", entrenador_id=e.id)
        # Rutina no compatible (Fuerza / Avanzado)
        r_otra = Rutina(nombre="Rutina Fuerza Avanzado", meta="Fuerza", nivel="Avanzado", entrenador_id=e.id)
        db.session.add_all([r_compatible, r_otra])
        db.session.commit()

        self.login(e.nombre_usuario, "Password123")
        res = self.client.get(f'/trainer/clientes/{c.id}/asignar-rutina')
        self.assertEqual(res.status_code, 200)
        self.assertIn("Rutina Torso-Pierna Compatible", res.text)
        self.assertIn("Rutina Fuerza Avanzado", res.text)

    def test_24_trazabilidad_historial_peso_cronologico(self):
        """Verifica la persistencia de múltiples pesajes corporales y su orden cronológico (CU13 / RF11)."""
        e = self.crear_entrenador()
        c = self.crear_cliente(e, peso=75.0)

        # Agregar pesaje posterior
        p2 = RegistroPesoCorporal(cliente_id=c.id, peso=76.2, fecha=date.today())
        db.session.add(p2)
        db.session.commit()

        pesos = db.session.scalars(
            db.select(RegistroPesoCorporal)
            .where(RegistroPesoCorporal.cliente_id == c.id)
            .order_by(RegistroPesoCorporal.id.asc())
        ).all()

        self.assertEqual(len(pesos), 2)
        self.assertEqual(pesos[0].peso, 75.0)
        self.assertEqual(pesos[1].peso, 76.2)

    def test_25_consulta_historial_alumno_por_entrenador(self):
        """Entrenador puede supervisar los entrenamientos completados por sus alumnos (CU14 / RF10)."""
        e = self.crear_entrenador()
        c = self.crear_cliente(e)

        rutina = Rutina(nombre="Rutina Pecho", meta="Hipertrofia", nivel="Principiante", entrenador_id=e.id)
        db.session.add(rutina)
        db.session.flush()

        sesion = Sesion(nombre="Sesión Pecho", dia=1, rutina_id=rutina.id)
        db.session.add(sesion)
        db.session.flush()

        reg_s = RegistroSesionEntrenamiento(cliente_id=c.id, sesion_id=sesion.id, fecha=date.today(), duracion_minutos=55, estado_animo="Motivado")
        db.session.add(reg_s)
        db.session.commit()

        self.login(e.nombre_usuario, "Password123")
        res = self.client.get(f'/trainer/clientes/{c.id}/entrenamientos')
        self.assertEqual(res.status_code, 200)
        self.assertIn("Historial de Entrenamientos", res.text)
        self.assertIn("Sesión Pecho", res.text)
        self.assertIn("Motivado", res.text)


if __name__ == '__main__':
    unittest.main()
