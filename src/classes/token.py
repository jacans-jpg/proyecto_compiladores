class Token:
    """
    Unidad léxica producida por el scanner.
    Almacena tipo, lexema y posición en el código fuente.
    """
    def __init__(self, type, value, line=0, column=0):
        self.type   = type    # Categoría del token (PALABRA_RESERVADA, IDENTIFICADOR, etc.)
        self.value  = value   # Lexema: cadena exacta del código fuente
        self.line   = line    # Línea donde aparece (1-based)
        self.column = column  # Columna donde aparece (1-based)

    def __repr__(self):
        return f"{self.type}({self.value!r}) [Ln {self.line}, Col {self.column}]"

    def __eq__(self, other):
        if isinstance(other, Token):
            return self.type == other.type and self.value == other.value
        return NotImplemented

    def __hash__(self):
        return hash((self.type, self.value))

    def is_keyword(self):
        return self.type == "PALABRA_RESERVADA"

    def is_identifier(self):
        return self.type == "IDENTIFICADOR"

    def is_literal(self):
        return self.type in ("INTEGER", "FLOAT", "STRING", "CHAR", "LITERAL_BOOLEANO")

    def is_operator(self):
        return self.type in (
            "SUMA","RESTA","MULTIPLICACION","DIVISION","MODULO",
            "INCREMENTO","DECREMENTO","ASIGNACION",
            "SUMA_ASIGN","RESTA_ASIGN","MULT_ASIGN","DIV_ASIGN","MOD_ASIGN",
            "IGUALDAD","DIFERENTE","MENOR","MAYOR","MENOR_IGUAL","MAYOR_IGUAL",
            "AND_LOGICO","OR_LOGICO","NOT_LOGICO",
            "AND_BIT","OR_BIT","XOR_BIT","NOT_BIT",
            "SHIFT_LEFT","SHIFT_RIGHT","SHIFT_RIGHT_UNSIGNED"
        )

    def is_delimiter(self):
        return self.type in (
            "PAREN_IZQ","PAREN_DER","LLAVE_IZQ","LLAVE_DER",
            "CORCHETE_IZQ","CORCHETE_DER","PUNTO_COMA","COMA",
            "PUNTO","DOS_PUNTOS","INTERROGACION","ARROBA"
        )
