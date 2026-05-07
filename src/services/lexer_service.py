import re
from ..lexer.patters import MASTER_PATTERN, KEYWORDS, LITERALS
from ..classes.token import Token


class LexerService:
    """
    Analizador Léxico (Scanner) — Compiladores, Fase 1
    Universidad Mariano Gálvez de Guatemala

    Implementa un scanner de una sola pasada usando un Master Regex
    (equivalente a un AFD combinado). Lee el código fuente carácter a
    carácter y produce:
      - Lista completa de tokens con tipo, lexema, línea y columna
      - Tabla léxica de símbolos (identificadores únicos + ocurrencias)
      - Lista de errores léxicos con posición exacta y lexema inválido

    Estrategia de reconocimiento:
      1. Patrones más específicos tienen prioridad (orden en MASTER_PATTERN)
      2. Identificadores se reconocen primero; luego se reclasifican
         consultando la tabla de KEYWORDS (técnica maximal munch)
      3. Recuperación de errores por pánico: carácter inválido se reporta
         y el análisis continúa desde el siguiente carácter
    """

    def __init__(self, code: str):
        self.code = code
        self.tokens: list = []
        self.tabla_simbolos: list = []
        self.errores: list = []
        self.stats: dict = {}   # Estadísticas por categoría de token

    # ----------------------------------------------------------------
    #  Método principal de tokenización
    # ----------------------------------------------------------------
    def tokenizar(self):
        self.tokens = []
        self.tabla_simbolos = []
        self.errores = []
        _sym_index = {}   # nombre -> índice en tabla_simbolos para actualizar ocurrencias

        for match in MASTER_PATTERN.finditer(self.code):
            kind = match.lastgroup        # nombre del grupo que hizo match
            value = match.group()         # texto capturado
            start = match.start()         # posición absoluta en el string

            # Calcular línea y columna
            line = self.code[:start].count("\n") + 1
            last_newline = self.code.rfind("\n", 0, start)
            column = start - last_newline  # 1-based

            # ---- Ignorar comentarios y espacios ----
            if kind in ("COMENTARIO_MULTI", "COMENTARIO_LINEA", "ESPACIO"):
                continue

            # ---- Error léxico ----
            if kind == "ERROR":
                # Intentar agrupar caracteres inválidos consecutivos
                desc = f"Carácter no reconocido en el alfabeto del lenguaje: '{value}'"
                self.errores.append({
                    "lexema": value,
                    "linea": line,
                    "columna": column,
                    "descripcion": desc
                })
                continue

            # ---- Clasificar identificadores vs palabras reservadas ----
            if kind == "ID":
                if value in KEYWORDS:
                    kind = "PALABRA_RESERVADA"
                elif value in LITERALS:
                    kind = "LITERAL_BOOLEANO"
                else:
                    kind = "IDENTIFICADOR"

                    if value in _sym_index:
                        # Ya existe: incrementar ocurrencias y registrar línea
                        entry = self.tabla_simbolos[_sym_index[value]]
                        entry["ocurrencias"] += 1
                        if line not in entry["lineas"]:
                            entry["lineas"].append(line)
                    else:
                        # Primera aparición: insertar en tabla de símbolos
                        idx = len(self.tabla_simbolos)
                        _sym_index[value] = idx
                        self.tabla_simbolos.append({
                            "nombre": value,
                            "tipo": "IDENTIFICADOR",
                            "linea": line,
                            "columna": column,
                            "valor": None,
                            "ocurrencias": 1,
                            "lineas": [line]   # todas las líneas donde aparece
                        })

            # ---- Crear el token y agregarlo a la lista ----
            self.tokens.append(Token(kind, value, line, column))

        # Calcular estadísticas por categoría
        from collections import Counter
        cat_count = Counter(t.type for t in self.tokens)
        self.stats = dict(cat_count)

        return self.tokens
