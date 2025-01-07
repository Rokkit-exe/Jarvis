import os
from langchain.agents import Tool

path = "C:\\Users\\franc\\Documents\\Obsidian Vault\\notes"
file = "Jarvis.md"

note_file = os.path.join(path, file)

def save_note(text) -> str:
    if not os.path.exists(note_file):
        open(note_file, "w")

    with open(note_file, "a") as f:
        f.writelines(f"{text}\n\n")

    return "Note saved"


note_saver = Tool(
        name="note_saver",
        func=save_note,
        description="""This tool can save a text based note to a file for the user. 
                        The only required argument is a string called 'text' containing the note to be saved.
                        The tool will return the string 'Note saved' for confirmation.
                        """,
    )



