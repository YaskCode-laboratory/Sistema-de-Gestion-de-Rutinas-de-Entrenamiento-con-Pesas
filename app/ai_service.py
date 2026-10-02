import os
import json
import urllib.request
import urllib.error
import sqlalchemy as sa
from datetime import date, datetime, timedelta
from flask import current_app
from app import db
from app.models import Cliente, RegistroSesionEntrenamiento, RegistroEjercicioSesion, RegistroSerie, RegistroPesoCorporal, Ejercicio

def recopilar_datos_entrenamiento(cliente: Cliente) -> dict:
    """
    Extrae y compila los datos cuantitativos y cualitativos de los entrenamientos
    y del historial físico del cliente para alimentar el contexto de la Inteligencia Artificial (CU17 / RF14).
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
    ejercicios_stats = {}  # {nombre_ejercicio: {'max_peso': float, 'primera_carga': float, 'total_series': int, 'total_reps': int, 'cargas': []}}
    total_minutos = 0

    for s in sesiones:
        total_minutos += s.duracion_minutos or 0
        ejercicios_sesion = []
        for reg_ej in s.registros_ejercicios:
            nombre_ej = reg_ej.ejercicio.nombre if reg_ej.ejercicio else "Ejercicio"
            grupo_ej = reg_ej.ejercicio.grupo_muscular if reg_ej.ejercicio else "General"

            if nombre_ej not in ejercicios_stats:
                ejercicios_stats[nombre_ej] = {
                    'nombre': nombre_ej,
                    'grupo': grupo_ej,
                    'max_peso': 0.0,
                    'primera_carga': None,
                    'ultima_carga': 0.0,
                    'total_series': 0,
                    'total_reps': 0,
                    'cargas': []
                }

            series_info = []
            for serie in reg_ej.series:
                peso = serie.peso_usado or 0.0
                reps = serie.repeticiones_logradas or 0
                series_info.append(f"{peso}kg x {reps} reps")

                if ejercicios_stats[nombre_ej]['primera_carga'] is None:
                    ejercicios_stats[nombre_ej]['primera_carga'] = peso
                if peso > ejercicios_stats[nombre_ej]['max_peso']:
                    ejercicios_stats[nombre_ej]['max_peso'] = peso
                ejercicios_stats[nombre_ej]['ultima_carga'] = peso
                ejercicios_stats[nombre_ej]['total_series'] += 1
                ejercicios_stats[nombre_ej]['total_reps'] += reps
                ejercicios_stats[nombre_ej]['cargas'].append(peso)

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

    # Asegurar que primera_carga no sea None
    for st in ejercicios_stats.values():
        if st['primera_carga'] is None:
            st['primera_carga'] = st['max_peso']
        st['delta_peso'] = round(st['max_peso'] - st['primera_carga'], 1)

    # 2. Historial de pesajes corporales (CU13)
    pesos_registrados = db.session.scalars(
        sa.select(RegistroPesoCorporal)
        .where(RegistroPesoCorporal.cliente_id == cliente.id)
        .order_by(RegistroPesoCorporal.fecha.asc())
    ).all()

    peso_actual = cliente.peso or 0.0
    if pesos_registrados:
        peso_actual = pesos_registrados[-1].peso
        peso_inicial = pesos_registrados[0].peso
    else:
        peso_inicial = peso_actual

    historial_peso_str = []
    for p in pesos_registrados[-6:]:
        historial_peso_str.append(f"{p.fecha.strftime('%d/%m/%Y')}: {p.peso} kg")

    # 3. Adherencia y frecuencia semanal
    hace_7_dias = date.today() - timedelta(days=7)
    sesiones_esta_semana = sum(1 for s in sesiones if s.fecha >= hace_7_dias)

    return {
        'total_sesiones': len(sesiones),
        'total_minutos': total_minutos,
        'resumen_sesiones': resumen_sesiones,
        'ejercicios_stats': ejercicios_stats,
        'peso_actual': peso_actual,
        'peso_inicial': peso_inicial,
        'peso_objetivo': cliente.peso_objetivo,
        'historial_pesos_resumen': historial_peso_str,
        'sesiones_esta_semana': sesiones_esta_semana,
        'dias_semana_meta': cliente.dias_semana_meta or 4
    }


def _extraer_titulo_y_cuerpo(texto_completo: str, modelo_usado: str = "") -> tuple[str, str]:
    """
    Parsea la respuesta generada por Gemini para separar el título del cuerpo del análisis.
    """
    lineas = texto_completo.split('\n')
    titulo = "Análisis y Proyección Inteligente"
    cuerpo_lineas = []

    for l in lineas:
        l_strip = l.strip()
        if l_strip.startswith("TITULO:") or l_strip.startswith("TÍTULO:"):
            titulo = l_strip.replace("TITULO:", "").replace("TÍTULO:", "").strip()
        elif l_strip.startswith("**TITULO:**") or l_strip.startswith("**TÍTULO:**"):
            titulo = l_strip.replace("**TITULO:**", "").replace("**TÍTULO:**", "").strip()
        elif l_strip.startswith("# TITULO:") or l_strip.startswith("# TÍTULO:"):
            titulo = l_strip.replace("# TITULO:", "").replace("# TÍTULO:", "").strip()
        elif l_strip.startswith("# ") and titulo == "Análisis y Proyección Inteligente":
            titulo = l_strip.replace("# ", "").strip()
        else:
            cuerpo_lineas.append(l)

    cuerpo = "\n".join(cuerpo_lineas).strip()
    return titulo, cuerpo


def _invocar_gemini_api(api_key: str, prompt: str) -> tuple[str, str]:
    """
    Invoca la API de Google Gemini para generar contenido con consumo mínimo de tokens.
    Prioriza el modelo 'gemini-3.5-flash-lite' (el más generoso en cuotas del Free Tier),
    con failover automático a 'gemini-flash-lite-latest', 'gemini-3.1-flash-lite' y 'gemini-3.8-flash'.
    Maneja conmutación resiliente ante códigos HTTP 503 (alta demanda temporal), 429, 404 y timeouts.
    """
    modelo_configurado = os.environ.get('GEMINI_MODEL')
    try:
        if not modelo_configurado and current_app:
            modelo_configurado = current_app.config.get('GEMINI_MODEL')
    except Exception:
        pass

    # Modelos candidatos válidos y actualizados (gemini-3.5-flash-lite prioritario)
    modelos_candidatos = [
        modelo_configurado,
        'gemini-3.5-flash-lite',
        'gemini-flash-lite-latest',
        'gemini-3.1-flash-lite',
        'gemini-3.8-flash',
        'gemini-flash-latest'
    ]
    # Filtrar None, vacíos y duplicados preservando orden de prioridad
    modelos = []
    for m in modelos_candidatos:
        if m and m not in modelos:
            modelos.append(m)

    ultimo_error = None
    for model in modelos:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            # Optimización estricta de tokens de acuerdo a guías oficiales de Gemini 3.x:
            # - Sin parámetros obsoletos (temperature, top_p, top_k no recomendados en Gemini 3.x)
            # - maxOutputTokens acotado para reservar suficiente para razonamiento interno + respuesta
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}]
                    }
                ],
                "generationConfig": {
                    "maxOutputTokens": 800
                }
            }
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=15) as resp:
                data_resp = json.loads(resp.read().decode('utf-8'))
                candidates = data_resp.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts:
                        texto = parts[0].get('text', '').strip()
                        if texto:
                            titulo, cuerpo = _extraer_titulo_y_cuerpo(texto, model)
                            cuerpo += f"\n\n*Análisis generado con Inteligencia Artificial Google Gemini ({model}) en base a tus registros reales.*"
                            return titulo, cuerpo

        except urllib.error.HTTPError as he:
            err_msg = he.read().decode('utf-8', errors='ignore')
            print(f"[Gemini API] HTTP {he.code} con modelo '{model}': {err_msg[:200]}")
            ultimo_error = f"HTTP {he.code} ({model})"
            # Si el modelo no está disponible (404), sufre pico de alta demanda temporal (503),
            # o saturación transitoria de cuota (429/500/502/504), conmutamos al siguiente modelo de respaldo
            if he.code in (404, 429, 500, 502, 503, 504):
                continue
            # Error fatal de credenciales inválidas (400, 401, 403)
            raise Exception(f"Gemini API Error: {ultimo_error} - {err_msg}")
        except Exception as e:
            print(f"[Gemini API] Error al invocar con modelo '{model}': {e}")
            ultimo_error = str(e)
            continue

    raise Exception(f"No fue posible conectar con ningún modelo de Gemini: {ultimo_error}")


def _generar_recomendacion_heuristica(cliente: Cliente, datos: dict) -> tuple[str, str]:
    """
    Motor analítico determinista / regla de expertos (Fallback de alta disponibilidad).
    Calcula diagnósticos y proyecciones matemáticas reales a partir de los datos
    cuantitativos de entrenamiento y peso corporal del cliente (CU17 / RF14),
    garantizando respuestas útiles incluso si no hay conexión a internet o API Key.
    """
    meta = (cliente.meta or 'Hipertrofia').strip()
    nivel = cliente.nivel_experiencia or 'Principiante'
    total_sesiones = datos['total_sesiones']
    total_minutos = datos['total_minutos']
    stats = datos['ejercicios_stats']
    peso_actual = datos['peso_actual']
    peso_objetivo = datos['peso_objetivo']
    dias_meta = datos['dias_semana_meta']

    # 1. Identificar ejercicios con sobrecarga progresiva y cargas máximas
    ejercicios_con_sobrecarga = []
    ejercicios_base = []
    total_kg_ganados = 0.0

    for nombre, st in stats.items():
        delta = st.get('delta_peso', 0.0)
        if delta > 0:
            ejercicios_con_sobrecarga.append(
                f"- **{nombre}**: Inició con {st['primera_carga']} kg y alcanzó carga máxima de **{st['max_peso']} kg** (+{delta} kg de sobrecarga en {st['total_series']} series)."
            )
            total_kg_ganados += delta
        else:
            ejercicios_base.append(
                f"- **{nombre}**: Carga de referencia establecida en **{st['max_peso']} kg** ({st['total_series']} series registradas)."
            )

    detalles_ejercicios = []
    if ejercicios_con_sobrecarga:
        detalles_ejercicios.extend(ejercicios_con_sobrecarga[:3])
    if len(detalles_ejercicios) < 3 and ejercicios_base:
        detalles_ejercicios.extend(ejercicios_base[:3 - len(detalles_ejercicios)])

    lista_ej_str = "\n".join(detalles_ejercicios) if detalles_ejercicios else "- Sesiones registradas con volumen de adaptación inicial."

    # 2. Diagnóstico y sugerencias según objetivo (Fuerza vs Hipertrofia)
    if meta.lower() == 'fuerza':
        titulo = f"Evaluación de Fuerza y Sobrecarga Progresiva ({nivel})"
        
        # Sugerencias técnicas
        ej_candidato = list(stats.keys())[0] if stats else "tus ejercicios principales"
        ajuste = (
            f"1. **Sobrecarga Progresiva Directa**: En ejercicios donde lograste completar todas las repeticiones prescritas (como {ej_candidato}), incrementa entre **1.25 kg y 2.5 kg** en la primera serie de la próxima semana.\n"
            "2. **Tiempos de Descanso y SNC**: Asegura entre **2 y 3 minutos completos de descanso** entre series efectivas para garantizar la recuperación del sistema nervioso central.\n"
            "3. **Técnica y RPE**: Entrena a un RPE 7-8 (2 a 3 repeticiones en recámara) antes de buscar un fallo técnico. Prioriza la velocidad de la fase concéntrica."
        )

        # Proyección de tiempo estimado (RF14)
        if nivel.lower() == 'principiante':
            proyeccion = (
                f"Con una adherencia constante a tu meta de **{dias_meta} días por semana**, las adaptaciones neuromusculares iniciales "
                "te permitirán incrementar entre un **10% y 15% tus marcas principales en las próximas 4 a 6 semanas**."
            )
        elif nivel.lower() == 'intermedio':
            proyeccion = (
                f"Manteniendo un ritmo de sobrecarga lineal de 1.25 kg a 2.5 kg por microciclo, proyectamos un incremento acumulado "
                f"del **5% al 8% en tus levantamientos clave durante las próximas 6 a 8 semanas**."
            )
        else:
            proyeccion = (
                "Para tu nivel avanzado, se proyecta un incremento del **2.5% al 4%** en marcas máximas en un bloque de **8 a 12 semanas**, "
                "optimizando la gestión de fatiga y volumen efectivo."
            )
    else:  # Hipertrofia / Ganancia Muscular
        titulo = f"Análisis de Volumen Muscular y Proyección ({nivel})"

        ajuste = (
            "1. **Rango de Repeticiones y Tensión Mecánica**: Busca acumular series efectivas en el rango de **8 a 12 repeticiones** con una fase excéntrica controlada (2 a 3 segundos de bajada).\n"
            "2. **Ajuste de Cargas**: Cuando superes las repeticiones objetivo con buena técnica en todas las series, incrementa la carga en el escalón mínimo (+1.25 kg o +2.5 kg) para mantener el estímulo hipertrófico.\n"
            "3. **Recuperación y Síntesis Proteica**: Mantén una ingesta diaria de **1.6 a 2.0g de proteína por kg de peso corporal** y al menos 7-8 horas de sueño para regenerar el tejido muscular."
        )

        # Proyección de tiempo estimado considerando peso corporal (RF14)
        if peso_objetivo and peso_actual > 0:
            dif_peso = round(peso_objetivo - peso_actual, 1)
            if dif_peso > 0:
                semanas_min = max(2, int(dif_peso / 0.5))
                semanas_max = max(4, int(dif_peso / 0.25))
                proyeccion = (
                    f"Para alcanzar tu peso objetivo de **{peso_objetivo} kg** (te faltan **{dif_peso} kg**), a una tasa segura y recomendada "
                    f"de ganancia muscular magra de **0.25 a 0.5 kg por semana**, tu tiempo estimado es de aproximadamente **{semanas_min} a {semanas_max} semanas** "
                    f"manteniendo un ligero superávit calórico y tu frecuencia de **{dias_meta} días por semana**."
                )
            elif dif_peso < 0:
                semanas_min = max(2, int(abs(dif_peso) / 0.75))
                semanas_max = max(4, int(abs(dif_peso) / 0.5))
                proyeccion = (
                    f"Para alcanzar tu peso objetivo de **{peso_objetivo} kg** (reducción de **{abs(dif_peso)} kg**), a un ritmo saludable de pérdida de grasa "
                    f"de **0.5 a 0.75 kg por semana**, tu tiempo estimado es de **{semanas_min} a {semanas_max} semanas** preservando masa muscular."
                )
            else:
                proyeccion = (
                    f"¡Has alcanzado tu peso objetivo de **{peso_objetivo} kg**! Tu proyección actual se enfoca en recomposición corporal y "
                    "aumento de densidad muscular, con cambios visibles en definición y vascularidad entre las **semanas 6 y 10**."
                )
        else:
            proyeccion = (
                f"A este ritmo de frecuencia ({dias_meta} días por semana) y volumen efectivo acumulado, las adaptaciones estructurales "
                "y ganancia muscular serán visualmente notorias entre las **semanas 6 y 10 de consistencia**."
            )

    # 3. Resumen de sobrecarga progresiva cuantitativa
    if total_kg_ganados > 0:
        resumen_sobrecarga = f"Has logrado un incremento acumulado de **+{total_kg_ganados} kg** entre los ejercicios con sobrecarga positiva registrada."
    else:
        resumen_sobrecarga = "Tus registros actuales sientan la base de cargas iniciales. Tu siguiente paso es iniciar el incremento escalonado."

    mensaje = f"""### Diagnóstico de Rendimiento
Has completado un total de **{total_sesiones} sesión(es)** de entrenamiento registradas en el sistema ({total_minutos} minutos de trabajo efectivo acumulado).
{resumen_sobrecarga}

**Análisis de Ejercicios y Cargas Registradas:**
{lista_ej_str}

### Sugerencias Técnicas para tus Próximas Sesiones
{ajuste}

### Proyección de Tiempo Estimado (RF14)
{proyeccion}

*Análisis generado por el Motor Analítico Experto de TrainerApp (Alta Disponibilidad / Modo Local) en base a tus registros reales.*"""

    return titulo, mensaje


def generar_recomendacion_ia(cliente_id: int) -> tuple[str, str]:
    """
    Orquestador principal de Inteligencia Artificial para el Caso de Uso CU17 (RF14).
    1. Extrae y compila los datos de los entrenamientos y peso corporal.
    2. Si existe GEMINI_API_KEY y hay conexión, invoca a Google Gemini.
    3. Si no hay API Key o falla la red, utiliza el motor analítico experto de respaldo (Fallback).
    Retorna (titulo, mensaje).
    """
    cliente = db.session.get(Cliente, cliente_id)
    if not cliente:
        return "Error", "Cliente no encontrado."

    datos = recopilar_datos_entrenamiento(cliente)
    if not datos:
        return None, "No hay suficientes entrenamientos registrados para realizar un análisis de IA. Completa al menos una sesión de entrenamiento."

    # Intentar invocar a Google Gemini API si hay API Key disponible
    api_key = os.environ.get('GEMINI_API_KEY')
    try:
        if not api_key and current_app:
            api_key = current_app.config.get('GEMINI_API_KEY')
    except Exception:
        pass

    if api_key and api_key.strip():
        api_key = api_key.strip()
        try:
            # Resumen conciso para minimizar drásticamente el consumo de tokens de entrada (Input Tokens)
            sesiones_recientes = datos['resumen_sesiones'][-3:]
            sesiones_texto = []
            for s in sesiones_recientes:
                sesiones_texto.append(f"• {s['fecha']} ({s['nombre_sesion']}): {'; '.join(s['ejercicios'][:3])}")
            historial_str = "\n".join(sesiones_texto)

            # Estadísticas de ejercicios clave con sobrecarga
            top_ejercicios = []
            for ej_nombre, st in list(datos['ejercicios_stats'].items())[:4]:
                delta = st.get('delta_peso', 0.0)
                delta_str = f" (+{delta}kg)" if delta > 0 else ""
                top_ejercicios.append(f"{ej_nombre}: máx {st['max_peso']}kg{delta_str}")
            ejercicios_resumen = ", ".join(top_ejercicios) if top_ejercicios else "Ejercicios base registrados"

            peso_historial_str = ", ".join(datos['historial_pesos_resumen']) if datos['historial_pesos_resumen'] else f"{datos['peso_actual']} kg"

            prompt = f"""Actúa como un entrenador científico y conciso (estilo Mike Israetel / Eric Helms).
Analiza estos registros reales y responde con un consumo mínimo de tokens (máximo 140 palabras en total).

DATOS:
- Alumno: {cliente.nombre_usuario} | Meta: {cliente.meta} | Nivel: {cliente.nivel_experiencia}
- Peso: {datos['peso_actual']} kg (Meta: {cliente.peso_objetivo or 'N/A'} kg) | Historial pesajes: [{peso_historial_str}]
- Sesiones totales: {datos['total_sesiones']} ({datos['total_minutos']} min) | Frecuencia meta: {datos['dias_semana_meta']} días/sem
- Cargas clave: {ejercicios_resumen}
- Últimos entrenamientos:
{historial_str}

REGLAS DE FORMATO (Obligatorio, máx 140 palabras):
TITULO: <título motivador en 6 palabras o menos>
### Diagnóstico del Rendimiento
<2 frases precisas sobre sobrecarga progresiva y adherencia>
### Recomendaciones y Ajuste de Cargas
<2 pautas técnicas directas: kg a subir en próximos entrenos y descanso>
### Proyección de Tiempo Estimado (RF14)
<1-2 frases indicando semanas o meses calculados para alcanzar el objetivo>"""

            titulo, cuerpo = _invocar_gemini_api(api_key, prompt)
            return titulo, cuerpo

        except Exception as e:
            print(f"[AI Service] No se pudo invocar Gemini API ({e}). Activando fallback analítico de alta disponibilidad...")
            return _generar_recomendacion_heuristica(cliente, datos)
    else:
        # Fallback analítico si no hay GEMINI_API_KEY configurada
        return _generar_recomendacion_heuristica(cliente, datos)
