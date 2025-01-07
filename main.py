import json
import asyncio
import pvporcupine
import pyaudio
import struct
import io
import os
import dotenv
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
from speech_to_text import record_and_convert
from langchain_ollama import ChatOllama
from langchain.memory import ConversationBufferMemory
from langchain.agents import initialize_agent, Tool
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from tools.note_engine import note_saver

dotenv.load_dotenv()

# give me the api key in dotenv
pvporcupine_api_key = os.getenv("PVPORCUPINE_API_KEY")

callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

async def run_command(command):
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return stdout.decode(), stderr.decode()

def text_to_speech(text):
    tts = gTTS(text=text, lang='en')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    audio = AudioSegment.from_file(fp, format="mp3")
    play(audio)


def text_to_speech_worker(q):
    while True:
        phrase = q.get()
        if phrase is None:  # Stop signal
            break
        tts = gTTS(text=phrase, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        audio = AudioSegment.from_file(fp, format="mp3")
        play(audio)
        q.task_done()

def process_stream_response(response, q):
    phrase = ""
    try:
        # Process each line of the streamed response
        for line in response.iter_lines():
            if line:
                response_json = json.loads(line.decode('utf-8'))
                # Convert the content to speech
                if 'message' in response_json and 'content' in response_json['message']:
                    if response_json['done'] == True:
                        print("done")
                        break
                    if response_json['message']['role'] == 'assistant':
                        if any(punct in response_json['message']['content'] for punct in [".", ",", "?", "!"]):
                            phrase += response_json['message']['content']
                            q.put(phrase)  # Send the complete phrase to the TTS thread
                            phrase = ""
                        else:
                            phrase += response_json['message']['content']
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e.msg}")

async def main():
    model = "Jarvis"
    wake_word = "jarvis"
    role = "user"
    command = '"C:\\Users\\franc\\AppData\\Local\\Programs\\Ollama\\ollama app.exe"'
    print("Starting ollama service")
    stdout, stderr = await run_command(command)
    print(stdout)
    print(stderr)

    llm = ChatOllama(
        model = "llama3.2",
        callback_manager=callback_manager,
        verbose=False
    )

    tools = [
        note_saver,
    ]

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent="conversational-react-description",  # Agent type
        verbose=False,
        memory=ConversationBufferMemory(memory_key="chat_history"),
    )

    # Initialize Porcupine with the "Jarvis" wake word
    porcupine = pvporcupine.create(access_key=pvporcupine_api_key, keywords=[wake_word])

    # Initialize PyAudio
    pa = pyaudio.PyAudio()

    # Open audio stream
    audio_stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length
    )

    print(f"Listening for wake word '{wake_word}'...")

    try:
        while True:
            pcm = audio_stream.read(porcupine.frame_length)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0:
                print(f"Wake word '{wake_word}' detected!")
                prompt = "user:" + record_and_convert()

                if prompt == "quit":
                    print("quitting")
                    text_to_speech("ok bye")
                    break

                if prompt == "error":
                    print("error")
                    text_to_speech("I'm sorry, I didn't understand that")
                    continue

                phrase = ""
                output_buffer = ""
                response = agent.invoke(prompt)
                text_to_speech(response['output'])
                continue

    finally:
        audio_stream.stop_stream()
        audio_stream.close()
        pa.terminate()
        porcupine.delete()



if __name__ == "__main__":
    asyncio.run(main())

