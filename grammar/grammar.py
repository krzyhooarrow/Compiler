import os
import re

import ply.yacc as yacc
from pip._vendor.distlib.compat import raw_input
from lekser.lex import Lexer

tokens = Lexer().tokens
replacement = ['JZERO', 'JNEG', 'JPOS', 'JUMP']
variables = {}  # contains var name and address
# temporary_variables = {} # contains loop iterators
arrays = {}  # contains array name and its address
initialized_variables = set()  # contains already initialized vars
current_instruction = 0
temp_vars = set()
register_number = 1  # memory counter


########################################################################################################################
# Declaring 10 temporary registers

########################################################################################################################
# program -> DECLARE declarations BEGIN commands END
# 2 | BEGIN commands END
########################################################################################################################
def p_program_with_libs(p):
    'program : DECLARE declarations BEGIN commands END'
    p[0] = str(p[4][0]) + '\nHALT'


def p_program_without_libs(p):
    'program : BEGIN commands END'
    p[0] = p[2][0] + '\nHALT'


########################################################################################################################
# 4 declarations -> declarations , pidentifier
# 5 | declarations , pidentifier (num :num )
# 6 | pidentifier
# 7 | pidentifier (num :num )
########################################################################################################################
def p_declarations_next_variable(p):
    'declarations : declarations COMMA pidentifier'
    new_variable(p[3], str(p.lineno(3)))


def p_declarations_next_array(p):
    'declarations : declarations COMMA pidentifier LEFT_BRACKET NUM COLON NUM RIGHT_BRACKET'
    new_array(p[3], p[5], p[7], str(p.lineno(3)))


def p_declarations_variable(p):
    'declarations : pidentifier'
    new_variable(p[1], str(p.lineno(1)))


def p_declarations_array(p):
    'declarations : pidentifier LEFT_BRACKET NUM COLON NUM RIGHT_BRACKET'
    new_array(p[1], p[3], p[5], str(p.lineno(1)))


def p_iterator(p):
    'loop_iterator	: pidentifier'
    new_variable(p[1], str(p.lineno(1)))
    initialized_variables.add(p[1])
    temp_vars.add(p[1])
    p[0] = p[1]


########################################################################################################################

# 9 commands -> commands command
# 10 | command
########################################################################################################################
def p_commands_multi(p):
    'commands : commands command'
    p[0] = (str(p[1][0]) + str(p[2][0]), p[1][1] + p[2][1], p[1][2] + p[2][2])


def p_commands_single(p):
    'commands : command'
    p[0] = p[1]


########################################################################################################################
# 12 command -> identifier ASSIGN expression ;
# 13 | IF condition THEN commands ELSE commands ENDIF
# 14 | IF condition THEN commands ENDIF
# 15 | WHILE condition DO commands ENDWHILE
# 16 | DO commands WHILE condition ENDDO
# 17 | FOR pidentifier FROM value TO value DO commands ENDFOR
# 18 | FOR pidentifier FROM value DOWNTO value DO commands ENDFOR
# 19 | READ identifier ;
# 20 | WRITE value ;
########################################################################################################################
### KOMENDY ZWRACAJA ICH KOSZT

def p_command_assign(p):
    'command : identifier ASSIGN expression SEMICOLON'

    variable_check(p[1][1], '0')
    initialized_variables.add(p[1][1])
    # print(p[3])
    ASSIGMENT = assign_value_to_variable(p[3], p[1])
    STORE = store_variable_or_array(p[1])
    p[0] = str(ASSIGMENT[0]) + f'{STORE[0]}', ASSIGMENT[1] + STORE[1],[]


def p_command_if_else(p):
    'command : IF condition THEN commands ELSE commands ENDIF'
    p[0] = (str(p[2][0]) + f'\nJZERO {p[6][1] + 2}' + str(p[6][0]) + f'\nJUMP {p[4][1] + 1}' + str(p[4][0]),
            p[2][1] + p[4][1] + p[6][1] + 2, [])


def p_command_if(p):
    'command : IF condition THEN commands ENDIF'
    p[0] = (str(p[2][0]) + f'\nJZERO 2\nJUMP {p[4][1] + 1}' + str(p[4][0]), p[2][1] + p[4][1] + 2, [])


def p_command_while_do(p):
    'command : WHILE condition DO commands ENDWHILE'
    p[0] = (str(p[2][0]) + f'\nJZERO 2\nJUMP {p[4][1] + 2}' + str(p[4][0]) + f'\nJUMP {-(p[4][1] + p[2][1] + 2)}',
            p[2][1] + p[4][1] + 3, [])
    # cofamy sie o roznice na początek condition!!


def p_command_do_while(p):
    'command : DO commands WHILE condition ENDDO'
    p[0] = (p[2][0] + p[4][0] + f'\nJPOS 3\nJNEG 2\nJUMP {-(p[4][1] + p[2][1] + 2)}', p[2][1] + p[4][1] + 3, [])


def p_command_from_upto(p):
    'command : FOR loop_iterator FROM value TO value DO commands ENDFOR'

    if p[2] in p[8][2]:
        raise Exception('Nested variable already exists')

    loop_validation = p_condition_greater(['', p[4], 'GE', p[6]])

    p[2] = ('variable', p[2])

    temp_var = new_temp_variable()

    STORE_FROM = assign_value_to_variable(p[4], p[2])
    STORE_TO = assign_value_to_variable(p[6], temp_var)

    LOOP_CONSTANTS = str(STORE_FROM[0]) + f'\nSTORE {variables[p[2][1]]}' +\
                     str(STORE_TO[0])+  f'\nSTORE {variables[temp_var[1]]}', STORE_FROM[1]+STORE_TO[1] + 2

    ITERATOR_INCREMENTATION = f'\nLOAD {variables[p[2][1]]}\nINC\nSTORE {variables[p[2][1]]}', 3

    LOOP_CONDITION_CHECK = p_condition_greater(['', p[2], 'GE', temp_var])

    JUMP_DISTANCE = -(ITERATOR_INCREMENTATION[1] + LOOP_CONDITION_CHECK[1] + p[8][1] + 1)

    LOOP_SIZE = LOOP_CONSTANTS[1] + p[8][1] + ITERATOR_INCREMENTATION[1] + LOOP_CONDITION_CHECK[1] + 2

    FULL_LOOP_CONDITION = loop_validation[0] + f'\nJZERO {LOOP_SIZE + 1}'

    IN_LOOP_VARIABLES = get_nested_variables(p[2][1], p[8])

    p[0] = FULL_LOOP_CONDITION + LOOP_CONSTANTS[0] + p[8][0] + ITERATOR_INCREMENTATION[0] + LOOP_CONDITION_CHECK[
        0] + f'\nJZERO 2 \nJUMP {JUMP_DISTANCE}', LOOP_SIZE + loop_validation[1] + 1, IN_LOOP_VARIABLES

    remove_temporary_variable(p[2][1])


def p_command_from_downto(p):
    'command : FOR loop_iterator FROM value DOWNTO value DO commands ENDFOR'

    if p[2] in p[8][2]:
        raise Exception('Nested variable already exists')

    loop_validation = p_condition_less(['', p[4], 'LE', p[6]])

    p[2] = ('variable', p[2])

    temp_var = new_temp_variable()

    STORE_FROM = assign_value_to_variable(p[4], p[2])
    STORE_TO = assign_value_to_variable(p[6], temp_var)

    # LOOP_CONSTANTS = str(STORE_FROM[0]) + f'\nSTORE {variables[p[2][1]]}', STORE_FROM[
    #     1] + 1
    LOOP_CONSTANTS = str(STORE_FROM[0]) + f'\nSTORE {variables[p[2][1]]}' + \
                     str(STORE_TO[0]) + f'\nSTORE {variables[temp_var[1]]}', STORE_FROM[1] + STORE_TO[1] + 2

    f'temp{register_number}'
    ITERATOR_INCREMENTATION = f'\nLOAD {variables[p[2][1]]}\nDEC\nSTORE {variables[p[2][1]]}', 3

    LOOP_CONDITION_CHECK = p_condition_less(['', p[2], 'LE', temp_var])

    JUMP_DISTANCE = -(ITERATOR_INCREMENTATION[1] + LOOP_CONDITION_CHECK[1] + p[8][1] + 1)

    LOOP_SIZE = LOOP_CONSTANTS[1] + p[8][1] + ITERATOR_INCREMENTATION[1] + LOOP_CONDITION_CHECK[1] + 2

    FULL_LOOP_CONDITION = loop_validation[0] + f'\nJZERO {LOOP_SIZE + 1}'

    IN_LOOP_VARIABLES = get_nested_variables(p[2][1], p[8])

    p[0] = FULL_LOOP_CONDITION + LOOP_CONSTANTS[0] + p[8][0] + ITERATOR_INCREMENTATION[0] + LOOP_CONDITION_CHECK[
        0] + f'\nJZERO 2 \nJUMP {JUMP_DISTANCE}', LOOP_SIZE + loop_validation[1] + 1, IN_LOOP_VARIABLES

    remove_temporary_variable(p[2][1])


def p_command_read(p):
    'command : READ identifier SEMICOLON'
    variable_check(p[2][1], '0')
    initialized_variables.add(p[2][1])
    p[0] = f'\nGET{store_variable_or_array(p[2])[0]}', 1+store_variable_or_array((p[2]))[1], []


def p_command_write(p):
    'command : WRITE value SEMICOLON'
    ASSIGMENT = assign_value_to_variable(p[2], p[2])
    p[0] = ASSIGMENT[0] + '\nPUT', ASSIGMENT[1] + 1, []


########################################################################################################################

# 21
# 22 expression -> value
# 23 | value PLUS value
# 24 | value MINUS value
# 25 | value TIMES value
# 26 | value DIV value
# 27 | value MOD value
########################################################################################################################
def p_expression_value(p):
    'expression : value'
    p[0] = (p[1])


def p_expression_plus(p):
    'expression : value PLUS value'
    ASSIGMENT1 = assign_value_to_variable(p[1], p[1])
    ASSIGMENT2 = assign_value_to_variable(p[3], p[3])
    p[0] = ASSIGMENT1[0] + f'\nSTORE 1' + \
           ASSIGMENT2[0] + '\nADD 1', ASSIGMENT1[1] + ASSIGMENT2[1] + 2


def p_expression_minus(p):
    'expression : value MINUS value'
    ASSIGMENT1 = assign_value_to_variable(p[1], p[1])
    ASSIGMENT2 = assign_value_to_variable(p[3], p[3])

    p[0] = ASSIGMENT2[0] + f'\nSTORE 1' + \
           ASSIGMENT1[0] + '\nSUB 1', ASSIGMENT1[1] + ASSIGMENT2[1] + 2


def p_expression_times(p):
    'expression : value TIMES value'
    ASSIGMENT1 = assign_value_to_variable(p[1], p[1])
    ASSIGMENT2 = assign_value_to_variable(p[3], p[3])

    PREPARE_FOR_MULTIPLICATION = load_registers()[0], +load_registers()[1]

    LOOP_DIST = load_least_significant_bit()[1] + check_if_LST_eq_0()[1] + add_subtotal_and_shift_by_2()[1] + 2

    p[0] = (ASSIGMENT1[0] + f'\nSTORE 6' + \
            ASSIGMENT2[0] + '\nSTORE 7' + negate_value_if_0()[0] \
            + PREPARE_FOR_MULTIPLICATION[0] + '\nLOAD 7' + \
            end_if_equals_0(LOOP_DIST)[0] + \
            load_least_significant_bit()[0] + \
            check_if_LST_eq_0()[0] + add_subtotal_and_shift_by_2()[
                0] + f'\nJUMP -{LOOP_DIST}\nLOAD 5\nJZERO 5\nLOAD 8\nSUB 8\nSUB 8\nSTORE 8\nLOAD 8'

            , PREPARE_FOR_MULTIPLICATION[1] + ASSIGMENT1[1] + ASSIGMENT2[1] + LOOP_DIST + end_if_equals_0(0)[1] + 9 +
            negate_value_if_0()[1])


########################################################################################################################
# powers are stored in 9
# adds in 8
# first_val is stored at 7
# second_val is stored at 6
# 5 wolny
# 4 wolny
# 3 contains -1 number
# 2 contains 1 number
# 1 value 0
def negate_value_if_0():
    return (f'\nJNEG 4\nSUB 0\nSTORE 5\nJUMP 7\nSUB 7\nSUB 7\nSTORE 7\nSUB 0\nINC\nSTORE 5', 10)


def load_registers():
    return '\nSUB 0\nINC\nSTORE 2\nDEC\nSTORE 8\nSTORE 9\nSTORE 1\nDEC\nSTORE 3', 9


def load_least_significant_bit():  # w tym momencie mamy 1 lub 0 w rejestrze
    return (f'\nSHIFT 3\nSHIFT 2\nSUB 7\nJNEG 2\nJUMP 3\nINC\nINC', 7)


def end_if_equals_0(loop_distance):
    return (f'\nJZERO {loop_distance}', 1)


def check_if_LST_eq_0():
    return (f'\nJZERO {add_subtotal_and_shift_by_2()[1] - divide_by_two()[1] - increase_power()[1] + 1}', 1)


def divide_by_two():
    return ('\nLOAD 7\nSHIFT 3\nSTORE 7', 3)


def increase_power():
    return ('\nLOAD 9\nINC\nSTORE 9', 3)


def add_subtotal_and_shift_by_2():
    return (f'\nLOAD 6\nSHIFT 9\nADD 8\nSTORE 8{increase_power()[0]}{divide_by_two()[0]}',
            4 + divide_by_two()[1] + increase_power()[1])


########################################################################################################################
def p_expression_div(p):
    'expression : value DIV value'
    ASSIGMENT1 = assign_value_to_variable(p[1], p[1])
    ASSIGMENT2 = assign_value_to_variable(p[3], p[3])

    TOTAL_DISTANCE = make_floor_if_neg()[1] + change_value_if_sign_flag_is_on()[1] + divide()[1] + 4

    LOOP_DISTANCE_FROM_ASSIGMENT_2_TO_END = TOTAL_DISTANCE + assert_bigger_value_division(1, 1)[1]
    LOOP_DISTANCE_FROM_ASSIGMENT_1_TO_END = LOOP_DISTANCE_FROM_ASSIGMENT_2_TO_END + assert_0_division(1)[1] + \
                                            check_sign_of_value()[1] + \
                                            2 * change_sign_flag()[1] + ASSIGMENT2[1] + 1

    p[0] = f'{load_registers_for_division()[0]}' + \
           ASSIGMENT1[0] + \
           f'\nSTORE 6\nSTORE 5\nJZERO {LOOP_DISTANCE_FROM_ASSIGMENT_1_TO_END}' + \
           f'{change_sign_flag()[0]}' + \
           ASSIGMENT2[0] + f'\nSTORE 7' \
                           f'{change_sign_flag()[0]}' \
                           f'{check_sign_of_value()[0]}' + \
           assert_0_division(LOOP_DISTANCE_FROM_ASSIGMENT_2_TO_END)[0] + \
           assert_bigger_value_division(TOTAL_DISTANCE, divide()[1] + 1)[0] + \
 \
           divide()[0] + \
 \
           f'\nJUMP 4\nSUB 0\nINC\nSTORE 8' \
 \
           f'{change_value_if_sign_flag_is_on()[0]}' \
           f'{make_floor_if_neg()[0]}' \
           f'\nLOAD 8' \
        , ASSIGMENT2[1] + ASSIGMENT1[1] + 2 * change_sign_flag()[1] + 9 + \
           check_sign_of_value()[1] + assert_0_division(0)[1] + \
           assert_bigger_value_division(1, 1)[1] + divide()[1] + \
           change_value_if_sign_flag_is_on()[1] + load_registers_for_division()[1] + \
           make_floor_if_neg()[1]


########################################################################################################################
# w 1 flaga znaku = 0 gdy są tego samego znaku
# w 6 liczba 1  --- liczba dzielona  dzielimy 6 : 7
# w 7 liczba 2  --- liczba wieksza
# w 8 temp value (lacznie)
# w 9 leca potegi, zaczyna sie od 1
# w 5 current value bedzie przechowywane
# w 4 wartosc ktora zostala wyznaczona

def change_sign_flag():
    return '\nJPOS 4\nLOAD 1\nDEC\nJUMP 3\nLOAD 1\nINC\nSTORE 1', 7


def check_sign_of_value():
    return '\nLOAD 6\nJPOS 5\nSUB 6\nSUB 6\nSTORE 6\nSTORE 5\nLOAD 7\nJPOS 4\nSUB 7\nSUB 7\nSTORE 7', 11


def increase_div_value():
    return (f'{increase_power()[0]}\nLOAD 5\nSHIFT 9\nSTORE 5', increase_power()[1] + 3)


def change_value_if_sign_flag_is_on():
    return (f'\nLOAD 1\nJPOS 6\nJNEG 5\nLOAD 8\nSUB 8\nSUB 8\nSTORE 8', 7)
    # p0 = p4 * -1


def divide():
    return f'' \
           f'\nLOAD 7\nSHIFT 9\nSUB 5\nJPOS {increase_power()[1] + 2}' \
           f'{increase_power()[0]}' \
           f'\nJUMP {-(increase_power()[1] + 4)}' \
           f'{decrease_power()[0]}' \
           f'{update_temp_value()[0]}' \
           f'{check_if_power_equals_1(0, add_power_to_sum()[1] + clear_power()[1] + 2)[0]}' \
 \
           f'{add_power_to_sum()[0]}' \
           f'{clear_power()[0]}' \
           f'\nJUMP {-(check_if_power_equals_1(0, 0)[1] + update_temp_value()[1] + increase_power()[1] + add_power_to_sum()[1] + clear_power()[1] + decrease_power()[1] + 5)}' \
           f'', 6 + increase_power()[1] + decrease_power()[1] + update_temp_value()[1] + check_if_power_equals_1(1, 1)[
               1] \
           + add_power_to_sum()[1] + clear_power()[1]


def check_if_power_equals_1(cond_dist, end_dist):
    return (f'\nJPOS {cond_dist + 4}\nJZERO {cond_dist + 3}\nLOAD 9\nJZERO {end_dist}', 4)


def make_floor_if_neg():
    return ('\nLOAD 5\nSUB 7\nJZERO 7\nLOAD 1\nJPOS 5\nJNEG 4\nLOAD 8\nDEC\nSTORE 8', 9)


def decrease_power():
    return ('\nLOAD 9\nDEC\nSTORE 9', 3)


def update_temp_value():
    return ('\nLOAD 7\nSHIFT 9\nSUB 5\nSTORE 3\nSUB 3\nSUB 3\nSTORE 5', 7)


def add_power_to_sum():
    return (f'\nSUB 0\nINC\nSHIFT 9\nADD 8\nSTORE 8', 5)


def check_if_equals(end_dist):
    return (f'\nLOAD 5\nJZERO {end_dist}', 2)


def clear_power():
    return (f'\nSUB 0\nINC\nSTORE 9', 3)


def assert_0_division(jump_end):
    return f'\nJZERO {jump_end}', 1


def assert_bigger_value_division(jump_end, jzero_value):
    return f'\nSUB 6\nJZERO {jzero_value + 4}\nJNEG 3\nSUB 0\nJUMP {jump_end}', 5


def load_registers_for_division():
    return '\nSUB 0\nINC\nSTORE 9\nDEC\nSTORE 8\nSTORE 1\nSTORE 4\nSTORE 3', 8
    ### czyszczenie flagi w mnozeniu


########################################################################################################################
def p_expression_mod(p):
    'expression : value MOD value'
    ASSIGMENT1 = assign_value_to_variable(p[1], p[1])
    ASSIGMENT2 = assign_value_to_variable(p[3], p[3])

    DISTANCE_TO_END = check_returned_sign()[1] + check_sign_of_value()[1] + find_modulus()[1] + \
                      change_modulo_if_flag_on()[1] + if_equals_0_end(1)[1] + 2

    p[0] = \
        f'{clear_sign_flag_and_set_power_to_0()[0]}' + \
        ASSIGMENT1[0] + f'\nSTORE 6\nSTORE 5' \
        + change_sign_flag()[0] + \
        ASSIGMENT2[0] + f'\nSTORE 7\nSTORE 3' \
                        f'{change_sign_flag()[0]}' + \
        check_if_divider_equals_0_or_1(DISTANCE_TO_END + 1)[0] + \
        check_sign_of_value()[0] + \
        find_modulus()[0] + \
        if_equals_0_end(change_modulo_if_flag_on()[1] + 1)[0] + \
        change_modulo_if_flag_on()[0] + \
        check_returned_sign()[0] + \
        '\nLOAD 5' \
            , \
        clear_sign_flag_and_set_power_to_0()[1] + ASSIGMENT1[1] + 2 + change_sign_flag()[1] * 2 + \
        ASSIGMENT2[1] + 2 + check_if_divider_equals_0_or_1(1)[1] + check_sign_of_value()[1] + \
        find_modulus()[1] + if_equals_0_end(0)[1] + change_modulo_if_flag_on()[1] + check_returned_sign()[1] + 1


########################################################################################################################

def check_returned_sign():
    return f'\nLOAD 3\nJPOS 4\nSUB 0\nSUB 5\nSTORE 5', 5


def check_if_divider_equals_0_or_1(end_distance):
    return (f'\nLOAD 7\nJZERO 7\nDEC\nJZERO 5\nINC\nINC\nJZERO 2\nJUMP 3\nSUB 0\nJUMP {end_distance}', 10)
    #### zwraca b jezeli jest w zakresie i skacze na koniec(-1,1)


def update_value():
    return (f'\nLOAD 7\nSHIFT 9\nSUB 5\nSTORE 5\nSUB 5\nSUB 5\nSTORE 5', 7)


def clear_sign_flag_and_set_power_to_0():
    return f'\nLOAD 1\nSUB 0\nSTORE 1\nSTORE 9', 4
    ### wynik jest kurwa w 5


def change_modulo_if_flag_on():  # skocz na koniec
    return f'\nLOAD 1\nJZERO 7\nLOAD 7\nJPOS 11\nLOAD 5\nSUB 5\nSUB 5\nJUMP 6\nLOAD 7\nJPOS 3\nADD 5\nJUMP 2\nSUB 5\nSTORE 5', 14
    ## jak byly tych samych znakow to trzeba przemnozyc przez -1 jezeli 2 wartosc jest jneg. Dla roznych jest git wynik juz


def if_equals_0_end(jump_dist):
    return f'\nLOAD 5\nJZERO {jump_dist}', 2


def find_modulus():
    WHOLE_DIST = 6 + increase_power()[1] + decrease_power()[1] + update_value()[1] + reset_power()[1]
    return (f'\nLOAD 7\nSHIFT 9\nSUB 5\nJPOS {2 + increase_power()[1]}{increase_power()[0]}'
            f'\nJUMP {-(increase_power()[1] + 4)}'
            f'{decrease_power()[0]}'
            f'\nJNEG {update_value()[1] + reset_power()[1] + 2}'
            f'{update_value()[0]}'
            f'{reset_power()[0]}'
            f'\nJUMP {-WHOLE_DIST}'
            ,
            7 + increase_power()[1] + decrease_power()[1] + update_value()[1] + reset_power()[1])


def reset_power():
    return (f'\nSUB 0\nSTORE 9', 2)


########################################################################################################################
# 29 condition -> value EQ value
# 30 | value NEQ value
# 31 | value LE value
# 32 | value GE value
# 33 | value LEQ value
# 34 | value GEQ value
########################################################################################################################
def p_condition_equals(p):
    'condition : value EQ value'
    ASSIGMENT1 = assign_value_to_variable(p[1], p[1])
    ASSIGMENT2 = assign_value_to_variable(p[3], p[3])

    p[0] = ASSIGMENT1[0] + f'\nSTORE 1' + \
           ASSIGMENT2[0] + '\nSUB 1', ASSIGMENT1[1] + ASSIGMENT2[1] + 2
    return p[0]


def p_condition_not_equals(p):
    'condition : value NEQ value'
    ASSIGMENT1 = assign_value_to_variable(p[1], p[1])
    ASSIGMENT2 = assign_value_to_variable(p[3], p[3])

    p[0] = ASSIGMENT1[0] + f'\nSTORE 1' + \
           ASSIGMENT2[0] + '\nSUB 1\nJZERO 3\nSUB 0\nJUMP 2\nINC', ASSIGMENT1[1] + ASSIGMENT2[1] + 6
    return p[0]


def p_condition_less(p):
    'condition : value LE value'
    ASSIGMENT1 = assign_value_to_variable(p[1], p[1])
    ASSIGMENT2 = assign_value_to_variable(p[3], p[3])

    p[0] = ASSIGMENT1[0] + f'\nSTORE 1' + \
           ASSIGMENT2[0] + f'\nSUB 1\nJNEG 4\nJZERO 3\nSUB 0\nJUMP 2\nDEC', ASSIGMENT1[1] + ASSIGMENT2[1] + 7
    return p[0]


def p_condition_greater(p):
    'condition : value GE value'
    ASSIGMENT1 = assign_value_to_variable(p[1], p[1])
    ASSIGMENT2 = assign_value_to_variable(p[3], p[3])

    p[0] = ASSIGMENT1[0] + f'\nSTORE 1' + \
           ASSIGMENT2[0] + f'\nSUB 1\nJPOS 4\nJZERO 3\nSUB 0\nJUMP 2\nINC', ASSIGMENT1[1] + ASSIGMENT2[1] + 7
    return p[0]


def p_condition_less_or_equal(p):
    'condition : value LEQ value'
    ASSIGMENT1 = assign_value_to_variable(p[1], p[1])
    ASSIGMENT2 = assign_value_to_variable(p[3], p[3])

    p[0] = ASSIGMENT1[0] + f'\nSTORE 1' + \
           ASSIGMENT2[0] + f'\nSUB 1\nJNEG 2\nSUB 0', ASSIGMENT1[1] + ASSIGMENT2[1] + 4
    return p[0]


def p_condition_greater_or_equal(p):
    'condition : value GEQ value'

    ASSIGMENT1 = assign_value_to_variable(p[1], p[1])
    ASSIGMENT2 = assign_value_to_variable(p[3], p[3])

    p[0] = ASSIGMENT1[0] + f'\nSTORE 1' + \
           ASSIGMENT2[0] + f'\nSUB 1\nJPOS 2\nSUB 0', ASSIGMENT1[1] + ASSIGMENT2[1] + 4
    return p[0]


########################################################################################################################
# 36 value -> num
# 37 | identifier

def p_value_num(p):
    'value : NUM'
    p[0] = ("CONSTANT", p[1])


def p_value_identifier(p):
    'value : identifier'
    p[0] = (p[1])


########################################################################################################################
# 39 identifier -> pidentifier
# 40 | pidentifier ( pidentifier )
# 41 | pidentifier (num )

def p_identifier_pidentifier(p):
    'identifier : pidentifier'
    p[0] = ("variable", p[1])


def p_identifier_pidentifier_pidentifier(p):
    'identifier : pidentifier LEFT_BRACKET pidentifier RIGHT_BRACKET'
    p[0] = ("array", p[1],p[3])



def p_identifier_pidentifier_num(p):
    'identifier : pidentifier LEFT_BRACKET NUM RIGHT_BRACKET'
    p[0] = ("array", p[1],p[3])


########################################################################################################################
def p_error(p):
    print("Syntax error in input!")


def array_check(id, lineno):
    if id not in arrays:
        if id in variables:
            raise Exception("Error at line " + lineno + ': ' + id)
        else:
            raise Exception("Error at line  " + lineno + ': ' + id)


def variable_check(id, lineno):
    if id not in variables and id not in  arrays:
        if id in arrays:
            raise Exception("Error at:  " + lineno + ': ' + id)
        else:
            raise Exception("Error at:  " + lineno + ': variable not declared: ' + str(id))
    if id in temp_vars:
        raise Exception("Error at: " + lineno + " cannot assign value to iterator")


def initialization_check(id, lineno):
    if id not in initialized_variables:
        raise Exception("Error at: " + lineno + ' variable not initialized: ' + id)


def loop_iterator_check(id, lineno):
    if id in initialized_variables:
        raise Exception("Error at: " + lineno + ' variable already exists: ' + id)


########################################################################################################################

# Function creates new variable and stores its address in dict variables.
def new_variable(var_name, line_number):
    global register_number
    if var_name in variables:
        raise Exception("Duplicated variable name at line: " + line_number)
    else:
        variables[var_name] = register_number
        register_number += 1


def remove_temporary_variable(var_name):
    variables.pop(var_name)
    initialized_variables.remove(var_name)
    temp_vars.remove(var_name)


def new_array(array_name, begin, end, line_number):
    global register_number
    if begin > end:
        raise Exception('Error in array range')
    if array_name in arrays:
        raise Exception("Duplicated array name at line: " + line_number)
    if array_name in variables:
        raise Exception("Duplicated array name at line: " + line_number)
    else:
        arrays[array_name] = begin, end,register_number
        register_number += end-begin+1


def create_temporary_registers(length):
    for k in range(length):
        new_variable(f'r{k}', 0)
        initialized_variables.add(f'r{k}')


def new_temp_variable():
    global register_number
    variable = ('variable',f'temp{register_number}')
    new_variable(variable[1], 0)
    initialized_variables.add(variable[1])
    register_number+=1
    return variable




########################################################################################################################


# returns string, cost of operations
def assign_value_to_variable(value, assigned=None):
    if value[0] == 'variable':
        # initialization_check(value[1], '0')
        # ZAKOMENTOWANE ZEBY PRZESZLO TESTY MGR.SLOWIKA ALE WYDAJE MI SIE ZE POWINNO BYC

        initialized_variables.add(assigned[1])
        return store_variable(value[1])
    elif value[0] == 'CONSTANT':
        initialized_variables.add(assigned[1])
        return store_constant(value)
    elif value[0] == 'array':
        temp_variable = new_temp_variable()
        if type(value[2]) == type(''):
            LOAD_ARRAY = store_constant(("CONSTANT", get_addres_from_variable(value)))
            return f'\nLOAD {variables[value[2]]}\nSTORE {get_addres_from_variable(temp_variable)}{LOAD_ARRAY[0]}\nADD {get_addres_from_variable(temp_variable)}' \
                   f'\nSTORE {get_addres_from_variable(temp_variable)}\nLOADI {get_addres_from_variable(temp_variable)}', 5 + LOAD_ARRAY[1]
        else:
            LOAD_ARRAY = store_constant(("CONSTANT", get_index_in_array(value[1],value[2])))
            return f'{LOAD_ARRAY[0]}\nSTORE {get_addres_from_variable(temp_variable)}\nLOADI {get_addres_from_variable(temp_variable)}',2+LOAD_ARRAY[1]
    else:
        return value


def get_addres_from_variable(variable):
    if variable[0] == 'variable':
        return variables[variable[1]]
    else:
        return arrays[variable[1]][2]


def get_index_in_array(array_name,index):
    array = arrays[array_name]
    return index -array[0]+array[2]



def store_variable(variable):
    return f'\nLOAD {variables[variable]}', 1


def store_constant(value):
    counter = 0
    value = value[1]
    STORE = '\nSUB 0'
    if value > 0:
        sign = True
    else:
        sign = False
    counter += 1
    binary_value = str(bin(abs(value)))[2:]

    for k in range(len(binary_value)):
        STORE += '\nADD 0'
        counter += 1
        if binary_value[k] == '1':
            counter += 1
            if sign:
                STORE += '\nINC'
            else:
                STORE += '\nDEC'
    return STORE, counter


def get_nested_variables(used_variables, nested_variables):
    VARIABLES = [used_variables]
    if len(nested_variables) == 3:
        nested_variables[2].append(used_variables)
        return nested_variables[2]
    return VARIABLES



def store_variable_or_array(variable):
    if variable[0] == 'variable':
        return f'\nSTORE {get_addres_from_variable(variable)}',1
    else:
        temp_variable = new_temp_variable()
        temp_variable_for_storage = new_temp_variable()

        if type(variable[2]) == type(''):
            LOAD_ARRAY = store_constant(("CONSTANT", get_addres_from_variable(variable)))
            return f'\nSTORE {get_addres_from_variable(temp_variable_for_storage)}\nLOAD {variables[variable[2]]}' \
                   f'\nSTORE {get_addres_from_variable(temp_variable)}{LOAD_ARRAY[0]}' \
                   f'\nADD {get_addres_from_variable(temp_variable)}\nSTORE {get_addres_from_variable(temp_variable)}' \
                   f'\nLOAD {get_addres_from_variable(temp_variable_for_storage)}' \
                   f'\nSTOREI {get_addres_from_variable(temp_variable)}',7 + LOAD_ARRAY[1]
        else:
            LOAD_ARRAY = store_constant(("CONSTANT", get_index_in_array(variable[1], variable[2])))
            return f'\nSTORE {get_addres_from_variable(temp_variable_for_storage)}' \
                   f'{LOAD_ARRAY[0]}\nSTORE {get_addres_from_variable(temp_variable)}' \
                   f'\nLOAD {get_addres_from_variable(temp_variable_for_storage)}' \
                   f'\nSTOREI {get_addres_from_variable(temp_variable)}', 4 + LOAD_ARRAY[1]

#### trzeba bedzie storowac w temp rejestrach.

#######################################################################################################################


input = '/home/krzyhoo/Desktop/Compiler/grammar/prog.txt'
output = 'output2.txt'

create_temporary_registers(10)
parser = yacc.yacc(
)
file = open(input, "r")
try:
    parsed = parser.parse(file.read(), tracking=True)
    if parsed == '\n':
        parsed = ''
    parsed = parsed.strip()
    i = 0
    commands = parsed.split('\n')
    while i < len(commands):
        if commands[i].split()[0] in replacement:
            commands[i] = commands[i].split()[0] + ' ' + str(int(commands[i].split()[1]) + i)
        i += 1
    PROGRAM = ''
    for command in commands:
        PROGRAM += command + '\n'
    print(PROGRAM)

except Exception as e:
    print(e)
    exit()
fw = open(output, "w")
# print(f'{parsed}')
# print(parsed.strip())
# print(variables)
# print(arrays)
# print(initialized_variables)
# print(temporary_variables)
# fw.write(f'{parsed.strip()}')
fw.write(PROGRAM)

#       /home/krzyhoo/Desktop/Compiler/virtual_machine/maszyna-wirtualna /home/krzyhoo/Desktop/Compiler/grammar/output2.txt

