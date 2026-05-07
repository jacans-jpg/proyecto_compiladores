/* ═══════════════════════════════════
   Compilador Java — Dashboard JS
   ═══════════════════════════════════ */

let currentData = null;
let cmEditor = null;
let zoomBeh = null;

// ════════════════════════════════════
//  HISTORY API — URLs amigables
// ════════════════════════════════════
const VIEW_URLS = {
    'home':       '/',
    'editor':     '/editor',
    'tokens':     '/tokens',
    'lexico':     '/lexico',
    'sintactico': '/sintactico',
    'ast':        '/ast',
    'semantico':  '/semantico',
    'simbolos':   '/simbolos',
    'errores':    '/errores',
    'gramatica':  '/gramatica',
};
const URL_VIEWS = Object.fromEntries(
    Object.entries(VIEW_URLS).map(([k,v]) => [v, k])
);

function navigateTo(viewName, pushHistory = true) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    const view = document.getElementById('view-' + viewName);
    if (view) view.classList.add('active');

    const nav = document.querySelector(`.nav-item[data-view="${viewName}"]`);
    if (nav) nav.classList.add('active');

    // Header solo en Inicio
    if (viewName === 'home') document.body.classList.remove('no-header');
    else document.body.classList.add('no-header');

    // Sidebar: visible solo en home y editor
    const hasSidebar = (viewName === 'home' || viewName === 'editor');
    const sidebar = document.querySelector('.sidebar');
    const main    = document.querySelector('.main');

    if (hasSidebar) {
        // Mostrar sidebar
        document.body.classList.remove('subpage');
        if (sidebar) sidebar.style.cssText = '';
        if (main)    main.style.cssText = '';
    } else {
        // Ocultar sidebar — main ocupa todo el ancho
        document.body.classList.add('subpage');
        if (sidebar) sidebar.style.cssText = 'display:none!important;width:0!important;';
        if (main)    main.style.cssText    = 'flex:1;width:100%;max-width:100%;min-width:0;';
        // Título de la barra superior
        const titles = {
            tokens:'Tokens', lexico:'Análisis Léxico',
            sintactico:'Análisis Sintáctico', ast:'Árbol AST',
            semantico:'Análisis Semántico', simbolos:'Tabla de Símbolos',
            errores:'Errores', gramatica:'Gramática EBNF'
        };
        const titleEl = document.getElementById('subpage-title');
        if (titleEl) titleEl.textContent = titles[viewName] || '';
    }

    // History API
    if (pushHistory) {
        const url = VIEW_URLS[viewName] || '/';
        const title = viewName === 'home'
            ? 'Compilador Java — UMG'
            : `${viewName.charAt(0).toUpperCase() + viewName.slice(1)} — Compilador Java`;
        history.pushState({ view: viewName }, title, url);
        document.title = title;
    }

    if (viewName === 'ast' && currentData) {
        renderAstTree(currentData.ast_tree);
        renderAstText(currentData.ast_text);
    }
    if (viewName === 'gramatica') loadGrammar();
}

// Botones ← → del navegador
window.addEventListener('popstate', (e) => {
    const viewName = e.state?.view
        || URL_VIEWS[location.pathname]
        || 'home';
    navigateTo(viewName, false);
});

// Sidebar nav — todo navega en la misma página
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', e => {
        e.preventDefault();
        navigateTo(item.dataset.view);
    });
});

// Section cards (home) — navegan en la misma página
document.querySelectorAll('.section-card').forEach(card => {
    card.addEventListener('click', () => {
        navigateTo(card.dataset.go);
    });
});

// ════════════════════════════════════
//  EDITOR (CodeMirror)
// ════════════════════════════════════
window.addEventListener('DOMContentLoaded', () => {
    // Navegar a la URL actual al cargar (permite bookmarks y refrescar en cualquier vista)
    const initialView = URL_VIEWS[location.pathname] || 'home';
    if (initialView !== 'home') {
        navigateTo(initialView, false);
    }
    // Establecer estado inicial en el historial
    history.replaceState(
        { view: initialView },
        document.title,
        location.pathname
    );

    cmEditor = CodeMirror.fromTextArea(document.getElementById('code-editor'), {
        mode: 'text/x-java',
        theme: 'dracula',
        lineNumbers: true,
        matchBrackets: true,
        autoCloseBrackets: true,
        indentUnit: 4,
        tabSize: 4,
        lineWrapping: false,
        extraKeys: { Tab: cm => cm.replaceSelection('    ') }
    });
    cmEditor.setSize('100%', 'calc(100vh - 280px)');
    cmEditor.on('change', () => {
        updateLineCount();
        // Si hay resultados del análisis anterior, limpiarlos al editar
        if (currentData) {
            currentData = null;
            clearAll();
            setStatus('Código modificado — presiona "Analizar todo" para analizar');
        }
    });
    updateClock();
    setInterval(updateClock, 1000);

    // ── Switching de pestañas AST (Gráfico / Texto) ──
    document.querySelectorAll('.ast-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.dataset.ast;  // "graph" o "text"
            // Quitar active de todos
            document.querySelectorAll('.ast-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.ast-panel').forEach(p => p.classList.remove('active'));
            // Activar la seleccionada
            tab.classList.add('active');
            const panel = document.getElementById('ast-panel-' + target);
            if (panel) panel.classList.add('active');
            // Si vamos al texto y hay datos, asegurarnos de renderizar
            if (target === 'text' && currentData) {
                renderAstText(currentData.ast_text);
            }
            if (target === 'graph' && currentData) {
                renderAstTree(currentData.ast_tree);
            }
        });
    });
});

function updateLineCount() {
    const lines = cmEditor.getValue().split('\n').length;
    document.getElementById('stat-lines').textContent = lines;
}

function updateClock() {
    const now = new Date();
    document.getElementById('bar-time').textContent =
        now.toLocaleTimeString('es', {hour:'2-digit', minute:'2-digit', second:'2-digit'});
}

// ════════════════════════════════════
//  ACCIONES (solo editor + tema/acerca)
// ════════════════════════════════════
const fileInput = document.getElementById('file-input');
document.getElementById('ed-open').addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', e => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = ev => {
        cmEditor.setValue(ev.target.result);
        document.getElementById('footer-filename').textContent = file.name;
        document.getElementById('bar-file').textContent = file.name;
        document.getElementById('sidebar-footer').style.display = '';
        document.getElementById('bar-file-wrap').style.display = '';
        setStatus(`Archivo cargado: ${file.name}`);
        navigateTo('editor');
    };
    reader.readAsText(file, 'utf-8');
    e.target.value = '';
});

document.getElementById('ed-analyze').addEventListener('click', analyze);
document.getElementById('ed-clear').addEventListener('click', () => {
    cmEditor.setValue('');
    clearAll();
});

document.getElementById('btn-theme').addEventListener('click', () => {
    document.body.classList.toggle('theme-light');
});

document.getElementById('btn-about').addEventListener('click', () => {
    alert('Compilador Java\nProyecto de Compiladores — UMG 2026\n\nFases implementadas:\n • Análisis Léxico\n • Análisis Sintáctico\n • Análisis Semántico');
});

// Editor actions extra
document.getElementById('ed-sample').addEventListener('click', loadSample);
document.getElementById('ed-txt').addEventListener('click', () => {
    if (!currentData) { alert('Analiza primero.'); return; }
    window.open('/api/export/txt', '_blank');
});
document.getElementById('ed-xl').addEventListener('click', () => {
    if (!currentData) { alert('Analiza primero.'); return; }
    window.open('/api/export/excel', '_blank');
});

function loadSample() {
    cmEditor.setValue(`public class Persona {
    private String nombre;
    private int edad;

    public Persona(String nombre, int edad) {
        this.nombre = nombre;
        this.edad = edad;
    }

    public void saludar() {
        System.out.println("Hola, me llamo " + nombre + " y tengo " + edad + " anios.");
    }

    public int getEdad() {
        return edad;
    }

    public static void main(String[] args) {
        Persona p1 = new Persona("Roberto", 25);
        Persona p2 = new Persona("Maria", 30);

        p1.saludar();
        p2.saludar();

        int suma = 10 + 20;
        double promedio = 15.5 / 2.0;
        boolean esAdulto = (p1.getEdad() >= 18) && (p2.getEdad() != 0);

        if (esAdulto) {
            System.out.println("Son adultos");
        } else {
            System.out.println("No son adultos");
        }

        for (int i = 0; i < 5; i++) {
            System.out.println(i);
        }
    }
}`);
    setStatus('Código de ejemplo cargado');
}

// ════════════════════════════════════
//  ANÁLISIS
// ════════════════════════════════════
let _analyzing = false;  // Evitar análisis doble

async function analyze() {
    if (_analyzing) return;  // Ignorar si ya está analizando

    const code = cmEditor.getValue();
    if (!code.trim()) { alert('No hay código fuente.'); return; }

    _analyzing = true;
    clearAll();  // Limpiar resultados anteriores SIEMPRE antes de analizar
    setStatus('Analizando...');
    const edBtn = document.getElementById('ed-analyze');
    if (edBtn) { edBtn.style.opacity = '0.6'; edBtn.disabled = true; }

    try {
        const resp = await fetch('/api/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({code})
        });
        if (!resp.ok) throw new Error((await resp.json()).error || 'Error del servidor');
        currentData = await resp.json();
        renderAll(currentData);
        const s = currentData.summary;
        const tot = s.lex_errors + s.syn_errors + s.sem_errors;
        setStatus(`Análisis completo — ${s.tokens} tokens · ${s.symbols} símbolos · ${tot===0?'✓ Sin errores':'✗ '+tot+' error(es)'}`);
    } catch(e) {
        setStatus(`Error: ${e.message}`);
        alert('Error durante el análisis: ' + e.message);
    } finally {
        _analyzing = false;
        if (edBtn) { edBtn.style.opacity = '1'; edBtn.disabled = false; }
    }
}

// ════════════════════════════════════
//  RENDERIZAR RESULTADOS
// ════════════════════════════════════
function renderAll(d) {
    const s = d.summary;

    // Stats home
    document.getElementById('stat-tokens').textContent = s.tokens;
    document.getElementById('stat-errors').textContent = s.lex_errors + s.syn_errors + s.sem_errors;
    document.getElementById('stat-warns').textContent = '0';

    // Sidebar badges
    document.getElementById('nav-cnt-tokens').textContent = s.tokens;
    document.getElementById('nav-cnt-lex').textContent = s.lex_errors;
    document.getElementById('nav-cnt-syn').textContent = s.syn_errors;
    document.getElementById('nav-cnt-sem').textContent = s.sem_errors;
    document.getElementById('nav-cnt-sym').textContent = s.symbols;
    document.getElementById('nav-cnt-err').textContent = s.lex_errors + s.syn_errors + s.sem_errors;

    // Tokens table - con clic
    document.getElementById('tk-total').textContent = s.tokens;
    renderTable('tokens-body', d.tokens, t =>
        `<div class="grid-row clickable-row" data-line="${t.linea}" data-col="${t.columna}" title="Clic para ir a la línea ${t.linea}">
            <div class="cell">${t.n}</div>
            <div class="cell">${escapeHtml(t.lexema)}</div>
            <div class="cell">${t.tipo}</div>
            <div class="cell">${t.linea}</div>
            <div class="cell">${t.columna}</div>
        </div>`);

    // Symbols table
    document.getElementById('sym-total').textContent = s.symbols;
    renderTable('symbols-body', d.symbols, sm =>
        `<div class="grid-row clickable-row" data-line="${sm.linea}" data-col="${sm.columna}" title="Clic para ir a la línea ${sm.linea}">
            <div class="cell">${sm.n}</div>
            <div class="cell">${escapeHtml(sm.nombre)}</div>
            <div class="cell">${sm.categoria}</div>
            <div class="cell">${sm.tipo}</div>
            <div class="cell">${sm.ambito}</div>
            <div class="cell">${sm.linea}</div>
            <div class="cell">${sm.columna}</div>
        </div>`);

    // Léxico
    document.getElementById('lex-tokens').textContent = s.tokens;
    document.getElementById('lex-errs').textContent = s.lex_errors;
    renderErrors('lex-errors-body', d.lex_errors, 'lex');

    // Tabla Léxica de Símbolos
    const lexSymCount = (d.lex_symbols || []).length;
    document.getElementById('lex-sym-total').textContent = lexSymCount;
    if (document.getElementById('nav-cnt-lex-sym')) document.getElementById('nav-cnt-lex-sym').textContent = lexSymCount;
    if (document.getElementById('stat-idents')) document.getElementById('stat-idents').textContent = lexSymCount;
    renderTable('lex-symbols-body', d.lex_symbols || [], s => {
        const lineas = s.lineas && s.lineas.length > 1
            ? s.lineas.map(l => `<span style="display:inline-block;background:rgba(123,108,237,0.15);border-radius:3px;padding:1px 5px;margin:1px;font-size:11px">Ln ${l}</span>`).join(' ')
            : `<span style="font-size:12px">Ln ${s.linea}</span>`;
        return `<div class="grid-row clickable-row" data-line="${s.linea}" data-col="${s.columna}" title="Clic para ir a la línea ${s.linea}">
            <div class="cell" style="text-align:center;color:var(--muted,#888);font-size:11px">${s.n}</div>
            <div class="cell"><strong>${escapeHtml(s.nombre)}</strong></div>
            <div class="cell">${s.tipo}</div>
            <div class="cell" style="text-align:center;font-weight:600;color:#27ae60">${s.ocurrencias ?? 1}</div>
            <div class="cell" style="white-space:normal">${lineas}</div>
        </div>`;
    });

    // Sintáctico
    document.getElementById('syn-rules').textContent = countRules(d.ast_text);
    document.getElementById('syn-errs').textContent = s.syn_errors;
    renderErrors('syn-errors-body', d.syn_errors, 'syn');

    // Semántico
    document.getElementById('sem-syms').textContent = s.symbols;
    document.getElementById('sem-errs').textContent = s.sem_errors;
    renderErrors('sem-errors-body', d.sem_errors, 'sem');

    // Errores totales
    document.getElementById('all-lex').textContent = s.lex_errors;
    document.getElementById('all-syn').textContent = s.syn_errors;
    document.getElementById('all-sem').textContent = s.sem_errors;
    renderAllErrors(d);

    // Estado del proyecto
    updateState(d);

    // Activar listeners de clic en filas
    attachRowClickListeners();

    // AST (si está visible)
    if (document.getElementById('view-ast').classList.contains('active')) {
        renderAstTree(d.ast_tree);
        renderAstText(d.ast_text);
    }
}

// ════════════════════════════════════
//  CLIC EN FILAS → IR AL EDITOR
// ════════════════════════════════════
function jumpToLine(line, col) {
    if (!cmEditor) return;
    const lineNum = parseInt(line) - 1;  // CodeMirror 0-indexed
    if (lineNum < 0) return;
    const colNum = Math.max(0, parseInt(col || 0));

    navigateTo('editor');
    setTimeout(() => {
        const totalLines = cmEditor.lineCount();
        if (lineNum >= totalLines) {
            setStatus(`⚠ Línea ${line} no existe en el código actual`);
            return;
        }
        cmEditor.setCursor({line: lineNum, ch: colNum});
        cmEditor.scrollIntoView({line: lineNum, ch: colNum}, 150);
        cmEditor.focus();
        if (highlightedLine !== null) {
            try { cmEditor.removeLineClass(highlightedLine, 'background', 'cm-jumped-line'); } catch(e){}
        }
        cmEditor.addLineClass(lineNum, 'background', 'cm-jumped-line');
        highlightedLine = lineNum;
        setTimeout(() => {
            try { cmEditor.removeLineClass(lineNum, 'background', 'cm-jumped-line'); } catch(e){}
            highlightedLine = null;
        }, 2500);
        setStatus(`📍 Línea ${line}${colNum > 0 ? ', columna ' + col : ''}`);
    }, 120);
}

let highlightedLine = null;
function clearLineHighlight() {
    if (highlightedLine !== null) {
        try { cmEditor.removeLineClass(highlightedLine, 'background', 'cm-jumped-line'); } catch(e){}
        highlightedLine = null;
    }
}

// Delegación de eventos: un solo listener global captura clicks en cualquier .clickable-row
document.addEventListener('click', (e) => {
    const row = e.target.closest('.clickable-row');
    if (!row) return;
    const line = parseInt(row.dataset.line || 0);
    const col  = parseInt(row.dataset.col  || 0);
    // Solo redirigir si la línea es mayor a 0 (0 = built-in, no existe en código)
    if (line > 0) {
        jumpToLine(line, col);
    }
});

function attachRowClickListeners() {
    // Ya no es necesario - la delegación global se encarga.
    // Se mantiene como función vacía por compatibilidad.
}

function renderTable(bodyId, rows, rowFn) {
    const tbody = document.getElementById(bodyId);
    if (!rows || rows.length === 0) {
        tbody.innerHTML = `<div class="grid-empty">Sin datos</div>`;
        return;
    }
    tbody.innerHTML = rows.map(rowFn).join('');
}

function renderErrors(bodyId, errs, kind) {
    const tbody = document.getElementById(bodyId);
    if (!errs || errs.length === 0) {
        tbody.innerHTML = '<div class="grid-empty">✓ Sin errores</div>';
        return;
    }
    tbody.innerHTML = errs.map(e =>
        `<div class="grid-row clickable-row" data-line="${e.linea}" data-col="${e.columna}" title="Clic para ir a la línea ${e.linea}">
            <div class="cell"><span class="err-tag ${kind}">${e.codigo}</span></div>
            ${kind === 'lex' ? `<div class="cell"><code>${escapeHtml(e.lexema ?? '—')}</code></div>` : ''}
            <div class="cell">${e.linea}</div>
            <div class="cell">${e.columna}</div>
            <div class="cell">${escapeHtml(e.mensaje)}</div>
        </div>`).join('');
}

function renderAllErrors(d) {
    const all = [
        ...d.lex_errors.map(e => ({...e, kind:'lex',  label:'Léxico'})),
        ...d.syn_errors.map(e => ({...e, kind:'syn',  label:'Sintáctico'})),
        ...d.sem_errors.map(e => ({...e, kind:'sem',  label:'Semántico'})),
    ];
    const tbody = document.getElementById('all-errors-body');
    if (all.length === 0) {
        tbody.innerHTML = '<div class="grid-empty">✓ Sin errores detectados</div>';
        return;
    }
    tbody.innerHTML = all.map(e =>
        `<div class="grid-row clickable-row" data-line="${e.linea}" data-col="${e.columna}" title="Clic para ir a la línea ${e.linea}">
            <div class="cell"><span class="err-tag ${e.kind}">${e.label}</span></div>
            <div class="cell">${e.codigo}</div>
            <div class="cell">${e.kind === 'lex' ? `<code>${escapeHtml(e.lexema ?? '—')}</code>` : '—'}</div>
            <div class="cell">${e.linea}</div>
            <div class="cell">${e.columna}</div>
            <div class="cell">${escapeHtml(e.mensaje)}</div>
        </div>`).join('');
}

function updateState(d) {
    const setOk = (id, ok) => {
        const el = document.getElementById('state-'+id);
        const tag = document.getElementById('state-'+id+'-tag');
        if (ok) { el.textContent='✓'; el.classList.add('ok'); tag.textContent='Completado'; tag.classList.add('ok'); }
        else { el.textContent='○'; el.classList.remove('ok'); tag.textContent='Con errores'; tag.classList.remove('ok'); }
    };
    setOk('lex', d.summary.lex_errors === 0);
    setOk('syn', d.summary.syn_errors === 0);
    setOk('sem', d.summary.sem_errors === 0);
    setOk('sym', d.summary.symbols > 0);

    const okCount = [
        d.summary.lex_errors === 0,
        d.summary.syn_errors === 0,
        d.summary.sem_errors === 0,
        d.summary.symbols > 0
    ].filter(Boolean).length;
    const pct = (okCount / 4) * 100;
    document.getElementById('progress-text').textContent = Math.round(pct) + '%';
    const circle = document.getElementById('progress-circle');
    const circ = 263.89;
    circle.style.strokeDashoffset = circ - (circ * pct / 100);
    circle.setAttribute('stroke', pct === 100 ? '#2ECC71' : pct >= 50 ? '#FFB13B' : '#E74C3C');
    document.getElementById('progress-label').textContent =
        pct === 100 ? 'Compilación exitosa' : pct >= 50 ? 'Con errores' : 'Análisis incompleto';
}

function countRules(astText) {
    return astText ? astText.length : 0;
}

function clearAll() {
    currentData = null;
    ['stat-tokens','stat-errors','stat-warns','stat-lines','stat-idents'].forEach(id => {
        const el = document.getElementById(id); if (el) el.textContent = '0';
    });
    ['nav-cnt-tokens','nav-cnt-lex','nav-cnt-syn','nav-cnt-sem','nav-cnt-sym','nav-cnt-err'].forEach(id => {
        document.getElementById(id).textContent = '0';
    });
    ['tk-total','sym-total','lex-sym-total','lex-tokens','lex-errs','syn-rules','syn-errs','sem-syms','sem-errs','all-lex','all-syn','all-sem'].forEach(id => {
        const el = document.getElementById(id); if (el) el.textContent = '0';
    });
    ['tokens-body','symbols-body','lex-symbols-body','lex-errors-body','syn-errors-body','sem-errors-body','all-errors-body'].forEach(id => {
        const t = document.getElementById(id);
        if (t) t.innerHTML = '<div class="grid-empty">Sin datos</div>';
    });
    document.getElementById('ast-svg-container').innerHTML = '<div class="grid-empty light">Analiza código primero</div>';
    document.getElementById('ast-text-code').innerHTML = '<span class="grid-empty light">Analiza código primero</span>';
    document.getElementById('ast-line-nums').textContent = '';

    // Reset progress
    ['lex','syn','sem','sym'].forEach(id => {
        document.getElementById('state-'+id).textContent = '○';
        document.getElementById('state-'+id).classList.remove('ok');
        document.getElementById('state-'+id+'-tag').textContent = 'Pendiente';
        document.getElementById('state-'+id+'-tag').classList.remove('ok');
    });
    document.getElementById('progress-text').textContent = '0%';
    document.getElementById('progress-circle').style.strokeDashoffset = '263.89';
    document.getElementById('progress-label').textContent = 'Sin análisis';
}

// ════════════════════════════════════
//  AST GRÁFICO (D3)
// ════════════════════════════════════
const AST_LEGEND = [
    ['Clase','#8e44ad'],['Método','#e91e8c'],['Campo/Var','#2471a3'],
    ['Control','#117a65'],['Operador','#00bcd4'],['Literal','#ff6f00'],
    ['Identificador','#1abc9c'],['Llamada','#f1c40f'],
    ['Bloque','#7f8c8d'],['Asignación','#d35400']
];

function renderLegend() {
    const lg = document.getElementById('ast-legend');
    lg.innerHTML = '<span style="font-weight:600;font-size:11px;color:var(--text-soft);margin-right:6px">Leyenda:</span>' +
        AST_LEGEND.map(([n,c]) => `<span class="ast-legend-item"><span class="ast-legend-dot" style="background:${c}"></span>${n}</span>`).join('');
}
renderLegend();

const COLOR_OVERRIDE = { 'IdentifierNode': '#1abc9c' };

function renderAstTree(treeData) {
    const container = document.getElementById('ast-svg-container');
    container.innerHTML = '';

    if (!treeData) {
        container.innerHTML = '<div class="empty light">No hay AST disponible</div>';
        return;
    }

    const margin = {top:40,right:80,bottom:40,left:80};
    const nodeW = 70, nodeH = 36;
    const cW = container.clientWidth || 800;
    const cH = container.clientHeight || 500;

    const root = d3.hierarchy(treeData);
    const maxLen = Math.max(...root.descendants().map(d => d.data.name.length));
    const dynW = Math.max(80, maxLen * 5.0 + 36);
    d3.tree().nodeSize([dynW, nodeH + 44])(root);

    let x0=Infinity, x1=-Infinity, y1=-Infinity;
    root.each(d => {
        if (d.x<x0) x0=d.x;
        if (d.x>x1) x1=d.x;
        if (d.y>y1) y1=d.y;
    });

    // SVG siempre ocupa 100% del contenedor — el pan/zoom de D3 maneja todo
    const svg = d3.select(container).append('svg')
        .attr('width', '100%').attr('height', '100%')
        .style('display','block');

    zoomBeh = d3.zoom().scaleExtent([0.05, 5])
        .on('zoom', e => g.attr('transform', e.transform));
    svg.call(zoomBeh);

    // Centrar árbol inicialmente en el contenedor
    const offsetX = (cW / 2) - ((x0 + x1) / 2);
    const offsetY = margin.top;

    const g = svg.append('g')
        .attr('transform', `translate(${offsetX},${offsetY})`);

    // Aplicar transform inicial al zoom para que sea consistente con pan posterior
    svg.call(zoomBeh.transform, d3.zoomIdentity.translate(offsetX, offsetY));

    g.selectAll('.ast-link')
        .data(root.links()).join('path').attr('class','ast-link')
        .attr('d', d => {
            const sx=d.source.x, sy=d.source.y+18;
            const tx=d.target.x, ty=d.target.y-18;
            const my=(sy+ty)/2;
            return `M${sx},${sy} C${sx},${my} ${tx},${my} ${tx},${ty}`;
        });

    const node = g.selectAll('.ast-node')
        .data(root.descendants()).join('g')
        .attr('class','ast-node clickable-node')
        .attr('transform', d => `translate(${d.x},${d.y})`)
        .style('cursor', 'pointer')
        .on('click', (event, d) => {
            const line = d.data.linea;
            const col = d.data.columna;
            if (line && line > 0) {
                jumpToLine(line, col);
            }
        });

    // Tooltip al pasar el mouse
    node.append('title')
        .text(d => {
            const ln = d.data.linea;
            return ln ? `${d.data.name} — Clic para ir a línea ${ln}` : d.data.name;
        });

    node.append('ellipse')
        .attr('rx', d => Math.max(38, d.data.name.length*5.8+18))
        .attr('ry', 22)
        .attr('fill', d => COLOR_OVERRIDE[d.data.type] || d.data.color || '#34495e');

    node.append('text').text(d => d.data.name);
}

function zoomIn()  { if (zoomBeh) d3.select('#ast-svg-container svg').call(zoomBeh.scaleBy, 1.3); }
function zoomOut() { if (zoomBeh) d3.select('#ast-svg-container svg').call(zoomBeh.scaleBy, 0.7); }
function resetZoom() { if (zoomBeh) d3.select('#ast-svg-container svg').call(zoomBeh.transform, d3.zoomIdentity); }

window.zoomIn = zoomIn;
window.zoomOut = zoomOut;
window.resetZoom = resetZoom;

// ── AST Text (con colores y clic) ──
const TYPE_CLASS = {
    'Clase:':'ast-class', 'Programa':'ast-class',
    'Método:':'ast-method', 'Constructor:':'ast-method',
    'Campo:':'ast-field', 'DeclVar:':'ast-vardecl',
    'If':'ast-control', 'While':'ast-control', 'For':'ast-control',
    'Return':'ast-return', 'Bloque':'ast-block',
    'BinOp:':'ast-op', 'UnaryOp:':'ast-op',
    'Literal:':'ast-literal', 'Id:':'ast-ident',
    'Asignación':'ast-assign',
    'LlamadaMétodo':'ast-call', 'New:':'ast-call',
    'AccesoMiembro:':'ast-call', 'ExprStmt':'ast-default'
};

function renderAstText(lines) {
    const codeEl = document.getElementById('ast-text-code');
    const numsEl = document.getElementById('ast-line-nums');
    const infoEl = document.getElementById('ast-text-info');

    if (!lines || lines.length === 0) {
        codeEl.innerHTML = '<span class="empty light">Sin AST</span>';
        numsEl.textContent = '';
        return;
    }

    // Generar mapeo de línea-AST → línea-código fuente recorriendo el árbol
    const sourceMap = buildAstSourceMap(currentData ? currentData.ast_tree : null);

    // Generar números con mismo line-height que codeEl
    numsEl.textContent = lines.map((_,i) => i+1).join('\n');
    // Forzar sincronización de scroll al cambiar contenido
    numsEl.scrollTop = 0;
    codeEl.innerHTML = '';
    let selected = null;

    lines.forEach((line, i) => {
        const trimmed = line.trim();
        let cls = 'ast-default';
        for (const [k,v] of Object.entries(TYPE_CLASS)) {
            if (trimmed.startsWith(k)) { cls = v; break; }
        }
        const span = document.createElement('span');
        span.className = 'ast-text-line ' + cls;
        span.dataset.line = i+1;
        span.textContent = line;

        // Línea del código fuente correspondiente
        const srcInfo = sourceMap[i] || null;
        if (srcInfo && srcInfo.linea > 0) {
            span.dataset.srcLine = srcInfo.linea;
            span.dataset.srcCol = srcInfo.columna;
            span.title = `Clic para ir al código (línea ${srcInfo.linea})`;
        }

        span.addEventListener('click', () => {
            if (selected) selected.classList.remove('active');
            span.classList.add('active');
            selected = span;
            infoEl.textContent = `Línea AST ${i+1}` +
                (srcInfo ? ` → código línea ${srcInfo.linea}` : '');

            // Si tiene info de línea, saltar al editor
            if (srcInfo && srcInfo.linea > 0) {
                jumpToLine(srcInfo.linea, srcInfo.columna);
            }
        });
        codeEl.appendChild(span);
        codeEl.appendChild(document.createTextNode('\n'));
    });

    codeEl.addEventListener('scroll', () => { numsEl.scrollTop = codeEl.scrollTop; });
}

// Recorrer el AST en el mismo orden que ast_to_text() en Python
// para mapear cada línea del texto a la posición en el código fuente
function buildAstSourceMap(treeNode) {
    const map = {};
    if (!treeNode) return map;

    let idx = 0;
    function traverse(node) {
        // Cada nodo agrega 1 línea al texto (con excepciones que también lo hacen)
        map[idx] = { linea: node.linea || 0, columna: node.columna || 0 };
        idx++;

        // Casos especiales que generan líneas extra (sub-headers como "Condición:", "Args:")
        // según ast_visualizer.py
        const t = node.type;
        if (t === 'IfNode') {
            // "Condición:" header
            map[idx] = { linea: node.linea, columna: node.columna }; idx++;
            // condición (se agrega en children)
            // "Entonces:" header
            // no lo predecimos exacto, mejor recorrer hijos normalmente
        }
        if (node.children) {
            node.children.forEach(traverse);
        }
    }
    // Como aproximación: el orden DFS del árbol coincide aproximadamente
    // con el orden de líneas del texto. Para precisión total, generamos línea por línea.
    traverse(treeNode);
    return map;
}

// ════════════════════════════════════
//  GRAMÁTICA EBNF
// ════════════════════════════════════
function loadGrammar() {
    const el = document.getElementById('grammar-text');
    if (el.dataset.loaded) return;
    el.dataset.loaded = '1';
    el.textContent = `(* ═══════════════════════════════════════════════ *)
(*  GRAMÁTICA EBNF — Subconjunto de Java          *)
(*  Compilador UMG — Proyecto 2                    *)
(* ═══════════════════════════════════════════════ *)

(* ── PROGRAMA ── *)
programa            = { declaracion_clase } ;

(* ── CLASE ── *)
declaracion_clase   = { modificador } , "class" , IDENTIFICADOR ,
                      "{" , { miembro_clase } , "}" ;

modificador         = "public" | "private" | "protected"
                    | "static" | "final" | "abstract" ;

miembro_clase       = declaracion_campo
                    | declaracion_metodo
                    | declaracion_constructor ;

(* ── CAMPOS Y MÉTODOS ── *)
declaracion_campo   = { modificador } , tipo , IDENTIFICADOR ,
                      [ "=" , expresion ] , ";" ;

declaracion_metodo  = { modificador } , ( tipo | "void" ) , IDENTIFICADOR ,
                      "(" , [ parametros ] , ")" , bloque ;

declaracion_constructor = { modificador } , IDENTIFICADOR ,
                          "(" , [ parametros ] , ")" , bloque ;

(* ── TIPOS ── *)
tipo                = tipo_primitivo | IDENTIFICADOR | tipo , "[]" ;
tipo_primitivo      = "int" | "float" | "double" | "boolean"
                    | "char" | "String" | "long" | "short" | "byte" ;

(* ── PARÁMETROS Y BLOQUE ── *)
parametros          = parametro , { "," , parametro } ;
parametro           = tipo , IDENTIFICADOR ;
bloque              = "{" , { sentencia } , "}" ;

(* ── SENTENCIAS ── *)
sentencia           = declaracion_variable
                    | sentencia_if
                    | sentencia_while
                    | sentencia_for
                    | sentencia_return
                    | sentencia_expresion
                    | bloque ;

declaracion_variable = tipo , IDENTIFICADOR , [ "=" , expresion ] , ";" ;
sentencia_if        = "if" , "(" , expresion , ")" , bloque ,
                      [ "else" , ( bloque | sentencia_if ) ] ;
sentencia_while     = "while" , "(" , expresion , ")" , bloque ;
sentencia_for       = "for" , "(" ,
                      ( declaracion_variable | sentencia_expresion ) ,
                      expresion , ";" , expresion , ")" , bloque ;
sentencia_return    = "return" , [ expresion ] , ";" ;
sentencia_expresion = expresion , [ operador_asignacion , expresion ] , ";" ;
operador_asignacion = "=" | "+=" | "-=" | "*=" | "/=" | "%=" ;

(* ── EXPRESIONES (precedencia menor → mayor) ── *)
expresion           = or_logico ;
or_logico           = and_logico , { "||" , and_logico } ;
and_logico          = igualdad , { "&&" , igualdad } ;
igualdad            = relacional , { ( "==" | "!=" ) , relacional } ;
relacional          = aditiva , { ( "<" | ">" | "<=" | ">=" ) , aditiva } ;
aditiva             = multiplicativa , { ( "+" | "-" ) , multiplicativa } ;
multiplicativa      = unaria , { ( "*" | "/" | "%" ) , unaria } ;
unaria              = ( "!" | "-" | "++" | "--" ) , unaria | postfija ;
postfija            = primaria , [ "++" | "--" ] ;

(* ── PRIMARIOS ── *)
primaria            = literal
                    | IDENTIFICADOR
                    | "this"
                    | "new" , IDENTIFICADOR , "(" , [ argumentos ] , ")"
                    | "(" , expresion , ")"
                    | acceso_miembro
                    | llamada_metodo ;

acceso_miembro      = primaria , { "." , IDENTIFICADOR } ;
llamada_metodo      = acceso_miembro , "(" , [ argumentos ] , ")" ;
argumentos          = expresion , { "," , expresion } ;

(* ── LITERALES ── *)
literal             = INTEGER | FLOAT | STRING | CHAR
                    | "true" | "false" | "null" ;

(* ── TOKENS TERMINALES ── *)
IDENTIFICADOR       = letra , { letra | digito } ;
INTEGER             = digito , { digito } ;
FLOAT               = digito , { digito } , "." , digito , { digito } ;
STRING              = '"' , { caracter } , '"' ;
CHAR                = "'" , caracter , "'" ;
letra               = "A".."Z" | "a".."z" | "_" | "$" ;
digito              = "0".."9" ;

(* Notación EBNF:
    =     definición
    ,     concatenación
    |     alternativa
    { }   cero o más
    [ ]   opcional
    " "   token literal
*)`;
}

// ════════════════════════════════════
//  UTILIDADES
// ════════════════════════════════════
// Botón "Editor" en barra de subpágina — navega al editor en la misma página
function goToEditor() {
    navigateTo('editor');
}
window.goToEditor = goToEditor;

function escapeHtml(s) {
    if (s === null || s === undefined) return '';
    return String(s)
        .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
        .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

function setStatus(msg) {
    document.getElementById('status').textContent = msg;
}

// ── Búsqueda en tablas ──
document.getElementById('tk-search').addEventListener('input', e => {
    filterTable('tokens-body', e.target.value);
});
document.getElementById('sym-search').addEventListener('input', e => {
    filterTable('symbols-body', e.target.value);
});
const lexSymSearch = document.getElementById('lex-sym-search');
if (lexSymSearch) lexSymSearch.addEventListener('input', e => {
    filterTable('lex-symbols-body', e.target.value);
});

function filterTable(bodyId, query) {
    const q = query.toLowerCase();
    document.querySelectorAll(`#${bodyId} .grid-row`).forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(q) ? '' : 'none';
    });
}
