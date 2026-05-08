# Compilador Java

Compilador de subconjunto del lenguaje Java desarrollado en Python con interfaz web, como proyecto de la asignatura de **Compiladores** de Universidad Mariano Gálvez de Guatemala.

## Descripción

La aplicación analiza código fuente Java y realiza tres fases de compilación:

- **Análisis Léxico:** tokenización del código fuente
- **Análisis Sintáctico:** construcción del Árbol de Sintaxis Abstracta (AST)
- **Análisis Semántico:** verificación de tipos y declaraciones

Los resultados se visualizan en una interfaz web interactiva y pueden exportarse a Excel.

## Tecnologías

- Python 3.x
- Flask
- Pillow
- openpyxl
- D3.js (visualización del AST)

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/jacans-jpg/proyecto_compiladores.git
cd proyecto_compiladores

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python app.py
```

Abrir en el navegador: `http://localhost:5000`

## Estructura del proyecto

```
├── app.py                  # Servidor Flask y rutas API
├── requirements.txt
├── src/
│   ├── classes/            # Nodos del AST y tokens
│   ├── lexer/              # Analizador léxico
│   ├── services/           # Parser, semántico, visualizador AST
│   └── providers/
├── templates/              # HTML de la interfaz
└── static/                 # CSS y JavaScript (D3.js)
```

## Autores

| Nombre | Carné |
|--------|-------|
| Cristian Rafael Tabico Asturias | 0910-15-3503 |
| José Roberto Acán Santizo | 0910-21-8911 |
| Jorge Ignacio Reyes Quezada | 0910-19-4915 |
| Jose Ivan Garcia Castellan | 0910-23-14036 |
| Nicomedes Eduardo Hernández Marroquín | 0910-20-3104 |

Universidad Mariano Gálvez de Guatemala 2026
