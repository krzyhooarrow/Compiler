import ply.yacc as yacc
from pip._vendor.distlib.compat import raw_input

from lekser.lex import Lexer


class Grammar(object):
    tokens = Lexer().tokens


    # program -> DECLARE declarations BEGIN commands END
    # 2 | BEGIN commands END

    def p_program_with_libs(p):
        'program : DECLARE declarations BEGIN commands END'
        p[0] = ('DECLARE', p[2], 'BEGIN', p[4], 'END')
        # print(p[0])

    def p_program_without_libs(p):
        'program : BEGIN commands END'
        p[0] = ('BEGIN', p[2], 'END')
        # print(p[0])

    # 4 declarations -> declarations , pidentifier
    # 5 | declarations , pidentifier (num :num )
    # 6 | pidentifier
    # 7 | pidentifier (num :num )

    def p_declarations_multi(p):
        'declarations : declarations COMMA pidentifier'
        p[0] = (p[1], 'COMMA', p[3])

    def p_declarations_multi_pidentifier_num(p):
        'declarations : declarations COMMA pidentifier LEFT_BRACKET NUM COLON NUM RIGHT_BRACKET'
        p[0] = (p[1], 'COMMA', p[3], 'LEFT_BRACKET', p[5], 'COLON', p[7], 'RIGHT_BRACKET')

    def p_declarations_pidentifier(p):
        'declarations : pidentifier'
        p[0] = (p[1])

    def p_declarations_pidentifier_num(p):
        'declarations : pidentifier LEFT_BRACKET NUM COLON NUM RIGHT_BRACKET'
        p[0] = (p[1], 'LEFT_BRACKET', p[3], 'COLON', p[5], 'RIGHT_BRACKET')

    # 9 commands -> commands command
    # 10 | command

    def p_commands_multi(p):
        'commands : commands command'
        p[0] = (p[1], p[2])

    def p_commands_single(p):
        'commands : command'
        p[0] = (p[1])

    # 12 command -> identifier ASSIGN expression ;
    # 13 | IF condition THEN commands ELSE commands ENDIF
    # 14 | IF condition THEN commands ENDIF
    # 15 | WHILE condition DO commands ENDWHILE
    # 16 | DO commands WHILE condition ENDDO
    # 17 | FOR pidentifier FROM value TO value DO commands ENDFOR
    # 18 | FOR pidentifier FROM value DOWNTO value DO commands ENDFOR
    # 19 | READ identifier ;
    # 20 | WRITE value ;

    def p_command_assign(p):
        'command : identifier ASSIGN expression SEMICOLON'
        p[0] = (p[1], 'ASSIGN', p[3], 'SEMICOLON')

    def p_command_if_else(p):
        'command : IF condition THEN commands ELSE commands ENDIF'
        p[0] = ('IF', p[2], 'THEN', p[4], 'ELSE', p[6], 'ENDIF')

    def p_command_if(p):
        'command : IF condition THEN commands ENDIF'
        p[0] = ('IF', p[2], 'THEN', p[4], 'ENDIF')

    def p_command_while_do(p):
        'command : WHILE condition DO commands ENDWHILE'
        p[0] = ('WHILE', p[2], 'DO', p[4], 'ENDWHILE')


    def p_command_do_while(p):
        'command : DO commands WHILE condition ENDDO'
        p[0] = ('DO', p[2], 'WHILE', p[4], 'ENDDO')

    def p_command_from_upto(p):
        'command : FOR pidentifier FROM value TO value DO commands ENDFOR'
        p[0] = ('FOR', p[2], 'FROM', p[4], 'TO', p[6], 'DO', p[8], 'ENDFOR')

    def p_command_from_downto(p):
        'command : FOR pidentifier FROM value DOWNTO value DO commands ENDFOR'
        p[0] = ('FOR', p[2], 'FROM', p[4], 'DOWNTO', p[6], 'DO', p[8], 'ENDFOR')

    def p_command_read(p):
        'command : READ identifier SEMICOLON'
        p[0] = ('READ', p[2], 'SEMICOLON')

    def p_command_write(p):
        'command : WRITE value SEMICOLON'
        p[0] = ('WRITE', p[2], 'SEMICOLON')

    # 21
    # 22 expression -> value
    # 23 | value PLUS value
    # 24 | value MINUS value
    # 25 | value TIMES value
    # 26 | value DIV value
    # 27 | value MOD value

    def p_expression_value(p):
        'expression : value'
        p[0] = (p[1])

    def p_expression_plus(p):
        'expression : value PLUS value'
        p[0] = (p[1], 'PLUS', p[3])

    def p_expression_minus(p):
        'expression : value MINUS value'
        p[0] = (p[1], 'MINUS', p[3])

    def p_expression_times(p):
        'expression : value TIMES value'
        p[0] = (p[1], 'TIMES', p[3])

    def p_expression_div(p):
        'expression : value DIV value'
        p[0] = (p[1], 'DIV', p[3])

    def p_expression_mod(p):
        'expression : value MOD value'
        p[0] = (p[1], 'MOD', p[3])

    # 29 condition -> value EQ value
    # 30 | value NEQ value
    # 31 | value LE value
    # 32 | value GE value
    # 33 | value LEQ value
    # 34 | value GEQ value

    def p_condition_equals(p):
        'condition : value EQ value'
        p[0] = (p[1], 'EQ', p[3])

    def p_condition_not_equals(p):
        'condition : value NEQ value'
        p[0] = (p[1], 'NEQ', p[3])

    def p_condition_less(p):
        'condition : value LE value'
        p[0] = (p[1], 'LE', p[3])

    def p_condition_greater(p):
        'condition : value GE value'
        p[0] = (p[1], 'GE', p[3])

    def p_condition_less_or_equal(p):
        'condition : value LEQ value'
        p[0] = (p[1], 'LEQ', p[3])

    def p_condition_greater_or_equal(p):
        'condition : value GEQ value'
        p[0] = (p[1], 'GEQ', p[3])


    # 36 value -> num
    # 37 | identifier

    def p_value_num(p):
        'value : NUM'
        p[0] = (p[1])

    def p_value_identifier(p):
        'value : identifier'
        p[0] = (p[1])


    # 39 identifier -> pidentifier
    # 40 | pidentifier ( pidentifier )
    # 41 | pidentifier (num )

    def p_identifier_pidentifier(p):
        'identifier : pidentifier'
        p[0] = (p[1])

    def p_identifier_pidentifier_pidentifier(p):
        'identifier : pidentifier LEFT_BRACKET pidentifier RIGHT_BRACKET'
        p[0] = (p[1], 'LEFT_BRACKET', p[3], 'RIGHT_BRACKET')


    def p_identifier_pidentifier_num(p):
        'identifier : pidentifier LEFT_BRACKET NUM RIGHT_BRACKET'
        p[0] = (p[1], 'LEFT_BRACKET', p[3], 'RIGHT_BRACKET')


    def p_error(p):
        print("Syntax error in input!")






    input = '/home/krzyhoo/Desktop/Compiler/examples/program0.imp'
    output = 'output.txt'

    parser = yacc.yacc()
    file = open(input, "r")
    try:
        parsed = parser.parse(file.read(), tracking=True)
    except Exception as e:
        print(e)
        exit()
    fw = open(output, "w")
    print(f'{parsed}')
    fw.write(f'{parsed}')




