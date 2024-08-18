from lex import *

source = '+= #fuck me\n *"fuck" 123.123 IF x'
lexer = Lexer(source)

token = lexer.getToken()
while token.kind != TokenType.EOF:
    print(token.kind, token.text)
    token = lexer.getToken()
