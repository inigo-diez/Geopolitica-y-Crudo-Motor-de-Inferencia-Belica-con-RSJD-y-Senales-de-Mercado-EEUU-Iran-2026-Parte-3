# Análisis y Predicción de Días de Alta Tensión en el Mercado del Petróleo Crudo (WTI) mediante Factores Geopolíticos e Indicadores de Mercado


## Resumen Ejecutivo

El petróleo crudo es, junto con las divisas, la materia prima con mayor influencia sobre la economía global. Su precio no depende únicamente de la oferta y la demanda física: está profundamente condicionado por la percepción del riesgo geopolítico, los conflictos armados en regiones productoras, las decisiones de cárteles como la OPEP+ y la fortaleza del dólar estadounidense. Esta interdependencia hace del mercado del crudo un laboratorio natural para estudiar si la información noticiosa anticipada puede traducirse en señales predictivas cuantificables.

Este proyecto responde a una pregunta concreta: **¿puede la actividad noticiosa geopolítica en zonas estratégicas de producción de petróleo anticipar, con un día de antelación, los días de alta tensión en el mercado del WTI?** Para responderla se construye un flujo de trabajo completo de ciencia de datos que integra cuatro fuentes heterogéneas — precios de mercado (FRED), índices de volatilidad (CBOE), un índice académico de riesgo geopolítico (Caldara & Iacoviello, 2022) y el proyecto GDELT de monitorización noticiosa global — sobre un horizonte temporal de 2010 a 2026.

Los resultados son honestos y matizados. El mejor modelo alcanza una puntuación F1 de **0,571** y un área bajo la curva ROC de **0,615** en el conjunto de validación (2021–2026), superando al clasificador aleatorio (AUC = 0,50) y al modelo de referencia lineal (AUC = 0,578). La señal geopolítica existe y es estadísticamente distinguible, pero es débil: las variables de memoria del propio mercado (volatilidad pasada del crudo, cambios rezagados en el OVX) resultan ser los predictores más potentes. Este hallazgo es coherente con la hipótesis de mercados semi-eficientes: si la información geopolítica pública fuera fácilmente explotable, ya habría sido incorporada al precio.

El proyecto tiene relevancia directa para gestores de riesgo en el sector energético, analistas de materias primas y cualquier inversor con exposición a productos derivados del crudo.

---

## Índice de Contenidos

1. [Introducción y Contexto](#1-introducción-y-contexto)
2. [Bases de Datos: Descripción Exhaustiva](#2-bases-de-datos-descripción-exhaustiva)
3. [Metodología](#3-metodología)
4. [Análisis Exploratorio de Datos](#4-análisis-exploratorio-de-datos)
5. [Estudio de Eventos Geopolíticos](#5-estudio-de-eventos-geopolíticos)
6. [Ingeniería de Variables Predictoras](#6-ingeniería-de-variables-predictoras)
7. [Modelos de Referencia](#7-modelos-de-referencia)
8. [Modelos de Clasificación](#8-modelos-de-clasificación)
9. [Modelos de Regresión](#9-modelos-de-regresión)
10. [Interpretabilidad y Robustez](#10-interpretabilidad-y-robustez)
11. [Aplicación Práctica para el Inversor en Crudo](#11-aplicación-práctica-para-el-inversor-en-crudo)
12. [Conclusiones Elaboradas](#12-conclusiones-elaboradas)
13. [Limitaciones y Sesgos Explícitos](#13-limitaciones-y-sesgos-explícitos)
14. [Transparencia Técnica y Reproducibilidad](#14-transparencia-técnica-y-reproducibilidad)
15. [Referencias Bibliográficas](#15-referencias-bibliográficas)
16. [Glosario Técnico](#16-glosario-técnico)

---

## 1. Introducción y Contexto

El petróleo crudo no es una materia prima ordinaria. Es el insumo energético sobre el que se asienta buena parte de la economía industrial moderna: mueve el transporte global, alimenta la petroquímica, calienta hogares y genera electricidad en decenas de países. Un aumento sostenido del 20% en su precio equivale, en términos de impacto macroeconómico, a un impuesto regresivo sobre la energía que recae con especial dureza sobre economías importadoras netas y sobre los segmentos de menor renta de la población.

Por eso el precio del crudo ocupa un lugar central en los modelos de previsión de inflación de los bancos centrales, en las matrices de riesgo de las aseguradoras de infraestructura energética y en las carteras de los fondos de inversión con exposición a materias primas. Su volatilidad ha sido históricamente elevada y está lejos de seguir un patrón predecible.

### ¿Por qué los eventos geopolíticos importan al precio del crudo?

La respuesta es estructural. Aproximadamente el 65% de las reservas probadas de petróleo del mundo se concentran en cuatro zonas geopolíticamente inestables: el Golfo Pérsico (Arabia Saudí, Irán, Irak, Kuwait, Emiratos Árabes Unidos), Rusia y las repúblicas del Asia Central, Venezuela y África Subsahariana. Cuando la estabilidad política o militar de cualquiera de estas regiones se ve amenazada, el mercado reacciona de forma casi inmediata: no porque el suministro físico se interrumpa necesariamente, sino porque los operadores anticipan que podría hacerlo.

A esto se añade la dimensión del transporte. Aproximadamente el 20% del petróleo que se comercia a nivel mundial pasa por el Estrecho de Ormuz, y otro porcentaje significativo por el Canal de Suez. Cualquier amenaza de cierre o bloqueo de estas rutas de paso genera picos de volatilidad en las plataformas de futuros en cuestión de minutos.

La tercera dimensión es el poder de mercado organizado. La OPEP+, coalición que agrupa a los países productores de la OPEP clásica más Rusia y otros aliados, controla aproximadamente el 40% de la producción mundial. Sus decisiones sobre cuotas de producción tienen capacidad para mover el precio del barril en varios dólares en cuestión de horas.

### Una década de volatilidad extrema

El período 2010–2026 que cubre este análisis ha sido extraordinariamente rico en perturbaciones:

- **2011**: la Primavera Árabe sacude Libia. El WTI supera los 110 USD/barril.
- **2014–2016**: Arabia Saudí decide no recortar producción para defender cuota de mercado. El WTI cae de 105 a 26 USD/barril en dieciocho meses.
- **2019**: ataque con drones a las instalaciones de Aramco en Abqaiq. El WTI sube más de un 14% en una sesión.
- **Abril de 2020**: los contratos de futuros WTI cotizan en **−37,63 USD/barril** por primera y única vez en la historia.
- **2022**: invasión rusa de Ucrania. El WTI supera los 120 USD/barril.
- **2023–2024**: conflicto Israel-Hamás y escalada en el Mar Rojo. Los ataques a buques obligan a redirigir el tráfico marítimo alrededor del Cabo de Buena Esperanza.

### Justificación del análisis

Si existiera un desfase temporal medible entre el incremento de la cobertura noticiosa de eventos conflictivos en zonas petroleras y los movimientos bruscos del mercado, ese desfase podría ser utilizado por gestores de riesgo para ajustar sus posiciones de cobertura antes de que el mercado reaccione. Este proyecto no pretende construir un sistema de negociación algorítmica. Su objetivo es más modesto y más sólido: construir y evaluar rigurosamente esa señal geopolítica cuantitativa y documentar con honestidad sus capacidades y limitaciones.

---

## 2. Bases de Datos: Descripción Exhaustiva

### 2.1 GDELT — Base de Datos Global de Eventos, Idioma y Tono

**¿Qué es GDELT?**

El proyecto GDELT (*Global Database of Events, Language and Tone*) es un sistema de monitorización de noticias globales que procesa en tiempo real más de 300 millones de artículos de prensa en más de 100 idiomas. Fue desarrollado por Kalev Leetaru y Philip Schrodt con el respaldo técnico de Google Jigsaw y está disponible de forma pública y gratuita. Cada noticia procesada genera uno o varios registros de eventos, codificados mediante el sistema CAMEO.

**El sistema CAMEO (Conflict and Mediation Event Observations)**

CAMEO es una taxonomía estandarizada que clasifica los eventos noticiosos internacionales en aproximadamente 20 categorías principales y más de 300 subcategorías. Fue desarrollada por Philip Schrodt (2012) para permitir el análisis sistemático y cuantitativo de eventos políticos a escala global. Las categorías van desde la cooperación verbal (código 1) hasta la violencia masiva (código 20).

| Código CAMEO | Descripción | Relevancia para el crudo |
|---|---|---|
| 13–14 | Amenaza, protesta | Tensión geopolítica moderada |
| 15 | Exhibición de fuerza militar | Posible perturbación de suministro |
| 17–18 | Coerción y asalto | Alta probabilidad de impacto en producción |
| 19–20 | Combate y violencia masiva | Máximo riesgo geopolítico |

**Dos dimensiones complementarias del GDELT**

Este proyecto utiliza el GDELT en dos dimensiones distintas:

- **GDELT-Eventos**: recuento de eventos por día y zona geográfica codificados en CAMEO. Mide la *cantidad* de actividad noticiosa conflictiva.
- **GDELT-Tono**: puntuación de sentimiento de −100 a +100. Puntuaciones negativas indican cobertura conflictiva o catastrofista; positivas indican cooperación. En este dataset, el tono medio es consistentemente negativo (entre −2 y −4), coherente con el filtro por zonas de conflicto.

**La Escala Goldstein**

La escala Goldstein es una puntuación de −10 a +10 asignada a cada código CAMEO que cuantifica el impacto teórico esperado del tipo de evento sobre la estabilidad de un país (Goldstein, 1992). Los valores extremos corresponden a:
- **−10**: uso de armas de destrucción masiva, bombardeo de poblaciones civiles
- **+10**: acuerdos de paz, firma de tratados de cooperación plena

Este proyecto identifica como "eventos extremos" los que tienen Goldstein inferior a −7.

**Limitación detectada: caída del 70% en el volumen post-2019**

A partir del año 2020, el volumen de eventos registrados cae aproximadamente un 70%. Esta caída no refleja una reducción en la actividad geopolítica real — el año 2022, con la invasión rusa de Ucrania, registra el mismo volumen que 2021 — sino un artefacto del proceso de extracción por cambios en los patrones de cobertura mediática de las fuentes primarias del GDELT. En la Sección 6 se detalla cómo se mitiga construyendo ratios relativos.

**Cobertura geográfica filtrada**

| Región | Países (códigos FIPS) | Justificación |
|---|---|---|
| Golfo Pérsico | SA, IR, IZ, QA, YM, BA, AE, KU, SY | ~35% de producción mundial |
| Rusia y antiguas repúblicas soviéticas | RS, UP, AJ, GG | ~12% de producción, exportador clave |
| África | LY, NI, AG, SU | Inestabilidad crónica, producción significativa |
| América | VE, MX, CU, EC | Venezuela y México, productores regionales |

**Archivo:** `Datasets/GDELT.csv` · Rango: 2015-01-05 a 2026-03-18 · ~60.000 registros

---

### 2.2 WTI — Precio del Petróleo Crudo West Texas Intermediate

El WTI es el petróleo crudo ligero y dulce producido en la cuenca Pérmica de Texas. Es el índice de referencia más utilizado globalmente para transacciones de petróleo crudo en el mercado americano y el subyacente de los contratos de futuros más líquidos del mundo (CME Group, NYMEX). Su precio de referencia se fija diariamente en el mercado de Cushing, Oklahoma.

En este proyecto el WTI actúa como variable para construir la variable objetivo (sus retornos logarítmicos) y como serie de precios de referencia en el estudio de eventos históricos (1986–2026).

**Rango observado (2010–2026):** −36,98 USD/barril (crisis de futuros, abril 2020) a 123,64 USD/barril (junio 2022).

**Archivo:** `Datasets/WTI_USA.csv` · Fuente: FRED, serie DCOILWTICO · Rango: 1986-01-02 a 2026-03-16

---

### 2.3 OVX — Índice de Volatilidad del Crudo CBOE

El OVX (*CBOE Crude Oil Volatility Index*) mide la volatilidad esperada del precio del WTI en los próximos 30 días naturales, derivada de los precios de opciones sobre el ETF USO. Es el análogo del VIX para el mercado del crudo: un OVX de 40 indica que el mercado anticipa movimientos anualizados del ±40% en el precio del WTI.

**Rol en este proyecto:** segunda componente de la variable objetivo. Sus incrementos diarios bruscos indican que el mercado percibe un aumento repentino en la incertidumbre sobre el precio futuro del crudo.

**Rango observado:** 14,5 (mercados calmados, 2017) a 325,15 (pico de abril 2020).

**Archivo:** `Datasets/OVX.csv` · Fuente: CBOE vía Yahoo Finance · Rango: 2007-05-10 a 2026-03-19

---

### 2.4 VIX — Índice de Volatilidad del Mercado Bursátil

El VIX mide la volatilidad esperada del índice S&P 500 en los próximos 30 días. Comúnmente llamado "índice del miedo", un VIX por encima de 30 indica estrés significativo en los mercados financieros globales.

**Relación con el crudo:** en episodios de pánico sistémico (COVID-19, 2020) el VIX y el OVX suben juntos. En shocks puramente geopolíticos (ataque a Abqaiq, 2019) el OVX puede dispararse mientras el VIX permanece estable, confirmando que la tensión es específica del mercado energético. Esta distinción es clave para interpretar el origen del riesgo.

**Rango observado:** 9,14 (enero 2018) a 82,69 (marzo 2020).

**Archivo:** `Datasets/VIX_History.csv` · Fuente: CBOE Historical Data · Rango: 1990-01-02 a 2026-03-18

---

### 2.5 GPR — Índice de Riesgo Geopolítico

El Índice de Riesgo Geopolítico (GPR) fue desarrollado por Dario Caldara y Matteo Iacoviello (economistas de la Reserva Federal de Estados Unidos) y publicado en el *American Economic Review* (2022). Es la medida de riesgo geopolítico con mayor respaldo empírico en la literatura de economía y finanzas.

**Metodología:** se construye contando la frecuencia con que ciertos términos relacionados con conflictos geopolíticos aparecen en once grandes periódicos internacionales de lengua inglesa. La frecuencia se normaliza: base 100 = promedio del período 1985–2019.

**Archivo:** `Datasets/data_gpr_daily_recent.csv` · Fuente: Caldara & Iacoviello (2022) · Rango: 1985-01-01 a 2026-03-16

---

### 2.6 DXY — Índice del Dólar Estadounidense

El DXY mide el valor del dólar frente a una cesta ponderada de seis divisas: euro (57,6%), yen (13,6%), libra esterlina (11,9%), dólar canadiense (9,1%), corona sueca (4,2%) y franco suizo (3,6%).

**Relación inversa estructural con el crudo:** dado que el petróleo se cotiza en dólares, un dólar más fuerte encarece el crudo para compradores no estadounidenses, reduciendo su demanda y presionando el precio a la baja.

**Rango observado:** 72,93 (2011, dólar débil) a 114,11 (septiembre 2022, máximos de 20 años).

**Archivo:** `Datasets/DXY.csv` · Fuente: Yahoo Finance · Rango: 2010-01-04 a 2026-03-19

---

### 2.7 Cronología de Eventos Geopolíticos: 35 Casos Seleccionados

Para el estudio de eventos se construyó manualmente una cronología de 35 hitos geopolíticos con potencial impacto directo o indirecto sobre la oferta de petróleo, el transporte marítimo o las expectativas del mercado.

| N.º | Fecha | Tipo | Evento | Severidad | Impacto WTI esperado |
|---|---|---|---|---|---|
| 1 | 2010-04-20 | Desastre | Explosión Deepwater Horizon | 7 | ↑ incertidumbre oferta |
| 2 | 2011-02-15 | Guerra | Inicio de la Guerra Civil libia | 9 | ↑ reducción oferta |
| 3 | 2011-03-19 | Guerra | Intervención de la OTAN en Libia | 9 | ↑ escalada |
| 4 | 2012-01-23 | Sanciones | Embargo de la UE al petróleo iraní | 8 | ↑ reducción exportaciones |
| 5 | 2014-03-18 | Anexión | Rusia anexiona Crimea | 8 | ↑ riesgo geopolítico |
| 6 | 2014-11-27 | OPEP | OPEP mantiene producción pese a caída de precios | 9 | ↓ guerra de precios |
| 7 | 2015-03-26 | Guerra | Intervención saudí en Yemen | 7 | ↑ riesgo regional |
| 8 | 2016-01-16 | Sanciones | Levantamiento de sanciones nucleares a Irán | 6 | ↓ aumento oferta |
| 9 | 2016-09-28 | OPEP | Acuerdo de Argel sobre recortes | 8 | ↑ reducción oferta |
| 10 | 2016-11-30 | OPEP | Primer acuerdo de recortes OPEP+ | 8 | ↑ reducción oferta |
| 11 | 2017-06-05 | Diplomacia | Inicio del bloqueo a Catar | 6 | ↑ incertidumbre regional |
| 12 | 2018-05-08 | Sanciones | EE. UU. abandona el acuerdo nuclear iraní | 8 | ↑ reducción exportaciones |
| 13 | 2019-09-14 | Ataque | Ataque con drones a la refinería Abqaiq de Aramco | 10 | ↑ shock oferta inmediato |
| 14 | 2020-01-03 | Conflicto | EE. UU. mata al general iraní Soleimani | 9 | ↑ escalada bélica |
| 15 | 2020-03-08 | Guerra de precios | Arabia Saudí-Rusia inician guerra de precios | 10 | ↓ colapso precio |
| 16 | 2020-04-20 | Colapso de mercado | WTI cotiza en precio negativo (−37,63 USD) | 10 | ↓ evento histórico |
| 17 | 2021-03-23 | Bloqueo | Canal de Suez bloqueado por el buque Ever Given | 8 | ↑ riesgo transporte |
| 18 | 2021-10-04 | Crisis energética | Crisis energética global se intensifica | 7 | ↑ tensión oferta |
| 19 | 2022-02-24 | Guerra | Rusia invade Ucrania | 10 | ↑ máxima perturbación |
| 20 | 2022-03-08 | Sanciones | EE. UU. prohíbe el petróleo ruso | 9 | ↑ reconfiguración flujos |
| 21 | 2022-06-01 | Sanciones | La UE impone embargo al petróleo ruso | 8 | ↑ reducción oferta europea |
| 22 | 2022-12-05 | Sanciones | El G7 establece tope de precio al crudo ruso | 7 | ± efecto ambiguo |
| 23 | 2023-04-02 | OPEP | OPEP+ anuncia recortes sorpresa de producción | 9 | ↑ reducción oferta |
| 24 | 2023-10-07 | Guerra | Inicio de la guerra Israel-Hamás | 9 | ↑ riesgo regional |
| 25 | 2024-01-12 | Conflicto | Escalada de ataques en el Mar Rojo | 8 | ↑ riesgo transporte |
| 26 | 2024-04-14 | Conflicto | Irán lanza ataque de drones sobre Israel | 9 | ↑ escalada directa |
| 27 | 2024-08-26 | Bloqueo | Administración libia oriental paraliza producción | 8 | ↑ reducción oferta |
| 28 | 2024-10-01 | Conflicto | Escalada de ataques a petroleros en el Mar Rojo | 8 | ↑ riesgo transporte |
| 29 | 2025-02-20 | Conflicto | Crisis de seguridad de petroleros en Oriente Medio | 8 | ↑ prima de riesgo |
| 30 | 2025-06-10 | OPEP | OPEP+ anuncia recortes adicionales de producción | 8 | ↑ reducción oferta |
| 31 | 2025-10-28 | Cambio de mercado | Banco Mundial alerta sobre exceso de oferta en 2026 | 7 | ↓ expectativas demanda |
| 32 | 2025-11-18 | Sanciones | Ampliación de sanciones al petróleo iraní | 7 | ↑ reducción exportaciones |
| 33 | 2026-02-28 | Conflicto | Ataques EE. UU.-Israel sobre infraestructura iraní | 10 | ↑ shock geopolítico máximo |
| 34 | 2026-03-01 | OPEP | OPEP+ extiende recortes voluntarios de producción | 8 | ↑ reducción oferta |
| 35 | 2026-03-09 | Bloqueo | Cierre del Estrecho de Ormuz al tráfico marítimo | 10 | ↑ shock transporte crítico |

---

## 3. Metodología

### 3.1 Limpieza y Preparación de Datos

Cada fuente presenta problemas específicos resueltos en el Cuaderno 01:

- **WTI y Brent (FRED):** se eliminan filas de fin de semana y festivos con valor nulo (el mercado no cotizó, no son datos faltantes reales).
- **OVX y DXY (Yahoo Finance):** formato con dos filas de cabecera de metadatos; se saltan con `skiprows=2`.
- **GPR (Caldara & Iacoviello):** separador de punto y coma y coma como separador decimal (convención europea). Se parsea explícitamente.
- **GDELT:** fecha en formato `YYYYMMDD`. Se convierte con `pd.to_datetime(..., format='%Y%m%d')`. Se eliminan duplicados exactos.

### 3.2 Construcción del Dataset Maestro

El Cuaderno 02 ensambla todas las fuentes limpias en `ml_dataset.parquet`. El esquema es:

1. **Calendario base:** los días hábiles con precio WTI disponible actúan como columna vertebral.
2. **VIX, DXY y GPR:** se propaga el último valor disponible hacia adelante con un límite de 3 días para cubrir festivos propios distintos al mercado del crudo.
3. **GDELT:** se agrega a nivel diario calculando recuentos, medias ponderadas por menciones y estadísticos de intensidad.
4. **Período 2010–2014 sin GDELT:** columnas de recuento se imputan a cero. Columnas de media (tono, Goldstein) se dejan como valores nulos para no introducir sesgo.

**Características del dataset maestro:**

| Característica | Valor |
|---|---|
| Total de observaciones | 4.059 días hábiles |
| Período | 2010-01-04 a 2026-03-13 |
| Conjunto de entrenamiento | 2.762 días (2010–2020) |
| Conjunto de validación | 1.297 días (2021–2026) |
| Columnas en el dataset maestro | 37 |

### 3.3 Definición de la Variable Objetivo

Un día `t` se clasifica como **día de alta tensión de mercado** si cumple al menos una de estas condiciones referidas al día siguiente (`t+1`):

1. El **retorno logarítmico absoluto del WTI** en `t+1` supera el percentil 80 calculado sobre el entrenamiento: |retorno| > **2,47%**
2. El **incremento diario del OVX** en `t+1` supera el percentil 80 calculado sobre el entrenamiento: ΔOVX > **1,042 puntos**

**Por qué solo sobre el conjunto de entrenamiento:** si los umbrales se calcularan sobre el dataset completo, la información del período de validación contaminaría la definición de lo que se pretende predecir — una forma de filtración temporal de datos que inflaría artificialmente las métricas. Los umbrales se guardan en `outputs/target_thresholds.csv` y se reutilizan sin recalcular.

La variable objetivo resultante presenta un **33,2% de días de alta tensión** (condición OR de dos variables al percentil 80, con correlación positiva entre ambas).

---

## 4. Análisis Exploratorio de Datos

### 4.1 Auditoría de Cobertura Temporal

![Auditoría de cobertura temporal](outputs/fig_coverage_audit.png)

*Figura 1. Izquierda: porcentaje de valores nulos por bloque de variables. Derecha: días con datos disponibles por fuente y año. Se aprecia claramente la ausencia de GDELT antes de 2015 y la caída en su volumen post-2019.*

### 4.2 Series Temporales Principales

![Series temporales principales](outputs/fig_timeseries_main_5panels.png)

*Figura 2. Cinco paneles sincronizados: (1) precio WTI en USD/barril; (2) OVX frente al VIX; (3) DXY con zona sombreada cuando supera su media histórica; (4) actividad noticiosa GDELT normalizada; (5) retorno absoluto diario del WTI coloreado por la variable objetivo (marrón = día normal, rojo = día de alta tensión al día siguiente).*

La figura condensa la narrativa del período. Son identificables la caída de 2014–2016, el precio negativo de abril 2020, la subida de 2022 por la guerra de Ucrania y la paradoja central del proyecto: el Panel 4 muestra actividad noticiosa GDELT baja en los meses previos al mayor shock del período (COVID-19), porque la pandemia fue un evento sanitario, no un conflicto geopolítico entre estados. El sistema CAMEO no está diseñado para capturar pandemias.

### 4.3 Distribuciones de las Variables de Mercado

![Distribuciones del mercado de crudo](outputs/fig_distributions_market.png)

*Figura 3. Distribuciones del retorno logarítmico diario, retorno absoluto, cambio en OVX, volatilidad móvil a 10 días, diferencial WTI-Brent y nivel del OVX. n = 4.059 observaciones. La distribución de retornos presenta colas extremadamente gruesas (curtosis en exceso > 10), rechazando la hipótesis de normalidad con p-valor < 0,001.*

![Distribuciones de riesgo sistémico](outputs/fig_distributions_risk_factors.png)

*Figura 4. Distribuciones del VIX y el DXY. El VIX presenta una cola derecha pronunciada reflejo de los episodios de pánico de 2020.*

La no-normalidad severa de los retornos del WTI justifica el uso de modelos no paramétricos (bosques aleatorios, XGBoost) y valida el uso de pruebas estadísticas como Mann-Whitney U.

### 4.4 Sesgos Temporales en el GDELT

![Sesgos temporales del GDELT](outputs/fig_gdelt_bias.png)

*Figura 5. Barras azules (escala izquierda): volumen de eventos GDELT por año. Línea roja (escala derecha): tono medio anual ponderado. La caída post-2019 en el volumen es un artefacto de extracción, no un reflejo de menor actividad geopolítica real.*

![Distribuciones GDELT](outputs/fig_gdelt_distributions.png)

*Figura 6. Distribuciones de las variables GDELT principales: escala Goldstein, menciones, tono y recuento de eventos.*

![GDELT por región y tipo de evento](outputs/fig_gdelt_by_region_type.png)

*Figura 7. Actividad GDELT por región geopolítica y por tipo de evento CAMEO. El Golfo Pérsico concentra el mayor volumen.*

### 4.5 Análisis de Correlaciones y Dependencias

![Matriz de correlación extendida](outputs/fig_correlation_matrix_extended.png)

*Figura 8. Matriz de correlaciones de Pearson entre todas las variables del dataset ML. OVX–VIX: ~0,65. DXY–WTI: ~−0,30. Variables GDELT–WTI: 0,02–0,08.*

### 4.6 Análisis de Adelanto Temporal GDELT → Mercado

![Análisis de adelanto temporal](outputs/fig_leadlag.png)

*Figura 9. Correlaciones cruzadas entre variables GDELT y la variable objetivo para retardos de −5 a +5 días. Las barras rojas (retardo positivo) indican que el GDELT del pasado se correlaciona con el mercado actual. La señal en retardo +1 es ligeramente superior al retardo 0, pero la diferencia es pequeña (~0,01–0,03 puntos).*

### 4.7 Días de Alta Tensión vs. Días Normales

![Días de estrés vs. normales](outputs/fig_stress_vs_normal.png)

*Figura 10. Comparativa mediante diagramas de violín entre días de alta tensión (rojo) y normales (verde) para las principales variables, con p-valor del test Mann-Whitney U.*

El test de Mann-Whitney U es una prueba estadística no paramétrica que no asume distribución normal — supuesto que los retornos financieros violan sistemáticamente. Compara si los valores de una variable en días de alta tensión tienden sistemáticamente a ser superiores a los de días normales. Un p-valor inferior a 0,05 confirma que la diferencia es estadísticamente significativa y no atribuible al azar. El VIX y el OVX muestran diferencias altamente significativas; las variables GDELT también son significativas pero con menor tamaño del efecto.

### 4.8 Comparativo de Índices de Riesgo

![Comparativo de índices de riesgo](outputs/fig_risk_indices_comparison.png)

*Figura 11. VIX, OVX y GPR normalizados (0-1) en el tiempo. La convergencia de los tres en 2020 indica crisis sistémica. En 2022, el GPR sube primero antes de que el OVX reaccione, patrón de shock geopolítico que se transmite al mercado energético.*

### 4.9 Análisis de Autocorrelación y Agrupamiento de Volatilidad

![Función de autocorrelación](outputs/fig_acf_volatility.png)

*Figura 12. Función de autocorrelación del retorno logarítmico (izquierda) y de la volatilidad (derecha). Los retornos no se autocorrelacionan significativamente (el mercado es eficiente en media), pero la volatilidad sí: los períodos de alta volatilidad tienden a persistir, fenómeno conocido como agrupamiento de volatilidad.*

### 4.10 Top Días Extremos

![Top días extremos](outputs/fig_top_extremes.png)

*Figura 13. Los 10 mayores shocks de mercado por retorno absoluto, marcados sobre el dataset completo. Se concentran en 2020 y 2022.*

---

## 5. Estudio de Eventos Geopolíticos

El estudio de eventos es una metodología clásica en economía financiera (MacKinlay, 1997) que aísla el impacto causal de un evento específico en una variable de interés. Para cada uno de los 35 hitos geopolíticos se define una ventana de análisis de [−5, +20] días hábiles. El **Retorno Acumulado Anormal** (RAA) se calcula como la suma de las diferencias entre el retorno observado y el retorno esperado sin el evento en cada día de la ventana posterior.

![Catálogo de eventos](outputs/fig_event_catalogue.png)

*Figura 14. Catálogo de los 35 eventos geopolíticos por tipo y severidad. Los eventos de mayor severidad (≥9) corresponden a guerras, guerras de precios OPEP y ataques directos a infraestructura.*

![Trayectoria del WTI alrededor del evento](outputs/fig_event_wti_path.png)

*Figura 15. Trayectoria media del WTI en la ventana [−5, +20] días alrededor del evento, por tipo. Las líneas finas representan cada evento individual; la línea gruesa es la media del grupo; la banda sombreada es ±1 desviación típica. El precio está normalizado a 100 en el día 0.*

![Retorno acumulado anormal](outputs/fig_event_car.png)

*Figura 16. Retorno acumulado anormal (RAA) medio por tipo de evento en los 10 días posteriores al hito.*

![Evolución del OVX alrededor del evento](outputs/fig_event_ovx_path.png)

*Figura 17. Evolución normalizada del OVX en la ventana del evento. La volatilidad implícita empieza a subir en los días −2 y −1 (antes del evento), alcanza su máximo en torno al día +2 y revierte gradualmente en 10–15 días.*

![Mapa de calor de retornos por evento](outputs/fig_event_heatmap.png)

*Figura 18. Mapa de calor de retornos WTI por evento individual (filas) y día relativo al evento (columnas). Rojo = retornos positivos; azul = negativos. La dispersión pone de manifiesto la heterogeneidad de las reacciones.*

![Test de volatilidad](outputs/fig_event_volatility_test.png)

*Figura 19. Test de Mann-Whitney U comparando la distribución de retornos absolutos del WTI dentro de la ventana del evento (días 0 a +20) frente a días fuera de la ventana (resto del período). Se comparan dos grupos: (1) retornos en los 20 días hábiles posteriores al hito geopolítico, y (2) retornos en días no vinculados a ningún evento. Un p-valor inferior a 0,05 confirma que el evento tuvo un impacto estadísticamente significativo en la volatilidad del mercado.*

**Conclusiones del estudio de eventos:**
- Los conflictos bélicos y ataques a infraestructura generan un incremento medio del WTI de entre el 3% y el 5% en los primeros 5 días.
- El OVX anticipa el evento: sube en los días −2 y −1 antes del hito geopolítico.
- Las decisiones de la OPEP+ tienen el efecto más predecible y sostenido.
- La heterogeneidad entre eventos del mismo tipo es elevada, lo que limita la generalización.

---

## 6. Ingeniería de Variables Predictoras

La ingeniería de variables predictoras es el proceso de construir nuevas variables a partir de los datos brutos para mejorar la capacidad predictiva de los modelos. Se construyeron **67 variables predictoras** en cinco grupos, todas con retardo temporal mínimo de 1 día respecto a la variable objetivo para garantizar que ninguna variable del día `t` incluye información de `t+1`.

![Análisis de variables predictoras](outputs/fig_feature_analysis.png)

*Figura 20. Análisis de las 67 variables predictoras: importancia, correlación con la variable objetivo y distribuciones por grupo.*

| Grupo | N.º variables | Fuente | Objetivo |
|---|---|---|---|
| Mercado | 16 | WTI, Brent, OVX | Capturar memoria a corto plazo del mercado |
| VIX/DXY | 16 | VIX, DXY | Contexto macroeconómico y de riesgo sistémico |
| GDELT | 24 | GDELT Project | Señal noticiosa geopolítica por región y tipo |
| GPR | 6 | Caldara & Iacoviello | Riesgo geopolítico con validación académica |
| Interacciones | 5 | Combinaciones cruzadas | Efectos no lineales combinados |

![Correlación de variables con la variable objetivo](outputs/fig_feature_target_corr.png)

*Figura 21. Correlación individual de cada variable predictora con la variable objetivo. Las variables de mercado presentan las correlaciones más altas; las GDELT, bajas pero positivas y consistentes.*

![Mapa de colinealidad entre variables](outputs/fig_feature_correlation.png)

*Figura 22. Mapa de calor de correlaciones entre variables predictoras. Permite identificar grupos redundantes antes del modelado.*

---

## 7. Modelos de Referencia

![Resumen visual del baseline](outputs/fig_baseline_summary.png)
*Figura 23. Métricas de los modelos de referencia.*

![Resultados baseline clasificación](outputs/fig_baseline_clf.png)
*Figura 24. Puntuación F1 y AUC-ROC de los modelos de referencia en clasificación.*

![Resultados baseline regresión](outputs/fig_baseline_reg.png)
*Figura 25. Error absoluto medio (MAE) y R² de los modelos de referencia en regresión.*

Los modelos de regresión logística y regresión lineal regularizada sirven como cota inferior. Sus resultados (F1 ~ 0,38–0,55, AUC ~ 0,56–0,58, R² ~ 0,05) confirman que la relación es fundamentalmente no lineal y que los modelos de conjunto tienen margen real de mejora.

---

## 8. Modelos de Clasificación

Se entrenan y optimizan cuatro modelos: regresión logística, bosque aleatorio, XGBoost y LightGBM. La validación se realiza con división temporal en 5 particiones que respeta el orden cronológico de los datos.

![Resultados de clasificación](outputs/fig_clf_results.png)

*Figura 26. Métricas en el conjunto de validación (2021–2026): puntuación F1, AUC-ROC, precisión y exhaustividad por modelo y conjunto de variables.*

![Importancia de variables](outputs/fig_clf_feature_importance.png)

*Figura 27. Importancia de las variables predictoras según el mejor modelo (bosque aleatorio con todas las variables).*

| Modelo | Variables | F1 | AUC-ROC |
|---|---|---|---|
| Regresión Logística | Solo mercado | 0,552 | 0,585 |
| Regresión Logística | Todas | 0,541 | 0,578 |
| **Bosque Aleatorio** | Solo mercado | 0,555 | 0,614 |
| **Bosque Aleatorio** | **Todas** | **0,571** | **0,615** |
| XGBoost | Solo mercado | 0,368 | 0,557 |
| XGBoost | Todas | 0,512 | 0,562 |

---

## 9. Modelos de Regresión

![Análisis de regresión](outputs/fig_reg_analysis.png)

*Figura 28. Predicciones frente a valores reales, distribución de residuos y métricas por modelo.*

| Modelo | Variables | MAE | R² |
|---|---|---|---|
| Media histórica (referencia) | — | 0,01119 | −0,006 |
| Regresión Ridge | Solo mercado | 0,01154 | 0,056 |
| **Bosque Aleatorio** | **Todas** | **0,01085** | **0,136** |
| XGBoost | Todas | 0,01109 | 0,086 |

El R² de 0,136 es bajo en términos absolutos pero esperado: predecir la magnitud exacta de retornos financieros diarios es uno de los problemas más difíciles de la econometría. El modelo captura el 13,6% de la varianza, suficiente para ordenar los días por nivel de riesgo esperado.

---

## 10. Interpretabilidad y Robustez

### Importancia mediante valores SHAP

Los valores SHAP (*SHapley Additive exPlanations*) asignan a cada variable predictora una contribución cuantificada a cada predicción individual, basándose en la teoría de juegos cooperativos de Shapley.

![Importancia SHAP media](outputs/fig_shap_importance.png)

*Figura 29. Importancia SHAP media absoluta. El eje horizontal representa la contribución media de cada variable para desplazar la predicción del modelo respecto al valor base (prevalencia media de días de alta tensión del 33,2%). Variables con SHAP alto son las que el modelo usa con mayor intensidad para discriminar.*

![Diagrama de enjambre SHAP](outputs/fig_shap_beeswarm.png)

*Figura 30. Diagrama de enjambre SHAP. Cada punto es una observación. Eje horizontal: valor SHAP (positivo = empuja hacia "día de alta tensión"; negativo = hacia "día normal"). Color: rojo = valor alto de la variable; azul = valor bajo. Una nube roja a la derecha indica que valores altos de esa variable se asocian con mayor probabilidad de alta tensión.*

![Estudio de ablación](outputs/fig_ablation.png)

*Figura 31. Puntuación F1 y AUC-ROC por conjunto de variables en el estudio de ablación.*

![Estabilidad temporal](outputs/fig_temporal_stability.png)
*Figura 32. Puntuación F1 por año en el período de validación.*

![Sensibilidad al umbral de decisión](outputs/fig_threshold_sensitivity.png)
*Figura 33. F1, precisión y exhaustividad en función del umbral de decisión del clasificador.*

![Robustez al percentil del objetivo](outputs/fig_robustness_percentile.png)
*Figura 34. Rendimiento del modelo con distintos percentiles de definición de la variable objetivo (P70 a P90).*

![Importancia por permutación](outputs/fig_permutation_importance.png)
*Figura 35. Importancia por permutación: descenso en la puntuación F1 cuando se aleatoriza cada variable por separado.*

![Curvas de dependencia parcial](outputs/fig_pdp.png)
*Figura 36. Curvas de dependencia parcial para las variables más importantes. Muestran la relación marginal entre cada variable y la probabilidad predicha.*

![Análisis por régimen de mercado](outputs/fig_regime_analysis.png)
*Figura 37. Rendimiento del modelo segmentado por régimen: alta volatilidad frente a baja volatilidad.*

![Análisis de errores](outputs/fig_error_analysis.png)
*Figura 38. Perfil de los errores del modelo: falsos positivos y falsos negativos.*

![Calibración de probabilidades](outputs/fig_calibration.png)
*Figura 39. Diagrama de calibración: compara probabilidades predichas con frecuencias observadas.*

![Robustez al horizonte temporal](outputs/fig_robustness_horizon.png)
*Figura 40. Rendimiento del modelo a horizontes de 1, 2 y 3 días. La señal es útil solo a 1 día.*

---

## 11. Aplicación Práctica para el Inversor en Crudo

### Información disponible hoy

**1. Probabilidad de tensión para el día siguiente**

El modelo asigna cada día hábil una probabilidad de que el siguiente sea un día de alta tensión. Con AUC de 0,615, ordena correctamente los días por nivel de riesgo más del 61% de las veces. Puede usarse como indicador de alerta temprana para ajustar posiciones de cobertura antes de que el mercado reaccione.

**2. Convergencia de señales como patrón más fiable**

Cuando el modelo detecta simultáneamente: actividad noticiosa GDELT elevada en el Golfo Pérsico o Rusia, GPR por encima del percentil 75 histórico y VIX en zona de estrés (>25), la probabilidad de día de alta tensión se eleva significativamente. En el análisis exploratorio, los días que cumplen las tres condiciones simultáneamente son de alta tensión en más del 60% de los casos.

**3. Identificación del origen del riesgo**

La descomposición mediante valores SHAP permite distinguir si el riesgo anticipado proviene de tensión geopolítica (variables GDELT/GPR dominantes) o de inercia del mercado (OVX/volatilidad rodante dominantes). Los shocks geopolíticos tienden a revertir en 10–15 días; los de inercia de volatilidad pueden persistir más.

### Limitaciones críticas para el inversor

1. **El modelo no predice la dirección del precio**, solo la probabilidad de movimiento brusco.
2. **La señal GDELT pierde utilidad en crisis no geopolíticas** (pandemias, crisis financieras sistémicas).
3. **Los costes de transacción no están considerados**.
4. **El rendimiento futuro no está garantizado** ante cambios estructurales (transición energética, nuevas dinámicas OPEP+).

### Extensiones futuras

Con datos en tiempo real y modelos más sofisticados sería posible:
- Reducir el horizonte de predicción de 1 día a pocas horas
- Incorporar sentimiento de plataformas financieras especializadas
- Distinguir entre impacto en precio *spot* y en curva de futuros
- Cuantificar la prima de riesgo geopolítico por vencimiento de futuros WTI
- Añadir posiciones especulativas del CFTC como indicador de sentimiento institucional

---

## 12. Conclusiones Elaboradas

**La señal geopolítica existe pero es débil.** El modelo alcanza F1 = 0,571 y AUC = 0,615, superando al azar y al modelo lineal. Sin embargo, la diferencia entre el modelo con todas las variables y el modelo con solo variables de mercado es pequeña, lo que confirma que la señal geopolítica es marginal, no dominante.

**La memoria del mercado es el predictor más potente.** Las variables más importantes según SHAP son las que capturan la inercia a corto plazo del propio mercado: retorno absoluto del día anterior, nivel del OVX y volatilidad rodante. Esto es coherente con el agrupamiento de volatilidad documentado en la literatura desde Engle (1982).

**La heterogeneidad entre eventos limita la generalización.** El estudio de eventos muestra reacciones muy dispares ante shocks aparentemente similares, dependiendo de si el mercado lo anticipaba, de la magnitud real de la interrupción y del contexto macroeconómico global.

**El horizonte predictivo óptimo es estrictamente de un día.** El rendimiento cae significativamente a 2 y 3 días de anticipación. No existe señal útil más allá del siguiente día hábil.

**El GDELT es un proxy de percepción mediática, no de realidad geopolítica.** La paradoja de 2020 ilustra este límite con claridad: el mayor shock de la década fue prácticamente invisible en el GDELT filtrado por zonas petroleras porque fue un evento sanitario, no un conflicto político entre estados.

---

## 13. Limitaciones y Sesgos Explícitos

- **Sesgo de cobertura temporal en el GDELT:** la caída del 70% en el volumen post-2019 limita la señal en el período de validación.
- **Muestra de eventos reducida:** con 35 eventos, el estudio de eventos carece de potencia estadística para generalizaciones robustas.
- **Ausencia de variables fundamentales de oferta y demanda:** sin inventarios de crudo (EIA), producción por país ni capacidad de refino.
- **Análisis correlacional, no causal:** los resultados muestran asociación estadística pero no prueban causalidad.
- **Cambios estructurales no modelados:** la revolución del *fracking*, la descarbonización y la nueva dinámica OPEP+ introducen no estacionariedad.
- **Crisis no geopolíticas no capturadas:** pandemias, crisis financieras sistémicas.

---

## 14. Transparencia Técnica y Reproducibilidad

### Archivos de datos

| Archivo | Período | Registros | Fuente | Acceso |
|---|---|---|---|---|
| `Datasets/WTI_USA.csv` | 1986–2026 | ~10.100 | FRED (DCOILWTICO) | Público |
| `Datasets/WTI_EUROPA.csv` | 1987–2026 | ~9.900 | FRED (DCOILBRENTEU) | Público |
| `Datasets/OVX.csv` | 2007–2026 | ~4.700 | CBOE/Yahoo Finance | Público |
| `Datasets/VIX_History.csv` | 1990–2026 | ~9.000 | CBOE | Público |
| `Datasets/DXY.csv` | 2010–2026 | ~4.000 | Yahoo Finance | Público |
| `Datasets/data_gpr_daily_recent.csv` | 1985–2026 | ~11.400 | Caldara & Iacoviello | Público |
| `Datasets/GDELT.csv` | 2015–2026 | ~60.000 | GDELT Project | Público |
| `Datasets/geopolitical_events_timeline.csv` | 2010–2026 | 35 | Elaboración propia | — |

### Outputs generados

| Archivo | Descripción |
|---|---|
| `outputs/ml_dataset.parquet` | Dataset maestro ML (4.059 × 37) |
| `outputs/historical_dataset.parquet` | Dataset histórico largo (1986–2026) |
| `outputs/train_engineered.parquet` | Conjunto de entrenamiento con 67 variables |
| `outputs/test_engineered.parquet` | Conjunto de validación con 67 variables |
| `outputs/feature_list.csv` | Lista de las 67 variables con grupo |
| `outputs/target_thresholds.csv` | Umbrales P80 para la variable objetivo |
| `outputs/results_clf_07.csv` | Métricas de clasificación en validación |
| `outputs/results_reg_08.csv` | Métricas de regresión en validación |
| `outputs/informe_geopolitica_crudo.pdf` | Informe completo en PDF con todas las figuras |

### Orden de ejecución

```
python build_01_data_cleaning.py        → 01_data_cleaning.ipynb
python build_02_master_dataset.py       → 02_master_dataset.ipynb
python build_03_eda.py                  → 03_eda.ipynb
python build_04_fe.py                   → 04_feature_engineering.ipynb
python build_05_event_study.py          → 05_event_study.ipynb
python build_06_baseline.py             → 06_baseline.ipynb
python build_07_classification.py       → 07_classification.ipynb
python build_08_regression.py           → 08_regression.ipynb
python build_09_interpretability.py     → 09_interpretability_robustness.ipynb
python merge_notebooks.py               → geopolitica_crudo_completo.ipynb
python build_informe_pdf.py             → outputs/informe_geopolitica_crudo.pdf
```

---

## 15. Referencias Bibliográficas

- **Caldara, D. & Iacoviello, M. (2022).** Measuring Geopolitical Risk. *American Economic Review*, 112(4), 1194–1225.
- **Leetaru, K. & Schrodt, P. (2013).** GDELT: Global Data on Events, Language, and Tone, 1979–2012. *ISA Annual Convention*.
- **MacKinlay, A. C. (1997).** Event Studies in Economics and Finance. *Journal of Economic Literature*, 35(1), 13–39.
- **Schrodt, P. (2012).** CAMEO: Conflict and Mediation Event Observations Codebook. Pennsylvania State University.
- **Goldstein, J. (1992).** A Conflict-Cooperation Scale for WEIS Events Data. *Journal of Conflict Resolution*, 36(2), 369–385.
- **Fama, E. F. (1970).** Efficient Capital Markets: A Review of Theory and Empirical Work. *Journal of Finance*, 25(2), 383–417.
- **Hamilton, J. D. (2009).** Understanding Crude Oil Prices. *The Energy Journal*, 30(2), 179–206.
- **Kilian, L. (2009).** Not All Oil Price Shocks Are Alike. *American Economic Review*, 99(3), 1053–1069.
- **Engle, R. F. (1982).** Autoregressive Conditional Heteroscedasticity with Estimates of the Variance of United Kingdom Inflation. *Econometrica*, 50(4), 987–1007.

---

## 16. Glosario Técnico

| Término | Definición |
|---|---|
| **AUC-ROC** | Área bajo la curva ROC. Mide la capacidad discriminativa del clasificador. Valor 1,0 = perfecto; 0,5 = azar. |
| **CAMEO** | Taxonomía estandarizada de eventos políticos internacionales en ~300 categorías (Schrodt, 2012). |
| **Escala Goldstein** | Puntuación de −10 a +10 que mide el impacto teórico esperado de un tipo de evento CAMEO sobre la estabilidad de un país. |
| **Estacionariedad** | Propiedad de una serie temporal cuya media y varianza no cambian con el tiempo. Los retornos logarítmicos son estacionarios; los precios nominales no. |
| **F1** | Media armónica de precisión y exhaustividad. Métrica adecuada para clasificación con clases desequilibradas. |
| **Filtración temporal de datos** | Uso inadvertido de información futura para entrenar un modelo predictivo. Produce métricas artificialmente optimistas. |
| **GDELT** | Global Database of Events, Language and Tone. Sistema de monitorización noticiosa global. |
| **GPR** | Geopolitical Risk Index (Caldara & Iacoviello, 2022). |
| **RAA** | Retorno Acumulado Anormal. Diferencia entre retorno observado y retorno esperado sin el evento, acumulada en la ventana temporal analizada. |
| **SHAP** | SHapley Additive exPlanations. Método de interpretabilidad basado en teoría de juegos que asigna a cada variable su contribución marginal a una predicción. |
| **Volatilidad implícita** | Volatilidad esperada por el mercado de opciones, derivada del precio de las opciones. Distinta de la volatilidad histórica, calculada sobre precios pasados. |
| **Colas gruesas** | Propiedad de una distribución con más probabilidad en los valores extremos de lo que predice la distribución normal. Los retornos financieros presentan esta característica de forma sistemática. |

---

*Proyecto desarrollado como portfolio de candidatura al Máster en Finanzas Cuantitativas de AFI Madrid (promoción 2026). Todas las fuentes de datos son de acceso público. Los resultados son reproducibles ejecutando los notebooks en el orden indicado.*
