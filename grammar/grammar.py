import os

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


########################################################################################################################

# 9 commands -> commands command
# 10 | command
########################################################################################################################
def p_commands_multi(p):
    'commands : commands command'
    # print(current_instruction)
    p[0] = (str(p[1][0]) + str(p[2][0]), p[1][1] + p[2][1])


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
    ASSIGMENT = assign_value_to_variable(p[3], p[1])

    p[0] = str(ASSIGMENT[0]) + f'\nSTORE {variables[p[1][1]]}', ASSIGMENT[1] + 1


def p_command_if_else(p):
    'command : IF condition THEN commands ELSE commands ENDIF'
    p[0] = (str(p[2][0]) + f'\nJZERO {p[6][1] + 2}' + str(p[6][0]) + f'\nJUMP {p[4][1] + 1}' + str(p[4][0]),
            p[2][1] + p[4][1] + p[6][1] + 2)


def p_command_if(p):
    'command : IF condition THEN commands ENDIF'
    p[0] = (str(p[2][0]) + f'\nJZERO 2\nJUMP {p[4][1] + 1}' + str(p[4][0]), p[2][1] + p[4][1] + 2)


def p_command_while_do(p):
    'command : WHILE condition DO commands ENDWHILE'
    p[0] = (str(p[2][0]) + f'\nJZERO 2\nJUMP {p[4][1] + 2}' + str(p[4][0]) + f'\nJUMP {-(p[4][1] + p[2][1] + 2)}',
            p[2][1] + p[4][1] + 3)
    # cofamy sie o roznice na początek condition!!


def p_command_do_while(p):
    'command : DO commands WHILE condition ENDDO'
    p[0] = (p[2][0] + p[4][0] + f'\nJPOS 3\nJNEG 2\nJUMP {-(p[4][1] + p[2][1] + 2)}', p[2][1] + p[4][1] + 3)


def p_command_from_upto(p):
    'command : FOR pidentifier FROM value TO value DO commands ENDFOR'

    loop_validation = p_condition_greater(['', p[4], 'GE', p[6]])

    new_variable(p[2], str(p.lineno(2)))
    p[2] = ('variable', p[2])

    STORE_FROM = assign_value_to_variable(p[4], p[2])
    STORE_TO = assign_value_to_variable(p[6], p[2])

    # storuje wartość początkową pod k a wartość początkową storujemy pod 5 .
    LOOP_CONSTANTS = str(STORE_FROM[0]) + f'\nSTORE {variables[p[2][1]]}' + str(STORE_TO[0]) + f'\nSTORE 5', STORE_FROM[
        1] + STORE_TO[1] + 2
    # tymczasowy rejestr wartosci na koniec petli
    ITERATOR_INCREMENTATION = f'\nLOAD {variables[p[2][1]]}\nINC\nSTORE {variables[p[2][1]]}', 3
    # to gdzie ja to loaduje i storuje to sam musze wymyslic !!! chyba?

    LOOP_CONDITION_CHECK = p_condition_greater(['', p[2], 'GE', p[6]])

    JUMP_DISTANCE = -(ITERATOR_INCREMENTATION[1] + LOOP_CONDITION_CHECK[1] + p[8][1] + 1)

    LOOP_SIZE = LOOP_CONSTANTS[1] + p[8][1] + ITERATOR_INCREMENTATION[1] + LOOP_CONDITION_CHECK[1] + 2

    FULL_LOOP_CONDITION = loop_validation[0] + f'\nJZERO {LOOP_SIZE + 1}'

    p[0] = FULL_LOOP_CONDITION + LOOP_CONSTANTS[0] + p[8][0] + ITERATOR_INCREMENTATION[0] + LOOP_CONDITION_CHECK[
        0] + f'\nJZERO 2 \nJUMP {JUMP_DISTANCE}', LOOP_SIZE + loop_validation[1] + 1
    # na 23 musi skakac
    remove_temporary_variable(p[2][1])

    # p[0] = str(ASSIGMENT[0]) + f'\nSTORE {variables[p[1][1]]}',ASSIGMENT[1]+1


def p_command_from_downto(p):
    'command : FOR pidentifier FROM value DOWNTO value DO commands ENDFOR'

    loop_validation = p_condition_less(['', p[4], 'LE', p[6]])

    new_variable(p[2], str(p.lineno(2)))
    p[2] = ('variable', p[2])

    STORE_FROM = assign_value_to_variable(p[4], p[2])
    STORE_TO = assign_value_to_variable(p[6], p[2])

    # storuje wartość początkową pod k a wartość początkową storujemy pod 5 .
    LOOP_CONSTANTS = str(STORE_FROM[0]) + f'\nSTORE {variables[p[2][1]]}' + str(STORE_TO[0]) + f'\nSTORE 5', STORE_FROM[
        1] + STORE_TO[1] + 2
    # tymczasowy rejestr wartosci na koniec petli
    ITERATOR_INCREMENTATION = f'\nLOAD {variables[p[2][1]]}\nDEC\nSTORE {variables[p[2][1]]}', 3
    # to gdzie ja to loaduje i storuje to sam musze wymyslic !!! chyba?

    LOOP_CONDITION_CHECK = p_condition_less(['', p[2], 'LE', p[6]])

    JUMP_DISTANCE = -(ITERATOR_INCREMENTATION[1] + LOOP_CONDITION_CHECK[1] + p[8][1] + 1)

    LOOP_SIZE = LOOP_CONSTANTS[1] + p[8][1] + ITERATOR_INCREMENTATION[1] + LOOP_CONDITION_CHECK[1] + 2

    FULL_LOOP_CONDITION = loop_validation[0] + f'\nJZERO {LOOP_SIZE + 1}'

    p[0] = FULL_LOOP_CONDITION + LOOP_CONSTANTS[0] + p[8][0] + ITERATOR_INCREMENTATION[0] + LOOP_CONDITION_CHECK[
        0] + f'\nJZERO 2 \nJUMP {JUMP_DISTANCE}', LOOP_SIZE + loop_validation[1] + 1

    remove_temporary_variable(p[2][1])


def p_command_read(p):
    'command : READ identifier SEMICOLON'
    variable_check(p[2][1], '0')
    initialized_variables.add(p[2][1])
    p[0] = f'\nGET\nSTORE {variables[p[2][1]]}', 2


def p_command_write(p):
    'command : WRITE value SEMICOLON'
    ASSIGMENT = assign_value_to_variable(p[2], p[2])
    p[0] = ASSIGMENT[0] + '\nPUT', ASSIGMENT[1] + 1


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
    # p[0] = (p[1], 'LEFT_BRACKET', p[3], 'RIGHT_BRACKET')
    p[0] = ("array", p[1], ("variable", p[3]))


def p_identifier_pidentifier_num(p):
    'identifier : pidentifier LEFT_BRACKET NUM RIGHT_BRACKET'
    p[0] = ("array", p[1], ("CONSTANT", p[3]))


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
    if id not in variables:
        if id in arrays:
            raise Exception("Error at:  " + lineno + ': ' + id)
        else:
            raise Exception("Error at:  " + lineno + ': variable not declared: ' + str(id))


def initialization_check(id, lineno):
    if id not in initialized_variables:
        raise Exception("Error at: " + lineno + ' variable not initialized: ' + id)


########################################################################################################################

# Function creates new variable and stores its address in dict variables.
def new_variable(var_name, line_number):
    global register_number
    if var_name in variables:
        raise Exception("Duplicated variable name at line: " + line_number)
    else:
        variables[var_name] = register_number
        # initialized_variables.add(var_name)
        register_number += 1


def remove_temporary_variable(var_name):
    variables.pop(var_name)


def new_array(array_name, begin, end, line_number):
    global register_number
    if begin > end:
        raise Exception('Error in array range')
    if array_name in arrays:
        raise Exception("Duplicated array name at line: " + line_number)
    else:
        arrays[array_name] = [register_number, begin, end]
        # initialized_variables.add(array_name)      # initialized_variables.add(array_name)
        register_number += begin - end + 1


def create_temporary_registers(length):
    for k in range(length):
        new_variable(f'r{k}', 0)
        initialized_variables.add(f'r{k}')


########################################################################################################################


# returns string, cost of operations
def assign_value_to_variable(value, assigned=None):
    if value[0] == 'variable':
        initialization_check(value[1], '0')
        initialized_variables.add(assigned[1])
        return store_variable(value[1])
    elif value[0] == 'CONSTANT':
        initialized_variables.add(assigned[1])
        return store_constant(value)
    elif value[0] == 'array':
        # if id[2][0] == 'CONSTANT':
        #     return arrays[id[1]][0] + id[2][1] - arrays[id[1]][1]
        # if id[2][0] == 'variable':
        pass  # to be done
    else:
        return value


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


#######################################################################################################################


input = '/home/krzyhoo/Desktop/Compiler/grammar/prog.txt'
output = 'output.txt'

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
print(variables)
# print(arrays)
print(initialized_variables)
# print(temporary_variables)
# fw.write(f'{parsed.strip()}')
fw.write(PROGRAM)

#       /home/krzyhoo/Desktop/Compiler/virtual_machine/maszyna-wirtualna /home/krzyhoo/Desktop/Compiler/grammar/output.txt

