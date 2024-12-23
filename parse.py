import sys
from lex import *

# Parser object keeps track of current token and checks if the code matches the grammar.


class Parser:
    def __init__(self, lexer):
        self.lexer: Lexer = lexer

        self.symbols = set()
        self.labelsDeclared = set()
        self.labelsGotoed = set()

        self.curToken = None
        self.peekToken = None
        self.nextToken()
        self.nextToken()  # Call twice ot init curToken and peekToken

    # Return true if the current token matches.
    def checkToken(self, kind):
        return kind == self.curToken.kind

    # Return true if the next token matches.
    def checkPeek(self, kind):
        return kind == self.peekToken.kind

    # Try to match current token. If not, error. Advances the current token.
    def match(self, kind):
        if not self.checkToken(kind):
            self.abort(f"Expected {kind.name}, got {self.curToken.text}")
        self.nextToken()

    # Advances the current token.
    def nextToken(self):
        self.curToken = self.peekToken
        self.peekToken = self.lexer.getToken()

    def abort(self, message):
        eprint(f"{self.lexer.sourceName}:{self.curToken.curLine}:{
               self.curToken.linePos} Error: " + message)
        sys.exit(69)

    def isComparisonOp(self):
        return self.checkToken(TokenType.GT) or self.checkToken(TokenType.GTEQ) or self.checkToken(TokenType.LT) or self.checkToken(TokenType.LTEQ) or self.checkToken(TokenType.EQEQ) or self.checkToken(TokenType.NOTEQ)

    # program ::= statements
    def program(self):

        # Strip newlines at start
        while self.checkToken(TokenType.NEWLINE):
            self.nextToken()

        # Parse all the statements
        output = {'program': self.statements()}

        # Check that each label referenced in a GOTO is declared.
        for label in self.labelsGotoed:
            if label not in self.labelsDeclared:
                self.abort("Attempting to GOTO to undeclared label: " + label)
        return output

    # statements ::= statement*
    def statements(self):
        ret = {'statements': list()}
        while not self.checkToken(TokenType.EOF):
            ret['statements'].append(self.statement())
        return ret

    def statement(self):
        # Check first token to see which statement

        ret = None
        # PRINT expression
        if self.checkToken(TokenType.print):
            ret = {'print_statement': None}
            self.nextToken()

            ret['print_statement'] = self.expression()
        # IF expression THEN {statement} END
        elif self.checkToken(TokenType.if_):
            self.nextToken()
            ret = {
                'if_statement': {
                    'condition': self.expression(),
                    'body': list(),
                }
            }
            upper, last = ret['if_statement'], ret['if_statement']['body']

            self.match(TokenType.then)
            self.nl()

            while not self.checkToken(TokenType.end):
                # ELSE IF comparison THEN {statement}
                if self.checkToken(TokenType.else_) and self.peekToken.kind is TokenType.if_:
                    self.nextToken()
                    self.nextToken()

                    if 'alternative' not in upper:
                        upper['alternative'] = list()
                    d = {'elseif_statement': {
                        'condition': self.comparison(),
                        'body': list(),
                    }}
                    upper['alternative'].append(d)
                    last = d['elseif_statement']['body']

                    self.match(TokenType.then)
                    self.nl()

                # ELSE
                elif self.checkToken(TokenType.else_):
                    if 'alternative' not in upper:
                        upper['alternative'] = list()
                    d = {'else_statement': {
                        'body': list(),
                    }}
                    upper['alternative'].append(d)
                    last = d['else_statement']['body']
                    self.nextToken()
                    self.nl()

                last.append(self.statement())

            self.match(TokenType.end)
        # WHILE comparison DO nl {statement nl} end nl
        elif self.checkToken(TokenType.while_):
            self.nextToken()
            ret = {
                'while_statement': {
                    'condition': self.comparison(),
                    'body': list(),
                }
            }

            self.match(TokenType.do)
            self.nl()

            while not self.checkToken(TokenType.end):
                ret['while_statement']['body'].append(self.statement())

            self.match(TokenType.end)
        # "GOTO" ident
        elif self.checkToken(TokenType.goto):
            self.nextToken()
            self.labelsGotoed.add(self.curToken.text)
            ret = {
                'goto_statement': {'destination': self.curToken.text}
            }
            self.match(TokenType.IDENT)
        # "LET" ident "=" expression
        elif self.checkToken(TokenType.let):
            self.nextToken()

            # Check if ident in symbols, if not we add it and emit it in headerLine
            if self.curToken.text not in self.symbols:
                self.symbols.add(self.curToken.text)

            ret = {'left': {
                'ident': {'text': self.curToken.text}
            }}
            self.match(TokenType.IDENT)
            self.match(TokenType.EQ)
            ret['right'] = self.expression()
            ret = {'let_statement': ret}
        # "INPUT" ident
        elif self.checkToken(TokenType.input):
            self.abort(f'Input statement is not implemented')
            # print("STATEMENT-INPUT")
            # self.nextToken()
            #
            # # Check if ident in symbols, if not we add it
            # if self.curToken.text not in self.symbols:
            #     self.symbols.add(self.curToken.text)
            #
            # # Emit scanf but also validate the input. If invalid, set the variable to 0 and clear the input.
            # self.match(TokenType.IDENT)
        # "IDENT"
        elif self.checkToken(TokenType.IDENT):
            # "IDENT" = expression
            if self.peekToken.kind is TokenType.EQ:
                ret = {'left': {
                    'ident': {'text': self.curToken.text}
                }}
                self.nextToken()
                self.nextToken()
                ret['right'] = self.expression()
                ret = {'assign_statement': ret}
            elif self.peekToken.kind is TokenType.COLON:

                # Check if this label already exist
                if self.curToken.text in self.labelsDeclared:
                    self.abort(f"Label already exists: {self.curToken.text}")
                self.labelsDeclared.add(self.curToken.text)

                ret = {
                    'label_statement': {'text': self.curToken.text}
                }
                self.nextToken()
                self.match(TokenType.COLON)
            else:
                ret = self.expression()
        # "return" [expression]
        elif self.checkToken(TokenType.return_):
            if self.peekToken.kind is TokenType.NEWLINE:
                self.nextToken()
                ret = {'return_statement': {'value': {'number': {'text': '0'}}}}
            else:
                self.nextToken()
                ret = {'return_statement': {'value': self.expression()}}
        else:
            self.abort(f"Invalid statement at {
                       self.curToken.text} ({self.curToken.kind.name})")

        self.nl()  # newline
        return ret

    # expression ::= comparison
    def expression(self):
        # 0 or 1 parenthese
        ret = {'expression': self.comparison()}
        return ret

    # comparison ::= sum (("==" | "!=" | ">" | ">=" | "<" | "<=") sum)*
    def comparison(self):

        ret = self.sum()
        while self.isComparisonOp():
            ret = {'comparison_op': {
                'text': self.curToken.text,
                'left': ret,
            }}
            self.nextToken()
            ret['comparison_op']['right'] = self.sum()

        return {'comparison': ret}

    # sum ::= term (op term)*
    def sum(self):

        ret = self.term()
        # And then 0 or more +/- and term
        while self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
            ret = {
                'operator': {
                    'text': self.curToken.text,
                    'left': ret,
                }
            }
            self.nextToken()
            ret['operator']['right'] = self.term()

        return {'sum': ret}

    # term ::= unary {( "/" | "*" ) unary}
    def term(self):

        ret = self.unary()
        while self.checkToken(TokenType.SLASH) or self.checkToken(TokenType.ASTERISK):
            ret = {
                'operator': {
                    'text': self.curToken.text,
                    'left': ret,
                }
            }
            self.nextToken()
            ret['operator']['right'] = self.unary()
        return {'term': ret}

    # unary ::= ["+" | "-"] value
    def unary(self):

        if self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
            ret = {
                'unary_operator': {
                    'text': self.curToken.text,
                }
            }
            self.nextToken()
            ret['unary_operator']['arg'] = self.value()
            return {'unary': ret}
        else:
            return {'unary': self.value()}

    # value ::= '(' expression ')' | number | string | ident
    def value(self):

        if self.checkToken(TokenType.LPARENT):
            self.nextToken()
            ret = self.expression()
            self.match(TokenType.RPARENT)
        elif self.checkToken(TokenType.NUMBER):
            ret = {'number': {
                'text': self.curToken.text
            }}
            self.nextToken()
        elif self.checkToken(TokenType.STRING):
            ret = {'string': {
                'text': self.curToken.text,
            }}
            self.nextToken()
        elif self.checkToken(TokenType.IDENT):
            # Ensure var exists
            if self.curToken.text not in self.symbols:
                self.abort(f"Referencing variable before assignment: {
                           self.curToken.text}")
            ret = {'ident': {
                'text': self.curToken.text
            }}
            self.nextToken()
        else:
            self.abort(f"Unexpected token at {self.curToken.text}")
        return {'value': ret}

    def nl(self):

        # Need at least one newline
        self.match(TokenType.NEWLINE)
        # But more is fine too
        while self.checkToken(TokenType.NEWLINE):
            self.nextToken()
