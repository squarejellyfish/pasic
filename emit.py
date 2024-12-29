# Emitter object keeps track of the generated code and outputs it.
from lex import SYMBOLS_IMPL


class Emitter:
    def __init__(self, fullPath):
        self.fullPath = fullPath
        self.header = ""
        self.ender = ""
        self.code = ""
        self.staticVarCount = 0
        self.stackTable = dict()  # position of var in stack
        self.stack = 8  # reserve 4 bytes for rbp himself
        self.labelTable = {'if': {'count': 0, 'stack': []}, 'if_end': {'count': 0, 'stack': []}, 'while': {
            'count': 0, 'stack': []}, 'while_end': {'count': 0, 'stack': []}}

    def fromdict(self, input: dict = dict()):
        assert 'program' in input
        assert 'statements' in input['program']

        self.headerLine('\tglobal _start')
        self.headerLine('section .data')
        self.emitLine('')
        self.emitLine('section .text')
        self.emitLine('_start:')
        self.emitLine('\tmov rbp, rsp')  # sync stack pointer
        self.emitLine('\tsub rsp, 1024')  # reserve space for stack pointer
        self.enderLine(DUMP)
        statements = input['program']['statements']
        for statement in statements:
            self.emitStatement(statement)

        # SYS_EXIT
        self.emitLine(f'')
        self.emitLine(f'\tmov rax, 60')
        self.emitLine(f'\tmov rdi, 0')
        self.emitLine(f'\tsyscall')

    def emit(self, code):
        self.code += code

    def emitLine(self, code):
        self.code += code + '\n'

    def headerLine(self, code):
        self.header += code + '\n'

    def enderLine(self, code):
        self.ender += code + '\n'

    def writeFile(self):
        with open(self.fullPath, 'w') as outputFile:
            outputFile.write(self.header + self.code + self.ender)

    def emitStatement(self, statement: dict):
        assert SYMBOLS_IMPL == 22, "Exhaustive handling of operation, notice that not all symbols need to be handled here, only those is a statement"
        if 'print_statement' in statement:
            # SYS_WRITE syscall
            self.emitLine(f'\t; -- print_statement --')
            expr_postfix = self.getExprValue(
                statement['print_statement']['expression'])
            if len(expr_postfix) == 1 and 'string' in expr_postfix[0]:
                text = expr_postfix[0]['string']['text']
                self.headerLine(
                    f'static_{self.staticVarCount}: db "{text}", 0x0A')
                self.emitLine(f'\tmov rax, 1')  # SYS_WRITE = 1
                self.emitLine(f'\tmov rdi, 1')  # stdout = 1
                rsi_arg = f'static_{self.staticVarCount}'
                self.emitLine(f'\tmov rsi, {rsi_arg}')  # mem location
                self.emitLine(f'\tmov rdx, {len(text) + 1}')  # length
                self.emitLine(f'\tsyscall')
                self.staticVarCount += 1
            else: # is a number, we call builtin function dump
                self.emitExpr(expr_postfix)
                # result will be at top of stack
                self.emitLine(f'\tpop rdi')
                self.emitLine(f'\tcall dump')
        elif 'write_statement' in statement:
            # SYS_WRITE but only write 1 char
            self.emitLine(f'\t; -- write_statement --')
            args = statement['write_statement']['args']
            assert len(args) == 2, f"Function write only takes 2 args, {len(args)} found."
            left, right = self.getExprValue(args[0]), self.getExprValue(args[1])
            self.emitExpr(right)
            self.emitExpr(left)
            if 'ident' in left[0]:
                self.emitLine(f'\tpop rsi')
            else:
                self.emitLine(f'\tmov rsi, rsp') # rsi takes address
                self.emitLine(f'\tadd rsp, 4')
            self.emitLine(f'\tpop rdx') # pop arg length
            self.emitLine(f'\tmov rax, 1')  # SYS_WRITE = 1
            self.emitLine(f'\tmov rdi, 1')  # stdout = 1
            self.emitLine(f'\tsyscall')
        elif 'let_statement' in statement:
            self.emitLine(f'\t; -- let_statement --')
            left, right_expr = statement['let_statement']['left'], statement['let_statement']['right']
            right_expr = self.getExprValue(right_expr['expression'])
            self.emitExpr(right_expr)
            # result will be at top of stack
            self.emitLine(f'\tpop rax')
            varName, size = left['ident']['text'], 8
            if varName not in self.stackTable:
                self.stackTable[varName] = self.stack
                self.emitLine(f'\tmov QWORD [rbp - {self.stack}], rax')
                self.stack += size
            else:
                self.emitLine(
                    f'\tmov QWORD [rbp - {self.stackTable[varName]}], rax')
        elif 'assign_statement' in statement:
            self.emitLine(f'\t; -- assign_statement')
            left, right_expr = statement['assign_statement']['left'], statement['assign_statement']['right']
            varName, right_expr = left['ident']['text'], self.getExprValue(
                right_expr)
            self.emitExpr(right_expr)
            # result will be at top of stack
            self.emitLine(f'\tpop rax')
            if varName not in self.stackTable:
                assert False, 'Variable cross-reference should be handle in parsing stage'
            else:
                self.emitLine(
                    f'\tmov QWORD [rbp - {self.stackTable[varName]}], rax')
        elif 'label_statement' in statement:
            self.emitLine(f'\t; -- label_statement --')
            text = statement['label_statement']['text']
            self.emitLine(f'{text}:')
        elif 'goto_statement' in statement:
            self.emitLine(f'\t; -- goto_statement')
            dest = statement['goto_statement']['destination']
            self.emitLine(f'\tjmp {dest}')
        elif 'if_statement' in statement:
            self.emitLine(f'\t; -- if_statement')
            condition, body = statement['if_statement']['condition'], statement['if_statement']['body']
            condition = self.getExprValue(condition)
            self.emitExpr(condition)
            # result on top of stack
            self.emitLine(f'\tpop rax')
            self.emitLine(f'\ttest rax, rax')
            self.emitLine(f'\tje IF_{self.labelTable['if']['count']}')
            self.addrStackPush('if')
            for stmt in body:
                self.emitStatement(stmt)
            self.emitLine(f'\tjmp END_{self.labelTable['if_end']['count']}')
            self.addrStackPush('if_end')
            alternative, end = statement['if_statement'].get(
                'alternative', []), False
            for stmt in alternative:
                if 'else_statement' in stmt:
                    end = True
                self.emitStatement(stmt)

            # 'else' will setup end jmp label for us, if no alternative, setup ourself
            if not end:  # no else, but has elif
                addr = self.addrStackPop('if')
                self.emitLine(f'IF_{addr}:')
                addr = self.addrStackPop('if_end')
                self.emitLine(f'END_{addr}:')
            # result will be at top of stack
        elif 'elseif_statement' in statement:
            self.emitLine(f'\t; -- elseif_statement')
            addr = self.addrStackPop('if')
            self.emitLine(f'IF_{addr}:')
            condition, body = statement['elseif_statement']['condition'], statement['elseif_statement']['body']
            condition = self.getExprValue(condition)
            self.emitExpr(condition)
            # result on top of stack
            self.emitLine(f'\tpop rax')
            self.emitLine(f'\ttest rax, rax')
            self.emitLine(f'\tje IF_{self.labelTable['if']['count']}')
            self.addrStackPush('if')
            for stmt in body:
                self.emitStatement(stmt)
            addr = self.addrStackPeek('if_end')
            self.emitLine(f'\tjmp END_{addr}')
        elif 'else_statement' in statement:
            self.emitLine(f'\t; -- else_statement --')
            addr = self.addrStackPop('if')
            self.emitLine(f'IF_{addr}:')
            body = statement['else_statement']['body']
            for stmt in body:
                self.emitStatement(stmt)
            addr = self.addrStackPop('if_end')
            self.emitLine(f'END_{addr}:')
        elif 'while_statement' in statement:
            self.emitLine(f'\t; -- while_statement --')
            self.emitLine(f'WHILE_{self.labelTable['while']['count']}:')
            self.addrStackPush('while')
            condition, body = statement['while_statement']['condition'], statement['while_statement']['body']
            condition = self.getExprValue(condition)
            self.emitExpr(condition)
            # result on top of stack
            self.emitLine(f'\tpop rax')
            self.emitLine(f'\ttest rax, rax')
            self.emitLine(f'\tje END_WHILE_{self.labelTable['while_end']['count']}')
            self.addrStackPush('while_end')
            for stmt in body:
                self.emitStatement(stmt)
            addr = self.addrStackPop('while')
            self.emitLine(f'\tjmp WHILE_{addr}')
            addr = self.addrStackPop('while_end')
            self.emitLine(f'END_WHILE_{addr}:')
        elif 'return_statement' in statement:
            exprs = self.getExprValue(statement['return_statement'])
            self.emitExpr(exprs)
            # result will be at top of stack
            self.emitLine(f'\tmov rax, 60')  # SYS_EXIT
            self.emitLine(f'\tmov rdi, [rsp]')
            self.emitLine(f'\tsyscall')

    def emitExpr(self, exprs: list):
        '''
        Expression result will be at top of stack
        '''
        for expr in exprs:
            if 'number' in expr:
                self.emitLine(f'\tpush {expr['number']['text']}')
            elif 'ident' in expr:
                self.emitLine(
                    f'\tmov rax, [rbp - {self.stackTable[expr['ident']['text']]}]')
                self.emitLine(f'\tpush rax')
            elif 'unary_operator' in expr:
                self.emitLine(f'\tpop rax')
                self.emitLine(f'\tneg rax')
                self.emitLine(f'\tpush rax')
            elif 'operator' in expr:
                operator = expr['operator']
                if operator == '+':  # pop top of stack to rax, and add back to top of stack
                    self.emitLine(f'\tpop rax')
                    self.emitLine(f'\tadd [rsp], rax')
                elif operator == '-':
                    self.emitLine(f'\tpop rax')
                    self.emitLine(f'\tsub [rsp], rax')
                elif operator == '*':
                    self.emitLine(f'\tpop rax')
                    self.emitLine(f'\tpop rbx')
                    self.emitLine(f'\timul rax, rbx')
                    self.emitLine(f'\tpush rax')
                elif operator == '/':
                    self.emitLine(f'\tpop rbx')
                    self.emitLine(f'\tpop rax')
                    self.emitLine(f'\txor rdx, rdx')  # remainder will be here
                    self.emitLine(f'\tidiv rbx')
                    self.emitLine(f'\tpush rax')
                elif operator == '==':
                    self.emitLine(f'\tpop rax')
                    self.emitLine(f'\tpop rbx')
                    self.emitLine(f'\tmov rcx, 0')
                    self.emitLine(f'\tmov rdx, 1')
                    self.emitLine(f'\tcmp rax, rbx')
                    self.emitLine(f'\tcmove rcx, rdx')
                    self.emitLine(f'\tpush rcx')
                elif operator == '%':
                    self.emitLine(f'\tpop rbx')
                    self.emitLine(f'\tpop rax')
                    self.emitLine(f'\txor rdx, rdx')  # remainder will be here
                    self.emitLine(f'\tidiv rbx')
                    self.emitLine(f'\tpush rdx')
                elif operator == '<<':
                    self.emitLine(f'\tpop rcx')
                    self.emitLine(f'\tpop rax')
                    self.emitLine(f'\tshl rax, cl')
                    self.emitLine(f'\tpush rax')
                elif operator == '>>':
                    self.emitLine(f'\tpop rcx')
                    self.emitLine(f'\tpop rax')
                    self.emitLine(f'\tshr rax, cl')
                    self.emitLine(f'\tpush rax')
                elif operator == '|':
                    self.emitLine(f'\tpop rbx')
                    self.emitLine(f'\tpop rax')
                    self.emitLine(f'\tor rax, rbx')
                    self.emitLine(f'\tpush rax')
                elif operator == '&':
                    self.emitLine(f'\tpop rbx')
                    self.emitLine(f'\tpop rax')
                    self.emitLine(f'\tand rax, rbx')
                    self.emitLine(f'\tpush rax')
                elif operator == '^':
                    self.emitLine(f'\tpop rbx')
                    self.emitLine(f'\tpop rax')
                    self.emitLine(f'\txor rax, rbx')
                    self.emitLine(f'\tpush rax')
                elif operator == '<' or operator == '>' or operator == '<=' or operator == '>=':
                    self.emitLine(f'\tpop rbx')
                    self.emitLine(f'\tpop rax')
                    self.emitLine(f'\txor rcx, rcx')
                    self.emitLine(f'\tmov rdx, 1')
                    self.emitLine(f'\tcmp rax, rbx')
                    if operator == '<':
                        self.emitLine(f'\tcmovl rcx, rdx')
                    elif operator == '>':
                        self.emitLine(f'\tcmovg rcx, rdx')
                    elif operator == '<=':
                        self.emitLine(f'\tcmovle rcx, rdx')
                    elif operator == '>=':
                        self.emitLine(f'\tcmovge rcx, rdx')
                    self.emitLine(f'\tpush rcx')
                else:
                    raise NotImplementedError(f'Operation {operator} is not implemented')
            elif 'string' in expr:
                if len(exprs) == 1:
                    self.headerLine(
                        f'static_{self.staticVarCount}: db "{expr['string']['text']}", 0x0A')
                    self.headerLine(
                        f'static_{self.staticVarCount}_len: equ $-static_{self.staticVarCount}')
                    self.emitLine(f'\tpush static_{self.staticVarCount}')
                    self.staticVarCount += 1
                else:
                    raise NotImplementedError(
                        'String operation is not implemented')
            else:
                raise NotImplementedError(f'Operation {expr} is not implemented')

    def addrStackPush(self, key: str):
        self.labelTable[key]['stack'].append(self.labelTable[key]['count'])
        self.labelTable[key]['count'] += 1

    def addrStackPop(self, key: str):
        return self.labelTable[key]['stack'].pop(-1)

    def addrStackPeek(self, key: str):
        return self.labelTable[key]['stack'][-1]

    @staticmethod
    def getExprValue(expr: dict):
        ret = []

        def get(expr: dict):
            items = list(expr.keys())
            if len(items) == 1:
                if 'number' in expr or 'string' in expr or 'ident' in expr:
                    ret.append(expr)
                    return
                get(expr[items[0]])
            elif len(items) == 2:  # unary operation
                get(expr['arg'])
                if expr['text'] == '-':
                    if 'number' in ret[-1]:
                        ret[-1]['number']['text'] = f'-{ret[-1]['number']['text']}'
                    else:
                        ret.append({'unary_operator': expr['text']})
            elif len(items) == 3:
                get(expr['left'])
                get(expr['right'])
                ret.append({'operator': expr['text']})
            return
        get(expr)
        return ret


DUMP = '''
dump:
    push    rbp
    mov     rbp, rsp
    sub     rsp, 64
    mov     DWORD  [rbp-52], edi
    mov     DWORD  [rbp-4], 1
    mov     eax, DWORD  [rbp-52]
    shr     eax, 31
    movzx   eax, al
    mov     DWORD  [rbp-8], eax
    cmp     DWORD  [rbp-8], 0
    je      .L2
    neg     DWORD  [rbp-52]
.L2:
    mov     BYTE  [rbp-17], 10
.L3:
    mov     edx, DWORD  [rbp-52]
    movsx   rax, edx
    imul    rax, rax, 1717986919
    shr     rax, 32
    mov     ecx, eax
    sar     ecx, 2
    mov     eax, edx
    sar     eax, 31
    sub     ecx, eax
    mov     eax, ecx
    sal     eax, 2
    add     eax, ecx
    add     eax, eax
    mov     ecx, edx
    sub     ecx, eax
    mov     eax, ecx
    lea     edx, [rax+48]
    mov     eax, 31
    sub     eax, DWORD  [rbp-4]
    cdqe
    mov     BYTE  [rbp-48+rax], dl
    add     DWORD  [rbp-4], 1
    mov     eax, DWORD  [rbp-52]
    movsx   rdx, eax
    imul    rdx, rdx, 1717986919
    shr     rdx, 32
    mov     ecx, edx
    sar     ecx, 2
    cdq
    mov     eax, ecx
    sub     eax, edx
    mov     DWORD  [rbp-52], eax
    cmp     DWORD  [rbp-52], 0
    jne     .L3
    cmp     DWORD  [rbp-8], 0
    je      .L4
    mov     eax, DWORD  [rbp-4]
    lea     edx, [rax+1]
    mov     DWORD  [rbp-4], edx
    mov     edx, 31
    sub     edx, eax
    movsx   rax, edx
    mov     BYTE  [rbp-48+rax], 45
.L4:
    mov     eax, DWORD  [rbp-4]
    cdqe
    mov     edx, 32
    sub     edx, DWORD  [rbp-4]
    lea     rcx, [rbp-48]
    movsx   rdx, edx
    add     rcx, rdx
    mov     rdx, rax
    mov     rsi, rcx
    mov     edi, 1
    mov rax, 1
    syscall
    nop
    leave
    ret
'''
