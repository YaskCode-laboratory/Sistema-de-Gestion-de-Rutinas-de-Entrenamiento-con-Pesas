**Universidad del Zulia**  
**Facultad de Ciencias**  
**Licenciatura en Computación**

**Diagrama de Objetos y Diagrama de Clases**  
**Sistema de Gestión de Rutinas de Entrenamiento con Pesas**

Jose Andres Maestre Horcadela C.I.: 30.934.412  
Daniel Isaac Niño Mayorga C.I.: 30.747.937  
Jose David Palmar Sabril C.I.: 31.727.421

1. ### Diagrama de Objetos

   

2. ### Diagrama de Clases

3. ### Código UML Diagrama de Clases

**classDiagram**  
direction TB  
    **class** Entrenador **{**  
        **\+**String nombreUsuario  
        **\+**String contrasena  
        **\+**String codigoEntrenador  
        **\+**registrarse**()**  
        **\+**iniciarSesion**()**  
        **\+**crearRutina**()**  
        **\+**asignarRutinaCliente**()**  
    **}**

    **class** Cliente **{**  
        **\+**String nombreUsuario  
        **\+**String contrasena  
        **\+**float Peso  
        **\+**String Meta  
        **\+**String nivelExperiencia  
        **\+**registrarse**()**  
        **\+**iniciarSesion**()**  
        **\+**verEntrenamientoDelDia**()**  
        **\+**registrarSesionEntrenamiento**()**  
    **}**

    **class** Rutina **{**  
        **\+**String rutinaEntrenamiento  
        **\+**String nivelRutina  
        **\+**String metaRutina  
        **\+**agregarSesion**()**  
        **\+**eliminarSesion**()**  
        **\+**obtenerSesiones**()**  
    **}**

    **class** Sesion **{**  
        **\+**String nombreSesion  
        **\+**int diaSemana  
        **\+**agregarPrescripcionEjercicio**()**  
        **\+**eliminarPrescripcionEjercicio**()**  
        **\+**obtenerPrescripciones**()**  
    **}**

    **class** PrescripcionEjercicioSesion **{**  
        **\+**int series  
        **\+**List**\~**int**\~** repeticiones  
        **\+**List**\~**float**\~** pesos  
        **\+**List**\~**int**\~** descansos  
        **\+**modificarPrescripcion**()**  
    **}**

    **class** Ejercicio **{**  
        **\+**String nombre  
        **\+**String grupoMuscular  
    **}**

    **class** RegistroSesionEntrenamiento **{**  
        **\+**Date fecha  
        **\+**int duracionMinutos  
        **\+**String estadoAnimo  
        **\+**iniciarCronometro**()**  
        **\+**detenerCronometro**()**  
        **\+**registrarEjercicioSesion**()**  
    **}**

    **class** RegistroEjercicioSesion **{**  
        **\+**int seriesCompletadas  
        **\+**List**\~**int**\~** repeticionesLogradas  
        **\+**List**\~**float**\~** pesosUsados  
        **\+**String notasAdicionales  
    **}**

    Entrenador "1" **\--\>** "\*" Cliente **:** supervisa  
    Entrenador "1" **\--\>** "\*" Rutina **:** diseña  
    Cliente "\*" **\--\>** "1" Rutina **:** tiene asignada  
    Rutina "1" **\*--** "\*" Sesion **:** contiene  
    Sesion "1" **\*--** "\*" PrescripcionEjercicioSesion **:** prescribe  
    PrescripcionEjercicioSesion "\*" **\--\>** "1" Ejercicio **:** refiere a  
    Cliente "1" **\*--** "\*" RegistroSesionEntrenamiento **:** asiste y realiza  
    RegistroSesionEntrenamiento "1" **\*--** "\*" RegistroEjercicioSesion **:** registra  
    RegistroSesionEntrenamiento "\*" **\--\>** "1" Sesion **:** basada en  
    RegistroEjercicioSesion "\*" **\--\>** "1" PrescripcionEjercicioSesion **:** responde a

4. ### Codigo Python

from datetime import date

**class** Ejercicio:  
    **def** \_\_init\_\_(self, nombre: str, grupoMuscular: str):  
        self.nombre \= nombre  
        self.grupoMuscular \= grupoMuscular

**class** PrescripcionEjercicioSesion:  
    **def** \_\_init\_\_(self, series: int, repeticiones: list\[int\], pesos: list\[float\], descansos: list\[int\], ejercicio: Ejercicio):  
        self.series \= series  
        self.repeticiones \= repeticiones  
        self.pesos \= pesos  
        self.descansos \= descansos  
        self.ejercicio \= ejercicio

    **def** modificarPrescripcion(self):  
        pass

**class** Sesion:  
    **def** \_\_init\_\_(self, nombreSesion: str, diaSemana: int):  
        self.nombreSesion \= nombreSesion  
        self.diaSemana \= diaSemana  
        self.prescripciones: list\[PrescripcionEjercicioSesion\] \= \[\]

    **def** agregarPrescripcionEjercicio(self, series: int, repeticiones: list\[int\], pesos: list\[float\], descansos: list\[int\], ejercicio: Ejercicio) \-\> PrescripcionEjercicioSesion:  
        nueva\_prescripcion \= PrescripcionEjercicioSesion(series, repeticiones, pesos, descansos, ejercicio)  
        self.prescripciones.append(nueva\_prescripcion)  
        return nueva\_prescripcion

    **def** eliminarPrescripcionEjercicio(self, prescripcion: PrescripcionEjercicioSesion):  
        if prescripcion in self.prescripciones:  
            self.prescripciones.remove(prescripcion)

    **def** obtenerPrescripciones(self) \-\> list\[PrescripcionEjercicioSesion\]:  
        return self.prescripciones

**class** Rutina:  
    **def** \_\_init\_\_(self, rutinaEntrenamiento: str, nivelRutina: str, metaRutina: str):  
        self.rutinaEntrenamiento \= rutinaEntrenamiento  
        self.nivelRutina \= nivelRutina  
        self.metaRutina \= metaRutina  
        self.sesiones: list\[Sesion\] \= \[\]

    **def** agregarSesion(self, nombreSesion: str, diaSemana: int) \-\> Sesion:  
        nueva\_sesion \= Sesion(nombreSesion, diaSemana)  
        self.sesiones.append(nueva\_sesion)  
        return nueva\_sesion

    **def** eliminarSesion(self, sesion: Sesion):  
        if sesion in self.sesiones:  
            self.sesiones.remove(sesion)

    **def** obtenerSesiones(self) \-\> list\[Sesion\]:  
        return self.sesiones

**class** RegistroEjercicioSesion:  
    **def** \_\_init\_\_(self, seriesCompletadas: int, repeticionesLogradas: list\[int\], pesosUsados: list\[float\], notasAdicionales: str, prescripcionBase: PrescripcionEjercicioSesion):  
        self.seriesCompletadas \= seriesCompletadas  
        self.repeticionesLogradas \= repeticionesLogradas  
        self.pesosUsados \= pesosUsados  
        self.notasAdicionales \= notasAdicionales  
        self.prescripcionBase \= prescripcionBase

**class** RegistroSesionEntrenamiento:  
    **def** \_\_init\_\_(self, fecha: date, duracionMinutos: int, estadoAnimo: str, sesionBase: Sesion):  
        self.fecha \= fecha  
        self.duracionMinutos \= duracionMinutos  
        self.estadoAnimo \= estadoAnimo  
        self.sesionBase \= sesionBase  
        self.registrosEjercicios: list\[RegistroEjercicioSesion\] \= \[\]

    **def** iniciarCronometro(self):  
        pass

    **def** detenerCronometro(self):  
        pass

    **def** registrarEjercicioSesion(self, seriesCompletadas: int, repeticionesLogradas: list\[int\], pesosUsados: list\[float\], notasAdicionales: str, prescripcionBase: PrescripcionEjercicioSesion) \-\> RegistroEjercicioSesion:  
        nuevo\_registro \= RegistroEjercicioSesion(seriesCompletadas, repeticionesLogradas, pesosUsados, notasAdicionales, prescripcionBase)  
        self.registrosEjercicios.append(nuevo\_registro)  
        return nuevo\_registro

**class** Cliente:  
    **def** \_\_init\_\_(self, nombreUsuario: str, contrasena: str, peso: float, meta: str, nivelExperiencia: str):  
        self.nombreUsuario \= nombreUsuario  
        self.contrasena \= contrasena  
        self.peso \= peso  
        self.meta \= meta  
        self.nivelExperiencia \= nivelExperiencia  
         
        *\# Usando la nueva sintaxis para valores opcionales*  
        self.rutinaAsignada: Rutina | None \= None  
         
        self.historialEntrenamientos: list\[RegistroSesionEntrenamiento\] \= \[\]

    **def** registrarse(self):  
        pass

    **def** iniciarSesion(self):  
        pass

    **def** verEntrenamientoDelDia(self):  
        pass

    **def** registrarSesionEntrenamiento(self, fecha: date, duracionMinutos: int, estadoAnimo: str, sesionBase: Sesion) \-\> RegistroSesionEntrenamiento:  
        nuevo\_registro\_sesion \= RegistroSesionEntrenamiento(fecha, duracionMinutos, estadoAnimo, sesionBase)  
        self.historialEntrenamientos.append(nuevo\_registro\_sesion)  
        return nuevo\_registro\_sesion

**class** Entrenador:  
    **def** \_\_init\_\_(self, nombreUsuario: str, contrasena: str, codigoEntrenador: str):  
        self.nombreUsuario \= nombreUsuario  
        self.contrasena \= contrasena  
        self.codigoEntrenador \= codigoEntrenador  
         
        self.clientesSupervisados: list\[Cliente\] \= \[\]  
        self.rutinasDisenadas: list\[Rutina\] \= \[\]

    **def** registrarse(self):  
        pass

    **def** iniciarSesion(self):  
        pass

    **def** crearRutina(self, rutinaEntrenamiento: str, nivelRutina: str, metaRutina: str) \-\> Rutina:  
        nueva\_rutina \= Rutina(rutinaEntrenamiento, nivelRutina, metaRutina)  
        self.rutinasDisenadas.append(nueva\_rutina)  
        return nueva\_rutina

    **def** asignarRutinaCliente(self, cliente: Cliente, rutina: Rutina):  
        cliente.rutinaAsignada \= rutina  
        if cliente not in self.clientesSupervisados:  
            self.clientesSupervisados.append(cliente)

