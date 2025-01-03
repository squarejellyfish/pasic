# Emitter object keeps track of the generated code and outputs it.
from src.parse import BinaryNode, ExpressionNode, StatementNode
from src.lex import Symbols, Keywords
from typing import Union
from math import log2, ceil

Node = BinaryNode | ExpressionNode | StatementNode

# TODO: list re-assignment will reallocate new list, old list is memory leaked (this is actually fine?)
# TODO: list init with [] will cause weird behaviors

class Emitter:
    def __init__(self, fullPath):
        self.fullPath = fullPath
        self.header = ""
        self.ender = ""
        self.codeheader = ""
        self.code = ""
        self.staticVarCount = 0
        self.stackTable = dict()  # position of var in stack
        self.stack = 8  # reserve 8 bytes for rbp himself
        self.labelTable = {'if': {'count': 0, 'stack': []}, 'if_end': {'count': 0, 'stack': []}, 'while': {
            'count': 0, 'stack': []}, 'while_end': {'count': 0, 'stack': []}}

    def fromdict(self, input: dict = dict()):
        assert 'program' in input
        assert 'statements' in input['program']

        self.headerLine('\tglobal _start')
        # self.headerLine('section .bss')
        # self.headerLine('mem: resb 6400000')
        self.headerLine('section .data')
        self.codeHeader('')
        self.codeHeader('section .text')
        self.codeHeader('_start:')
        self.codeHeader('\tmov rbp, rsp')  # sync stack pointer
        self.enderLine(DUMP)
        statements = input['program']['statements']
        for statement in statements:
            self.emitStatement(statement)
        stack_padding = 2**ceil(log2(self.stack))
        self.codeHeader(f'\tsub rsp, {stack_padding}')  # reserve space for stack pointer

        # SYS_EXIT
        self.emitLine(f'')
        self.emitLine(f'\tmov rax, 60')
        self.emitLine(f'\tmov rdi, 0')
        self.emitLine(f'\tsyscall')

    def emit(self, code):
        self.code += code

    def emitLine(self, code):
        self.code += code + '\n'

    def codeHeader(self, code):
        self.codeheader += code + '\n'

    def headerLine(self, code):
        self.header += code + '\n'

    def enderLine(self, code):
        self.ender += code + '\n'

    def writeFile(self):
        with open(self.fullPath, 'w') as outputFile:
            outputFile.write(self.header + self.codeheader + self.code + self.ender)

    def emitStatement(self, statement: Union[StatementNode, ExpressionNode, BinaryNode]):
        assert len(Symbols) + len(Keywords) == 44, "Exhaustive handling of operation, notice that not all symbols need to be handled here, only those is a statement"
        if isinstance(statement, StatementNode):
            if statement.typ == 'print_statement':
                # SYS_WRITE syscall
                self.emitLine(f'\t; -- print_statement --')
                expr_postfix = self.getExprValue(
                    statement.child)
                if len(expr_postfix) == 1 and expr_postfix[0].typ == 'string':
                    text = bytes(expr_postfix[0].text.encode('utf-8')).decode('unicode_escape')
                    output = ', '.join([hex(ord(char)) for char in text])
                    self.headerLine(
                        f'static_{self.staticVarCount}: db {output}')
                    self.emitLine(f'\tmov rax, 1')  # SYS_WRITE = 1
                    self.emitLine(f'\tmov rdi, 1')  # stdout = 1
                    rsi_arg = f'static_{self.staticVarCount}'
                    self.emitLine(f'\tmov rsi, {rsi_arg}')  # mem location
                    self.emitLine(f'\tmov rdx, {len(text)}')  # length
                    self.emitLine(f'\tsyscall')
                    self.staticVarCount += 1
                else: # is a number, we call builtin function dump
                    self.emitExpr(expr_postfix)
                    # result will be at top of stack
                    self.emitLine(f'\tpop rdi')
                    self.emitLine(f'\tcall dump')
            elif statement.typ == 'write_statement':
                # SYS_WRITE but only write 1 char
                self.emitLine(f'\t; -- write_statement --')
                args = statement.args
                left, right = self.getExprValue(args[0]), self.getExprValue(args[1])
                self.emitExpr(right)
                self.emitExpr(left)
                if left[0].typ == 'ident':
                    self.emitLine(f'\tpop rsi')
                else:
                    self.emitLine(f'\tmov rsi, rsp') # rsi takes address
                    self.emitLine(f'\tadd rsp, 8')
                self.emitLine(f'\tpop rdx') # pop arg length
                self.emitLine(f'\tmov rax, 1')  # SYS_WRITE = 1
                self.emitLine(f'\tmov rdi, 1')  # stdout = 1
                self.emitLine(f'\tsyscall')
            elif statement.typ == 'let_statement':
                self.emitLine(f'\t; -- let_statement --')
                left, right_expr = statement.left, statement.right
                right_expr = self.getExprValue(right_expr)
                self.emitExpr(right_expr) # pointer to the list will be on top of stack
                self.emitLine(f'\tpop rax')
                varName, size = left.text, 8
                if statement.args: # means that this is list init statement
                    arg = statement.args[0]
                    arg = Emitter.evalExpr(arg)
                    size = arg * 8
                    self.allocVariable(varName, size)
                else:
                    varName, size = left.text, 8
                    self.allocVariable(varName, size)
            elif statement.typ == 'label_statement':
                self.emitLine(f'\t; -- label_statement --')
                text = statement['label_statement']['text']
                self.emitLine(f'{text}:')
            elif statement.typ == 'goto_statement':
                self.emitLine(f'\t; -- goto_statement')
                dest = statement['goto_statement']['destination']
                self.emitLine(f'\tjmp {dest}')
            elif statement.typ == 'if_statement':
                self.emitLine(f'\t; -- if_statement')
                condition, body = statement.condition, statement.body
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
                alternative, end = statement.alternative if statement.alternative else [], False
                for stmt in alternative:
                    if stmt.typ == 'else_statement':
                        end = True
                    self.emitStatement(stmt)

                # 'else' will setup end jmp label for us, if no alternative, setup ourself
                if not end:  # no else, but has elif
                    addr = self.addrStackPop('if')
                    self.emitLine(f'IF_{addr}:')
                    addr = self.addrStackPop('if_end')
                    self.emitLine(f'END_{addr}:')
                # result will be at top of stack
            elif statement.typ == 'elseif_statement':
                self.emitLine(f'\t; -- elseif_statement')
                addr = self.addrStackPop('if')
                self.emitLine(f'IF_{addr}:')
                condition, body = statement.condition, statement.body
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
            elif statement.typ == 'else_statement':
                self.emitLine(f'\t; -- else_statement --')
                addr = self.addrStackPop('if')
                self.emitLine(f'IF_{addr}:')
                body = statement.body
                for stmt in body:
                    self.emitStatement(stmt)
                addr = self.addrStackPop('if_end')
                self.emitLine(f'END_{addr}:')
            elif statement.typ == 'while_statement':
                self.emitLine(f'\t; -- while_statement --')
                self.emitLine(f'WHILE_{self.labelTable['while']['count']}:')
                self.addrStackPush('while')
                condition, body = statement.condition, statement.body
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
            elif statement.typ == 'return_statement':
                exprs = self.getExprValue(statement['return_statement'])
                self.emitExpr(exprs)
                # result will be at top of stack
                self.emitLine(f'\tmov rax, 60')  # SYS_EXIT
                self.emitLine(f'\tmov rdi, [rsp]')
                self.emitLine(f'\tsyscall')
            elif statement.typ == 'pointer_assignment':
                # TODO: deprecate this
                left, right = statement.left, statement.right
                left, right = self.getExprValue(left), self.getExprValue(right)
                self.emitExpr(left[:-1])
                # result (address) will be on the top of stack
                self.emitExpr(right)
                self.emitLine('\tpop rdx')
                self.emitLine('\tpop rax') # contains the address
                self.emitLine('\tmov QWORD [rax], rdx')
                # print(left)
                # raise NotImplementedError('Pointer assignment is not implemented yet')
        else:
            expr = self.getExprValue(statement)
            self.emitExpr(expr)

    def emitExpr(self, exprs: list):
        '''
        Expression result will be at top of stack
        '''
        for expr in exprs:
            if expr.typ == 'number':
                self.emitLine(f'\tpush {expr.text}')
            elif expr.typ == 'ident':
                self.emitLine(
                    f'\tmov rax, [rbp - {self.stackTable[expr.text]}]')
                self.emitLine(f'\tpush rax')
            elif expr.typ == 'unary_operator':
                self.emitLine(f'\tpop rax')
                self.emitLine(f'\tneg rax')
                self.emitLine(f'\tpush rax')
            elif expr.typ == 'operator':
                operator = expr.text
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
            elif expr.typ == 'string':
                if len(exprs) == 1:
                    text = bytes(expr.text.encode('utf-8')).decode('unicode_escape')
                    text += '\0'
                    output = ', '.join([hex(ord(char)) for char in text])
                    self.headerLine(
                        f'static_{self.staticVarCount}: db {output}')
                    self.headerLine(
                        f'static_{self.staticVarCount}_len: equ $-static_{self.staticVarCount}')
                    self.emitLine(f'\tpush static_{self.staticVarCount}')
                    self.staticVarCount += 1
                else:
                    raise NotImplementedError(
                        'String operation is not implemented')
            elif expr.typ == 'call_expression':
                name, argc = expr.text, len(expr.args)
                if name == 'syscall':
                    convention = ['rax', 'rdi', 'rsi', 'rdx', 'r10', 'r8', 'r9']
                    for i in reversed(range(argc)):
                        self.emitLine(f'\tpop {convention[i]}')
                    self.emitLine('\tsyscall')
                    self.emitLine('\tpush rax') # push result on to the stack
                else:
                    raise NotImplementedError(f"Call expression {name} is not implemented")
            elif expr.typ == 'list_expression':
                exprs = expr.items
                # print(exprs)
                for expr in exprs:
                    self.emitExpr(expr)
                # there will be len(exprs) vars on stack after above
                # the following allocates len(exprs) vars and then push the pointer to the first element on top of the stack
                for i in range(len(exprs)):
                    self.emitLine('\tpop rax')
                    if i == (len(exprs) - 1):
                        self.emitLine(f'\tmov rbx, rbp')
                        self.emitLine(f'\tsub rbx, {self.stack}')
                        self.emitLine(f'\tpush rbx')
                    self.allocStack(self.stack, 8)
            elif expr.typ == 'assignment_expression':
                self.emitLine(f'\t; -- assignment_expression --')
                left, right = expr.left, expr.right
                left, right = self.getExprValue(left), self.getExprValue(right)
                self.emitExpr(right)
                # result will be at top of stack
                if len(left) == 1:
                    if left[0].typ == 'ident':
                        self.emitLine(f'\tpop rax')
                        varName = left[0].text
                        if varName not in self.stackTable:
                            print(f'{varName} is not in stack table, {expr=}')
                            assert False, 'Variable cross-reference should be handle in parsing stage'
                        else:
                            self.allocStack(self.stackTable[varName], 0)
                    elif left[0].typ == 'subscript_expression':
                        value, child = self.getExprValue(left[0].value), left[0].child
                        assert child.typ == 'ident', "Subcript other than identifiers are not implemented"
                        varName = child.text
                        assert varName in self.stackTable, "Variable cross-reference should be handle in parsing stage"
                        self.emitExpr(value)
                        self.emitLine(f'\tpop rax') # subscript value
                        self.emitLine(f'\tlea rdx, [rbp-{self.stackTable[varName] - 8}+rax*8]') # rdx contains address now
                        self.emitLine(f'\tpop rbx') # rhs
                        self.emitLine(f'\tmov QWORD [rdx], rbx')
                        self.emitLine(f'\tpush rbx')
                        # print(child)
                        # raise NotImplementedError('In subscript_expression')
                elif left[-1].typ == 'pointer':
                    self.emitExpr(left[:-1]) # omit pointer (deref) operation
                    # result (address) will be on the top of stack
                    self.emitLine('\tpop rdx') # contains the address
                    self.emitLine('\tpop rax')
                    self.emitLine('\tmov QWORD [rdx], rax')
                    self.emitLine('\tpush rax')
                else:
                    raise NotImplementedError('assignment_expression in emitExpr')
            elif expr.typ == 'subscript_expression':
                value, child = self.getExprValue(expr.value), expr.child
                assert child.typ == 'ident', "Subcript other than identifiers are not implemented"
                varName = child.text
                assert varName in self.stackTable, "Variable cross-reference should be handle in parsing stage"
                self.emitExpr(value)
                self.emitLine(f'\tpop rax') # subscript value
                self.emitLine(f'\tlea rdx, [rbp-{self.stackTable[varName] - 8}+rax*8]') # rdx contains address now
                self.emitLine(f'\tpush QWORD [rdx]')
                # raise NotImplementedError('subscript_expression in emitExpr')
            elif expr.typ == 'pointer':
                self.emitLine('\tpop rax')
                self.emitLine('\tpush QWORD [rax]')
            else:
                raise NotImplementedError(f'Operation {expr} is not implemented')

    def addrStackPush(self, key: str):
        self.labelTable[key]['stack'].append(self.labelTable[key]['count'])
        self.labelTable[key]['count'] += 1

    def addrStackPop(self, key: str):
        return self.labelTable[key]['stack'].pop(-1)

    def addrStackPeek(self, key: str):
        return self.labelTable[key]['stack'][-1]

    def allocVariable(self, varName: str, size: int):
        ''' Allocate variable in rax on the stack '''
        if varName not in self.stackTable:
            self.stackTable[varName] = self.stack
            self.allocStack(self.stack, size)
        else:
            self.allocStack(self.stackTable[varName], 0)

    def allocStack(self, pos: int, size: int):
        self.emitLine(f'\tmov QWORD [rbp - {pos}], rax')
        self.stack += size

    @staticmethod
    def evalExpr(expr: ExpressionNode | BinaryNode) -> int:
        if expr.typ in ['number']:
            return int(expr.text)
        elif expr.typ == 'unary_operator':  # unary operation
            arg = Emitter.evalExpr(expr.arg)
            if expr.text == '-':
                return -arg
        elif isinstance(expr, ExpressionNode):
            return Emitter.evalExpr(expr.child)
        elif isinstance(expr, BinaryNode):
            left = Emitter.evalExpr(expr.left)
            right = Emitter.evalExpr(expr.right)
            return eval(f'{left} {expr.text} {right}')
        else:
            raise NotImplementedError(f'evalExpr only supports evaluating integer arithmetics right now')

    @staticmethod
    def getExprValue(expr: ExpressionNode | BinaryNode):
        ret = []

        def get(expr: ExpressionNode):
            if expr.typ in ['number', 'string', 'ident']:
                ret.append(expr)
                return
            elif expr.typ == 'list_expression':
                elements, list_ret = expr.items, ExpressionNode('list_expression', items=[])
                for element in elements:
                    # get(element)
                    element = Emitter.getExprValue(element)
                    list_ret.items.append(element)
                ret.append(list_ret)
                return
            elif expr.typ == 'pointer':
                get(expr.child)
                ret.append(ExpressionNode('pointer'))
                # print(ret)
                return
            elif expr.typ == 'unary_operator':  # unary operation
                get(expr.arg)
                if expr.text == '-':
                    if ret[-1].typ == 'number':
                        ret[-1].text = f'-{ret[-1]['number']['text']}'
                    else:
                        ret.append(ExpressionNode('unary_operator'))
                        # ret.append({'unary_operator': expr['text']})
            elif expr.typ == 'call_expression': # call expression
                args = expr.args
                text = expr.text
                if text == 'syscall':
                    assert len(args) > 0 and len(args) <= 7, f"Syscall statement expects 1 to 7 args, found {len(args)}"
                    for arg in args: get(arg)
                    ret.append(expr)
            elif expr.typ == 'assignment_expression':
                ret.append(expr)
                return 
            elif expr.typ == 'subscript_expression':
                ret.append(expr)
                return
            elif isinstance(expr, ExpressionNode):
                get(expr.child)
            elif isinstance(expr, BinaryNode):
                get(expr.left)
                get(expr.right)
                ret.append(ExpressionNode('operator', text=expr.text))
            else:
                raise NotImplementedError(f'{expr}')
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
