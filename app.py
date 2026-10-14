#!/usr/bin/env python3
"""Traductor bilingüe de voz a voz con detección automática de idioma."""

import time
import speech_recognition as sr
from deep_translator import GoogleTranslator
from gtts import gTTS
import pygame
from langdetect import detect_langs, DetectorFactory

DetectorFactory.seed = 0  # hace que la detección dé siempre el mismo resultado

IDIOMAS = {
    "es": "es-ES",
    "en": "en-US",
    "fr": "fr-FR",
    "de": "de-DE",
    "it": "it-IT",
    "pt": "pt-BR",
}

NOMBRES = {"es": "español", "en": "inglés", "fr": "francés",
           "de": "alemán", "it": "italiano", "pt": "portugués"}


def pedir_dos_idiomas():
    while True:
        a = input(f"Idioma A ({', '.join(IDIOMAS)}): ").strip().lower()
        b = input("Idioma B: ").strip().lower()
        if a in IDIOMAS and b in IDIOMAS and a != b:
            return a, b
        print("Deben ser dos códigos distintos de la lista.")


def detectar(texto, candidatos):
    """Devuelve la probabilidad de que 'texto' esté en cada idioma candidato."""
    try:
        dets = {d.lang: d.prob for d in detect_langs(texto)}
    except Exception:
        return {c: 0.0 for c in candidatos}
    return {c: dets.get(c, 0.0) for c in candidatos}


def transcribir(r, audio, lang_a, lang_b):
    """Transcribe el audio probando ambos idiomas. Devuelve (texto, idioma)."""
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
            candidatos.append({
                "cod": cod,
                "texto": texto,
                "conf": float(alt.get("confidence", 0.0)),
            })

    if not candidatos:
        return None, None
    if len(candidatos) == 1:
        c = candidatos[0]
        return c["texto"], c["cod"]

    # Decisión: gana la confianza de Google; si están muy igualadas, desempata langdetect
    ca, cb = candidatos
    if abs(ca["conf"] - cb["conf"]) >= 0.10:
        ganador = max(candidatos, key=lambda c: c["conf"])
    else:
        pa = detectar(ca["texto"], (lang_a, lang_b))[lang_a]
        pb = detectar(cb["texto"], (lang_a, lang_b))[lang_b]
        ganador = ca if pa >= pb else cb
    return ganador["texto"], ganador["cod"]


def hablar(texto, cod):
    gTTS(text=texto, lang=cod).save("temp.mp3")
    pygame.mixer.music.load("temp.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)


def main():
    pygame.mixer.init()
    r = sr.Recognizer()

    print("=== Traductor bilingüe con detección automática ===")
    print("Elige los DOS idiomas de la conversación (el orden no importa).")
    lang_a, lang_b = pedir_dos_idiomas()
    print(f"\nConversación: {NOMBRES[lang_a]} <-> {NOMBRES[lang_b]}")
    print("Habla en cualquiera de los dos; se traducirá al otro. (Ctrl+C para salir)")

    with sr.Microphone() as mic:
        r.adjust_for_ambient_noise(mic, duration=1)
        while True:
            print("\n🎤 Escuchando...")
            try:
                audio = r.listen(mic, timeout=5, phrase_time_limit=10)
            except sr.WaitTimeoutError:
                continue

            try:
                texto, idioma = transcribir(r, audio, lang_a, lang_b)
            except sr.RequestError as e:
                print("Error de conexión:", e)
                continue

            if texto is None:
                print("No te entendí, repite por favor.")
                continue

            destino = lang_b if idioma == lang_a else lang_a
            print(f"Tú ({idioma}): {texto}")

            traduccion = GoogleTranslator(source=idioma, target=destino).translate(texto)
            print(f"Traducción ({destino}): {traduccion}")

            hablar(traduccion, destino)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n¡Adiós!")
