import re

# ============================================================
# ESPECIFICACIÓN LÉXICA — Analizador Léxico Java
# Universidad Mariano Gálvez de Guatemala | Compiladores
#
# Implementación: Master Regex (AFD combinado)
# Un único patrón combinado con grupos nombrados equivale a la
# unión de múltiples AFDs, con prioridad determinada por orden.
# Técnica: Maximal Munch — siempre se consume el lexema más largo.
# ============================================================

# ============================================================
# PALABRAS RESERVADAS DE JAVA (50 keywords oficiales)
# Fuente: Java Language Specification, SE 21
# ============================================================
KEYWORDS = {
    "abstract", "assert", "boolean", "break", "byte",
    "case", "catch", "char", "class", "const",
    "continue", "default", "do", "double",
    "else", "enum", "extends",
    "final", "finally", "float", "for",
    "goto",
    "if", "implements", "import", "instanceof", "int", "interface",
    "long",
    "native", "new",
    "package", "private", "protected", "public",
    "return",
    "short", "static", "strictfp", "super", "switch", "synchronized",
    "this", "throw", "throws", "transient", "try",
    "void", "volatile", "while",
    # String y System son clases de la librería estándar, NO keywords de Java
}

# Literales booleanos y null
LITERALS = {"true", "false", "null"}

# ============================================================
# MASTER REGEX - Un solo patrón combinado con grupos nombrados
# El ORDEN importa: patrones más específicos van primero
# ============================================================
MASTER_PATTERN = re.compile('|'.join([
    # ---------- COMENTARIOS (se ignoran) ----------
    r'(?P<COMENTARIO_MULTI>/\*[\s\S]*?\*/)',       # /* ... */
    r'(?P<COMENTARIO_LINEA>//[^\n]*)',              # // ...

    # ---------- LITERALES ----------
    r'(?P<STRING>"(?:[^"\\]|\\.)*")',               # "cadena"
    r'(?P<CHAR>\'(?:[^\'\\]|\\.)\'){1}',            # 'c'
    r'(?P<FLOAT>\d+\.\d+(?:[eE][+-]?\d+)?)',       # 3.14, 1.5e10
    r'(?P<INTEGER>\d+[lL]?)',                       # 42, 100L

    # ---------- IDENTIFICADORES / PALABRAS RESERVADAS ----------
    r'(?P<ID>[A-Za-z_$][A-Za-z0-9_$]*)',

    # ---------- OPERADORES (de mayor a menor longitud) ----------
    r'(?P<INCREMENTO>\+\+)',
    r'(?P<DECREMENTO>--)',
    r'(?P<SHIFT_LEFT_ASSIGN><<=)',
    r'(?P<SHIFT_RIGHT_ASSIGN>>>=|>>=)',
    r'(?P<SHIFT_LEFT><<)',
    r'(?P<SHIFT_RIGHT_UNSIGNED>>>>)',
    r'(?P<SHIFT_RIGHT>>>)',
    r'(?P<AND_LOGICO>&&)',
    r'(?P<OR_LOGICO>\|\|)',
    r'(?P<MENOR_IGUAL><=)',
    r'(?P<MAYOR_IGUAL>>=)',
    r'(?P<IGUALDAD>==)',
    r'(?P<DIFERENTE>!=)',
    r'(?P<SUMA_ASIGN>\+=)',
    r'(?P<RESTA_ASIGN>-=)',
    r'(?P<MULT_ASIGN>\*=)',
    r'(?P<DIV_ASIGN>/=)',
    r'(?P<MOD_ASIGN>%=)',
    r'(?P<AND_ASIGN>&=)',
    r'(?P<OR_ASIGN>\|=)',
    r'(?P<XOR_ASIGN>\^=)',
    r'(?P<ASIGNACION>=)',
    r'(?P<MENOR><)',
    r'(?P<MAYOR>>)',
    r'(?P<SUMA>\+)',
    r'(?P<RESTA>-)',
    r'(?P<MULTIPLICACION>\*)',
    r'(?P<DIVISION>/)',
    r'(?P<MODULO>%)',
    r'(?P<NOT_LOGICO>!)',
    r'(?P<AND_BIT>&)',
    r'(?P<OR_BIT>\|)',
    r'(?P<XOR_BIT>\^)',
    r'(?P<NOT_BIT>~)',

    # ---------- DELIMITADORES ----------
    r'(?P<PAREN_IZQ>\()',
    r'(?P<PAREN_DER>\))',
    r'(?P<LLAVE_IZQ>\{)',
    r'(?P<LLAVE_DER>\})',
    r'(?P<CORCHETE_IZQ>\[)',
    r'(?P<CORCHETE_DER>\])',
    r'(?P<PUNTO_COMA>;)',
    r'(?P<COMA>,)',
    r'(?P<PUNTO>\.)',
    r'(?P<DOS_PUNTOS>:)',
    r'(?P<INTERROGACION>\?)',
    r'(?P<ARROBA>@)',

    # ---------- ESPACIOS EN BLANCO (se ignoran) ----------
    r'(?P<ESPACIO>\s+)',

    # ---------- CUALQUIER OTRO CARÁCTER = ERROR LÉXICO ----------
    r'(?P<ERROR>.)',
]))
