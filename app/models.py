from typing import Optional, List
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db

class Usuario(db.Model):
    # Fields internos
    id: so.Mapped[int] = so.mapped_column(primary_key=True) #PK interna
    tipo: so.Mapped[str] = so.mapped_column(sa.String(10)) #Field interno para implementar el JTI (Joined Table Inheritance), identifica el tipo de usuario

    #Fields del diagrama de clases
    nombre_usuario: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True) #PK natural y de logica de negocio
    contraseña: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256)) #Contraseña hasheada

    # Configuracion de Herencia JTI (Joined Table Inheritance)
    __mapper_args__ = {
        "polymorphic_identity":"usuario", # Define qué columna de la base de datos se utilizará como "discriminador" para la herencia de las subclases
        "polymorphic_on": "tipo", # Define el valor exacto que identifica a esa clase en particular dentro de la columna discriminadora.
    }

    # Funcion de como imprimir este objeto
    def __repr__(self):
        return '<Usuario: {}>'.format(self.nombre_usuario)

class Entrenador(Usuario):
    # Fields internos
    id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Usuario.id), primary_key=True) # Codigo de identificacion interno para terminos de eficiencia de la base de datos
    clientes: so.Mapped[List["Cliente"]] = so.relationship(back_populates="entrenador") #Relacion 1-N

    #Fields del diagrama de clases
    codigo_entrenador: so.Mapped[str] = so.mapped_column(sa.String(12), unique=True, index=True) # Codigo que introducira el cliente al registrarse para vincularse al entrenador

    # Configuracion de Herencia JTI (Joined Table Inheritance)
    __mapper_args__ = {
        "polymorphic_identity":"entrenador", # valor exacto que identifica a esa subclase en particular
    }

class Cliente(Usuario): 
    # Fields internos
    id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Usuario.id), primary_key=True)
    entrenador_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Entrenador.id, name='fk_cliente_entrenador'), index=True)
    entrenador: so.Mapped["Entrenador"] = so.relationship(back_populates="clientes") # Relacion 1-1

    #Fields del diagrama de clases
    peso: so.Mapped[float] = so.mapped_column(sa.Float)
    meta: so.Mapped[str] = so.mapped_column(sa.String(12)) # Ganar Fuerza o Ganar Musculo (Hipertrofia)
    nivel_experiencia: so.Mapped[str] = so.mapped_column(sa.String(12)) # Principiante - Intermedio - Avanzado

    # Configuracion de Herencia JTI (Joined Table Inheritance)
    __mapper_args__ = {
        "polymorphic_identity":"cliente", # valor exacto que identifica a esa subclase en particular
    }


