"""
Utilidades para visualizar el AST como texto y en la GUI.
"""

from ..classes.ast_nodes import *


def ast_to_text(node, indent=0):
    """Convertir un nodo AST a representación de texto indentado."""
    prefix = "  " * indent
    lines = []

    if node is None:
        return [f"{prefix}(null)"]

    name = type(node).__name__

    if isinstance(node, ProgramNode):
        lines.append(f"{prefix}Programa")
        for cls in node.classes:
            lines.extend(ast_to_text(cls, indent + 1))

    elif isinstance(node, ClassDeclNode):
        mods = " ".join(node.modifiers) + " " if node.modifiers else ""
        lines.append(f"{prefix}Clase: {mods}{node.name}")
        for m in node.members:
            lines.extend(ast_to_text(m, indent + 1))

    elif isinstance(node, FieldDeclNode):
        mods = " ".join(node.modifiers) + " " if node.modifiers else ""
        init = ""
        if node.initializer:
            init_lines = ast_to_text(node.initializer, 0)
            init = " = " + init_lines[0].strip() if init_lines else ""
        lines.append(f"{prefix}Campo: {mods}{node.type_name} {node.name}{init}")

    elif isinstance(node, MethodDeclNode):
        mods = " ".join(node.modifiers) + " " if node.modifiers else ""
        params_str = ", ".join(f"{p.type_name} {p.name}" for p in node.params)
        lines.append(f"{prefix}Método: {mods}{node.return_type} {node.name}({params_str})")
        lines.extend(ast_to_text(node.body, indent + 1))

    elif isinstance(node, ConstructorDeclNode):
        mods = " ".join(node.modifiers) + " " if node.modifiers else ""
        params_str = ", ".join(f"{p.type_name} {p.name}" for p in node.params)
        lines.append(f"{prefix}Constructor: {mods}{node.name}({params_str})")
        lines.extend(ast_to_text(node.body, indent + 1))

    elif isinstance(node, BlockNode):
        lines.append(f"{prefix}Bloque")
        for stmt in node.statements:
            lines.extend(ast_to_text(stmt, indent + 1))

    elif isinstance(node, VarDeclNode):
        lines.append(f"{prefix}DeclVar: {node.type_name} {node.name}")
        if node.initializer:
            lines.extend(ast_to_text(node.initializer, indent + 1))

    elif isinstance(node, AssignmentNode):
        lines.append(f"{prefix}Asignación ({node.operator})")
        lines.extend(ast_to_text(node.target, indent + 1))
        lines.extend(ast_to_text(node.value, indent + 1))

    elif isinstance(node, IfNode):
        lines.append(f"{prefix}If")
        lines.append(f"{prefix}  Condición:")
        lines.extend(ast_to_text(node.condition, indent + 2))
        lines.append(f"{prefix}  Entonces:")
        lines.extend(ast_to_text(node.then_block, indent + 2))
        if node.else_block:
            lines.append(f"{prefix}  SiNo:")
            lines.extend(ast_to_text(node.else_block, indent + 2))

    elif isinstance(node, WhileNode):
        lines.append(f"{prefix}While")
        lines.append(f"{prefix}  Condición:")
        lines.extend(ast_to_text(node.condition, indent + 2))
        lines.append(f"{prefix}  Cuerpo:")
        lines.extend(ast_to_text(node.body, indent + 2))

    elif isinstance(node, ForNode):
        lines.append(f"{prefix}For")
        lines.append(f"{prefix}  Init:")
        lines.extend(ast_to_text(node.init, indent + 2))
        lines.append(f"{prefix}  Condición:")
        lines.extend(ast_to_text(node.condition, indent + 2))
        lines.append(f"{prefix}  Update:")
        lines.extend(ast_to_text(node.update, indent + 2))
        lines.append(f"{prefix}  Cuerpo:")
        lines.extend(ast_to_text(node.body, indent + 2))

    elif isinstance(node, ReturnNode):
        lines.append(f"{prefix}Return")
        if node.value:
            lines.extend(ast_to_text(node.value, indent + 1))

    elif isinstance(node, ExpressionStmtNode):
        lines.append(f"{prefix}ExprStmt")
        lines.extend(ast_to_text(node.expression, indent + 1))

    elif isinstance(node, BinaryOpNode):
        lines.append(f"{prefix}BinOp: {node.operator}")
        lines.extend(ast_to_text(node.left, indent + 1))
        lines.extend(ast_to_text(node.right, indent + 1))

    elif isinstance(node, UnaryOpNode):
        pos = "pre" if node.prefix else "post"
        lines.append(f"{prefix}UnaryOp: {node.operator} ({pos})")
        lines.extend(ast_to_text(node.operand, indent + 1))

    elif isinstance(node, LiteralNode):
        lines.append(f"{prefix}Literal: {node.value} ({node.literal_type})")

    elif isinstance(node, IdentifierNode):
        lines.append(f"{prefix}Id: {node.name}")

    elif isinstance(node, MemberAccessNode):
        lines.append(f"{prefix}AccesoMiembro: .{node.member}")
        lines.extend(ast_to_text(node.object, indent + 1))

    elif isinstance(node, MethodCallNode):
        lines.append(f"{prefix}LlamadaMétodo")
        lines.extend(ast_to_text(node.callee, indent + 1))
        if node.arguments:
            lines.append(f"{prefix}  Args:")
            for arg in node.arguments:
                lines.extend(ast_to_text(arg, indent + 2))

    elif isinstance(node, NewObjectNode):
        lines.append(f"{prefix}New: {node.class_name}")
        if node.arguments:
            lines.append(f"{prefix}  Args:")
            for arg in node.arguments:
                lines.extend(ast_to_text(arg, indent + 2))

    elif isinstance(node, ThisNode):
        lines.append(f"{prefix}this")

    elif isinstance(node, ArrayAccessNode):
        lines.append(f"{prefix}ArrayAccess")
        lines.extend(ast_to_text(node.array, indent + 1))
        lines.append(f"{prefix}  Índice:")
        lines.extend(ast_to_text(node.index, indent + 2))

    else:
        lines.append(f"{prefix}{name}")

    return lines


def populate_treeview(treeview, node, parent=""):
    """Poblar un ttk.Treeview con la estructura del AST."""
    if node is None:
        return

    name = type(node).__name__

    if isinstance(node, ProgramNode):
        root_id = treeview.insert(parent, "end", text="Programa", open=True)
        for cls in node.classes:
            populate_treeview(treeview, cls, root_id)

    elif isinstance(node, ClassDeclNode):
        mods = " ".join(node.modifiers) + " " if node.modifiers else ""
        nid = treeview.insert(parent, "end",
                              text=f"Clase: {mods}{node.name}",
                              open=True)
        for m in node.members:
            populate_treeview(treeview, m, nid)

    elif isinstance(node, FieldDeclNode):
        mods = " ".join(node.modifiers) + " " if node.modifiers else ""
        nid = treeview.insert(parent, "end",
                              text=f"Campo: {mods}{node.type_name} {node.name}")
        if node.initializer:
            populate_treeview(treeview, node.initializer, nid)

    elif isinstance(node, MethodDeclNode):
        mods = " ".join(node.modifiers) + " " if node.modifiers else ""
        params_str = ", ".join(f"{p.type_name} {p.name}" for p in node.params)
        nid = treeview.insert(parent, "end",
                              text=f"Método: {mods}{node.return_type} {node.name}({params_str})",
                              open=True)
        populate_treeview(treeview, node.body, nid)

    elif isinstance(node, ConstructorDeclNode):
        mods = " ".join(node.modifiers) + " " if node.modifiers else ""
        params_str = ", ".join(f"{p.type_name} {p.name}" for p in node.params)
        nid = treeview.insert(parent, "end",
                              text=f"Constructor: {mods}{node.name}({params_str})",
                              open=True)
        populate_treeview(treeview, node.body, nid)

    elif isinstance(node, BlockNode):
        nid = treeview.insert(parent, "end", text="Bloque", open=True)
        for stmt in node.statements:
            populate_treeview(treeview, stmt, nid)

    elif isinstance(node, VarDeclNode):
        nid = treeview.insert(parent, "end",
                              text=f"DeclVar: {node.type_name} {node.name}")
        if node.initializer:
            populate_treeview(treeview, node.initializer, nid)

    elif isinstance(node, AssignmentNode):
        nid = treeview.insert(parent, "end", text=f"Asignación ({node.operator})")
        populate_treeview(treeview, node.target, nid)
        populate_treeview(treeview, node.value, nid)

    elif isinstance(node, IfNode):
        nid = treeview.insert(parent, "end", text="If", open=True)
        cond_id = treeview.insert(nid, "end", text="Condición")
        populate_treeview(treeview, node.condition, cond_id)
        then_id = treeview.insert(nid, "end", text="Entonces", open=True)
        populate_treeview(treeview, node.then_block, then_id)
        if node.else_block:
            else_id = treeview.insert(nid, "end", text="SiNo", open=True)
            populate_treeview(treeview, node.else_block, else_id)

    elif isinstance(node, WhileNode):
        nid = treeview.insert(parent, "end", text="While", open=True)
        cond_id = treeview.insert(nid, "end", text="Condición")
        populate_treeview(treeview, node.condition, cond_id)
        body_id = treeview.insert(nid, "end", text="Cuerpo", open=True)
        populate_treeview(treeview, node.body, body_id)

    elif isinstance(node, ForNode):
        nid = treeview.insert(parent, "end", text="For", open=True)
        init_id = treeview.insert(nid, "end", text="Init")
        populate_treeview(treeview, node.init, init_id)
        cond_id = treeview.insert(nid, "end", text="Condición")
        populate_treeview(treeview, node.condition, cond_id)
        upd_id = treeview.insert(nid, "end", text="Update")
        populate_treeview(treeview, node.update, upd_id)
        body_id = treeview.insert(nid, "end", text="Cuerpo", open=True)
        populate_treeview(treeview, node.body, body_id)

    elif isinstance(node, ReturnNode):
        nid = treeview.insert(parent, "end", text="Return")
        if node.value:
            populate_treeview(treeview, node.value, nid)

    elif isinstance(node, ExpressionStmtNode):
        populate_treeview(treeview, node.expression, parent)

    elif isinstance(node, BinaryOpNode):
        nid = treeview.insert(parent, "end", text=f"Op: {node.operator}")
        populate_treeview(treeview, node.left, nid)
        populate_treeview(treeview, node.right, nid)

    elif isinstance(node, UnaryOpNode):
        pos = "pre" if node.prefix else "post"
        nid = treeview.insert(parent, "end", text=f"Unario: {node.operator}({pos})")
        populate_treeview(treeview, node.operand, nid)

    elif isinstance(node, LiteralNode):
        treeview.insert(parent, "end", text=f"{node.value} ({node.literal_type})")

    elif isinstance(node, IdentifierNode):
        treeview.insert(parent, "end", text=f"Id: {node.name}")

    elif isinstance(node, MemberAccessNode):
        nid = treeview.insert(parent, "end", text=f".{node.member}")
        populate_treeview(treeview, node.object, nid)

    elif isinstance(node, MethodCallNode):
        nid = treeview.insert(parent, "end", text="Llamada()")
        populate_treeview(treeview, node.callee, nid)
        if node.arguments:
            args_id = treeview.insert(nid, "end", text="Argumentos")
            for arg in node.arguments:
                populate_treeview(treeview, arg, args_id)

    elif isinstance(node, NewObjectNode):
        nid = treeview.insert(parent, "end", text=f"new {node.class_name}")
        if node.arguments:
            args_id = treeview.insert(nid, "end", text="Argumentos")
            for arg in node.arguments:
                populate_treeview(treeview, arg, args_id)

    elif isinstance(node, ThisNode):
        treeview.insert(parent, "end", text="this")

    elif isinstance(node, ArrayAccessNode):
        nid = treeview.insert(parent, "end", text="ArrayAccess")
        populate_treeview(treeview, node.array, nid)
        idx_id = treeview.insert(nid, "end", text="Índice")
        populate_treeview(treeview, node.index, idx_id)
