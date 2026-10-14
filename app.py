#!/usr/bin/env python3
"""Traductor de voz a voz en 6 idiomas: es, en, fr, de, it, pt"""

import time
import speech_recognition as sr
from deep_translator import GoogleTranslator
from gtts import gTTS
import pygame

IDIOMAS = {
    "es": "es-ES",
    "en": "en-US",
    "fr": "fr-FR",
    "de": "de-DE",
    "it": "it-IT",
    "pt": "pt-BR",
}


def pedir_idioma(mensaje):
    while True:
        cod = input(mensaje).strip().lower()
        if cod in IDIOMAS:
            return cod
        print("Idioma no válido. Opciones:", ", ".join(IDIOMAS))


def hablar(texto, idioma):
    gTTS(text=texto, lang=idioma).save("temp.mp3")
    pygame.mixer.music.load("temp.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)


def main():
    pygame.mixer.init()
    r = sr.Recognizer()

    print("=== Traductor de voz a voz (Python) ===")
    print("Idiomas:", ", ".join(IDIOMAS))

    origen = pedir_idioma("Idioma de origen: ")
    destino = pedir_idioma("Idioma de destino: ")

    with sr.Microphone() as mic:
        r.adjust_for_ambient_noise(mic, duration=1)
        print(f"\nListo. Habla en '{origen}' (Ctrl+C para salir).")
        while True:
            print("\n🎤 Escuchando...")
            try:
                audio = r.listen(mic, timeout=5, phrase_time_limit=10)
            except sr.WaitTimeoutError:
                continue

            try:
                texto = r.recognize_google(audio, language=IDIOMAS[origen])
            except sr.UnknownValueError:
                print("No te entendí, repite por favor.")
                continue
            except sr.RequestError as e:
                print("Error de conexión:", e)
                continue

            print(f"Tú ({origen}): {texto}")

            traduccion = GoogleTranslator(source=origen, target=destino).translate(texto)
            print(f"Traducción ({destino}): {traduccion}")

            hablar(traduccion, destino)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n¡Adiós!")
