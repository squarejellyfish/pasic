from ast import parse
import sys
from typing import Optional, Union
from src.lex import *
from dataclasses import dataclass
from itertools import chain
from collections.abc import Iterable

# TODO: add support for command line args
# TODO: type system

EOF = Token('\0', Symbols.EOF)

def flatten(x):
    if isinstance(x, Iterable):
        return [a for i in x for a in flatten(i)]
    else:
        return [x]

class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.ip = 0  # instruction pointer

        self.symbols: set[str] = set()
        self.macros: dict[str, Macro] = dict()
        self.includes: dict[str, int] = dict()
        self.funcs: dict[str, StatementNode] = dict()
        self.labelsDeclared: set[str] = set()
        self.labelsGotoed: set[str] = set()
        self.funcSymStack: list[list] = [[]]
        self.ast: dict = {}

    # Return true if the current token matches.
    def checkToken(self, kind):
        return kind == self.curToken.kind

    # Return true if the next token matches.
    def checkPeek(self, kind):
        return kind == self.peekToken.kind

    # Try to match current token. If not, error. Advances the current token.
    def match(self, kind):
        if not self.checkToken(kind):
            self.abort(f"Expected {kind.name}, got {repr(self.curToken.text)}")
        self.nextToken()

    def expect(self, kind):
        '''Try to match the token, abort if does not match. Does not advance'''
        if not self.checkToken(kind):
            self.abort(f"Expected {kind.name}, got {repr(self.curToken.text)}")

    # Advances the current token.
    def nextToken(self):
        self.curToken = self.peekToken
        self.peekToken = self.tokens[self.ip] if self.ip != len(
            self.tokens) else Token('\0', Symbols.EOF)
        self.ip += 1

    def abort(self, message):
        self.error(self.curToken, message)
        sys.exit(1)

    def error(self, token: Token, message):
        if token.expandFrom:
            self.error(token.expandFrom, 'expanded from here')
        filename, line, col = token.pos
        eprint(f"{filename}:{line}:{col} Error: " + message)

    def isComparisonOp(self):
        return self.checkToken(Symbols.GT) or self.checkToken(Symbols.GTEQ) or self.checkToken(Symbols.LT) or self.checkToken(Symbols.LTEQ) or self.checkToken(Symbols.EQEQ) or self.checkToken(Symbols.NOTEQ)

    def isShiftOp(self):
        return self.checkToken(Symbols.GTGT) or self.checkToken(Symbols.LTLT)

    def dumpTokens(self):
        print('Dump tokens:')
        for i, token in enumerate(self.tokens):
            print(i, token)

    def init(self):
        self.ip = 0
        self.curToken = EOF
        self.peekToken = EOF
        self.nextToken()
        self.nextToken()  # Call twice ot init curToken and peekToken

    def expandIncludes(self):
        ip = 0
        while ip < len(self.tokens) and self.tokens[ip].kind is not Symbols.EOF:
            token = self.tokens[ip]
            # print(f'current token = {token}')
            if token.kind is Keywords.INCLUDE:
                start = ip
                next_tok = self.tokens[ip + 1]
                filename = next_tok.text
                # print(f'including {filename}')
                if filename not in self.includes:
                    self.includes[filename] = 1
                else:
                    self.includes[filename] += 1

                assert self.includes[filename] < 100, "Include file expansion limit exceeded"
                end = ip + 2
                lexer = Lexer(filename)
                tokens = lexer.lexfile()
                self.tokens[start:end] = tokens[:-1] # exclude EOF
                # print(ip, self.includes[filename])
                continue
            ip += 1

    def expandMacros(self):
        # Register all macro definitions
        keep = []
        while not self.checkToken(Symbols.EOF):
            if self.checkToken(Keywords.MACRO):
                self.nextToken()
                self.expect(Symbols.IDENT)
                text = self.curToken.text
                self.nextToken()
                args, body = [], []
                if self.checkToken(Symbols.LPARENT): # means this is a macro with args
                    self.nextToken()
                    consumed = False
                    while not self.checkToken(Symbols.RPARENT):
                        if not consumed:
                            consumed = True
                        else:
                            self.match(Symbols.COMMA)
                        self.expect(Symbols.IDENT)
                        args.append(self.curToken.text)
                        self.nextToken()
                    self.nextToken()

                while not self.checkToken(Keywords.END):
                    body.append(self.curToken)
                    if self.checkToken(Symbols.BANG):
                        body.pop()
                        self.nextToken()
                        self.expect(Keywords.END)
                        body.append(self.curToken)
                    if self.peekToken.kind is Symbols.EOF:
                        self.abort(f'Macro definition unclosed, forgot an `end`?')
                    self.nextToken()
                self.match(Keywords.END)
                self.macros[text] = Macro(text, args, body, 0)
            else:
                keep.append(self.curToken)
                self.nextToken()
        keep.append(self.curToken)
        self.tokens = keep

        # expansion
        i = 0
        while i < len(keep):
            curr = keep[i]
            if curr.text in self.macros:
                macro = self.macros[curr.text]
                # print(self.macros[curr.text])
                if macro.args:
                    start = i
                    if self.tokens[i + 1].kind is not Symbols.LPARENT:
                        self.error(self.tokens[i + 1], f'Macro {macro.name} expects arguments, found {self.tokens[i + 1]}')
                        sys.exit(1)
                    st = i + 2 # pos of first arg
                    parsed_args = {}
                    for t in range(len(macro.args)):
                        series, delim = [], Symbols.COMMA if t != len(macro.args) - 1 else Symbols.RPARENT
                        while self.tokens[st].kind is not delim:
                            series.append(self.tokens[st])
                            st += 1
                        if t != len(macro.args) - 1: st += 1
                        parsed_args[macro.args[t]] = series
                    if self.tokens[st].kind is not Symbols.RPARENT:
                        self.error(self.tokens[st], f'Expected right parenthese, found {self.tokens[st]}')
                        sys.exit(1)
                    end = st + 1
                    expanded = [parsed_args[token.text] if token.text in parsed_args else token for token in macro.body]
                    expanded = flatten(expanded)
                    expanded = list(map(lambda token: Token(token.text, token.kind, curr.pos, token), expanded))
                    keep[start:end] = expanded
                    # for token in (keep):
                    #     print(token)
                    # raise NotImplementedError('Macro with args')
                else:
                    body = macro.body
                    for j, token in enumerate(body):
                        # new token instance with the pos updated
                        token = Token(token.text, token.kind, curr.pos, token)
                        body[j] = token
                    keep[i:i + 1] = body
                    macro.expandCount += 1
                    assert self.macros[curr.text].expandCount < 1000, "Macros expansion exceeds 1000"
            else:
                i += 1

    # program ::= statements
    def program(self):

        self.expandIncludes()
        self.init()
        self.expandMacros()
        self.init()
        # self.dumpTokens()
        # Strip newlines at start
        while self.checkToken(Symbols.NEWLINE):
            self.nextToken()

        # Parse all the statements
        output = {'program': self.statements()}

        # Check that each label referenced in a GOTO is declared.
        for label in self.labelsGotoed:
            if label not in self.labelsDeclared:
                self.abort("Attempting to GOTO to undeclared label: " + label)
        self.ast = output
        return output

    # statements ::= statement*
    def statements(self) -> dict:
        ret: dict = {'statements': list()}
        while not self.checkToken(Symbols.EOF):
            ret['statements'].append(self.statement())
        return ret

    # statement ::= statement | expression
    def statement(self):
        # Check first token to see which statement

        ret = None
        assert len(Symbols) + len(Keywords) == 46, "Exhaustive handling of operation, notice that not all symbols need to be handled, only those who need a statement"
        # PRINT expression
        if self.checkToken(Keywords.PRINT):
            self.nextToken()
            ret = StatementNode('print_statement', child=self.expression())
        # IF expression THEN {statement} END
        elif self.checkToken(Keywords.IF):
            self.nextToken()
            ret = StatementNode(
                'if_statement', condition=self.expression(), body=list())
            upper, last = ret, ret.body

            self.match(Keywords.THEN)
            self.nl()

            while not self.checkToken(Keywords.END):
                # ELSE IF comparison THEN {statement}
                if self.checkToken(Keywords.ELSE) and self.peekToken.kind is Keywords.IF:
                    self.nextToken()
                    self.nextToken()

                    if upper.alternative == None:
                        upper.alternative = list()
                    d = StatementNode('elseif_statement',
                                      condition=self.comparison(), body=list())
                    upper.alternative.append(d)
                    last = d.body

                    self.match(Keywords.THEN)
                    self.nl()

                # ELSE
                elif self.checkToken(Keywords.ELSE):
                    if upper.alternative == None:
                        upper.alternative = list()
                    d = StatementNode('else_statement', body=list())
                    upper.alternative.append(d)
                    last = d.body
                    self.nextToken()
                    self.nl()

                last.append(self.statement())

            self.match(Keywords.END)
        # WHILE comparison DO nl {statement nl} end nl
        elif self.checkToken(Keywords.WHILE):
            self.nextToken()
            ret = StatementNode('while_statement',
                                condition=self.comparison(), body=list())

            self.match(Keywords.DO)
            self.nl()

            while not self.checkToken(Keywords.END):
                ret.body.append(self.statement())

            self.match(Keywords.END)
        # "GOTO" ident
        elif self.checkToken(Keywords.GOTO):
            self.nextToken()
            self.labelsGotoed.add(self.curToken.text)
            ret = StatementNode(
                'goto_statement', destination=self.curToken.text)
            self.match(Symbols.IDENT)
        # let_statement ::= 'let' ident '=' expression
        #               |   'let' ident '[' expression ']' '=' list_expression
        elif self.checkToken(Keywords.LET):
            self.nextToken()

            # Check if ident in symbols, if not we add it and emit it in headerLine
            if self.curToken.text not in self.symbols:
                self.symbols.add(self.curToken.text)

            ret = StatementNode('let_statement', left=ExpressionNode(
                'ident', text=self.curToken.text))
            self.match(Symbols.IDENT)
            if self.checkToken(Symbols.LBRACKET):
                self.nextToken()
                ret.args = [self.expression()]
                self.match(Symbols.RBRACKET)

            self.match(Symbols.EQ)
            ret.right = self.expression()
        # "IDENT"
        elif self.checkToken(Symbols.IDENT):
            if self.peekToken.kind is Symbols.COLON:
                # Check if this label already exist
                if self.curToken.text in self.labelsDeclared:
                    self.abort(f"Label already exists: {self.curToken.text}")
                self.labelsDeclared.add(self.curToken.text)

                ret = StatementNode('label_statement', text=self.curToken.text)
                self.nextToken()
                self.match(Symbols.COLON)
            else:
                ret = self.expression()
        # 'func' ident '(' args ')' statements 'end'
        elif self.checkToken(Keywords.FUNC):
            self.nextToken()
            ret = StatementNode('func_declaration',
                                text=self.curToken.text, args=[], body=[])
            func_name = self.curToken.text
            self.match(Symbols.IDENT)
            self.match(Symbols.LPARENT)
            consumed, stack = False, []
            while not self.checkToken(Symbols.RPARENT):
                if not consumed:
                    consumed = True
                else:
                    self.match(Symbols.COMMA)
                ret.args.append(ExpressionNode(
                    'ident', text=self.curToken.text))
                stack.append(self.curToken.text)
                self.match(Symbols.IDENT)
            self.match(Symbols.RPARENT)
            self.nl()
            self.funcs[func_name] = ret
            self.funcSymStack.append(stack)
            while not self.checkToken(Keywords.END):
                ret.body.append(self.statement())
            self.funcSymStack.pop()
            self.match(Keywords.END)
        # "return" [expression]
        elif self.checkToken(Keywords.RETURN):
            if self.peekToken.kind is Symbols.NEWLINE:
                self.nextToken()
                ret = StatementNode('return_statement',
                                    value=ExpressionNode('number', text='0'))
            else:
                self.nextToken()
                ret = StatementNode('return_statement',
                                    value=self.expression())
        # 'include' string
        elif self.checkToken(Keywords.INCLUDE):
            raise Exception("include block is not reachable")
        elif self.checkToken(Keywords.BREAK):
            ret = StatementNode('break_statement')
            self.nextToken()
        else:
            ret = self.expression()
            # self.abort(f"Invalid statement at {
            #            self.curToken.text} ({self.curToken.kind.name})")

        self.nl()  # newline
        return ret

    # expression ::= comparison
    def expression(self):
        # 0 or 1 parenthese
        return ExpressionNode('expression', child=self.assignment_expression())

    # assignment_expression ::= comparison '=' expression
    #                       |   comparison
    def assignment_expression(self):
        ret = self.comparison()
        if self.checkToken(Symbols.EQ):
            self.nextToken()
            ret = ExpressionNode('assignment_expression',
                                 left=ret, right=self.expression())
        return ret

    # comparison ::= bor_expr (("==" | "!=" | ">" | ">=" | "<" | "<=") bor_expr)*
    def comparison(self):

        ret = self.bor_expr()
        while self.isComparisonOp():
            ret = BinaryNode(
                'comparison_op', self.curToken.text, left=ret, right=None)
            self.nextToken()
            ret.right = self.bor_expr()

        return ret

    # bor_expr  ::= xor_expr
    #           |  bor_expr "|" xor_expr
    def bor_expr(self):
        ret = self.xor_expr()
        while self.checkToken(Symbols.BOR):
            ret = BinaryNode('bor_op', self.curToken.text,
                             left=ret, right=None)
            self.nextToken()
            ret.right = self.xor_expr()
        return ret

    # xor_expr ::= and_expr
    #           |  xor_expr "^" and_expr
    def xor_expr(self):
        ret = self.band_expr()
        while self.checkToken(Symbols.BXOR):
            ret = BinaryNode('xor_op', self.curToken.text,
                             left=ret, right=None)
            self.nextToken()
            ret.right = self.band_expr()
        return ret

    # band_expr ::= shift_expr ("&" shift_expr)*
    def band_expr(self):
        ret = self.shift_expr()
        while self.checkToken(Symbols.BAND):
            ret = BinaryNode('band_op', self.curToken.text,
                             left=ret, right=None)
            self.nextToken()
            ret.right = self.shift_expr()
        return ret

    # shift_expr ::= sum (("<<" | ">>") sum)*
    def shift_expr(self):
        ret = self.sum()
        while self.isShiftOp():
            ret = BinaryNode('shift_op', self.curToken.text,
                             left=ret, right=None)
            self.nextToken()
            ret.right = self.sum()
        return ret

    # sum ::= term (op term)*
    def sum(self):

        ret = self.term()
        # And then 0 or more +/- and term
        while self.checkToken(Symbols.PLUS) or self.checkToken(Symbols.MINUS):
            ret = BinaryNode('operator', self.curToken.text,
                             left=ret, right=None)
            self.nextToken()
            ret.right = self.term()

        return ret

    # term ::= unary {( "/" | "*" | "%" ) unary}
    def term(self):

        ret = self.unary()
        while self.checkToken(Symbols.SLASH) or self.checkToken(Symbols.ASTERISK) or self.checkToken(Symbols.MOD):
            ret = BinaryNode('operator', self.curToken.text,
                             left=ret, right=None)
            self.nextToken()
            ret.right = self.unary()
        return ret

    # unary ::= ["+" | "-"] primary
    def unary(self):

        if self.checkToken(Symbols.PLUS) or self.checkToken(Symbols.MINUS):
            ret = ExpressionNode('unary_operator', text=self.curToken.text)
            self.nextToken()
            ret.child = self.postfix_expression()
            return ret
        else:
            return self.postfix_expression()

    # primary: (from python grammar)
    #     | primary '.' NAME
    #     | primary genexp
    #     | primary '(' [arguments] ')'
    #     | primary '[' slices ']'
    #     | atom

    # postfix_expression ::= pointer ['(' [expression (',' expression)*] ')']
    #                      | pointer '[' expression ']'
    #                      | pointer
    def postfix_expression(self):
        ret = self.pointer()
        if self.checkToken(Symbols.LBRACKET):
            self.nextToken()
            ret = ExpressionNode('subscript_expression',
                                 child=ret, value=self.expression())
            self.match(Symbols.RBRACKET)
        elif self.checkToken(Symbols.LPARENT):
            self.nextToken()
            ret = ExpressionNode('call_expression', text=ret.text, args=[])
            args_list, consumed = ret.args, False
            while not self.checkToken(Symbols.RPARENT):
                if not consumed:
                    args_list.append(self.expression())
                    consumed = True
                    continue
                self.match(Symbols.COMMA)
                args_list.append(self.expression())
            # TODO: move this to type check (yes we are going to have type checks)
            # if len(args_list) < 1 or len(args_list) > 7:
            #     self.abort(f"Syscall statement expects 1 to 7 args, found {
            #                len(args_list)}")
            self.match(Symbols.RPARENT)

        return ret

    # pointer ::= '*' value
    #           | value
    def pointer(self):
        if self.checkToken(Symbols.ASTERISK):
            self.nextToken()
            ret = ExpressionNode('pointer', child=self.value())
        else:
            ret = self.value()
        return ret

    # value ::= '(' expression ')' | number | string | ident | list
    def value(self):

        if self.checkToken(Symbols.LPARENT):
            self.nextToken()
            ret = self.expression()
            self.match(Symbols.RPARENT)
        elif self.checkToken(Symbols.NUMBER):
            ret = ExpressionNode('number', text=self.curToken.text)
            self.nextToken()
        elif self.checkToken(Symbols.STRING):
            ret = ExpressionNode('string', text=self.curToken.text)
            self.nextToken()
        elif self.checkToken(Symbols.IDENT):
            # Ensure var exists
            if self.curToken.text in self.symbols or \
                    self.curToken.text in self.funcSymStack[-1] or \
                    self.curToken.text in self.funcs or \
                    self.curToken.text in self.macros:
                ret = ExpressionNode('ident', text=self.curToken.text)
                self.nextToken()
            else:
                self.abort(f"Undefined word: {
                           self.curToken.text}")
        elif isinstance(self.curToken.kind, Builtins):
            # TODO: this doesn't make sense?
            ret = ExpressionNode('ident', text=self.curToken.text)
            self.nextToken()
        else:
            ret = self.list_expression()

        return ret

    # list ::= '[' [expression (',' expression)*] ']'
    def list_expression(self):
        if self.checkToken(Symbols.LBRACKET):
            ret = ExpressionNode('list_expression', items=[])
            self.nextToken()
            consumed = False
            while not self.checkToken(Symbols.RBRACKET):
                if not consumed:
                    ret.items.append(self.expression())
                    consumed = True
                    continue
                self.match(Symbols.COMMA)
                ret.items.append(self.expression())
            self.match(Symbols.RBRACKET)

        else:
            self.abort(f"Unexpected token at {repr(self.curToken.text)}: {self.curToken}")

        return ret

    def nl(self):
        # 0 or more newline
        while self.checkToken(Symbols.NEWLINE):
            self.nextToken()


@dataclass
class ExpressionNode:
    typ: str
    text: Optional[str] = None
    items: Optional[list] = None
    args: Optional[list] = None
    child: Optional[Union['ExpressionNode', 'BinaryNode']] = None
    value: Optional[Union['ExpressionNode', 'BinaryNode']] = None
    left: Optional['ExpressionNode'] = None
    right: Optional['ExpressionNode'] = None


@dataclass
class StatementNode:
    typ: str
    text: Optional[str] = None
    args: Optional[list] = None
    child: Optional[Union['ExpressionNode', 'BinaryNode']] = None
    # for if, else, while, func statement
    condition: Optional[ExpressionNode] = None
    body: Optional[list] = None
    alternative: Optional[list] = None
    destination: Optional[str] = None
    # let statement
    left: Optional[ExpressionNode] = None
    right: Optional[ExpressionNode] = None
    # return statement
    value: Optional[ExpressionNode] = None


@dataclass
class BinaryNode:
    typ: str
    text: str
    left: ExpressionNode
    right: ExpressionNode

@dataclass
class Macro:
    name: str
    args: list[str]
    body: list[Token]
    expandCount: int
