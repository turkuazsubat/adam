import click
from colorama import Fore, Style
from stt import transcribe_audio
from nlu import interpret_text
from response import generate_response
from memory import MemoryManager
from logger import setup_logger

logger = setup_logger()
memory = MemoryManager("db/project.db")

@click.command()
@click.option("--run", is_flag=True, help="Asistanı başlatır.")
def main(run):
    if run:
        print(Fore.GREEN + "Proje X Asistan başlatılıyor..." + Style.RESET_ALL)
        text = transcribe_audio()
        intent = interpret_text(text)
        response = generate_response(intent, memory)
        print(Fore.CYAN + f"Asistan: {response}" + Style.RESET_ALL)
        memory.save_interaction(text, response)
        logger.info(f"Input: {text} | Response: {response}")

if __name__ == "__main__":
    main()
