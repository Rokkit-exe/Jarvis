import speech_recognition as sr
import pyttsx3


def text_to_speech(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def record_and_convert():
    # Initialize recognizer
    recognizer = sr.Recognizer()

    # Record audio from the microphone
    with sr.Microphone() as source:
        print("Please say something...")
        audio = recognizer.listen(source)

    # Recognize speech using Google Web Speech API
    try:
        recognized_text = recognizer.recognize_google(audio)
        if recognized_text == "quit":
            return "quit"
        print("Recognized text:", recognized_text)
        return recognized_text
    except sr.UnknownValueError:
        return "error"
    except sr.RequestError as e:
        print(f"Could not request results from Google Web Speech API; {e}")