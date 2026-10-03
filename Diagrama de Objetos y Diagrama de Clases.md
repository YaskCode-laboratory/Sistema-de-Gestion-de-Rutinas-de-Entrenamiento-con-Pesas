**Universidad del Zulia**  
**Facultad de Ciencias**  
**Licenciatura en Computación**  
**Ingeniería de Software / Auditoría de Sistemas**  

**Diagrama de Objetos y Diagrama de Clases**  
**Sistema de Gestión de Rutinas de Entrenamiento con Pesas**  

Jose Andres Maestre Horcadela C.I.: 30.934.412  
Daniel Isaac Niño Mayorga C.I.: 30.747.937  
Jose David Palmar Sabril C.I.: 31.727.421  

---

1. ### Diagrama de Objetos

El siguiente diagrama ilustra una instancia concreta del sistema en tiempo de ejecución, reflejando el flujo de trabajo implementado en la rama `main` (un entrenador supervisando a un cliente, con rutina asignada, ejecución de sesiones con series descompuestas, historial antropométrico de peso objetivo y recomendaciones asistidas por IA):

```mermaid
classDiagram
direction TB
    class carlosTrainer {
        <<Object : Entrenador>>
        id = 1
        nombre_usuario = "CarlosTrainer"
        codigo_entrenador = "ENT-A7B8C9"
    }

    class juanAlumno {
        <<Object : Cliente>>
        id = 2
        nombre_usuario = "JuanAlumno"
        peso = 76.5
        peso_objetivo = 80.0
        dias_semana_meta = 4
        meta = "Fuerza"
        nivel_experiencia = "Intermedio"
    }

    class rutinaFuerza {
        <<Object : Rutina>>
        id = 1
        nombre = "Fuerza Base 5x5"
        nivel = "Intermedio"
        meta = "Fuerza"
    }

    class sesionTorso {
        <<Object : Sesion>>
        id = 1
        nombre = "Día 1 - Torso"
        dia = 1
    }

    class pressBanca {
        <<Object : Ejercicio>>
        id = 1
        nombre = "Press de banca plano con barra"
        grupo_muscular = "Pecho"
        patron_movimiento = "Empuje"
    }

    class prescripcion1 {
        <<Object : PrescripcionEjercicioSesion>>
        id = 1
        series = 5
        repeticiones = "5"
        descanso_segundos = 180
        intensidad = "@ RPE 8"
        notas = "Pausa de 1 segundo en el pecho"
    }

    class regSesion1 {
        <<Object : RegistroSesionEntrenamiento>>
        id = 1
        fecha = 2026-09-21
        duracion_minutos = 65
        estado_animo = "Motivado"
    }

    class regEj1 {
        <<Object : RegistroEjercicioSesion>>
        id = 1
        notas_adicionales = "Buena técnica en series efectivas"
    }

    class serie1 {
        <<Object : RegistroSerie>>
        id = 1
        numero_serie = 1
        peso_usado = 80.0
        repeticiones_logradas = 5
    }

    class regPeso1 {
        <<Object : RegistroPesoCorporal>>
        id = 1
        fecha = 2026-09-21
        peso = 76.5
    }

    class recom1 {
        <<Object : Recomendacion>>
        id = 1
        fecha = 2026-09-22 10:30:00
        titulo = "Ajuste de Cargas"
        mensaje = "Excelente progresión en banca. Mantén el RPE planificado."
        leido = false
    }

    carlosTrainer --> juanAlumno : supervisa
    carlosTrainer --> rutinaFuerza : diseña
    carlosTrainer --> recom1 : redacta
    juanAlumno --> rutinaFuerza : tiene asignada
    juanAlumno --> regSesion1 : realiza
    juanAlumno --> regPeso1 : registra
    juanAlumno --> recom1 : recibe
    rutinaFuerza *-- sesionTorso : contiene
    sesionTorso *-- prescripcion1 : prescribe
    prescripcion1 --> pressBanca : refiere a
    regSesion1 --> sesionTorso : basada en
    regSesion1 *-- regEj1 : registra
    regEj1 --> pressBanca : refiere a
    regEj1 *-- serie1 : detalla series
```

---

2. ### Diagrama de Clases

El diagrama de clases representa la arquitectura orientada a objetos y el esquema relacional implementado en `main`, incluyendo la herencia polimórfica (Joined Table Inheritance - JTI), las entidades de prescripción y ejecución detallada, el seguimiento de parámetros meta antropométricos y el módulo de recomendaciones.

```mermaid
classDiagram
direction TB

    class Usuario {
        +int id
        +String tipo
        +String nombre_usuario
        +String contrasena
        +guardar_contrasena(contrasena: String)
        +chequear_contrasena(contrasena: String) bool
        +registrarse()
        +iniciarSesion()
    }

    class Entrenador {
        +String codigo_entrenador
        +generar_codigo_entrenador()
        +crearRutina()
        +asignarRutinaCliente()
        +enviarRecomendacion()
    }

    class Cliente {
        +float peso
        +float peso_objetivo
        +int dias_semana_meta
        +String meta
        +String nivel_experiencia
        +verEntrenamientoDelDia()
        +registrarSesionEntrenamiento()
        +registrarPesoCorporal()
    }

    class Ejercicio {
        +int id
        +String nombre
        +String grupo_muscular
        +String patron_movimiento
        +int entrenador_id
    }

    class Rutina {
        +int id
        +String nombre
        +String nivel
        +String meta
        +int entrenador_id
        +agregarSesion()
        +eliminarSesion()
        +obtenerSesiones()
    }

    class Sesion {
        +int id
        +int rutina_id
        +String nombre
        +int dia
        +agregarPrescripcionEjercicio()
        +eliminarPrescripcionEjercicio()
        +obtenerPrescripciones()
    }

    class PrescripcionEjercicioSesion {
        +int id
        +int sesion_id
        +int ejercicio_id
        +int series
        +String repeticiones
        +int descanso_segundos
        +String intensidad
        +String notas
        +modificarPrescripcion()
    }

    class RegistroSesionEntrenamiento {
        +int id
        +int cliente_id
        +int sesion_id
        +Date fecha
        +int duracion_minutos
        +String estado_animo
        +iniciarCronometro()
        +detenerCronometro()
        +registrarEjercicioSesion()
    }

    class RegistroEjercicioSesion {
        +int id
        +int registro_sesion_id
        +int ejercicio_id
        +String notas_adicionales
    }

    class RegistroSerie {
        +int id
        +int registro_ejercicio_id
        +int numero_serie
        +float peso_usado
        +int repeticiones_logradas
    }

    class RegistroPesoCorporal {
        +int id
        +int cliente_id
        +Date fecha
        +float peso
    }

    class Recomendacion {
        +int id
        +int cliente_id
        +int entrenador_id
        +DateTime fecha
        +String titulo
        +String mensaje
        +bool leido
    }

    Usuario <|-- Entrenador : hereda (JTI)
    Usuario <|-- Cliente : hereda (JTI)

    Entrenador "1" --> "*" Cliente : supervisa
    Entrenador "1" --> "*" Rutina : diseña
    Entrenador "0..1" --> "*" Ejercicio : crea personalizado
    Entrenador "1" --> "*" Recomendacion : redacta

    Cliente "*" --> "0..1" Rutina : tiene asignada
    Cliente "1" *-- "*" RegistroSesionEntrenamiento : realiza
    Cliente "1" *-- "*" RegistroPesoCorporal : registra historial
    Cliente "1" *-- "*" Recomendacion : recibe

    Rutina "1" *-- "*" Sesion : contiene
    Sesion "1" *-- "*" PrescripcionEjercicioSesion : prescribe
    PrescripcionEjercicioSesion "*" --> "1" Ejercicio : refiere a

    RegistroSesionEntrenamiento "*" --> "1" Sesion : basada en
    RegistroSesionEntrenamiento "1" *-- "*" RegistroEjercicioSesion : registra
    RegistroEjercicioSesion "*" --> "1" Ejercicio : refiere a
    RegistroEjercicioSesion "1" *-- "*" RegistroSerie : detalla series
```

---

3. ### Código UML Diagrama de Clases y Especificación de Cambios

#### Principales actualizaciones respecto a la versión inicial:
1. **Herencia de Usuarios (Joined Table Inheritance - JTI)**:
   - Se introdujo la clase base `Usuario` (`id`, `tipo`, `nombre_usuario`, `contraseña`, `guardar_contraseña()`, `chequear_contraseña()`), unificando la autenticación (Flask-Login / UserMixin).
   - `Entrenador` y `Cliente` heredan directamente de `Usuario`.
2. **Atributos de Meta y Frecuencia Semanal en `Cliente`**:
   - `peso_objetivo` (Float, parámetro meta cuantitativo para evaluar progreso físico).
   - `dias_semana_meta` (Integer, meta semanal de adherencia a entrenamientos).
3. **Catálogo y Clasificación de Ejercicios (`Ejercicio`)**:
   - Incorporación del atributo `patron_movimiento` ("Empuje", "Tracción", "Sentadilla", "Bisagra de Cadera", "Aislamiento / Core") para la lógica de fuerza y balance muscular.
   - Atributo `entrenador_id` opcional para permitir ejercicios canónicos globales (`None`) o personalizados por cada entrenador.
4. **Prescripción Adaptada (`PrescripcionEjercicioSesion`)**:
   - Campos escalares normalizados: `series` (int), `repeticiones` (string, ej. "8-10" o "5"), `descanso_segundos` (int), `intensidad` (string opcional, ej. "@ RPE 8") y `notas` (string opcional).
5. **Normalización del Registro de Series (`RegistroSerie`)**:
   - Se desacopló la lista de repeticiones y cargas de `RegistroEjercicioSesion` en una entidad normalizada `RegistroSerie` (`numero_serie`, `peso_usado`, `repeticiones_logradas`).
6. **Historial de Peso Corporal (`RegistroPesoCorporal`)**:
   - Nueva clase que almacena las mediciones periódicas (`fecha`, `peso`) para graficar y auditar la consecución del parámetro meta.
7. **Módulo de Recomendaciones (`Recomendacion`)**:
   - Nueva clase para almacenar las observaciones y sugerencias generadas por el entrenador (asistido por IA Gemini) hacia el cliente (`fecha`, `titulo`, `mensaje`, `leido`).

---

4. ### Codigo Python

A continuación se presenta la implementación correspondiente de las clases del modelo de datos y dominio (`app/models.py`), utilizando SQLAlchemy 2.0 con tipado estático `Mapped` y relaciones bidireccionales:

```python
from typing import Optional, List
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import secrets
import string
from datetime import date, datetime

class Usuario(UserMixin, db.Model):
    # Identificadores y discriminador de herencia JTI
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    tipo: so.Mapped[str] = so.mapped_column(sa.String(10))

    # Atributos de credenciales
    nombre_usuario: so.Mapped[str] = so.mapped_column(sa.String(64, collation="NOCASE"), index=True, unique=True)
    contraseña: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))

    __mapper_args__ = {
        "polymorphic_identity": "usuario",
        "polymorphic_on": "tipo",
    }

    def __repr__(self):
        return f'<Usuario: {self.nombre_usuario}>'

    def guardar_contraseña(self, contraseña: str) -> None:
        self.contraseña = generate_password_hash(contraseña)

    def chequear_contraseña(self, contraseña: str) -> bool:
        return check_password_hash(self.contraseña, contraseña)


class Entrenador(Usuario):
    id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Usuario.id), primary_key=True)
    codigo_entrenador: so.Mapped[str] = so.mapped_column(sa.String(12), unique=True, index=True)

    # Relaciones
    clientes: so.Mapped[List["Cliente"]] = so.relationship(back_populates="entrenador", foreign_keys="[Cliente.entrenador_id]")
    rutinas: so.Mapped[List["Rutina"]] = so.relationship(back_populates="entrenador", foreign_keys="[Rutina.entrenador_id]")
    recomendaciones_enviadas: so.Mapped[List["Recomendacion"]] = so.relationship(back_populates="entrenador", cascade="all, delete-orphan")

    __mapper_args__ = {
        "polymorphic_identity": "entrenador",
    }

    def generar_codigo_entrenador(self) -> None:
        longitud = 6
        caracteres = string.ascii_uppercase + string.digits
        sufijo = "".join(secrets.choice(caracteres) for _ in range(longitud))
        self.codigo_entrenador = f"ENT-{sufijo}"


class Cliente(Usuario):
    id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Usuario.id), primary_key=True)
    entrenador_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Entrenador.id, name="fk_cliente_entrenador"), index=True)
    rutina_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey("rutina.id", name="fk_cliente_rutina"), nullable=True, index=True)

    # Parámetros físicos y metas
    peso: so.Mapped[float] = so.mapped_column(sa.Float)
    peso_objetivo: so.Mapped[Optional[float]] = so.mapped_column(sa.Float, nullable=True)
    dias_semana_meta: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer, nullable=True, default=4)
    meta: so.Mapped[str] = so.mapped_column(sa.String(12))  # Hipertrofia / Fuerza
    nivel_experiencia: so.Mapped[str] = so.mapped_column(sa.String(12))  # Principiante / Intermedio / Avanzado

    # Relaciones
    entrenador: so.Mapped["Entrenador"] = so.relationship(back_populates="clientes", foreign_keys="[Cliente.entrenador_id]")
    rutina_asignada: so.Mapped[Optional["Rutina"]] = so.relationship(foreign_keys="[Cliente.rutina_id]")
    historial_peso: so.Mapped[List["RegistroPesoCorporal"]] = so.relationship(back_populates="cliente", cascade="all, delete-orphan")
    recomendaciones: so.Mapped[List["Recomendacion"]] = so.relationship(back_populates="cliente", cascade="all, delete-orphan")

    __mapper_args__ = {
        "polymorphic_identity": "cliente",
    }


class Ejercicio(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    nombre: so.Mapped[str] = so.mapped_column(sa.String(100), index=True)
    grupo_muscular: so.Mapped[str] = so.mapped_column(sa.String(50), index=True)
    patron_movimiento: so.Mapped[Optional[str]] = so.mapped_column(sa.String(50), index=True, nullable=True)
    entrenador_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey(Entrenador.id), index=True, nullable=True)


class Rutina(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    nombre: so.Mapped[str] = so.mapped_column(sa.String(100), index=True)
    nivel: so.Mapped[str] = so.mapped_column(sa.String(12))
    meta: so.Mapped[str] = so.mapped_column(sa.String(12))
    entrenador_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Entrenador.id), index=True)

    # Relaciones
    entrenador: so.Mapped["Entrenador"] = so.relationship(back_populates="rutinas")
    sesiones: so.Mapped[List["Sesion"]] = so.relationship(back_populates="rutina", cascade="all, delete-orphan")


class Sesion(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    rutina_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Rutina.id, ondelete="CASCADE"), index=True)
    nombre: so.Mapped[str] = so.mapped_column(sa.String(100))
    dia: so.Mapped[int] = so.mapped_column(sa.Integer)

    # Relaciones
    rutina: so.Mapped["Rutina"] = so.relationship(back_populates="sesiones", foreign_keys="[Sesion.rutina_id]")
    prescripciones: so.Mapped[List["PrescripcionEjercicioSesion"]] = so.relationship(back_populates="sesion", cascade="all, delete-orphan")


class PrescripcionEjercicioSesion(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    sesion_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Sesion.id, ondelete="CASCADE"), index=True)
    ejercicio_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Ejercicio.id), index=True)

    series: so.Mapped[int] = so.mapped_column(sa.Integer)
    repeticiones: so.Mapped[str] = so.mapped_column(sa.String(20))
    descanso_segundos: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer, nullable=True)
    intensidad: so.Mapped[Optional[str]] = so.mapped_column(sa.String(30), nullable=True)
    notas: so.Mapped[Optional[str]] = so.mapped_column(sa.String(200), nullable=True)

    # Relaciones
    sesion: so.Mapped["Sesion"] = so.relationship(back_populates="prescripciones")
    ejercicio: so.Mapped["Ejercicio"] = so.relationship()


class RegistroSesionEntrenamiento(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    cliente_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Cliente.id), index=True)
    sesion_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Sesion.id), index=True)

    fecha: so.Mapped[date] = so.mapped_column(sa.Date, default=date.today)
    duracion_minutos: so.Mapped[int] = so.mapped_column(sa.Integer)
    estado_animo: so.Mapped[Optional[str]] = so.mapped_column(sa.String(50), nullable=True)

    # Relaciones
    cliente: so.Mapped["Cliente"] = so.relationship()
    sesion: so.Mapped["Sesion"] = so.relationship()
    registros_ejercicios: so.Mapped[List["RegistroEjercicioSesion"]] = so.relationship(back_populates="registro_sesion", cascade="all, delete-orphan")


class RegistroEjercicioSesion(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    registro_sesion_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(RegistroSesionEntrenamiento.id, ondelete="CASCADE"), index=True)
    ejercicio_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Ejercicio.id), index=True)

    notas_adicionales: so.Mapped[Optional[str]] = so.mapped_column(sa.String(200), nullable=True)

    # Relaciones
    registro_sesion: so.Mapped["RegistroSesionEntrenamiento"] = so.relationship(back_populates="registros_ejercicios")
    ejercicio: so.Mapped["Ejercicio"] = so.relationship()
    series: so.Mapped[List["RegistroSerie"]] = so.relationship(back_populates="registro_ejercicio", cascade="all, delete-orphan")


class RegistroSerie(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    registro_ejercicio_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(RegistroEjercicioSesion.id, ondelete="CASCADE"), index=True)

    numero_serie: so.Mapped[int] = so.mapped_column(sa.Integer)
    peso_usado: so.Mapped[float] = so.mapped_column(sa.Float)
    repeticiones_logradas: so.Mapped[int] = so.mapped_column(sa.Integer)

    # Relaciones
    registro_ejercicio: so.Mapped["RegistroEjercicioSesion"] = so.relationship(back_populates="series")


class RegistroPesoCorporal(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    cliente_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Cliente.id), index=True)

    fecha: so.Mapped[date] = so.mapped_column(sa.Date, default=date.today, index=True)
    peso: so.Mapped[float] = so.mapped_column(sa.Float)

    # Relaciones
    cliente: so.Mapped["Cliente"] = so.relationship(back_populates="historial_peso")


class Recomendacion(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    cliente_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Cliente.id, ondelete="CASCADE"), index=True)
    entrenador_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Entrenador.id), index=True)

    fecha: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.now, index=True)
    titulo: so.Mapped[str] = so.mapped_column(sa.String(100))
    mensaje: so.Mapped[str] = so.mapped_column(sa.Text)
    leido: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False)

    # Relaciones
    cliente: so.Mapped["Cliente"] = so.relationship(back_populates="recomendaciones")
    entrenador: so.Mapped["Entrenador"] = so.relationship(back_populates="recomendaciones_enviadas")


@login.user_loader
def cargar_usuario(id):
    return db.session.get(Usuario, int(id))
```