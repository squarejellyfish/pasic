# Emitter object keeps track of the generated code and outputs it.
from sys import stdin, stdout

class Emitter:
    def __init__(self, fullPath):
        self.fullPath = fullPath
        self.header = ""
        self.code = ""
        self.staticVarCount = 0

    def fromdict(self, input: dict=dict()):
        assert 'program' in input
        assert 'statements' in input['program']

        self.headerLine('\tglobal _start')
        self.headerLine('section .data')
        self.emitLine('')
        self.emitLine('section .text')
        self.emitLine('_start:')
        statements = input['program']['statements']
        for statement in statements:
            if 'print_statement' in statement:
                # SYS_WRITE syscall
                expr_value = self.getExprValue(statement['print_statement']['expression'])
                if 'number' in expr_value:
                    text = expr_value['number']['text']
                    self.headerLine(f'static_{self.staticVarCount}: db "{text}", 0x0A')

                self.emitLine(f'\tmov rax, 1') # SYS_WRITE = 1
                self.emitLine(f'\tmov rdi, 1') # stdout = 1
                self.emitLine(f'\tmov rsi, static_{self.staticVarCount}') # stdout = 1
                self.emitLine(f'\tmov rdx, {len(text) + 1}') # stdout = 1
                self.emitLine(f'\tsyscall')
                self.staticVarCount += 1

        # SYS_EXIT
        self.emitLine(f'')
        self.emitLine(f'\tmov rax, 60')
        self.emitLine(f'\tmov rdi, 69')
        self.emitLine(f'\tsyscall')

    def emit(self, code):
        self.code += code

    def emitLine(self, code):
        self.code += code + '\n'

    def headerLine(self, code):
        self.header += code + '\n'

    def writeFile(self):
        with open(self.fullPath, 'w') as outputFile:
            outputFile.write(self.header + self.code)

    @staticmethod
    def getExprValue(expr: dict):
        assert 'comparison' in expr
        assert 'sum' in expr['comparison']
        assert 'term' in expr['comparison']['sum']
        assert 'unary' in expr['comparison']['sum']['term']
        assert 'value' in expr['comparison']['sum']['term']['unary']
        return expr['comparison']['sum']['term']['unary']['value']


