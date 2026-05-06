# backend/audio/speech_to_text.py
import speech_recognition as sr
import streamlit as st
from typing import Optional, Tuple
import time

class SpeechToTextConverter:
    def __init__(self):
        """Initialise le convertisseur voix-texte"""
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.available = True
        
        # Ajuster pour le bruit ambiant
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("✅ Microphone initialisé avec succès")
        except Exception as e:
            print(f"⚠️ Erreur microphone: {e}")
            self.available = False
    
    def listen_and_convert(self, duration: int = 5, language: str = "ar-SA") -> Tuple[Optional[str], float]:
        """
        Écoute le microphone et convertit la parole en texte
        
        Args:
            duration: Durée d'écoute en secondes
            language: Langue (ar-SA pour arabe, fr-FR pour français, en-US pour anglais)
        
        Returns:
            Tuple (texte_transcrit, temps_écoute)
        """
        if not self.available:
            return None, 0
        
        try:
            start_time = time.time()
            
            with st.spinner(f"🎤 Écoute en cours... ({duration} secondes)"):
                with self.microphone as source:
                    # Écouter l'audio
                    audio = self.recognizer.listen(source, timeout=duration, phrase_time_limit=duration)
                
                # Transcrire l'audio
                text = self.recognizer.recognize_google(audio, language=language)
                
                elapsed_time = time.time() - start_time
                return text, elapsed_time
                
        except sr.WaitTimeoutError:
            st.warning("⏰ Délai dépassé. Aucune parole détectée.")
            return None, 0
        except sr.UnknownValueError:
            st.warning("😕 Impossible de comprendre l'audio. Veuillez réessayer.")
            return None, 0
        except sr.RequestError as e:
            st.error(f"❌ Erreur de service: {e}")
            return None, 0
        except Exception as e:
            st.error(f"❌ Erreur inattendue: {e}")
            return None, 0
    
    def convert_from_file(self, audio_file_path: str, language: str = "ar-SA") -> Optional[str]:
        """
        Convertit un fichier audio en texte
        
        Args:
            audio_file_path: Chemin vers le fichier audio
            language: Langue
        
        Returns:
            Texte transcrit
        """
        try:
            with sr.AudioFile(audio_file_path) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio, language=language)
                return text
        except Exception as e:
            print(f"Erreur conversion fichier: {e}")
            return None
    
    def test_microphone(self) -> bool:
        """Teste si le microphone fonctionne"""
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=2)
                test_text = self.recognizer.recognize_google(audio, language="ar-SA")
                return True
        except:
            return False