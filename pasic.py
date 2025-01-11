from src.lex import *
from src.parse import *
from src.emit import *
from pathlib import Path
from dataclasses import is_dataclass, asdict
import sys
import json
import subprocess

def main():
    if len(sys.argv) < 2:
        sys.exit("Error: no input file.")
    fileName = sys.argv[1]
    outputName = Path(f"{Path(fileName).stem}.asm")

    lexer = Lexer(fileName)
    parser = Parser(lexer.lexfile())
    emitter = Emitter(outputName.name)

    program = parser.program()
    with open('parse.json', 'w') as file:
        json.dump(program, file, indent=2, cls=EnhancedJSONEncoder)
    emitter.fromdict(program)
    emitter.writeFile()

    subprocess.run(["nasm", "-felf64", "-g", outputName.name])
    subprocess.run(["ld", "-o", outputName.stem, f'{outputName.stem}.o'])
    if '-r' in sys.argv or '--run' in sys.argv:
        execute = subprocess.run([f"./{outputName.stem}"])
        print(f'return code: {execute.returncode}')

class EnhancedJSONEncoder(json.JSONEncoder):
        def default(self, o):
            if is_dataclass(StatementNode) or is_dataclass(ExpressionNode) or is_dataclass(BinaryNode):
                return asdict(o)
            return super().default(o)

if __name__ == "__main__":
    main()
