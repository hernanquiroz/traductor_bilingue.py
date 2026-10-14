import io
import streamlit as st
import speech_recognition as sr
from deep_translator import GoogleTranslator
from gtts import gTTS
from langdetect import detect_langs, DetectorFactory

DetectorFactory.seed = 0

st.set_page_config(page_title="Traductor bilingüe de voz", page_icon="🎤")

IDIOMAS = {"es": "es-ES", "en": "en-US", "fr": "fr-FR",
           "de": "de-DE", "it": "it-IT", "pt": "pt-BR"}
NOMBRES = {"es": "Español", "en": "Inglés", "fr": "Francés",
           "de": "Alemán", "it": "Italiano", "pt": "Portugués"}


def transcribir(audio_bytes, lang_a, lang_b):
    """Transcribe el audio probando ambos idiomas. Devuelve (texto, idioma)."""
    r = sr.Recognizer()
    try:
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            audio = r.record(source)
    except Exception:
        return None, None

    candidatos = []
    for cod in (lang_a, lang_b):
        try:
            res = r.recognize_google(audio, language=IDIOMAS[cod], show_all=True)
        except sr.UnknownValueError:
            continue
        if not res or "alternative" not in res:
            continue
        alt = res["alternative"][0]
        texto = alt.get("transcript", "").strip()
        if texto:
            candidatos.append({"cod": cod, "texto": texto,
                               "conf": float(alt.get("confidence", 0.0))})

    if not candidatos:
        return None, None
    if len(candidatos) == 1:
        return candidatos[0]["texto"], candidatos[0]["cod"]

    # Dos candidatos: decide la confianza; si está muy igualada, langdetect
    ca, cb = candidatos
    if abs(ca["conf"] - cb["conf"]) >= 0.10:
        ganador = max(candidatos, key=lambda c: c["conf"])
    else:
        def prob(texto, cod):
            try:
                return max((d.prob for d in detect_langs(texto) if d.lang == cod),
                           default=0.0)
            except Exception:
                return 0.0
        ganador = ca if prob(ca["texto"], lang_a) >= prob(cb["texto"], lang_b) else cb
    return ganador["texto"], ganador["cod"]


def tts_bytes(texto, cod):
    """Genera el audio mp3 en memoria (sin archivos temporales)."""
    buf = io.BytesIO()
    gTTS(text=texto, lang=cod).write_to_fp(buf)
    buf.seek(0)
    return buf


if "historial" not in st.session_state:
    st.session_state.historial = []

st.title("🎤🌍 Traductor bilingüe de voz")
st.caption("Habla en cualquiera de los dos idiomas: se detecta solo y se traduce al otro.")

col1, _, col2 = st.columns([1, 0.2, 1])
with col1:
    lang_a = st.selectbox("Idioma A", list(IDIOMAS),
                          format_func=lambda c: NOMBRES[c])
with col2:
    lang_b = st.selectbox("Idioma B", list(IDIOMAS), index=1,
                          format_func=lambda c: NOMBRES[c])

with st.sidebar:
    st.header("Cómo usar")
    st.markdown("1. Elige los dos idiomas\n2. Graba tu frase\n3. Detén y escucha la traducción")
    if st.button("🗑️ Borrar conversación"):
        st.session_state.historial = []
        st.rerun()

if lang_a == lang_b:
    st.warning("Elige dos idiomas distintos.")
    st.stop()

# Historial de turnos anteriores
for idioma, texto, destino, traduccion in st.session_state.historial:
    with st.chat_message("user"):
        st.markdown(f"**{NOMBRES[idioma]}:** {texto}")
    with st.chat_message("assistant"):
        st.markdown(f"**{NOMBRES[destino]}:** {traduccion}")

# Grabación desde el navegador (widget nativo de Streamlit)
audio_file = st.audio_input("🎙️ Pulsa para grabar tu frase")

if audio_file is not None:
    with st.spinner("Detectando idioma y transcribiendo..."):
        texto, idioma = transcribir(audio_file.getvalue(), lang_a, lang_b)

    if texto is None:
        st.error("No se entendió el audio. Graba de nuevo, hablando más claro y cerca del micrófono.")
    else:
        destino = lang_b if idioma == lang_a else lang_a
        with st.spinner("Traduciendo..."):
            traduccion = GoogleTranslator(source=idioma, target=destino).translate(texto)
        with st.spinner("Generando voz..."):
            mp3 = tts_bytes(traduccion, destino)

        with st.chat_message("user"):
            st.markdown(f"**{NOMBRES[idioma]}:** {texto}")
        with st.chat_message("assistant"):
            st.markdown(f"**{NOMBRES[destino]}:** {traduccion}")

        st.audio(mp3, format="audio/mp3", autoplay=True)
        st.session_state.historial.append((idioma, texto, destino, traduccion))
