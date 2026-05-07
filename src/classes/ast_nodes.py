"""
Nodos del Árbol de Sintaxis Abstracta (AST)
Cada clase representa una construcción del lenguaje Java.
"""


# ================================================================
#  NODO BASE
# ================================================================
class ASTNode:
    """Clase base para todos los nodos del AST."""
    def __init__(self, line=0, column=0):
        self.line = line
        self.column = column

    def accept(self, visitor):
        method_name = f"visit_{type(self).__name__}"
        visitor_method = getattr(visitor, method_name, visitor.generic_visit)
        return visitor_method(self)


# ================================================================
#  PROGRAMA Y CLASE
# ================================================================
class ProgramNode(ASTNode):
    def __init__(self, classes, **kw):
        super().__init__(**kw)
        self.classes = classes  # lista de ClassDeclNode


class ClassDeclNode(ASTNode):
    def __init__(self, name, modifiers, members, **kw):
        super().__init__(**kw)
        self.name = name
        self.modifiers = modifiers    # ["public", "static", ...]
        self.members = members        # lista de nodos miembro


# ================================================================
#  MIEMBROS DE CLASE
# ================================================================
class FieldDeclNode(ASTNode):
    """Declaración de atributo de clase."""
    def __init__(self, type_name, name, modifiers, initializer=None, **kw):
        super().__init__(**kw)
        self.type_name = type_name
        self.name = name
        self.modifiers = modifiers
        self.initializer = initializer


class MethodDeclNode(ASTNode):
    """Declaración de método."""
    def __init__(self, return_type, name, modifiers, params, body, **kw):
        super().__init__(**kw)
        self.return_type = return_type
        self.name = name
        self.modifiers = modifiers
        self.params = params          # lista de ParameterNode
        self.body = body              # BlockNode


class ConstructorDeclNode(ASTNode):
    """Declaración de constructor."""
    def __init__(self, name, modifiers, params, body, **kw):
        super().__init__(**kw)
        self.name = name
        self.modifiers = modifiers
        self.params = params
        self.body = body


class ParameterNode(ASTNode):
    def __init__(self, type_name, name, **kw):
        super().__init__(**kw)
        self.type_name = type_name
        self.name = name


# ================================================================
#  SENTENCIAS
# ================================================================
class BlockNode(ASTNode):
    def __init__(self, statements, **kw):
        super().__init__(**kw)
        self.statements = statements


class VarDeclNode(ASTNode):
    """Declaración de variable local."""
    def __init__(self, type_name, name, initializer=None, **kw):
        super().__init__(**kw)
        self.type_name = type_name
        self.name = name
        self.initializer = initializer


class AssignmentNode(ASTNode):
    def __init__(self, target, operator, value, **kw):
        super().__init__(**kw)
        self.target = target        # IdentifierNode o MemberAccessNode
        self.operator = operator    # "=", "+=", "-=", etc.
        self.value = value


class IfNode(ASTNode):
    def __init__(self, condition, then_block, else_block=None, **kw):
        super().__init__(**kw)
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block


class WhileNode(ASTNode):
    def __init__(self, condition, body, **kw):
        super().__init__(**kw)
        self.condition = condition
        self.body = body


class ForNode(ASTNode):
    def __init__(self, init, condition, update, body, **kw):
        super().__init__(**kw)
        self.init = init
        self.condition = condition
        self.update = update
        self.body = body


class ReturnNode(ASTNode):
    def __init__(self, value=None, **kw):
        super().__init__(**kw)
        self.value = value


class ExpressionStmtNode(ASTNode):
    """Sentencia que es solo una expresión (e.g., llamada a método)."""
    def __init__(self, expression, **kw):
        super().__init__(**kw)
        self.expression = expression


# ================================================================
#  EXPRESIONES
# ================================================================
class BinaryOpNode(ASTNode):
    def __init__(self, left, operator, right, **kw):
        super().__init__(**kw)
        self.left = left
        self.operator = operator
        self.right = right


class UnaryOpNode(ASTNode):
    def __init__(self, operator, operand, prefix=True, **kw):
        super().__init__(**kw)
        self.operator = operator
        self.operand = operand
        self.prefix = prefix          # True=prefijo, False=postfijo


class LiteralNode(ASTNode):
    def __init__(self, value, literal_type, **kw):
        super().__init__(**kw)
        self.value = value
        self.literal_type = literal_type  # "int", "float", "String", "boolean", "null", "char"


class IdentifierNode(ASTNode):
    def __init__(self, name, **kw):
        super().__init__(**kw)
        self.name = name


class MemberAccessNode(ASTNode):
    """Acceso a miembro: obj.field"""
    def __init__(self, object, member, **kw):
        super().__init__(**kw)
        self.object = object
        self.member = member


class MethodCallNode(ASTNode):
    """Llamada a método: obj.method(args) o method(args)"""
    def __init__(self, callee, arguments, **kw):
        super().__init__(**kw)
        self.callee = callee          # IdentifierNode o MemberAccessNode
        self.arguments = arguments


class NewObjectNode(ASTNode):
    """Creación de objeto: new ClassName(args)"""
    def __init__(self, class_name, arguments, **kw):
        super().__init__(**kw)
        self.class_name = class_name
        self.arguments = arguments


class ThisNode(ASTNode):
    pass


class ArrayAccessNode(ASTNode):
    def __init__(self, array, index, **kw):
        super().__init__(**kw)
        self.array = array
        self.index = index


class CastNode(ASTNode):
    def __init__(self, type_name, expression, **kw):
        super().__init__(**kw)
        self.type_name = type_name
        self.expression = expression
