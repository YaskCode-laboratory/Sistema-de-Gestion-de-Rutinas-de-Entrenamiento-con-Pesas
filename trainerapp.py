from app import app
from app import db   
from app.models import Ejercicio                                                                                         
import sqlalchemy as sa                                                                                                                     
                                                                                                                                                
EJERCICIOS_BASE = [                                                                                                                         
# Pecho (Empuje)                                                                                                                                                                                         
    {"nombre": "Press de banca plano con barra", "grupo_muscular": "Pecho", "patron": "Empuje"},                                                                                                             
    {"nombre": "Press inclinado con mancuernas", "grupo_muscular": "Pecho", "patron": "Empuje"},                                                                                                             
    {"nombre": "Fondos en paralelas", "grupo_muscular": "Pecho", "patron": "Empuje"},                                                                                                                        
    {"nombre": "Aperturas con mancuernas", "grupo_muscular": "Pecho", "patron": "Aislamiento / Core"},                                                                                                       
    # Espalda (Tracción y Bisagra)                                                                                                                                                                           
    {"nombre": "Peso muerto convencional", "grupo_muscular": "Espalda", "patron": "Bisagra de Cadera"},                                                                                                      
    {"nombre": "Dominadas", "grupo_muscular": "Espalda", "patron": "Tracción"},                                                                                                                              
    {"nombre": "Remo con barra", "grupo_muscular": "Espalda", "patron": "Tracción"},                                                                                                                         
    {"nombre": "Jalón al pecho en polea", "grupo_muscular": "Espalda", "patron": "Tracción"},                                                                                                                
    {"nombre": "Remo en polea baja", "grupo_muscular": "Espalda", "patron": "Tracción"},                                                                                                                     
    # Piernas (Sentadilla y Bisagra)                                                                                                                                                                         
    {"nombre": "Sentadilla trasera con barra", "grupo_muscular": "Piernas", "patron": "Sentadilla"},                                                                                                         
    {"nombre": "Prensa de piernas 45°", "grupo_muscular": "Piernas", "patron": "Sentadilla"},                                                                                                                
    {"nombre": "Peso muerto rumano", "grupo_muscular": "Piernas", "patron": "Bisagra de Cadera"},                                                                                                            
    {"nombre": "Extensiones de cuádriceps", "grupo_muscular": "Piernas", "patron": "Aislamiento / Core"},                                                                                                    
    {"nombre": "Curl femoral tumbado", "grupo_muscular": "Piernas", "patron": "Aislamiento / Core"},                                                                                                         
    {"nombre": "Elevación de talones (Gemelos)", "grupo_muscular": "Piernas", "patron": "Aislamiento / Core"},                                                                                               
    # Hombros (Empuje y Aislamiento)                                                                                                                                                                         
    {"nombre": "Press militar con barra", "grupo_muscular": "Hombros", "patron": "Empuje"},                                                                                                                  
    {"nombre": "Elevaciones laterales con mancuernas", "grupo_muscular": "Hombros", "patron": "Aislamiento / Core"},                                                                                         
    {"nombre": "Pájaros (Deltoides posterior)", "grupo_muscular": "Hombros", "patron": "Aislamiento / Core"},                                                                                                
    # Brazos (Aislamiento)                                                                                                                                                                                   
    {"nombre": "Curl de bíceps con barra Z", "grupo_muscular": "Brazos", "patron": "Aislamiento / Core"},                                                                                                    
    {"nombre": "Curl martillo con mancuernas", "grupo_muscular": "Brazos", "patron": "Aislamiento / Core"},                                                                                                  
    {"nombre": "Extensiones de tríceps en polea", "grupo_muscular": "Brazos", "patron": "Aislamiento / Core"},                                                                                               
    {"nombre": "Press francés con barra Z", "grupo_muscular": "Brazos", "patron": "Aislamiento / Core"},                                                                                                     
    # Core                                                                                                                                                                                                   
    {"nombre": "Plancha abdominal", "grupo_muscular": "Core", "patron": "Aislamiento / Core"},
    {"nombre": "Elevaciones de piernas colgado", "grupo_muscular": "Core", "patron": "Aislamiento / Core"}                                                                                                                                                                             
]                                                                                                                                           
                                                                                                                                                
@app.cli.command("seed")                                                                                                                    
def seed():                                                                                                                                 
    """Puebla la base de datos con los ejercicios canonicos por defecto."""                                                                 
    contador = 0                                                                                                                            
    for data in EJERCICIOS_BASE:                                                                                                            
        # Comprobar si ya existe para evitar duplicados                                                                                     
        existe = db.session.scalar(                                                                                                         
            sa.select(Ejercicio).where(                                                                                                     
                Ejercicio.nombre == data["nombre"],                                                                                         
                Ejercicio.entrenador_id.is_(None)                                                                                           
            )                                                                                                                               
        )                                                                                                                                   
        if not existe:                                                                                                                      
            ejercicio = Ejercicio(                                                                                                          
                nombre=data["nombre"],                                                                                                      
                grupo_muscular=data["grupo_muscular"],
                patron_movimiento=data["patron"],                                                                                      
                entrenador_id=None # Ejercicio base del sistema                                                                             
            )                                                                                                                               
            db.session.add(ejercicio)                                                                                                       
            contador += 1                                                                                                                   
                                                                                                                                            
    db.session.commit()                                                                                                                     
    print(f"Se insertaron {contador} ejercicios base correctamente.")       

@app.cli.command("seed-log")
def seed_log():
    """Puebla el archivo plano de auditoría con registros de al menos 3 días previos (requisito de cátedra)."""
    import os
    from datetime import datetime, timedelta
    from app.models import Usuario

    log_path = app.config.get('AUDITORIA_LOG_FILE') or 'auditoria_log.txt'

    # Buscar usuarios existentes para hacer los logs reales
    entrenador = db.session.scalar(sa.select(Usuario).where(Usuario.tipo == 'entrenador'))
    cliente = db.session.scalar(sa.select(Usuario).where(Usuario.tipo == 'cliente'))

    trainer_name = entrenador.nombre_usuario if entrenador else "CarlosTrainer"
    client_name = cliente.nombre_usuario if cliente else "JuanAlumno"

    ahora = datetime.now()
    d3 = (ahora - timedelta(days=3)).strftime('%Y-%m-%d')
    d2 = (ahora - timedelta(days=2)).strftime('%Y-%m-%d')
    d1 = (ahora - timedelta(days=1)).strftime('%Y-%m-%d')
    d0 = ahora.strftime('%Y-%m-%d')

    entradas = [
        # Día -3
        f"{d3} 09:14:22, {trainer_name}, Login\n",
        f"{d3} 09:15:05, {trainer_name}, Consulta: Librería de Ejercicios\n",
        f"{d3} 09:22:40, {trainer_name}, Registro: Rutina \"Fuerza Base 5x5\"\n",
        f"{d3} 09:30:12, {trainer_name}, Logout\n",
        # Día -2
        f"{d2} 10:05:18, {client_name}, Login\n",
        f"{d2} 10:06:02, {client_name}, Consulta: Mi Rutina\n",
        f"{d2} 10:52:44, {client_name}, Registro: Entrenamiento completado \"Día de Piernas\"\n",
        f"{d2} 10:53:10, {client_name}, Logout\n",
        # Día -1
        f"{d1} 15:30:00, {trainer_name}, Login\n",
        f"{d1} 15:31:12, {trainer_name}, Consulta: Mis Clientes\n",
        f"{d1} 15:35:40, {trainer_name}, Consulta: Historial Entrenamientos de Cliente {client_name}\n",
        f"{d1} 15:40:05, {trainer_name}, Logout\n",
        # Día de hoy
        f"{d0} 08:12:00, {client_name}, Login\n",
        f"{d0} 08:13:25, {client_name}, Consulta: Entrenamiento del Día\n"
    ]

    with open(log_path, 'a', encoding='utf-8') as f:
        f.writelines(entradas)

    print(f"Log de auditoría poblado con registros de 4 días en '{log_path}'.")       