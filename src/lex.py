from enum import Enum, auto
import sys

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


class Lexer:
    def __init__(self, sourceName):
        self.sourceName = sourceName
        with open(self.sourceName, 'r') as file:
            self.source: str = file.read()
        self.curChar: str = ''   # Current character in the string.
        self.curPos: int = -1    # Current position in the string.
        self.curLine: int = 1
        self.linePos: int = 0
        self.nextChar()

    # Process the next character.
    def nextChar(self):
        if self.curChar == '\n':
            self.curLine += 1
            self.linePos = -1
        self.curPos += 1
        self.linePos += 1
        if self.curPos >= len(self.source):
            self.curChar = '\0'
        else:
            self.curChar = self.source[self.curPos]

    # Return the lookahead character.
    def peek(self):
        if self.curPos + 1 >= len(self.source):
            return '\0'

        return self.source[self.curPos + 1]

    # Invalid token found, print error message and exit.
    def abort(self, message):
        eprint(f"{self.sourceName}:{self.curLine}:{
               self.linePos} Lexing error. " + message)
        sys.exit(69)

    # Skip whitespace except newlines, which we will use to indicate the end of a statement.
    def skipWhitespace(self):
        while self.curChar == ' ' or self.curChar == '\t' or self.curChar == '\r':
            self.nextChar()

    # Skip comments in the code.
    def skipComment(self):
        if self.curChar == '/' and self.peek() == '/':
            while self.curChar != '\n':
                self.nextChar()

    # Return the next token.
    def getToken(self):
        self.skipWhitespace()
        self.skipComment()
        token = None

        # Check the first character of this token to see if we can decide what it is.
        # If it is a multiple character operator (e.g., !=), number, identifier, or keyword then we will process the rest.
        assert len(Symbols) == 29, "Exhaustive handling of symbols"
        if self.curChar == '+':
            token = Token(self.curChar, Symbols.PLUS,
                          (self.sourceName, self.curLine, self.linePos))
        elif self.curChar == '-':
            token = Token(self.curChar, Symbols.MINUS,
                          (self.sourceName, self.curLine, self.linePos))
        elif self.curChar == '*':
            token = Token(self.curChar, Symbols.ASTERISK,
                          (self.sourceName, self.curLine, self.linePos))
        elif self.curChar == '/':
            token = Token(self.curChar, Symbols.SLASH,
                          (self.sourceName, self.curLine, self.linePos))
        elif self.curChar == '=':
            # Check if this token is '=' or '==' by peeking the next char
            if self.peek() == '=':
                lastChar = self.curChar
                self.nextChar()
                token = Token(lastChar + self.curChar, Symbols.EQEQ,
                              (self.sourceName, self.curLine, self.linePos))
            else:
                token = Token(self.curChar, Symbols.EQ,
                              (self.sourceName, self.curLine, self.linePos))
        elif self.curChar == '>':
            # Check whether this is token is > or >= or >>
            if self.peek() == '=':
                lastChar = self.curChar
                self.nextChar()
                token = Token(lastChar + self.curChar, Symbols.GTEQ,
                              (self.sourceName, self.curLine, self.linePos))
            elif self.peek() == '>':
                lastChar = self.curChar
                self.nextChar()
                token = Token(lastChar + self.curChar, Symbols.GTGT,
                              (self.sourceName, self.curLine, self.linePos))
            else:
                token = Token(self.curChar, Symbols.GT,
                              (self.sourceName, self.curLine, self.linePos))
        elif self.curChar == '<':
            # Check whether this is token is < or <= or <<
            if self.peek() == '=':
                lastChar = self.curChar
                self.nextChar()
                token = Token(lastChar + self.curChar, Symbols.LTEQ,
                              (self.sourceName, self.curLine, self.linePos))
            elif self.peek() == '<':
                lastChar = self.curChar
                self.nextChar()
                token = Token(lastChar + self.curChar, Symbols.LTLT,
                              (self.sourceName, self.curLine, self.linePos))
            else:
                token = Token(self.curChar, Symbols.LT,
                              (self.sourceName, self.curLine, self.linePos))
        elif self.curChar == '!':
            if self.peek() == '=':
                lastChar = self.curChar
                self.nextChar()
                token = Token(lastChar + self.curChar, Symbols.NOTEQ,
                              (self.sourceName, self.curLine, self.linePos))
            else:
                self.abort("Expected !=, got !" + self.peek())
        elif self.curChar == '"':
            self.nextChar()
            startPos = self.curPos

            while self.curChar != '"':
                self.nextChar()

            text = self.source[startPos:self.curPos]
            token = Token(text, Symbols.STRING,
                          (self.sourceName, self.curLine, self.linePos))
        elif self.curChar == '(':
            token = Token(self.curChar, Symbols.LPARENT,
                          (self.sourceName, self.curLine, self.linePos))
        elif self.curChar == ')':
            token = Token(self.curChar, Symbols.RPARENT,
                          (self.sourceName, self.curLine, self.linePos))
        elif self.curChar.isdigit():
            # Assume this is a number, if not we abort
            # Get all consecutive digits and decimal
            startPos = self.curPos
            while self.peek().isdigit():
                self.nextChar()
            if self.peek() == '.':  # decimal
                self.nextChar()

                if not self.peek().isdigit():
                    self.abort("Illegal character in number: " + self.peek())
                while self.peek().isdigit():
                    self.nextChar()

            text = self.source[startPos:self.curPos + 1]
            token = Token(text, Symbols.NUMBER,
                          (self.sourceName, self.curLine, self.linePos))
        elif self.curChar.isalpha() or self.curChar == '_':
            startPos = self.curPos
            while self.peek().isalpha() or self.peek().isdigit() or self.peek() in ['_', '-']:
                self.nextChar()

            text = self.source[startPos:self.curPos + 1]
            token = Token(text, Token.getKind(text), (self.sourceName, self.curLine, self.linePos))
        elif self.curChar == '\n':
            token = Token(self.curChar, Symbols.NEWLINE,
                          (self.sourceName, self.curLine, self.linePos))
        elif self.curChar == '\0':
            token = Token(self.curChar, Symbols.EOF,
                          (self.sourceName, self.curLine, self.linePos))
        elif self.curChar == ':':
            token = Token(self.curChar, Symbols.COLON,
                          (self.sourceName, self.curLine, self.linePos))
        elif self.curChar == '%':
            token = Token(self.curChar, Symbols.MOD,
                          (self.sourceName, self.curLine, self.linePos))
        elif self.curChar == ',':
            token = Token(self.curChar, Symbols.COMMA,
                          (self.sourceName, self.curLine, self.linePos))
        elif self.curChar == '&':
            token = Token(self.curChar, Symbols.BAND,
                          (self.sourceName, self.curLine, self.linePos))
        elif self.curChar == '|':
            token = Token(self.curChar, Symbols.BOR,
                          (self.sourceName, self.curLine, self.linePos))
        elif self.curChar == '^':
            token = Token(self.curChar, Symbols.BXOR,
                          (self.sourceName, self.curLine, self.linePos))
        elif self.curChar == '#':
            token = Token(self.curChar, Symbols.BANG,
                          (self.sourceName, self.curLine, self.linePos))
        elif self.curChar == '[':
            token = Token(self.curChar, Symbols.LBRACKET,
                          (self.sourceName, self.curLine, self.linePos))
        elif self.curChar == ']':
            token = Token(self.curChar, Symbols.RBRACKET,
                          (self.sourceName, self.curLine, self.linePos))
        else:
            # Unknown token!
            self.abort("Unknown token: " + self.curChar)

        self.nextChar()
        return token

    def lexfile(self):
        tokens = list()
        while True:
            token = self.getToken()
            tokens.append(token)
            if token.kind == Symbols.EOF:
                break
        return tokens


# TokenType is our enum for all the types of tokens.
class Symbols(Enum):
    EOF = auto()
    NEWLINE = auto()
    NUMBER = auto()
    IDENT = auto()
    STRING = auto()
    LPARENT = auto()
    RPARENT = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COLON = auto()
    COMMA = auto()
    BANG = auto()
    EQ = auto()
    PLUS = auto()
    MINUS = auto()
    ASTERISK = auto()
    SLASH = auto()
    EQEQ = auto()
    NOTEQ = auto()
    LT = auto()
    LTEQ = auto()
    GT = auto()
    GTEQ = auto()
    MOD = auto()
    LTLT = auto()  # left shift
    GTGT = auto()  # right shift
    BAND = auto()  # bitwise and
    BOR = auto()  # bitwise or
    BXOR = auto()  # bitwise xor


class Keywords(Enum):
    LABEL = auto()
    GOTO = auto()
    PRINT = auto()
    LET = auto()
    IF = auto()
    THEN = auto()
    END = auto()
    WHILE = auto()
    DO = auto()
    NOT = auto()
    ELSE = auto()
    RETURN = auto()
    DEFINE = auto()
    FUNC = auto()
    INCLUDE = auto()
    MACRO = auto()
    BREAK = auto()

assert len(
    Keywords) == 17, "Exhaustive handling of keywords table, forgot to add support for a keyword?"
KEYWORDS_TABLE = {
    'if': Keywords.IF,
    'label': Keywords.LABEL,
    'goto': Keywords.GOTO,
    'print': Keywords.PRINT,
    'let': Keywords.LET,
    'then': Keywords.THEN,
    'end': Keywords.END,
    'while': Keywords.WHILE,
    'do': Keywords.DO,
    'not': Keywords.NOT,
    'else': Keywords.ELSE,
    'return': Keywords.RETURN,
    'define': Keywords.DEFINE,
    'func': Keywords.FUNC,
    'include': Keywords.INCLUDE,
    'macro': Keywords.MACRO,
    'break': Keywords.BREAK,
}


class Builtins(Enum):
    SYSCALL = auto()
    MEM = auto()


assert len(Builtins) == 2, "Exhaustive handling of builtins table"
BUILTINS_TABLE = {
    'syscall': Builtins.SYSCALL,
    '__mem__': Builtins.MEM,
}


class Token:
    def __init__(self, tokenText, tokenKind, pos=('', 0, 0), expandFrom=None):
        # The token's actual text. Used for identifiers, strings, and numbers.
        self.text = tokenText
        # The TokenType that this token is classified as.
        self.kind = tokenKind
        self.pos = pos
        self.expandFrom = expandFrom

    @staticmethod
    def getKind(text):
        if text  in KEYWORDS_TABLE:
            return KEYWORDS_TABLE[text]
        elif text in BUILTINS_TABLE:
            return BUILTINS_TABLE[text]

        return Symbols.IDENT

    def __str__(self) -> str:
        return f'({self.kind}, {repr(self.text)}, {self.pos}, expandFrom={self.expandFrom})'
