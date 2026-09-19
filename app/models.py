from typing import Optional, List
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import secrets # Para generar el codigo del entrenador
import string # Para los caracteres a utilizar para generar el codigo del entrenador
from datetime import date, datetime

class Usuario(UserMixin, db.Model):
    # Fields internos
    id: so.Mapped[int] = so.mapped_column(primary_key=True) #PK interna autoincremental para terminos de eficiencia en la identificacion y relaciones de la base de datos 
    tipo: so.Mapped[str] = so.mapped_column(sa.String(10)) #Field interno para implementar el JTI (Joined Table Inheritance), identifica el tipo de usuario

    #Fields del diagrama de clases
    nombre_usuario: so.Mapped[str] = so.mapped_column(sa.String(64, collation="NOCASE"), index=True, unique=True) #PK natural y de logica de negocio, Collation=Nocase asegura que sea guardado en minusculas
    contraseña: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256)) #Contraseña hasheada

    # Configuracion de Herencia JTI (Joined Table Inheritance)
    __mapper_args__ = {
        "polymorphic_identity":"usuario", # Define qué columna de la base de datos se utilizará como "discriminador" para la herencia de las subclases
        "polymorphic_on": "tipo", # Define el valor exacto que identifica a esa clase en particular dentro de la columna discriminadora.
    }

    # Funcion de como imprimir este objeto
    def __repr__(self):
        return '<Usuario: {}>'.format(self.nombre_usuario)

    # Funcion para guardar hasheada la contraseña dada 
    def guardar_contraseña(self, contraseña):
        self.contraseña = generate_password_hash(contraseña)

    # Funcion para checkear el hash de la contraseña dada contra el hash guardado de la contraseña del usuario
    def chequear_contraseña(self, contraseña):
        return check_password_hash(self.contraseña, contraseña)


class Entrenador(Usuario):
    # Fields internos
    id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Usuario.id), primary_key=True) 
    clientes: so.Mapped[List["Cliente"]] = so.relationship(back_populates="entrenador", foreign_keys="[Cliente.entrenador_id]") #Relacion 1-N
    rutinas: so.Mapped[List['Rutina']] = so.relationship(back_populates='entrenador', foreign_keys='[Rutina.entrenador_id]')

    #Fields del diagrama de clases
    codigo_entrenador: so.Mapped[str] = so.mapped_column(sa.String(12), unique=True, index=True) # Codigo que introducira el cliente al registrarse para vincularse al entrenador

    # Configuracion de Herencia JTI (Joined Table Inheritance)
    __mapper_args__ = {
        "polymorphic_identity":"entrenador", # Valor exacto que identifica a esa subclase en particular
    }

    # Funcion que crea y asigna a el entrenador su codigo
    def generar_codigo_entrenador(self):
        longitud = 6
        caracteres = string.ascii_uppercase + string.digits
        sufijo = "".join(secrets.choice(caracteres) for _ in range(longitud))
        self.codigo_entrenador =f"ENT-{sufijo}"

class Cliente(Usuario): 
    # Fields internos
    id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Usuario.id), primary_key=True)
    entrenador_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Entrenador.id, name='fk_cliente_entrenador'), index=True)
    rutina_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey('rutina.id', name='fk_cliente_rutina'), nullable=True, index=True)
    
   

    #Fields del diagrama de clases
    peso: so.Mapped[float] = so.mapped_column(sa.Float)
    meta: so.Mapped[str] = so.mapped_column(sa.String(12)) # Ganar Fuerza o Ganar Musculo (Hipertrofia)
    nivel_experiencia: so.Mapped[str] = so.mapped_column(sa.String(12)) # Principiante - Intermedio - Avanzado

    # Relaciones
    entrenador: so.Mapped["Entrenador"] = so.relationship(back_populates="clientes", foreign_keys="[Cliente.entrenador_id]") # Relacion 1-1
    rutina_asignada: so.Mapped[Optional['Rutina']] = so.relationship(foreign_keys='[Cliente.rutina_id]')

    # Configuracion de Herencia JTI (Joined Table Inheritance)
    __mapper_args__ = {
        "polymorphic_identity":"cliente", # valor exacto que identifica a esa subclase en particular
    }

class Ejercicio(db.Model):
    #Fields internos
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    #Fields del diagrama  de clases
    nombre: so.Mapped[str] = so.mapped_column(sa.String(100), index=True)

    #Para clientes de Hipertrofia (Ganar Masa Muscular)
    grupo_muscular: so.Mapped[str] = so.mapped_column(sa.String(50), index=True) # Pecho, Espalda, Piernas, etc.     

    # Para clientes de Powerlifting (Ganar Fuerza) NECESITO AGREGARLO AL DIAGRAMA DE CLASES
    patron_movimiento: so.Mapped[Optional[str]] = so.mapped_column(sa.String(50), index=True, nullable=True)

    # Si entrenador_id es NULL -> Es ejercicio global (por defecto, para todos)                                                                                                                                         
    # Si entrenador_id tiene un ID -> Es un ejercicio propio de ese entrenador                                                                                                                                          
    entrenador_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey(Entrenador.id), index=True, nullable=True)     

class Rutina(db.Model):
    #Fields Internos
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    #Fields del diagrama de clases
    nombre: so.Mapped[str] = so.mapped_column(sa.String(100), index=True)
    nivel: so.Mapped[str] = so.mapped_column(sa.String(12))
    meta: so.Mapped[str] = so.mapped_column(sa.String(12))
    entrenador_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Entrenador.id), index=True)

    #Relaciones
    entrenador: so.Mapped['Entrenador'] = so.relationship(back_populates='rutinas')
    sesiones: so.Mapped[List['Sesion']] = so.relationship(back_populates='rutina', cascade='all, delete-orphan')

class Sesion(db.Model):
    #Fields Internos:
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    rutina_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Rutina.id, ondelete='CASCADE'), index=True)
    

    #Fields diagrama de clases
    nombre: so.Mapped[str] = so.mapped_column(sa.String(100))
    dia: so.Mapped[int] = so.mapped_column(sa.Integer)

    #Relaciones
    rutina: so.Mapped['Rutina'] = so.relationship(back_populates='sesiones', foreign_keys='[Sesion.rutina_id]')
    prescripciones: so.Mapped[List['PrescripcionEjercicioSesion']] = so.relationship(back_populates='sesion', cascade='all, delete-orphan')


class PrescripcionEjercicioSesion(db.Model):
    # Fields Internos
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    sesion_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Sesion.id, ondelete='CASCADE'), index=True)
    ejercicio_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Ejercicio.id), index=True)

    # Fields del diagrama de clases (adaptados a tipos escalares atómicos)
    series: so.Mapped[int] = so.mapped_column(sa.Integer) # Ej: 4
    repeticiones: so.Mapped[str] = so.mapped_column(sa.String(20)) # Ej: "8-10" o "12"
    descanso_segundos: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer, nullable=True) # Ej: 90

    # CLAVE PARA POWERLIFTING (Opcionales):
    # Permite al entrenador indicar "@ RPE 8" o "80% 1RM" o "Top set @9"
    intensidad: so.Mapped[Optional[str]] = so.mapped_column(sa.String(30), nullable=True)
    notas: so.Mapped[Optional[str]] = so.mapped_column(sa.String(200), nullable=True) # Ej: "Pausa de 1 seg en el pecho"

    # Relaciones
    sesion: so.Mapped['Sesion'] = so.relationship(back_populates='prescripciones')
    ejercicio: so.Mapped['Ejercicio'] = so.relationship()

class RegistroSesionEntrenamiento(db.Model):
    #Fields Internos
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    cliente_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Cliente.id), index=True)
    sesion_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Sesion.id), index=True)

    #Fields del diagrama de clases
    fecha: so.Mapped[date] = so.mapped_column(sa.Date, default=date.today)
    duracion_minutos: so.Mapped[int] = so.mapped_column(sa.Integer)
    estado_animo: so.Mapped[Optional[str]] = so.mapped_column(sa.String(50), nullable=True) 

    # Relaciones
    cliente: so.Mapped['Cliente'] = so.relationship()
    sesion: so.Mapped['Sesion'] = so.relationship()
    registros_ejercicios: so.Mapped[List['RegistroEjercicioSesion']] = so.relationship(back_populates='registro_sesion', cascade='all, delete-orphan')


class RegistroEjercicioSesion(db.Model):
    #Fields Internos
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    registro_sesion_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(RegistroSesionEntrenamiento.id, ondelete='CASCADE'), index=True)
    ejercicio_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Ejercicio.id), index=True)

    #Fields diagrama de clases
    notas_adicionales: so.Mapped[Optional[str]] = so.mapped_column(sa.String(200), nullable=True)

    #Relaciones
    registro_sesion: so.Mapped['RegistroSesionEntrenamiento'] = so.relationship(back_populates='registros_ejercicios')
    series: so.Mapped[List['RegistroSerie']] = so.relationship(back_populates='registro_ejercicio', cascade='all, delete-orphan')

class RegistroSerie(db.Model):
    #Fields Internos
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    registro_ejercicio_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(RegistroEjercicioSesion.id, ondelete='CASCADE'), index=True)

    #Fields diagrama de clases
    numero_serie: so.Mapped[int] = so.mapped_column(sa.Integer)
    peso_usado: so.Mapped[float] = so.mapped_column(sa.Float)
    repeticiones_logradas: so.Mapped[int] = so.mapped_column(sa.Integer)

    #Relaciones
    registro_ejercicio: so.Mapped['RegistroEjercicioSesion'] = so.relationship(back_populates='series')

class RegistroPesoCorporal(db.Model):
    #Fields Internos
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    cliente_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Cliente.id), index=True)

    #Fields del diagrama de clase
    fecha: so.Mapped[date] = so.mapped_column(sa.Date, default=date.today, index=True)
    peso: so.Mapped[float] = so.mapped_column(sa.Float)

    #Relaciones
    Cliente: so.Mapped['Cliente'] = so.relationship


@login.user_loader
def cargar_usuario(id):
    return db.session.get(Usuario, int(id))