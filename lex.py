import ply.lex as lex


class Lexer(object):
    tokens = (
        'DECLARE', 'BEGIN', 'END', 'SEMICOLON', 'COMMA',
        'NUM',
        'PLUS', 'MINUS', 'TIMES', 'DIV', 'MOD',
        'EQ', 'NEQ', 'LE', 'GE', 'LEQ', 'GEQ',
        'ASSIGN',
        'LEFT_BRACKET', 'RIGHT_BRACKET', 'COLON',
        'IF', 'THEN', 'ELSE', 'ENDIF',
        'WHILE', 'ENDDO', 'ENDWHILE','DO',
        'FOR', 'FROM', 'TO', 'DOWNTO', 'ENDFOR',
        'READ', 'WRITE',
        'pidentifier'
    )

    # TOKENS_LIST
    t_DECLARE = r'DECLARE'
    t_BEGIN = r'BEGIN'
    t_END = r'END'
    t_SEMICOLON = r';'
    t_COMMA = r','

    t_PLUS = r'PLUS'
    t_MINUS = r'MINUS'
    t_TIMES = r'TIMES'
    t_DIV = r'DIV'
    t_MOD = r'MOD'

    t_EQ = r'EQ'
    t_NEQ = r'NEQ'
    t_LE = r'LE'
    t_GE = r'GE'
    t_LEQ = r'LEQ'
    t_GEQ = r'GEQ'

    t_ASSIGN = r'ASSIGN'
    t_LEFT_BRACKET = r'\('
    t_RIGHT_BRACKET = r'\)'
    t_COLON = r':'

    t_IF = r'IF'
    t_THEN = r'THEN'
    t_ELSE = r'ELSE'
    t_ENDIF = r'ENDIF'

    t_DO = r'DO'
    t_FOR = r'FOR'
    t_FROM = r'FROM'
    t_TO = r'TO'
    t_DOWNTO = r'DOWNTO'
    t_ENDFOR = r'ENDFOR'

    t_WHILE = r'WHILE'
    t_ENDDO = r'ENDDO'
    t_ENDWHILE = r'ENDWHILE'
    t_READ = r'READ'
    t_WRITE = r'WRITE'
    t_pidentifier = r'[_a-z]+'

    # IGNORES COMMENTS
    # comment = '\[.*]'
    t_ignore_COMMENT = r'\[[^\]]*\]'
    t_ignore = " \t\n"  # IGNORES SPACES AND TABS


    def t_NUM(t):
        r'[-+]?[0-9]+'

        t.value = int(t.value)
        return t

    # def t_COMMENT(t):
    #     r'\#.*'
    #     pass
    #     # No return value. Token discarded

    def t_newline(t):
        r'\r?\n+'
        t.lexer.lineno += len(t.value)

    def t_error(t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)


    def run(self, data):
        tokens = []
        self.lexer.input(data)
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            tokens.append(tok)

        return (tok)

    lexer = lex.lex()






# data = '''
# [ test 12312321 ]
# DECLARE 5 TIMES 5 ASSIGN 13  [ [ test 12312321 ] test 12312321 ]
#
# 3essad
# '''
# lexer = Lexer()
#
# lexer.run(data)