from src.lex import *
from src.parse import *
from src.emit import *
from pathlib import Path
import sys
import json
import subprocess

def main():
    if len(sys.argv) < 2:
        sys.exit("Error: no input file.")
    fileName = sys.argv[1]
    outputName = Path(f"{Path(fileName).stem}.asm")
    with open(fileName, 'r') as inputFile:
        source = inputFile.read()

    lexer = Lexer(source, fileName)
    parser = Parser(lexer.lexfile())
    emitter = Emitter(outputName.name)

    program = parser.program()
    with open('parse.json', 'w') as file:
        json.dump(program, file, indent=2)
    emitter.fromdict(program)
    emitter.writeFile()

    subprocess.run(["nasm", "-felf64", "-g", outputName.name])
    subprocess.run(["ld", "-o", outputName.stem, f'{outputName.stem}.o'])
    if '-r' in sys.argv or '--run' in sys.argv:
        execute = subprocess.run([f"./{outputName.stem}"])
        print(f'return code: {execute.returncode}')

if __name__ == "__main__":
    main()
