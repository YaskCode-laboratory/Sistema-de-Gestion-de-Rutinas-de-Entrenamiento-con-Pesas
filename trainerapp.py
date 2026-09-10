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