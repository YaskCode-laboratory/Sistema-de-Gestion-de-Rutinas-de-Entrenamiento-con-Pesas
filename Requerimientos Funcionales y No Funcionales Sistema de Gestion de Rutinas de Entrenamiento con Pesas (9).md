**Universidad del Zulia**  
**Facultad de Ciencias**  
**Licenciatura en Computación**

**REQUERIMIENTOS FUNCIONALES Y NO FUNCIONALES**  
**PROYECTO SISTEMA DE GESTIÓN DE RUTINAS DE ENTRENAMIENTO CON PESAS**

Jose Andres Maestre Horcadela C.I.: 30.934.412  
Daniel Isaac Niño Mayorga C.I.: 30.747.937  
Jose David Palmar Sabril C.I.: 31.727.421

1. **RF.- Roles de Usuario:** El sistema debe diferenciar entre dos tipos de usuarios: administrador (entrenador) y usuario (cliente).  
   * **RNF.- Seguridad \- Control de Acceso:** El sistema no debe permitir a un usuario (cliente) acceder a las interfaces o funcionalidades del administrador (entrenador).  
2. **RF.- Vinculación:** El sistema debe permitir que un cliente se vincule a un entrenador al registrarse mediante un código de entrenador. No puede haber clientes sin entrenador.

   * **RNF.-  Seguridad \- Integridad:** Cada Cliente debe estar asociado a únicamente un entrenador, si un cliente no tiene entrenador no puede acceder al sistema. 

3. **RF.- Onboarding de Clientes:** El sistema debe permitir al usuario (cliente) ingresar sus datos básicos al registrarse: peso corporal, altura, edad (fecha de nacimiento),  género, nivel de experiencia de entrenamiento aproximado y las metas específicas que quiere lograr (como ganar masa muscular, ganar fuerza, perder grasa), y cuantos dias a la semana quiere/puede entrenar.

   * **RNF.- Capacidad de Interacción \- Auto Descriptividad  y Operabilidad:** El formulario inicial de captura de datos (peso, altura, metas, etc.) debe estar diseñado para que un usuario promedio lo complete con facilidad.

4. **RF.- Panel de Clientes:** El administrador (entrenador) debe tener una lista de todos los usuarios (clientes) que están bajo su supervisión.

   * **RNF.- Eficiencia de Desempeño \- Comportamiento Temporal:** El panel del administrador debe cargar la lista completa de sus clientes asignados de manera rápida.

5. **RF.- Creacion de rutinas:** El administrador (entrenador) debe poder crear rutinas de entrenamiento para un target específico (nivel de experiencia y meta) para tenerlas a la mano a la hora de asignarlas a los clientes.

   * **RNF.- Capacidad de Interacción \- Auto Descriptividad y Operabilidad:** La interfaz debe permitir al administrador crear una rutina nueva e indexarla en el sistema de manera sencilla e intuitiva.

6. **RF.- Asignacion de rutinas:** El administrador (entrenador) debe poder asignar una rutina de entrenamiento a cada cliente.  
   * **RNF.- Fiabilidad \- Integridad de datos:** Al asignar una rutina a un cliente, el sistema debe asegurar que el registro se guarde en la base de datos sin pérdida de información.  
7. **RF.-  Libreria de Ejercicios:** El administrador (entrenador) debe contar a una colección de ejercicios que será la  que utilizara para crear las rutinas. Esta debe estar previamente populada con los ejercicios mas comunes y el administrador puede añadir o eliminar los ejercicios "propios" (ese ejercicio solo le aparecerá a él en su lista, y solo él podrá editarlo o eliminarlo).  
   * **RNF.- Fiabilidad \- Integridad de datos:** La acción de añadir, editar o eliminar ejercicios de la librería por parte del administrador no debe alterar otros datos el sistema ni causar errores o fallas  inesperadas en el mismo. (Por ejemplo, un entrenador solo debe ver y poder modificar o eliminar los ejercicios propios (los que el agrego), y no los de otros entrenadores o los que estan por defecto)  
8. **RF.- Entrenamiento del día:** El sistema debe mostrar el entrenamiento correspondiente del día al cliente (usuario) de manera automática.   
   * **RNF.- Fiabilidad \- Disponibilidad:** El sistema debe garantizar que la rutina diaria se muestre correctamente siempre que el usuario lo necesite.   
9. **Registro de Entrenamiento:** El usuario (cliente) debe poder registrar los datos correspondiente a el entrenamiento del día  de la rutina que le fue asignada (la sesión de entrenamiento asignada para ese día con sus ejercicios, pesos, reps y series completadas)  que ha realizado.  
   * **RNF.- Capacidad de Interacción \- Auto Descriptividad y Operabilidad:** La vista para registrar pesos, series y repeticiones debe ser sencilla e intuitiva para el usuario.  
10. **RF.- Observación de Entrenamientos:** El administrador debe poder visualizar los entrenamientos  (las sesiones de entrenamiento completadas con sus ejercicios, pesos, reps y series respectivos)  que ha realizado el cliente de la rutina que le asignó.  
    * **RNF.- Capacidad de Interacción \- Auto Descriptividad y Operabilidad:**La visualización de los registros de cada cliente debe mostrarse con una estructura de lectura clara y directa.   
11. **RF.- Actualización registrada de datos del cliente:** El usuario (cliente) debe poder actualizar sus datos relevantes al entrenamiento (peso corporal y metas) en cualquier momento después de registrarse. El entrenador solo debe poder cambiar el nivel de experiencia del cliente y solo él lo debe poder hacer. Cada actualización debe ser guardada en un registro para no perder la trazabilidad del progreso logrado.  
    * **RNF.- Fiabilidad \- Prevención de errores de usuario:** Los campos para actualizar datos físicos (como el peso) deben restringirse para aceptar únicamente valores coherentes.  
12. **RF.- Filtrado de rutinas por meta para sugerir asignación de rutinas para un cliente al administrador:** El sistema debe poder filtrar para el administrador (entrenador) sus rutinas según la meta específica (ganar masa muscular, ganar fuerza, perder grasa) y el nivel de experiencia de el cliente (principiante, intermedio, avanzado) para recomendarle la asignación de rutinas que él ya haya creado para ese target en específico.  
    * **RNF.-** **Eficiencia de Desempeño \- Comportamiento Temporal:** El filtrado en pantalla debe realizarse de forma inmediata   
13. **RF.- Estado de Espera y Notificación de Asignación:** Tras el proceso de Onboarding, el panel del usuario debe mostrar un estado de "Esperando sugerencias del entrenador". Una vez el administrador analice sus metas y le asigne una rutina manualmente, el sistema actualizará la interfaz para permitirle ver y registrar el entrenamiento del dia de la rutina asignada para poder comenzar a entrenar.   
    * **RNF. \- Capacidad de Interacción- Autodescriptividad:** El estado de espera debe ser visualmente evidente  y descriptivo  (por ejemplo, mediante colores, iconos y mensajes) de manera que el usuario entienda en la fase de espera que se encuentra.   
14. **RF.- Proyección de Tiempo Estimado para lograr las metas y sugerencias:** El sistema debe procesar los datos iniciales del usuario y el objetivo específico seleccionado y la rutina que le fue asignada por el entrenador, para generar y mostrar en pantalla una estimación de tiempo (en semanas o meses) indicando cuándo podría alcanzar su meta o ver resultados significativos y sugerencias para lograrlo, esto después se haría en base al progreso mensual, ya cuando el cliente lleve varios entrenamientos registrados (al menos un mes).  
    * **RNF.- Eficiencia de Desempeño \- Comportamiento Temporal:** El cálculo de la proyección de tiempo debe generarse y mostrarse al usuario sin tiempos de carga prolongados.   
15. **RF.- Visualización de Progreso Mensual:** El sistema debe compilar automáticamente los registros diarios de entrenamiento y las actualizaciones de datos físicos para generar un resumen mensual, permitiendo al usuario visualizar de forma rápida la evolución del volumen/peso levantado en los ejercicios y la evolución de su peso corporal.  
    * **RNF. \- Capacidad de Interacción- Autodescriptividad:** Los resúmenes de progreso deben ser legibles y autoexplicativos para que el usuario no necesite asistencia para entenderlos. 

