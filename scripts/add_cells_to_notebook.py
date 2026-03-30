# -*- coding: utf-8 -*-
"""
Script auxiliar: añade las celdas de los Bloques 6, 7 y Sub-bloque 4.6
al notebook parte3_completo.ipynb
"""

import json
from pathlib import Path

NB_PATH = Path("notebooks/parte3_completo.ipynb")

with open(NB_PATH, "r", encoding="utf-8") as f:
    nb = json.load(f)

print(f"Celdas actuales: {len(nb['cells'])}")


def md_cell(lines):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": lines,
    }


def code_cell(lines):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": lines,
    }


new_cells = []

# ══════════════════════════════════════════════════════════════
# BLOQUE 6
# ══════════════════════════════════════════════════════════════
new_cells.append(md_cell([
    "---\n",
    "# Bloque 6 — Análisis Comparativo: Episodio Actual vs. Precedente Ucrania 2022\n",
    "\n",
    "El precedente más cercano al escenario del 23 de marzo de 2026 es la invasión rusa de Ucrania "
    "(24 de febrero de 2022). Ambos son guerras activas con impacto directo en infraestructura "
    "energética y OVX/GPR en percentiles extremos. Este bloque construye la comparación en cuatro sub-bloques:\n",
    "\n",
    "- **6.1** Trayectoria normalizada WTI, OVX y VIX (90 días desde el inicio de cada conflicto, base 100)\n",
    "- **6.2** Trayectoria del GPR: ambos episodios sobre el mismo eje temporal relativo\n",
    "- **6.3** Calibración empírica del RSJD: cuánto tardó OVX en salir de la zona de alta tensión en Ucrania\n",
    "- **6.4** Tabla comparativa de características de cada episodio\n",
    "\n",
    "> **Por qué se incluye:** La comparación con Ucrania 2022 es la única forma de contrastar empíricamente "
    "si el parámetro de persistencia del RSJD (p\\_stay = 0.977, duración esperada ≈43 días) es realista. "
    "En el episodio de Ucrania, OVX no cayó por debajo de 40 en los primeros 90 días de negociación.\n",
]))

new_cells.append(code_cell([
    "# Ejecutar Bloque 6\n",
    "%run scripts/bloque6_ukraine_comparison.py\n",
]))

new_cells.append(md_cell([
    "### 6.1 Trayectoria normalizada WTI, OVX y VIX\n",
    "\n",
    "![Trayectoria normalizada](outputs/figures/parte3/bloque6_trayectoria_normalizada.png)\n",
    "\n",
    "**Qué lectura se extrae:** El episodio de 2026 arranca con una aceleración de WTI más pronunciada "
    "(+47% vs +33% en Ucrania), pero con un OVX que ya estaba elevado el día 0 (64.7 vs 49.0). "
    "La proyección RSJD desde el día 17 muestra un IC 80% amplio, coherente con la incertidumbre extrema.\n",
]))

new_cells.append(md_cell([
    "### 6.2 Trayectoria GPR\n",
    "\n",
    "![GPR comparativa](outputs/figures/parte3/bloque6_gpr_comparativa.png)\n",
    "\n",
    "**Qué lectura se extrae:** Ambos episodios superan el umbral crítico (GPR > 120) desde el día 0. "
    "La diferencia clave es que en 2026 el GPR ya partía de un nivel muy elevado (229 el día 0), "
    "mientras que en Ucrania el escalón inicial fue más brusco desde un nivel más bajo.\n",
]))

new_cells.append(md_cell([
    "### 6.3 Calibración empírica del RSJD: duración real en Ucrania 2022\n",
    "\n",
    "![Calibración RSJD](outputs/figures/parte3/bloque6_rsjd_calibracion.png)\n",
    "\n",
    "**Resultado:** El régimen de alta tensión (OVX > 40) en Ucrania NO salió del umbral en los primeros "
    "90 días de negociación. El RSJD predice una duración esperada de ≈43 días, "
    "que resultó ser una subestimación significativa. "
    "Esto valida empíricamente la advertencia de la Parte 2 sobre el error de magnitud del 136.9% del RSJD "
    "en extrapolación fuera del dominio de calibración.\n",
]))

new_cells.append(md_cell([
    "### 6.4 Tabla comparativa de episodios\n",
    "\n",
    "![Tabla comparativa](outputs/figures/parte3/bloque6_tabla_comparativa.png)\n",
    "\n",
    "**Diferencia estructural clave:** El bloqueo del Estrecho de Ormuz en 2026 elimina el mecanismo "
    "de sustitución de rutas que existía en el episodio ucraniano, situando el escenario actual "
    "de forma más definitiva fuera del dominio de calibración del modelo.\n",
]))

# ══════════════════════════════════════════════════════════════
# BLOQUE 7
# ══════════════════════════════════════════════════════════════
new_cells.append(md_cell([
    "---\n",
    "# Bloque 7 — Análisis de Correlaciones Rodantes\n",
    "\n",
    "Las correlaciones entre activos no son estables: cambian con el régimen. "
    "Un shock energético extremo reorganiza las relaciones entre el crudo, la volatilidad, "
    "el dólar y la renta variable de forma que los modelos calibrados sobre periodos tranquilos "
    "no anticipan. Este bloque cuantifica esa reorganización en tres sub-bloques:\n",
    "\n",
    "- **7.1** Correlaciones rodantes (ventana 30d) para 5 pares clave: 2020-2026\n",
    "- **7.2** Comparativa de matrices de correlación: periodo pre-bélico vs. periodo bélico\n",
    "- **7.3** Heatmap completo del periodo bélico (los 13 activos del snapshot)\n",
    "\n",
    "> **Cifra más destacada:** WTI-OVX pasa de correlación **-0.285** (pre-guerra) a **+0.606** (guerra). "
    "El signo se invierte. Esto cierra con evidencia cuantitativa el análisis de canales de contagio del Bloque 4.5.\n",
]))

new_cells.append(code_cell([
    "# Ejecutar Bloque 7\n",
    "%run scripts/bloque7_rolling_correlations.py\n",
]))

new_cells.append(md_cell([
    "### 7.1 Correlaciones rodantes 2020-2026\n",
    "\n",
    "![Correlaciones rodantes](outputs/figures/parte3/bloque7_correlaciones_rodantes.png)\n",
    "\n",
    "**Rupturas identificadas:**\n",
    "\n",
    "| Par | Media pre-guerra | Media guerra | Delta | Interpretación |\n",
    "|-----|-----------------|--------------|-------|----------------|\n",
    "| WTI-OVX | -0.285 | +0.606 | **+0.890** | Inversión de signo: crudo y su volatilidad implícita se mueven juntos |\n",
    "| WTI-VIX | -0.122 | +0.260 | +0.382 | El crudo se acopla al miedo sistémico |\n",
    "| WTI-DXY | -0.059 | +0.177 | +0.236 | Se rompe la relación inversa estructural crudo-dólar |\n",
    "| OVX-VIX | +0.355 | +0.345 | -0.010 | Estable: volatilidades siguen moviéndose juntas |\n",
    "| WTI-Brent | +0.816 | +0.846 | +0.030 | Estable: spread WTI-Brent muy acoplado |\n",
]))

new_cells.append(md_cell([
    "### 7.2 Matrices de correlación: pre-bélico vs. periodo bélico\n",
    "\n",
    "![Matrices correlación](outputs/figures/parte3/bloque7_matrices_correlacion.png)\n",
    "\n",
    "**Qué lectura se extrae del delta (panel derecho):** Prácticamente **todos** los pares aumentan "
    "su correlación durante la guerra. El sistema financiero se comporta como un bloque más correlacionado: "
    "cuando el crudo sube, todo sube junto; cuando cae (evento Trump), todo cae junto. "
    "Esto reduce las posibilidades de diversificación intra-cartera en régimen de alta tensión.\n",
]))

new_cells.append(md_cell([
    "### 7.3 Heatmap completo periodo bélico (13 activos)\n",
    "\n",
    "![Heatmap bélico completo](outputs/figures/parte3/bloque7_heatmap_belico_completo.png)\n",
    "\n",
    "**Correlaciones destacadas (|r| > 0.60):**\n",
    "- **WTI-Brent (+0.953):** prácticamente perfecta — el spread se comprime en shocks extremos\n",
    "- **S&P500-NASDAQ (+0.985):** renta variable como bloque sincronizado\n",
    "- **VIX-S&P500 (-0.886):** canal inverso clásico, reforzado durante la guerra\n",
    "- **Oro-Plata (+0.807):** metales preciosos como bloque de refugio unificado\n",
    "- **XOM-CVX (+0.752):** equity energético acoplado — el canal de contagio confirmado del Bloque 4.5\n",
    "- **DXY-TNX (+0.653):** dólar y yields de bonos juntos: canal de política monetaria activo\n",
    "\n",
    "> *Nota metodológica:* Con solo 17 días de negociación en el periodo bélico, "
    "estas correlaciones son indicativas de la dinámica del periodo, no estimaciones robustas de largo plazo.\n",
]))

# ══════════════════════════════════════════════════════════════
# SUB-BLOQUE 4.6
# ══════════════════════════════════════════════════════════════
new_cells.append(md_cell([
    "---\n",
    "# Sub-bloque 4.6 — Semáforo de Salida del Régimen de Alta Tensión\n",
    "\n",
    "El motor de inferencia del Bloque 4 analiza escenarios *dentro* del régimen de estrés. "
    "Este sub-bloque responde la pregunta inversa: **¿qué condiciones cuantitativas indicarían "
    "una transición de vuelta al régimen normal?**\n",
    "\n",
    "Se definen cuatro condiciones de salida basadas en los umbrales del modelo de la Parte 1, "
    "ponderadas por su importancia SHAP:\n",
    "\n",
    "| Condición | Umbral | Peso |\n",
    "|-----------|--------|------|\n",
    "| OVX < 40 (umbral alerta modelo) | 40.0 | 30% |\n",
    "| OVX < 46.1 (P80 high\\_stress) | 46.1 | 30% |\n",
    "| GPR < 120 (umbral crítico modelo) | 120.0 | 20% |\n",
    "| VIX < 25 (nivel estrés macro) | 25.0 | 20% |\n",
    "\n",
    "**Criterio compuesto:** TODAS las condiciones deben cumplirse durante 5 días hábiles consecutivos.\n",
    "\n",
    "> **Por qué se incluye:** Un sistema de alerta es más útil si define explícitamente "
    "cuándo *dejar* de estar en alerta. La Parte 1 identifica las condiciones de entrada "
    "en el régimen de alta tensión; este sub-bloque define simétricamente las de salida.\n",
]))

new_cells.append(code_cell([
    "# Ejecutar Sub-bloque 4.6\n",
    "%run scripts/bloque4_6_exit_signal.py\n",
]))

new_cells.append(md_cell([
    "### Semáforo: estado actual vs. umbrales de salida\n",
    "\n",
    "![Semáforo de salida](outputs/figures/parte3/bloque4_6_semaforo_salida.png)\n",
    "\n",
    "**Resultado del snapshot (23-mar-2026): Exit Score = 18.8/100 | Estado: RÉGIMEN MÁXIMO ESTRÉS**\n",
    "\n",
    "| Condición | Actual | Umbral | Brecha | OK |\n",
    "|-----------|--------|--------|--------|----|\n",
    "| OVX < 40 | 91.85 | 40.0 | +51.85 | NO |\n",
    "| GPR < 120 | 248.83 | 120.0 | +128.83 | NO |\n",
    "| VIX < 25 | 26.78 | 25.0 | +1.78 | NO |\n",
    "| OVX < 46.1 | 91.85 | 46.1 | +45.75 | NO |\n",
    "\n",
    "**Lectura:** El indicador más cercano a su umbral es VIX (+1.78 puntos): el estrés financiero "
    "sistémico es moderado incluso con OVX en P98.6 — el patrón exacto de shock sectorial sin crisis "
    "financiera global. El indicador más alejado es GPR: necesita reducirse un 52% desde su nivel actual.\n",
]))

new_cells.append(md_cell([
    "### Precedente histórico: distribución de duraciones de episodios OVX > 40\n",
    "\n",
    "![Duración del régimen](outputs/figures/parte3/bloque4_6_duracion_regimen.png)\n",
    "\n",
    "**Qué lectura se extrae:**\n",
    "- Se identifican **57 episodios** históricos con OVX > 40 en el histórico completo desde 2007\n",
    "- Duración media: **34.9 días** | Duración mediana: **10 días** (distribución sesgada a la derecha)\n",
    "- El RSJD predice **≈43 días** — por encima de la media histórica, coherente con la severidad del episodio\n",
    "- El episodio actual llevaba **17 días** en el snapshot → percentil 61 de la distribución histórica\n",
    "  → El 39% de los episodios históricos ya habría terminado a esas alturas\n",
    "- El panel derecho (duración vs. OVX pico) muestra que los episodios con OVX > 90 "
    "tienden a durar significativamente más que la mediana — el único precedente comparable es COVID-2020\n",
    "\n",
    "> **Conclusión del sub-bloque:** Con ninguna de las cuatro condiciones de salida satisfecha "
    "y el OVX necesitando reducirse un 56% desde su nivel actual para alcanzar el umbral principal, "
    "el modelo no puede declarar proximidad a una transición de régimen. "
    "Esta es la respuesta correcta: un sistema de alerta honesto incluye explícitamente "
    "cuándo *no* puede señalar la salida.\n",
]))

nb["cells"].extend(new_cells)

with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f"Notebook actualizado correctamente.")
print(f"Total de celdas: {len(nb['cells'])} (antes: 66, añadidas: {len(new_cells)})")
