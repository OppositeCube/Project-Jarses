#!/usr/bin/env python3
"""
JARVIS - Integrated Intelligent Assistant System

A comprehensive AI-powered personal assistant with advanced capabilities:
- Natural Language Processing (using DeepSeek-V3 from Hugging Face)
- Speech Recognition and Synthesis
- Practical Task Automation
- Memory Management
- System Diagnostics

Prerequisites:
- Install required dependencies using:
  pip install SpeechRecognition gtts pygame transformers huggingface_hub
"""

import os
import tempfile
import time
import sys
import logging
import json
import queue
import datetime
import webbrowser
import random
import pygame
import speech_recognition as sr
from gtts import gTTS
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('jarvis_system.log'),
        logging.StreamHandler()
    ]
)

@dataclass
class SystemConfig:
    """
    Centralized configuration management for the JARVIS system.
    Provides a type-safe, comprehensive configuration structure.
    """
    wake_word: str = "jarvis"
    language: str = "en"
    system_name: str = "JARVIS"
    user_name: str = "User"
    log_level: str = "INFO"
    music_directory: str = "music"  # Default music directory
    huggingface_api_key: str = "enter-your-api-key"  # Your Hugging Face API key
    model_name: str = "deepseek-ai/DeepSeek-V3"  # DeepSeek-V3 model

class Memory:
    """
    Advanced memory management system with sophisticated 
    short-term and long-term memory capabilities.
    """
    def __init__(self, memory_file: str = "jarvis_memory.json"):
        self.memory_file = memory_file
        self.short_term = queue.Queue(maxsize=100)
        self.long_term = self._load_memory()

    def _load_memory(self) -> Dict:
        """Load persistent memory from storage"""
        try:
            with open(self.memory_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "conversations": [],
                "learned_preferences": {},
                "system_interactions": []
            }

    def add_memory(self, memory_type: str, content: Any) -> None:
        """
        Intelligently manage memory storage with automatic timestamping.
        Supports ephemeral and persistent memory types.
        """
        timestamp = datetime.datetime.now().isoformat()
        
        if memory_type == "short_term":
            if self.short_term.full():
                self.short_term.get()
            self.short_term.put({"timestamp": timestamp, "content": content})
        
        elif memory_type == "long_term":
            self.long_term["conversations"].append({
                "timestamp": timestamp,
                "content": content
            })
            self._save_memory()

    def _save_memory(self) -> None:
        """Persist long-term memories to disk"""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.long_term, f, indent=4)
        except IOError as e:
            logging.error(f"Memory save error: {e}")

class PracticalFeatures:
    """
    Handles practical system interactions like web browsing, 
    email, music playback, and application management.
    """
    def __init__(self, config: SystemConfig):
        self.config = config
        self.music_queue = queue.Queue()

    def open_website(self, site: str) -> Tuple[bool, str]:
        """Open specified website with error handling"""
        try:
            known_sites = {
                'youtube': 'https://www.youtube.com',
                'google': 'https://www.google.com',
                'stackoverflow': 'https://stackoverflow.com'
            }
            url = known_sites.get(site.lower(), site)
            webbrowser.open(url)
            return True, f"Opening {url}"
        except Exception as e:
            logging.error(f"Website opening error: {e}")
            return False, f"Could not open {site}"

    def play_music(self, track_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Intelligent music playback with track selection logic.
        Supports specific track requests and random selection.
        """
        try:
            music_dir = self.config.music_directory
            if not os.path.exists(music_dir):
                return False, "Music directory not found"

            music_files = [
                f for f in os.listdir(music_dir) 
                if f.lower().endswith(('.mp3', '.wav', '.flac'))
            ]

            if not music_files:
                return False, "No music files found"

            selected_track = (
                next((track for track in music_files if track_name.lower() in track.lower()), None)
                if track_name else random.choice(music_files)
            )

            if not selected_track:
                return False, f"Track {track_name} not found"

            full_path = os.path.join(music_dir, selected_track)
            pygame.mixer.init()
            pygame.mixer.music.load(full_path)
            pygame.mixer.music.play()

            return True, f"Now playing: {selected_track}"

        except Exception as e:
            logging.error(f"Music playback error: {e}")
            return False, "Music playback failed"

class AudioSystem:
    """
    Advanced audio input/output management with 
    speech recognition and text-to-speech capabilities.
    """
    def __init__(self, config: SystemConfig):
        self.config = config
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        pygame.mixer.init()

    def listen(self, timeout: int = 5, phrase_time_limit: int = 3) -> Tuple[bool, str]:
        """
        Robust speech recognition with enhanced noise handling and timeout management
        """
        with self.microphone as source:
            try:
                self.recognizer.adjust_for_ambient_noise(source, duration=1.5)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                text = self.recognizer.recognize_google(audio).lower()
                return True, text
            except sr.UnknownValueError:
                logging.warning("Speech was unintelligible")
                return False, ""
            except sr.RequestError as e:
                logging.error(f"Could not request results from Google Speech Recognition service: {e}")
                return False, ""
            except Exception as e:
                logging.error(f"Listening error: {e}")
                return False, ""

    def speak(self, text: str) -> None:
        """Enhanced text-to-speech conversion with robust error handling"""
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                filename = temp_file.name
                tts = gTTS(text=text, lang=self.config.language)
                tts.save(filename)

                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()

                start_time = time.time()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                    if time.time() - start_time > 10:  # 10-second timeout
                        pygame.mixer.music.stop()
                        break
        except Exception as e:
            logging.error(f"Speech synthesis error: {e}")
            print(f"Speech synthesis failed: {e}")

class NLPEngine:
    """
    Natural Language Processing core with intent classification,
    sentiment analysis, and conversational capabilities.
    """
    def __init__(self, config: SystemConfig):
        self.config = config
        try:
            # Load tokenizer and model with trust_remote_code=True
            self.tokenizer = AutoTokenizer.from_pretrained(config.model_name, trust_remote_code=True)
            self.model = AutoModelForCausalLM.from_pretrained(config.model_name, trust_remote_code=True)
        except Exception as e:
            logging.critical(f"Failed to load NLP model: {e}")
            raise RuntimeError(f"NLP model initialization failed: {e}")

    def generate_response(self, prompt: str) -> str:
        """Generate a response using the DeepSeek-V3 model"""
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt")
            outputs = self.model.generate(**inputs, max_length=150)
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        except Exception as e:
            logging.error(f"Response generation error: {e}")
            return "I encountered an error while generating a response."

class JARVIS:
    """
    Central orchestration system integrating all JARVIS components.
    Manages system state, command processing, and inter-component communication.
    """
    def __init__(self):
        self.config = SystemConfig()
        self.memory = Memory()
        self.audio = AudioSystem(self.config)
        try:
            self.nlp = NLPEngine(self.config)
        except RuntimeError as e:
            logging.critical(f"Failed to initialize NLP engine: {e}")
            raise
        self.practical = PracticalFeatures(self.config)

    def process_command(self, command: str) -> None:
        """Intelligent command routing and processing"""
        response = self.nlp.generate_response(command)
        self.audio.speak(response)

    def run(self):
        """Main system execution loop"""
        self.audio.speak("JARVIS system online. How may I help you?")
        
        while True:
            try:
                success, command = self.audio.listen()
                
                if success:
                    if self.config.wake_word in command:
                        self.audio.speak("Yes, sir?")
                        success, command = self.audio.listen()
                        if success:
                            self.process_command(command)
                            
            except KeyboardInterrupt:
                self.audio.speak("System shutting down. Goodbye!")
                break
            except Exception as e:
                logging.error(f"Runtime error: {e}")
                self.audio.speak("I encountered an unexpected error.")

def main():
    """Entry point for JARVIS system"""
    try:
        jarvis = JARVIS()
        jarvis.run()
    except Exception as e:
        logging.critical(f"Critical system error: {e}")
        print(f"JARVIS initialization failed: {e}")

if __name__ == "__main__":
    main()