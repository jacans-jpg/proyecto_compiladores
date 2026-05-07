"""
Analizador Sintáctico (Parser) - Recursive Descent
Convierte el flujo de tokens del Scanner en un Árbol de Sintaxis Abstracta (AST).
Implementa recuperación de errores (modo pánico) para no detenerse en el primer error.
"""

from ..classes.ast_nodes import *


class ParseError(Exception):
    """Error sintáctico con ubicación."""
    def __init__(self, message, line=0, column=0):
        super().__init__(message)
        self.line = line
        self.column = column


class Parser:
    # Tipos de datos primitivos de Java
    TYPE_KEYWORDS = {
        "int", "float", "double", "boolean", "char",
        "String", "long", "short", "byte", "void"
    }

    # Modificadores de acceso y otros
    MODIFIERS = {"public", "private", "protected", "static", "final", "abstract"}

    # Operadores de asignación
    ASSIGN_OPS = {"ASIGNACION", "SUMA_ASIGN", "RESTA_ASIGN", "MULT_ASIGN", "DIV_ASIGN", "MOD_ASIGN"}

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.errors = []
        self.ast = None

    # ================================================================
    #  UTILIDADES DE NAVEGACIÓN DE TOKENS
    # ================================================================
    def current(self):
        """Token actual."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def peek(self, offset=1):
        """Mirar token adelante sin consumir."""
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return None

    def advance(self):
        """Consumir token actual y devolver el anterior."""
        tok = self.current()
        if self.pos < len(self.tokens):
            self.pos += 1
        return tok

    def check(self, token_type, value=None):
        """Verificar si el token actual coincide."""
        tok = self.current()
        if tok is None:
            return False
        if tok.type != token_type and tok.value != value:
            return False
        if value is not None:
            return tok.value == value
        return tok.type == token_type

    def check_value(self, value):
        """Verificar solo por valor del token."""
        tok = self.current()
        return tok is not None and tok.value == value

    def check_type(self, token_type):
        """Verificar solo por tipo de token."""
        tok = self.current()
        return tok is not None and tok.type == token_type

    def match_value(self, value):
        """Consumir si el valor coincide."""
        if self.check_value(value):
            return self.advance()
        return None

    def match_type(self, token_type):
        """Consumir si el tipo coincide."""
        if self.check_type(token_type):
            return self.advance()
        return None

    def expect_value(self, value):
        """Consumir valor esperado o reportar error."""
        tok = self.match_value(value)
        if tok:
            return tok
        curr = self.current()
        if curr:
            self.report_error(
                f"Se esperaba '{value}' pero se encontró '{curr.value}'",
                curr.line, curr.column
            )
        else:
            self.report_error(f"Se esperaba '{value}' pero se llegó al final del archivo")
        return None

    def expect_type(self, token_type):
        """Consumir tipo esperado o reportar error."""
        tok = self.match_type(token_type)
        if tok:
            return tok
        curr = self.current()
        if curr:
            self.report_error(
                f"Se esperaba {token_type} pero se encontró '{curr.value}' ({curr.type})",
                curr.line, curr.column
            )
        else:
            self.report_error(f"Se esperaba {token_type} pero se llegó al final del archivo")
        return None

    def report_error(self, message, line=0, column=0):
        """Registrar error sintáctico."""
        code = f"SYN-{len(self.errors) + 1:03d}"
        self.errors.append({
            "codigo": code,
            "mensaje": message,
            "linea": line,
            "columna": column
        })

    def synchronize(self):
        """Recuperación en modo pánico: avanzar hasta un punto seguro."""
        while self.current() is not None:
            # Si encontramos punto y coma, avanzamos y seguimos
            if self.check_value(";"):
                self.advance()
                return
            # Si encontramos inicio de sentencia, nos detenemos
            tok = self.current()
            if tok.value in ("if", "while", "for", "return", "class", "public",
                             "private", "protected", "static", "int", "float",
                             "double", "boolean", "String", "void"):
                return
            if tok.value in ("}", "{"):
                return
            self.advance()

    def is_at_end(self):
        return self.pos >= len(self.tokens)

    # ================================================================
    #  HELPERS PARA IDENTIFICAR TIPOS Y MODIFICADORES
    # ================================================================
    def is_type_token(self):
        """¿El token actual es un tipo de dato?"""
        tok = self.current()
        if tok is None:
            return False
        if tok.value in self.TYPE_KEYWORDS:
            return True
        # Un identificador podría ser un tipo (clase definida por usuario)
        if tok.type == "IDENTIFICADOR":
            next_tok = self.peek()
            if next_tok and (next_tok.type == "IDENTIFICADOR" or next_tok.value == "["):
                return True
        return False

    def is_modifier(self):
        tok = self.current()
        return tok is not None and tok.value in self.MODIFIERS

    def parse_modifiers(self):
        """Parsear lista de modificadores."""
        mods = []
        while self.is_modifier():
            mods.append(self.advance().value)
        return mods

    def parse_type(self):
        """Parsear un tipo de dato (incluyendo arrays)."""
        tok = self.current()
        if tok is None:
            return None

        type_name = None
        if tok.value in self.TYPE_KEYWORDS or tok.type == "IDENTIFICADOR":
            type_name = self.advance().value
        else:
            self.report_error(
                f"Se esperaba un tipo de dato pero se encontró '{tok.value}'",
                tok.line, tok.column
            )
            return None

        # Verificar si es array: tipo[]
        while self.check_value("["):
            self.advance()
            self.expect_value("]")
            type_name += "[]"

        return type_name

    # ================================================================
    #  PUNTO DE ENTRADA
    # ================================================================
    def parse(self):
        """Punto de entrada del parser. Retorna el AST."""
        # Consumir import/package silenciosamente (no soportados pero no deben crashear)
        while not self.is_at_end():
            tok = self.current()
            if tok and tok.value in ("import", "package"):
                while not self.is_at_end() and not self.check_value(";"):
                    self.advance()
                if self.check_value(";"): self.advance()
            else:
                break

        classes = []
        while not self.is_at_end():
            prev_pos = self.pos
            try:
                cls = self.parse_class_declaration()
                if cls:
                    classes.append(cls)
            except ParseError:
                self.synchronize()

            if self.pos == prev_pos:
                tok = self.current()
                if tok:
                    self.report_error(
                        f"Token inesperado fuera de una clase: '{tok.value}'",
                        tok.line, tok.column
                    )
                self.advance()

        self.ast = ProgramNode(classes, line=1, column=1)
        return self.ast

    # ================================================================
    #  DECLARACIÓN DE CLASE
    # ================================================================
    def parse_class_declaration(self):
        tok = self.current()
        if tok is None:
            return None

        line, col = tok.line, tok.column
        modifiers = self.parse_modifiers()

        if not self.check_value("class"):
            # No es una clase, intentar recuperar
            self.report_error(
                f"Se esperaba 'class' pero se encontró '{tok.value}'",
                tok.line, tok.column
            )
            self.synchronize()
            return None

        self.advance()  # consumir 'class'

        name_tok = self.expect_type("IDENTIFICADOR")
        name = name_tok.value if name_tok else "???"

        # Soportar: extends ClaseBase, implements Interfaz1, Interfaz2
        # Se consumen silenciosamente (no se validan semánticamente)
        if self.current() and self.current().value == "extends":
            self.advance()  # consumir 'extends'
            self.expect_type("IDENTIFICADOR")  # nombre de la clase base
        if self.current() and self.current().value == "implements":
            self.advance()  # consumir 'implements'
            self.expect_type("IDENTIFICADOR")  # primera interfaz
            while self.check_type("COMA"):
                self.advance()
                self.expect_type("IDENTIFICADOR")

        self.expect_value("{")

        members = []
        while not self.is_at_end() and not self.check_value("}"):
            try:
                member = self.parse_class_member(name)
                if member:
                    members.append(member)
            except ParseError:
                self.synchronize()

        self.expect_value("}")

        return ClassDeclNode(name, modifiers, members, line=line, column=col)

    # ================================================================
    #  MIEMBROS DE CLASE (campo, método, constructor)
    # ================================================================
    def parse_class_member(self, class_name):
        """Distinguir entre campo, método y constructor."""
        tok = self.current()
        if tok is None:
            return None

        line, col = tok.line, tok.column
        modifiers = self.parse_modifiers()

        # Constructor: si el siguiente token es el nombre de la clase seguido de "("
        tok = self.current()
        if tok and tok.type == "IDENTIFICADOR" and tok.value == class_name:
            next_tok = self.peek()
            if next_tok and next_tok.value == "(":
                return self.parse_constructor(modifiers, line, col)

        # Método void: void nombreMetodo(...)
        if tok and tok.value == "void":
            return self.parse_method(modifiers, line, col)

        # Tipo + nombre: puede ser campo o método
        type_name = self.parse_type()
        if type_name is None:
            self.synchronize()
            return None

        name_tok = self.expect_type("IDENTIFICADOR")
        if name_tok is None:
            self.synchronize()
            return None

        # Si sigue "(", es método
        if self.check_value("("):
            return self.parse_method_rest(modifiers, type_name, name_tok.value, line, col)
        else:
            # Es campo
            return self.parse_field_rest(modifiers, type_name, name_tok.value, line, col)

    def parse_constructor(self, modifiers, line, col):
        name = self.advance().value  # nombre del constructor
        self.expect_value("(")
        params = self.parse_parameters()
        self.expect_value(")")
        body = self.parse_block()
        return ConstructorDeclNode(name, modifiers, params, body, line=line, column=col)

    def parse_method(self, modifiers, line, col):
        return_type = self.advance().value  # "void" u otro tipo
        name_tok = self.expect_type("IDENTIFICADOR")
        name = name_tok.value if name_tok else "???"
        self.expect_value("(")
        params = self.parse_parameters()
        self.expect_value(")")
        body = self.parse_block()
        return MethodDeclNode(return_type, name, modifiers, params, body, line=line, column=col)

    def parse_method_rest(self, modifiers, return_type, name, line, col):
        self.expect_value("(")
        params = self.parse_parameters()
        self.expect_value(")")
        body = self.parse_block()
        return MethodDeclNode(return_type, name, modifiers, params, body, line=line, column=col)

    def parse_field_rest(self, modifiers, type_name, name, line, col):
        initializer = None
        if self.match_value("="):
            initializer = self.parse_expression()
        self.expect_value(";")
        return FieldDeclNode(type_name, name, modifiers, initializer, line=line, column=col)

    # ================================================================
    #  PARÁMETROS
    # ================================================================
    def parse_parameters(self):
        params = []
        if self.check_value(")"):
            return params

        params.append(self.parse_single_parameter())
        while self.match_value(","):
            params.append(self.parse_single_parameter())
        return params

    def parse_single_parameter(self):
        tok = self.current()
        line = tok.line if tok else 0
        col = tok.column if tok else 0
        type_name = self.parse_type()
        name_tok = self.expect_type("IDENTIFICADOR")
        name = name_tok.value if name_tok else "???"
        return ParameterNode(type_name or "???", name, line=line, column=col)

    # ================================================================
    #  BLOQUE
    # ================================================================
    def parse_block(self):
        tok = self.current()
        line = tok.line if tok else 0
        col = tok.column if tok else 0

        self.expect_value("{")
        stmts = []
        while not self.is_at_end() and not self.check_value("}"):
            try:
                stmt = self.parse_statement()
                if stmt:
                    stmts.append(stmt)
            except ParseError:
                self.synchronize()

        self.expect_value("}")
        return BlockNode(stmts, line=line, column=col)

    # ================================================================
    #  SENTENCIAS
    # ================================================================
    def parse_statement(self):
        tok = self.current()
        if tok is None:
            return None

        # Bloque anidado
        if tok.value == "{":
            return self.parse_block()

        # Sentencias de control
        if tok.value == "if":
            return self.parse_if()
        if tok.value == "while":
            return self.parse_while()
        if tok.value == "for":
            return self.parse_for()
        if tok.value == "return":
            return self.parse_return()

        # do-while
        if tok.value == "do":
            return self.parse_do_while()

        # switch — consumir completo silenciosamente
        if tok.value == "switch":
            return self.parse_switch()

        # try/catch/finally — consumir completo silenciosamente
        if tok.value == "try":
            return self.parse_try()

        # break / continue / throw — sentencias simples
        if tok.value in ("break", "continue"):
            self.advance()
            self.expect_value(";")
            return None
        if tok.value == "throw":
            self.advance()
            self.parse_expression()
            self.expect_value(";")
            return None

        # Declaración de variable: tipo nombre ...
        if self.is_variable_declaration():
            return self.parse_var_declaration()

        # Expresión como sentencia (asignación, llamada a método, etc.)
        return self.parse_expression_statement()

    def is_variable_declaration(self):
        """Determinar si estamos ante una declaración de variable."""
        tok = self.current()
        if tok is None:
            return False

        # Tipo primitivo + identificador
        if tok.value in self.TYPE_KEYWORDS and tok.value != "void":
            next_tok = self.peek()
            if next_tok and (next_tok.type == "IDENTIFICADOR" or next_tok.value == "["):
                return True

        # Tipo de clase (identificador) + identificador
        if tok.type == "IDENTIFICADOR":
            next_tok = self.peek()
            if next_tok:
                # ClassName varName
                if next_tok.type == "IDENTIFICADOR":
                    return True
                # ClassName[] varName
                if next_tok.value == "[":
                    peek2 = self.peek(2)
                    if peek2 and peek2.value == "]":
                        return True
        return False

    def parse_var_declaration(self):
        tok = self.current()
        line, col = tok.line, tok.column
        type_name = self.parse_type()
        name_tok = self.expect_type("IDENTIFICADOR")
        name = name_tok.value if name_tok else "???"

        initializer = None
        if self.match_value("="):
            initializer = self.parse_expression()

        self.expect_value(";")
        return VarDeclNode(type_name, name, initializer, line=line, column=col)

    def parse_if(self):
        tok = self.advance()  # consumir 'if'
        line, col = tok.line, tok.column
        self.expect_value("(")
        condition = self.parse_expression()
        self.expect_value(")")
        # Permitir cuerpo sin llaves: if (cond) stmt;
        then_block = self.parse_block_or_statement()
        else_block = None
        if self.match_value("else"):
            if self.check_value("if"):
                inner_if = self.parse_if()
                else_block = BlockNode([inner_if], line=inner_if.line, column=inner_if.column)
            else:
                else_block = self.parse_block_or_statement()
        return IfNode(condition, then_block, else_block, line=line, column=col)

    def parse_block_or_statement(self):
        """Parsear bloque { } o sentencia simple."""
        if self.check_value("{"):
            return self.parse_block()
        # Sentencia simple → envolver en BlockNode
        stmt = self.parse_statement()
        stmts = [stmt] if stmt else []
        return BlockNode(stmts, line=0, column=0)

    def parse_while(self):
        tok = self.advance()  # consumir 'while'
        line, col = tok.line, tok.column
        self.expect_value("(")
        condition = self.parse_expression()
        self.expect_value(")")
        body = self.parse_block_or_statement()
        return WhileNode(condition, body, line=line, column=col)

    def parse_for(self):
        tok = self.advance()  # consumir 'for'
        line, col = tok.line, tok.column
        self.expect_value("(")

        # Init
        if self.is_variable_declaration():
            init = self.parse_var_declaration()
        else:
            init = self.parse_expression_for_init()

        # Condition
        condition = self.parse_expression()
        self.expect_value(";")

        # Update
        update = self.parse_expression()

        self.expect_value(")")
        body = self.parse_block()
        return ForNode(init, condition, update, body, line=line, column=col)

    def parse_expression_for_init(self):
        """Parsear la parte init del for como asignación."""
        expr = self.parse_expression()
        self.expect_value(";")
        return expr

    def parse_return(self):
        tok = self.advance()  # consumir 'return'
        line, col = tok.line, tok.column
        value = None
        if not self.check_value(";"):
            value = self.parse_expression()
        self.expect_value(";")
        return ReturnNode(value, line=line, column=col)

    def parse_expression_statement(self):
        tok = self.current()
        line = tok.line if tok else 0
        col = tok.column if tok else 0
        expr = self.parse_expression()

        # Verificar si es asignación (expr = valor)
        curr = self.current()
        if curr and curr.type in self.ASSIGN_OPS:
            op_tok = self.advance()
            value = self.parse_expression()
            self.expect_value(";")
            return AssignmentNode(expr, op_tok.value, value, line=line, column=col)

        self.expect_value(";")
        return ExpressionStmtNode(expr, line=line, column=col)

    # ================================================================
    #  EXPRESIONES CON PRECEDENCIA (de menor a mayor)
    # ================================================================
    def parse_expression(self):
        return self.parse_ternary()

    def parse_ternary(self):
        """expr ? then : else — operador ternario."""
        cond = self.parse_or()
        if self.check_type("INTERROGACION"):
            op = self.advance()  # consumir '?'
            then_expr = self.parse_or()
            self.expect_value(":")
            else_expr = self.parse_or()
            return BinaryOpNode(cond, "?:", BinaryOpNode(then_expr, ":", else_expr,
                                line=op.line, column=op.column),
                                line=op.line, column=op.column)
        return cond

    def parse_or(self):
        left = self.parse_and()
        while self.check_type("OR_LOGICO"):
            op = self.advance()
            right = self.parse_and()
            left = BinaryOpNode(left, op.value, right, line=op.line, column=op.column)
        return left

    def parse_and(self):
        left = self.parse_equality()
        while self.check_type("AND_LOGICO"):
            op = self.advance()
            right = self.parse_equality()
            left = BinaryOpNode(left, op.value, right, line=op.line, column=op.column)
        return left

    def parse_equality(self):
        left = self.parse_relational()
        while self.check_type("IGUALDAD") or self.check_type("DIFERENTE"):
            op = self.advance()
            right = self.parse_relational()
            left = BinaryOpNode(left, op.value, right, line=op.line, column=op.column)
        return left

    def parse_relational(self):
        left = self.parse_additive()
        while self.current() and self.current().type in ("MENOR", "MAYOR", "MENOR_IGUAL", "MAYOR_IGUAL"):
            op = self.advance()
            right = self.parse_additive()
            left = BinaryOpNode(left, op.value, right, line=op.line, column=op.column)
        return left

    def parse_additive(self):
        left = self.parse_multiplicative()
        while self.current() and self.current().type in ("SUMA", "RESTA"):
            op = self.advance()
            right = self.parse_multiplicative()
            left = BinaryOpNode(left, op.value, right, line=op.line, column=op.column)
        return left

    def parse_multiplicative(self):
        left = self.parse_unary()
        while self.current() and self.current().type in ("MULTIPLICACION", "DIVISION", "MODULO"):
            op = self.advance()
            right = self.parse_unary()
            left = BinaryOpNode(left, op.value, right, line=op.line, column=op.column)
        return left

    def parse_unary(self):
        tok = self.current()
        if tok is None:
            self.report_error("Se esperaba una expresión pero se llegó al final del archivo")
            return LiteralNode(0, "int", line=0, column=0)

        # ! (NOT lógico)
        if tok.type == "NOT_LOGICO":
            op = self.advance()
            operand = self.parse_unary()
            return UnaryOpNode(op.value, operand, prefix=True, line=op.line, column=op.column)

        # - (negación)
        if tok.type == "RESTA":
            op = self.advance()
            operand = self.parse_unary()
            return UnaryOpNode(op.value, operand, prefix=True, line=op.line, column=op.column)

        # ++ / -- prefijo
        if tok.type in ("INCREMENTO", "DECREMENTO"):
            op = self.advance()
            operand = self.parse_postfix()
            return UnaryOpNode(op.value, operand, prefix=True, line=op.line, column=op.column)

        return self.parse_postfix()

    def parse_postfix(self):
        expr = self.parse_call_or_access()

        # ++ / -- postfijo
        if self.current() and self.current().type in ("INCREMENTO", "DECREMENTO"):
            op = self.advance()
            expr = UnaryOpNode(op.value, expr, prefix=False, line=op.line, column=op.column)

        return expr

    # ================================================================
    #  ACCESO A MIEMBROS Y LLAMADAS A MÉTODOS
    # ================================================================
    def parse_call_or_access(self):
        expr = self.parse_primary()

        while True:
            if self.check_value("."):
                self.advance()  # consumir '.'
                member_tok = self.expect_type("IDENTIFICADOR")
                member = member_tok.value if member_tok else "???"
                expr = MemberAccessNode(expr, member,
                                        line=member_tok.line if member_tok else 0,
                                        column=member_tok.column if member_tok else 0)
            elif self.check_value("("):
                self.advance()  # consumir '('
                args = self.parse_arguments()
                self.expect_value(")")
                expr = MethodCallNode(expr, args, line=expr.line, column=expr.column)
            elif self.check_value("["):
                self.advance()
                index = self.parse_expression()
                self.expect_value("]")
                expr = ArrayAccessNode(expr, index, line=expr.line, column=expr.column)
            else:
                break

        return expr

    def parse_arguments(self):
        args = []
        if self.check_value(")"):
            return args
        args.append(self.parse_expression())
        while self.match_value(","):
            args.append(self.parse_expression())
        return args

    # ================================================================
    #  PRIMARIOS (literales, identificadores, paréntesis, new, this)
    # ================================================================
    def parse_primary(self):
        tok = self.current()
        if tok is None:
            self.report_error("Se esperaba una expresión pero se llegó al final del archivo")
            return LiteralNode(0, "int", line=0, column=0)

        # Literales numéricos
        if tok.type == "INTEGER":
            self.advance()
            return LiteralNode(int(tok.value.rstrip("lL")), "int", line=tok.line, column=tok.column)

        if tok.type == "FLOAT":
            self.advance()
            return LiteralNode(float(tok.value), "double", line=tok.line, column=tok.column)

        # String literal
        if tok.type == "STRING":
            self.advance()
            return LiteralNode(tok.value, "String", line=tok.line, column=tok.column)

        # Char literal
        if tok.type == "CHAR":
            self.advance()
            return LiteralNode(tok.value, "char", line=tok.line, column=tok.column)

        # Booleanos y null
        if tok.type == "LITERAL_BOOLEANO":
            self.advance()
            if tok.value == "null":
                return LiteralNode(None, "null", line=tok.line, column=tok.column)
            return LiteralNode(tok.value == "true", "boolean", line=tok.line, column=tok.column)

        # this
        if tok.value == "this":
            self.advance()
            return ThisNode(line=tok.line, column=tok.column)

        # new ClassName(args)
        if tok.value == "new":
            return self.parse_new_expression()

        # Paréntesis (expresión agrupada)
        if tok.value == "(":
            self.advance()
            expr = self.parse_expression()
            self.expect_value(")")
            return expr

        # Identificador
        if tok.type == "IDENTIFICADOR" or tok.type == "PALABRA_RESERVADA":
            # Permitir System, out, println como identificadores en expresiones
            if tok.value not in ("if", "else", "while", "for", "return", "class",
                                 "new", "this", "void"):
                self.advance()
                return IdentifierNode(tok.value, line=tok.line, column=tok.column)

        # Error: token inesperado
        self.report_error(
            f"Token inesperado: '{tok.value}' ({tok.type})",
            tok.line, tok.column
        )
        self.advance()  # consumir para no quedarnos en loop
        return LiteralNode(0, "int", line=tok.line, column=tok.column)

    def parse_new_expression(self):
        tok = self.advance()  # consumir 'new'
        line, col = tok.line, tok.column
        name_tok = self.expect_type("IDENTIFICADOR")
        class_name = name_tok.value if name_tok else "???"
        self.expect_value("(")
        args = self.parse_arguments()
        self.expect_value(")")
        return NewObjectNode(class_name, args, line=line, column=col)

    # ================================================================
    #  SENTENCIAS ADICIONALES
    # ================================================================
    def parse_do_while(self):
        """do { } while (cond);"""
        self.advance()  # consumir 'do'
        body = self.parse_block()
        if self.current() and self.current().value == "while":
            self.advance()
            self.expect_value("(")
            cond = self.parse_expression()
            self.expect_value(")")
            self.expect_value(";")
        return WhileNode(cond if 'cond' in dir() else None, body,
                         line=body.line if body else 0,
                         column=body.column if body else 0)

    def parse_switch(self):
        """switch (expr) { case x: ... default: ... }"""
        tok = self.advance()  # consumir 'switch'
        self.expect_value("(")
        self.parse_expression()
        self.expect_value(")")
        self.expect_value("{")
        # Consumir todo el cuerpo del switch
        depth = 1
        while not self.is_at_end() and depth > 0:
            t = self.current()
            if t.value == "{": depth += 1
            elif t.value == "}": depth -= 1
            self.advance()
        return None  # switch no genera nodo AST (simplificación)

    def parse_try(self):
        """try { } catch (Type e) { } finally { }"""
        self.advance()  # consumir 'try'
        self.parse_block()
        # Uno o más catch
        while self.current() and self.current().value == "catch":
            self.advance()
            self.expect_value("(")
            # Consumir el parámetro del catch
            while not self.is_at_end() and not self.check_value(")"):
                self.advance()
            self.expect_value(")")
            self.parse_block()
        # Finally opcional
        if self.current() and self.current().value == "finally":
            self.advance()
            self.parse_block()
        return None  # try no genera nodo AST (simplificación)
