import speech_recognition as sr
import threading
import unicodedata

class SttWorker:
    def __init__(self, wxmain):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.on = False
        self.wxmain = wxmain
        speech_thread = threading.Thread(target=self.recognize_continuous_speech)
        speech_thread.daemon = True
        speech_thread.start()


    def recognize_continuous_speech(self):
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)  # Prizpusobeni na okolni sum

            while True:
                if self.on:
                    try:
                        print("Reknete neco...")
                        audio = self.recognizer.listen(source)
                        text = self.recognizer.recognize_google(audio, language="cs-CZ")  # Cestina
                        print("Rozpoznany text:", text)
                        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
                        if self.on:
                            self.wxmain.tts_entry.WriteText(text)
                    except sr.UnknownValueError:
                        print("Nerozumel jsem, zkuste to znovu.")
                    except sr.RequestError:
                        print("Chyba pri spojeni s rozpoznavacim serverem.")
                    except KeyboardInterrupt:
                        print("\nUkonceni programu.")

    def Close(self):
        self.on = False