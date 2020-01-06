import ply.yacc as yacc
from pip._vendor.distlib.compat import raw_input

from lekser.lex import Lexer


class Grammar(object):
    tokens = Lexer().tokens
    # program -> DECLARE declarations BEGIN commands END
    # 2 | BEGIN commands END

    def p_program_without_libs(p):
        'program : BEGIN command END'
        p[0] = p[1]


    # 3
    # 4 declarations -> declarations , pidentifier
    # 5 | declarations , pidentifier (num :num )
    # 6 | pidentifier
    # 7 | pidentifier (num :num )
    # 8
    # 9 commands -> commands command
    # 10 | command
    # def p_commands_commands(p):
    #     'commands : num'
    #     p[0] = (p[1])

    def p_commands_command(p):
        'command : command command'
        p[0] = (p[1],p[2])

    def p_command_num(p):
        'command : NUM'
        p[0] = p[1]


    # 11
    # 12 command -> identifier ASSIGN expression ;
    # 13 | IF condition THEN commands ELSE commands ENDIF
    # 14 | IF condition THEN commands ENDIF
    # 15 | WHILE condition DO commands ENDWHILE
    # 16 | DO commands WHILE condition ENDDO
    # 17 | FOR pidentifier FROM value TO value DO commands ENDFOR
    # 18 | FOR pidentifier FROM value DOWNTO value DO commands ENDFOR
    # 19 | READ identifier ;
    # 20 | WRITE value ;
    # 21
    # 22 expression -> value
    # 23 | value PLUS value
    # 24 | value MINUS value
    # 25 | value TIMES value
    # 26 | value DIV value
    # 27 | value MOD value
    # 28
    # 29 condition -> value EQ value
    # 30 | value NEQ value
    # 31 | value LE value
    # 32 | value GE value
    # 33 | value LEQ value
    # 34 | value GEQ value
    # 35
    # 36 value -> num
    # 37 | identifier

    # def p_value_num(p):
    #     'value : num'
    #     p[0] = p[1]
    #
    # def p_value_identifier(p):
    #     'value : identifier'
    #     p[0] = p[1]
    # 38
    # 39 identifier -> pidentifier
    # 40 | pidentifier ( pidentifier )
    # 41 | pidentifier (num )

    # def p_identifier(p):
    #     'identifier : pidentifier'
    #     p[0] = p[1]
    #
    # def p_identifier_pidentifier_pidentifier(p):
    #     'identifier : pidentifier LEFT_BRACKET pidentifier RIGHT_BRACKET'
    #     p[0] = p[1]
    #
    #
    # def p_identifier_pidentifier_num(p):
    #     'identifier : pidentifier LEFT_BRACKET NUM RIGHT_BRACKET'
    #     p[0] = p[1]


#
#
# def p_expression_plus(p):
#     'expression : expression PLUS term'
#     p[0] = p[1] + p[3]
#
#
# def p_expression_minus(p):
#     'expression : expression MINUS term'
#     p[0] = p[1] - p[3]
#
#
# def p_expression_term(p):
#     'expression : term'
#     p[0] = p[1]
#
#
# def p_term_times(p):
#     'term : term TIMES factor'
#     p[0] = p[1] * p[3]
#
#
# def p_term_div(p):
#     'term : term DIVIDE factor'
#     p[0] = p[1] / p[3]
#
#
# def p_term_factor(p):
#     'term : factor'
#     p[0] = p[1]
#
#
# def p_factor_num(p):
#     'factor : NUMBER'
#     p[0] = p[1]
#
#
# def p_factor_expr(p):
#     'factor : LPAREN expression RPAREN'
#     p[0] = p[2]

    # Error rule for syntax errors


    def p_error(p):
        print("Syntax error in input!")

        # Build the parser

    data = '''
    5
    '''


    parser = yacc.yacc()

    # while True:
    #     try:
    #         s = raw_input('calc > ')
    #     except EOFError:
    #         break
    #     if not s: continue
    #     result = parser.parse(s)
    #     print(result)


# while True:
#     try:
#         s = raw_input('calc > ')
#     except EOFError:
#         break
#     if not s: continue
#     result = parser.parse(s)
#     print(result)

gramar = Grammar()
