"""
Analizador Semántico
Recorre el AST validando:
  1. Chequeo de tipos (Type Checking)
  2. Gestión de ámbitos (Scope)
  3. Declaración previa de variables
  4. Compatibilidad de operaciones
"""

from ..classes.ast_nodes import *


# ================================================================
#  TABLA DE SÍMBOLOS CON SCOPES
# ================================================================
class Symbol:
    """Un símbolo en la tabla."""
    def __init__(self, name, sym_type, data_type, line=0, column=0,
                 params=None, modifiers=None):
        self.name = name
        self.sym_type = sym_type       # "variable", "method", "class", "parameter", "field"
        self.data_type = data_type     # "int", "String", "void", etc.
        self.line = line
        self.column = column
        self.params = params or []     # para métodos: lista de (tipo, nombre)
        self.modifiers = modifiers or []

    def __repr__(self):
        return f"Symbol({self.name}, {self.sym_type}, {self.data_type})"


class Scope:
    """Un ámbito léxico (scope)."""
    def __init__(self, name="global", parent=None):
        self.name = name
        self.parent = parent
        self.symbols = {}
        self.children = []
        if parent:
            parent.children.append(self)

    def define(self, symbol):
        self.symbols[symbol.name] = symbol

    def lookup(self, name):
        """Buscar símbolo en este scope y sus ancestros."""
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def lookup_local(self, name):
        """Buscar solo en este scope (para detectar redeclaraciones)."""
        return self.symbols.get(name)


class SymbolTable:
    """Tabla de símbolos global con gestión de scopes."""
    def __init__(self):
        self.global_scope = Scope("global")
        self.current_scope = self.global_scope
        self.all_symbols = []  # lista plana para visualización

    def enter_scope(self, name):
        new_scope = Scope(name, self.current_scope)
        self.current_scope = new_scope
        return new_scope

    def exit_scope(self):
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent

    def define(self, symbol):
        self.current_scope.define(symbol)
        self.all_symbols.append(symbol)

    def lookup(self, name):
        return self.current_scope.lookup(name)

    def lookup_local(self, name):
        return self.current_scope.lookup_local(name)


# ================================================================
#  COMPATIBILIDAD DE TIPOS
# ================================================================
NUMERIC_TYPES = {"int", "float", "double", "long", "short", "byte"}
INTEGER_TYPES = {"int", "long", "short", "byte"}

def types_compatible(left, right):
    """Verificar si dos tipos son compatibles para asignación."""
    if left == right:
        return True
    # Object acepta cualquier tipo (polimorfismo)
    if left == "Object" or right == "Object":
        return True
    if left in NUMERIC_TYPES and right in NUMERIC_TYPES:
        return True
    if left == "String" and right == "String":
        return True
    # null es compatible con tipos de referencia
    if right == "null" and left not in NUMERIC_TYPES and left != "boolean":
        return True
    if left == "null" and right not in NUMERIC_TYPES and right != "boolean":
        return True
    return False


def result_type(left, op, right):
    """Determinar el tipo resultado de una operación binaria."""
    # Concatenación de strings
    if op == "+" and (left == "String" or right == "String"):
        return "String"

    # Operaciones aritméticas
    if op in ("+", "-", "*", "/", "%"):
        if left in NUMERIC_TYPES and right in NUMERIC_TYPES:
            if "double" in (left, right):
                return "double"
            if "float" in (left, right):
                return "float"
            if "long" in (left, right):
                return "long"
            return "int"
        return None

    # Comparaciones
    if op in ("<", ">", "<=", ">="):
        if left in NUMERIC_TYPES and right in NUMERIC_TYPES:
            return "boolean"
        return None

    # Igualdad
    if op in ("==", "!="):
        return "boolean"

    # Lógicos
    if op in ("&&", "||"):
        if left == "boolean" and right == "boolean":
            return "boolean"
        return None

    return None


# ================================================================
#  ANALIZADOR SEMÁNTICO (VISITOR)
# ================================================================
class SemanticAnalyzer:
    """Recorre el AST validando semántica."""

    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors = []
        self.current_class = None
        self.current_method_return = None
        self._register_builtins()

    def _register_builtins(self):
        """Registrar clases y métodos built-in de Java."""
        builtins = [
            Symbol("System", "class", "System", 0, 0),
            Symbol("out", "field", "PrintStream", 0, 0),
            Symbol("println", "method", "void", 0, 0,
                   params=[("Object", "msg")]),
            Symbol("print", "method", "void", 0, 0,
                   params=[("Object", "msg")]),
            Symbol("parseInt", "method", "int", 0, 0,
                   params=[("String", "s")]),
            Symbol("toString", "method", "String", 0, 0),
            Symbol("length", "method", "int", 0, 0),
            Symbol("equals", "method", "boolean", 0, 0,
                   params=[("Object", "obj")]),
        ]
        for sym in builtins:
            self.symbol_table.global_scope.define(sym)

    def report_error(self, message, line=0, column=0):
        code = f"SEM-{len(self.errors) + 1:03d}"
        self.errors.append({
            "codigo": code,
            "mensaje": message,
            "linea": line,
            "columna": column
        })

    def analyze(self, ast):
        """Punto de entrada."""
        if ast is None:
            return
        self.visit(ast)

    def visit(self, node):
        if node is None:
            return "void"
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        return "void"

    # ================================================================
    #  PROGRAMA Y CLASE
    # ================================================================
    def visit_ProgramNode(self, node):
        for cls in node.classes:
            self.visit(cls)

    def visit_ClassDeclNode(self, node):
        # Registrar la clase
        sym = Symbol(node.name, "class", node.name,
                     node.line, node.column, modifiers=node.modifiers)
        existing = self.symbol_table.lookup_local(node.name)
        if existing:
            self.report_error(
                f"La clase '{node.name}' ya fue declarada en línea {existing.line}",
                node.line, node.column
            )
        else:
            self.symbol_table.define(sym)

        self.current_class = node.name
        self.symbol_table.enter_scope(f"class_{node.name}")

        # Primer pase: registrar todos los campos y métodos
        for member in node.members:
            if isinstance(member, FieldDeclNode):
                self._register_field(member)
            elif isinstance(member, MethodDeclNode):
                self._register_method(member)
            elif isinstance(member, ConstructorDeclNode):
                self._register_constructor(member)

        # Segundo pase: analizar cuerpos
        for member in node.members:
            if isinstance(member, FieldDeclNode):
                if member.initializer:
                    init_type = self.visit(member.initializer)
                    if not types_compatible(member.type_name, init_type):
                        self.report_error(
                            f"No se puede asignar '{init_type}' a campo '{member.name}' de tipo '{member.type_name}'",
                            member.line, member.column
                        )
            elif isinstance(member, MethodDeclNode):
                self._analyze_method(member)
            elif isinstance(member, ConstructorDeclNode):
                self._analyze_constructor(member)

        self.symbol_table.exit_scope()
        self.current_class = None

    def _register_field(self, node):
        existing = self.symbol_table.lookup_local(node.name)
        if existing:
            self.report_error(
                f"El campo '{node.name}' ya fue declarado en línea {existing.line}",
                node.line, node.column
            )
        else:
            sym = Symbol(node.name, "field", node.type_name,
                         node.line, node.column, modifiers=node.modifiers)
            self.symbol_table.define(sym)

    def _register_method(self, node):
        params = [(p.type_name, p.name) for p in node.params]
        sym = Symbol(node.name, "method", node.return_type,
                     node.line, node.column, params=params, modifiers=node.modifiers)
        existing = self.symbol_table.lookup_local(node.name)
        if existing and existing.sym_type == "method":
            self.report_error(
                f"El método '{node.name}' ya fue declarado en línea {existing.line}",
                node.line, node.column
            )
        else:
            self.symbol_table.define(sym)

    def _register_constructor(self, node):
        params = [(p.type_name, p.name) for p in node.params]
        sym = Symbol(node.name, "constructor", node.name,
                     node.line, node.column, params=params, modifiers=node.modifiers)
        self.symbol_table.define(sym)

    def _analyze_method(self, node):
        self.current_method_return = node.return_type
        self.symbol_table.enter_scope(f"method_{node.name}")

        for param in node.params:
            sym = Symbol(param.name, "parameter", param.type_name,
                         param.line, param.column)
            self.symbol_table.define(sym)

        self.visit(node.body)
        self.symbol_table.exit_scope()
        self.current_method_return = None

    def _analyze_constructor(self, node):
        self.current_method_return = "void"
        self.symbol_table.enter_scope(f"constructor_{node.name}")

        for param in node.params:
            sym = Symbol(param.name, "parameter", param.type_name,
                         param.line, param.column)
            self.symbol_table.define(sym)

        self.visit(node.body)
        self.symbol_table.exit_scope()
        self.current_method_return = None

    # ================================================================
    #  SENTENCIAS
    # ================================================================
    def visit_BlockNode(self, node):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_VarDeclNode(self, node):
        existing = self.symbol_table.lookup_local(node.name)
        if existing:
            self.report_error(
                f"La variable '{node.name}' ya fue declarada en este ámbito (línea {existing.line})",
                node.line, node.column
            )
        else:
            sym = Symbol(node.name, "variable", node.type_name,
                         node.line, node.column)
            self.symbol_table.define(sym)

        if node.initializer:
            init_type = self.visit(node.initializer)
            if init_type and not types_compatible(node.type_name, init_type):
                self.report_error(
                    f"No se puede asignar '{init_type}' a variable '{node.name}' de tipo '{node.type_name}'",
                    node.line, node.column
                )

    def visit_AssignmentNode(self, node):
        target_type = self.visit(node.target)
        value_type = self.visit(node.value)

        if target_type and value_type:
            if node.operator == "=":
                if not types_compatible(target_type, value_type):
                    self.report_error(
                        f"No se puede asignar '{value_type}' a tipo '{target_type}'",
                        node.line, node.column
                    )
            else:
                # +=, -=, etc.
                rt = result_type(target_type, node.operator[0], value_type)
                if rt is None:
                    self.report_error(
                        f"Operador '{node.operator}' no es compatible entre '{target_type}' y '{value_type}'",
                        node.line, node.column
                    )

    def visit_IfNode(self, node):
        cond_type = self.visit(node.condition)
        if cond_type != "boolean" and cond_type is not None:
            self.report_error(
                f"La condición del 'if' debe ser boolean, se encontró '{cond_type}'",
                node.line, node.column
            )

        self.symbol_table.enter_scope("if_then")
        self.visit(node.then_block)
        self.symbol_table.exit_scope()

        if node.else_block:
            self.symbol_table.enter_scope("if_else")
            self.visit(node.else_block)
            self.symbol_table.exit_scope()

    def visit_WhileNode(self, node):
        cond_type = self.visit(node.condition)
        if cond_type != "boolean" and cond_type is not None:
            self.report_error(
                f"La condición del 'while' debe ser boolean, se encontró '{cond_type}'",
                node.line, node.column
            )

        self.symbol_table.enter_scope("while")
        self.visit(node.body)
        self.symbol_table.exit_scope()

    def visit_ForNode(self, node):
        self.symbol_table.enter_scope("for")
        self.visit(node.init)
        cond_type = self.visit(node.condition)
        if cond_type != "boolean" and cond_type is not None:
            self.report_error(
                f"La condición del 'for' debe ser boolean, se encontró '{cond_type}'",
                node.line, node.column
            )
        self.visit(node.update)
        self.visit(node.body)
        self.symbol_table.exit_scope()

    def visit_ReturnNode(self, node):
        if node.value:
            ret_type = self.visit(node.value)
            if self.current_method_return and self.current_method_return != "void":
                if ret_type and not types_compatible(self.current_method_return, ret_type):
                    self.report_error(
                        f"Tipo de retorno incompatible: se esperaba '{self.current_method_return}' "
                        f"pero se encontró '{ret_type}'",
                        node.line, node.column
                    )
        else:
            if self.current_method_return and self.current_method_return != "void":
                self.report_error(
                    f"El método debe retornar un valor de tipo '{self.current_method_return}'",
                    node.line, node.column
                )

    def visit_ExpressionStmtNode(self, node):
        self.visit(node.expression)

    # ================================================================
    #  EXPRESIONES
    # ================================================================
    def visit_BinaryOpNode(self, node):
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)

        rt = result_type(left_type, node.operator, right_type)
        if rt is None:
            self.report_error(
                f"Operación '{node.operator}' no válida entre '{left_type}' y '{right_type}'",
                node.line, node.column
            )
            return "void"
        return rt

    def visit_UnaryOpNode(self, node):
        operand_type = self.visit(node.operand)

        if node.operator == "!":
            if operand_type != "boolean":
                self.report_error(
                    f"Operador '!' requiere tipo boolean, se encontró '{operand_type}'",
                    node.line, node.column
                )
            return "boolean"

        if node.operator == "-":
            if operand_type not in NUMERIC_TYPES:
                self.report_error(
                    f"Operador unario '-' requiere tipo numérico, se encontró '{operand_type}'",
                    node.line, node.column
                )
            return operand_type

        if node.operator in ("++", "--"):
            if operand_type not in NUMERIC_TYPES:
                self.report_error(
                    f"Operador '{node.operator}' requiere tipo numérico, se encontró '{operand_type}'",
                    node.line, node.column
                )
            return operand_type

        return operand_type

    def visit_LiteralNode(self, node):
        return node.literal_type

    def visit_IdentifierNode(self, node):
        sym = self.symbol_table.lookup(node.name)
        if sym is None:
            self.report_error(
                f"Identificador '{node.name}' no declarado",
                node.line, node.column
            )
            return "void"
        return sym.data_type

    def visit_MemberAccessNode(self, node):
        obj_type = self.visit(node.object)

        # this.field -> buscar el campo en la clase actual (saltar parámetros locales)
        if isinstance(node.object, ThisNode) and self.current_class:
            # Buscar en todos los scopes por un campo con ese nombre
            scope = self.symbol_table.current_scope
            while scope:
                sym = scope.symbols.get(node.member)
                if sym and sym.sym_type == "field":
                    return sym.data_type
                scope = scope.parent
            # Si no encontramos field, buscar cualquier símbolo
            sym = self.symbol_table.lookup(node.member)
            if sym:
                return sym.data_type

        # obj.field donde obj es un tipo conocido -> intentar resolver miembro
        if obj_type and obj_type not in ("void",):
            sym = self.symbol_table.lookup(node.member)
            if sym:
                return sym.data_type

        # Para cadenas tipo System.out.println, no validamos más profundo
        return "void"

    def visit_MethodCallNode(self, node):
        # Resolver el tipo del método llamado
        method_name = None
        sym = None

        if isinstance(node.callee, IdentifierNode):
            method_name = node.callee.name
            sym = self.symbol_table.lookup(method_name)
        elif isinstance(node.callee, MemberAccessNode):
            # obj.method() — resolver el nombre del método
            method_name = node.callee.member
            sym = self.symbol_table.lookup(method_name)
            # Visitar el objeto para validarlo
            self.visit(node.callee.object)

        if sym and sym.sym_type in ("method", "constructor"):
            # Validar cantidad de argumentos
            if len(node.arguments) != len(sym.params):
                self.report_error(
                    f"Método '{sym.name}' espera {len(sym.params)} argumento(s) "
                    f"pero recibió {len(node.arguments)}",
                    node.line, node.column
                )
            # Validar tipos de argumentos
            for i, (arg, param) in enumerate(zip(node.arguments, sym.params)):
                arg_type = self.visit(arg)
                param_type = param[0]
                if arg_type and not types_compatible(param_type, arg_type):
                    self.report_error(
                        f"Argumento {i+1} del método '{sym.name}': "
                        f"se esperaba '{param_type}' pero se recibió '{arg_type}'",
                        node.line, node.column
                    )
            return sym.data_type

        # Para llamadas no resueltas (System.out.println, etc.), validar args
        for arg in node.arguments:
            self.visit(arg)
        return "void"

    def visit_NewObjectNode(self, node):
        for arg in node.arguments:
            self.visit(arg)
        return node.class_name

    def visit_ThisNode(self, node):
        if self.current_class:
            return self.current_class
        self.report_error("'this' usado fuera de una clase", node.line, node.column)
        return "void"

    def visit_ArrayAccessNode(self, node):
        arr_type = self.visit(node.array)
        idx_type = self.visit(node.index)
        if idx_type not in INTEGER_TYPES:
            self.report_error(
                f"El índice del array debe ser entero, se encontró '{idx_type}'",
                node.line, node.column
            )
        if arr_type and arr_type.endswith("[]"):
            return arr_type[:-2]
        return "void"

    def visit_CastNode(self, node):
        self.visit(node.expression)
        return node.type_name
