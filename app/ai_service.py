import os
import sqlalchemy as sa
from datetime import date, datetime
from flask import current_app
from app import db
from app.models import Cliente, RegistroSesionEntrenamiento, RegistroEjercicioSesion, RegistroSerie, Ejercicio

def recopilar_datos_entrenamiento(cliente: Cliente) -> dict:
    """
    Extrae y compila los datos cuantitativos y cualitativos de los entrenamientos
    del cliente para alimentar el contexto de la Inteligencia Artificial (CU17 / RF14).
    """
    # 1. Sesiones del cliente ordenadas cronológicamente
    sesiones = db.session.scalars(
        sa.select(RegistroSesionEntrenamiento)
        .where(RegistroSesionEntrenamiento.cliente_id == cliente.id)
        .order_by(RegistroSesionEntrenamiento.fecha.asc())
    ).all()

    if not sesiones:
        return None

    resumen_sesiones = []
    ejercicios_stats = {} # {nombre_ejercicio: {'max_peso': float, 'total_series': int, 'total_reps': int}}

    for s in sesiones:
        ejercicios_sesion = []
        for reg_ej in s.registros_ejercicios:
            nombre_ej = reg_ej.ejercicio.nombre
            if nombre_ej not in ejercicios_stats:
                ejercicios_stats[nombre_ej] = {'max_peso': 0.0, 'total_series': 0, 'total_reps': 0, 'cargas': []}

            series_info = []
            for serie in reg_ej.series:
                series_info.append(f"{serie.peso_usado}kg x {serie.repeticiones_logradas} reps")
                if serie.peso_usado > ejercicios_stats[nombre_ej]['max_peso']:
                    ejercicios_stats[nombre_ej]['max_peso'] = serie.peso_usado
                ejercicios_stats[nombre_ej]['total_series'] += 1
                ejercicios_stats[nombre_ej]['total_reps'] += serie.repeticiones_logradas
                ejercicios_stats[nombre_ej]['cargas'].append(serie.peso_usado)

            detalle_ej = f"{nombre_ej}: [{', '.join(series_info)}]"
            if reg_ej.notas_adicionales:
                detalle_ej += f" (Nota del alumno: '{reg_ej.notas_adicionales}')"
            ejercicios_sesion.append(detalle_ej)

        resumen_sesiones.append({
            'fecha': s.fecha.strftime('%d/%m/%Y'),
            'nombre_sesion': s.sesion.nombre if s.sesion else 'Sesión',
            'duracion_minutos': s.duracion_minutos,
            'estado_animo': s.estado_animo or 'Normal',
            'ejercicios': ejercicios_sesion
        })

    return {
        'total_sesiones': len(sesiones),
        'resumen_sesiones': resumen_sesiones,
        'ejercicios_stats': ejercicios_stats
    }


def _generar_recomendacion_heuristica(cliente: Cliente, datos: dict) -> tuple[str, str]:
    """
    Motor analítico determinista / regla de expertos (Fallback de alta disponibilidad).
    Garantiza que el sistema responda de forma coherente con datos reales
    incluso si no hay conexión a internet o no se ha configurado la API Key de Gemini.
    """
    meta = cliente.meta or 'Hipertrofia'
    nivel = cliente.nivel_experiencia or 'Principiante'
    total_sesiones = datos['total_sesiones']
    stats = datos['ejercicios_stats']

    ejercicios_destacados = []
    for ej, st in list(stats.items())[:3]:
        ejercicios_destacados.append(f"- **{ej}**: Carga máxima registrada de {st['max_peso']} kg a lo largo de {st['total_series']} series.")

    lista_ej_str = "\n".join(ejercicios_destacados) if ejercicios_destacados else "- Sesiones registradas con volumen de adaptación inicial."

    if meta.lower() == 'fuerza':
        titulo = f"Evaluación de Fuerza y Sobrecarga Progresiva ({nivel})"
        proyeccion = (
            "En base a tus registros iniciales y a un ritmo de sobrecarga progresiva del 2.5% al 5% mensual, "
            "podrías incrementar entre un 10% y 15% tus marcas principales en las próximas 6 a 8 semanas."
        )
        ajuste = (
            "1. **Sobrecarga Progresiva**: Para los ejercicios donde completaste todas las repeticiones prescritas, aumenta entre 1.25 kg y 2.5 kg en la primera serie de la próxima semana.\n"
            "2. **Tiempos de Descanso**: Asegura de 2 a 3 minutos completos de descanso entre series efectivas para maximizar la recuperación del sistema nervioso central.\n"
            "3. **Técnica y RPE**: Mantén un RPE 7-8 (2 a 3 repeticiones en reserva) antes de buscar un fallo técnico."
        )
    else: # Hipertrofia
        titulo = f"Análisis de Volumen Muscular y Proyección ({nivel})"
        proyeccion = (
            "A este ritmo de frecuencia y volumen efectivo, los primeros cambios significativos en hipertrofia "
            "y densidad muscular serán visualmente notorios entre las semanas 8 y 12 de consistencia."
        )
        ajuste = (
            "1. **Rango de Repeticiones**: Busca acumular series efectivas en el rango de 8 a 12 repeticiones con una fase excéntrica controlada (2-3 segundos de bajada).\n"
            "2. **Ajuste de Carga**: Si en un ejercicio superas las repeticiones objetivo con buena técnica, incrementa la carga un escalón mínimo para mantener el estímulo mecánico.\n"
            "3. **Recuperación**: Procura mantener una ingesta de 1.6 a 2.0g de proteína por kg de peso corporal para apoyar la síntesis proteica de tus sesiones."
        )

    mensaje = f"""### Diagnóstico de Rendimiento
Has completado un total de **{total_sesiones} sesión(es)** de entrenamiento registradas en el sistema.

**Análisis de Ejercicios y Cargas:**
{lista_ej_str}

### Sugerencias Técnicas para tus Próximas Sesiones
{ajuste}

### Proyección de Tiempo Estimado (RF14)
{proyeccion}

*Nota generada automáticamente por el Asistente Inteligente de TrainerApp en base a tus registros.*"""

    return titulo, mensaje


def generar_recomendacion_ia(cliente_id: int) -> tuple[str, str]:
    """
    Orquestador principal de Inteligencia Artificial para el Caso de Uso CU17 (RF14).
    1. Extrae los datos recopilados de los entrenamientos.
    2. Si existe GEMINI_API_KEY, invoca a Google Gemini (gemini-3.8-flash).
    3. Si no hay API Key o falla la red, utiliza el motor analítico de respaldo (Fallback).
    Retorna (titulo, mensaje).
    """
    cliente = db.session.get(Cliente, cliente_id)
    if not cliente:
        return "Error", "Cliente no encontrado."

    datos = recopilar_datos_entrenamiento(cliente)
    if not datos:
        return None, "No hay suficientes entrenamientos registrados para realizar un análisis de IA. Completa al menos una sesión."

    # Intentar invocar a Google Gemini API si hay API Key disponible
    api_key = os.environ.get('GEMINI_API_KEY') or current_app.config.get('GEMINI_API_KEY')
    
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)

            # Construcción del prompt estructurado con los datos compilados
            sesiones_texto = []
            for s in datos['resumen_sesiones']:
                sesiones_texto.append(f"• Fecha {s['fecha']} ({s['nombre_sesion']}, ánimo: {s['estado_animo']}): {'; '.join(s['ejercicios'])}")
            historial_str = "\n".join(sesiones_texto)

            prompt = f"""Actúa como un entrenador científico y especialista en biomecánica y sobrecarga progresiva (estilo Eric Helms, Mike Israetel, 3DMJ).
Analiza el siguiente perfil y los registros reales de entrenamiento de este cliente:

DATOS DEL CLIENTE:
- Nombre: {cliente.nombre_usuario}
- Objetivo Principal: {cliente.meta}
- Nivel de Experiencia: {cliente.nivel_experiencia}
- Peso Corporal: {cliente.peso} kg
- Rutina Asignada: {cliente.rutina_asignada.nombre if cliente.rutina_asignada else 'Rutina personalizada'}
- Total de Sesiones Registradas: {datos['total_sesiones']}

HISTORIAL DE ENTRENAMIENTOS REALIZADOS (PESOS Y REPETICIONES):
{historial_str}

REQUERIMIENTOS DE LA RESPUESTA (Caso de Uso CU17 / Requerimiento RF14):
1. Proporciona en la primera línea un TÍTULO directo en el formato: "TITULO: <tu titulo breve>"
2. Diagnóstico del Rendimiento: Evalúa la sobrecarga progresiva, los pesos usados y las notas dejadas por el alumno.
3. Recomendaciones Específicas: Indica pautas claras de ajuste de cargas (cuántos kg subir, mantener o ajustar) y descansos para sus próximas sesiones.
4. Proyección de Tiempo Estimado: Calcula en cuántas semanas o meses comenzará a ver resultados notorios según su meta y adherencia.
5. Usa formato markdown limpio y amigable. No inventes ejercicios que el cliente no haya registrado."""

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )
            
            texto_completo = response.text.strip()
            
            # Extraer título si viene con el prefijo TITULO:
            lineas = texto_completo.split('\n')
            titulo = "Análisis y Proyección Inteligente"
            cuerpo_lineas = []
            for l in lineas:
                if l.startswith("TITULO:"):
                    titulo = l.replace("TITULO:", "").strip()
                elif l.startswith("**TITULO:**"):
                    titulo = l.replace("**TITULO:**", "").strip()
                else:
                    cuerpo_lineas.append(l)

            cuerpo = "\n".join(cuerpo_lineas).strip()
            return titulo, cuerpo
        except Exception as e:
            print(f"[AI Service] Error invocando Gemini API: {e}. Activando fallback analítico...")
            # Fallback inteligente si la API falla
            return _generar_recomendacion_heuristica(cliente, datos)
    else:
        # Fallback analítico si no hay GEMINI_API_KEY configurada
        return _generar_recomendacion_heuristica(cliente, datos)
