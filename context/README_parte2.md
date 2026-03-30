# Geopolítica y Petróleo Crudo WTI — Simulación Estocástica Multibloque (Parte 2)

**Notebook:** `00_pipeline_completo.ipynb`

---

## Tabla de Contenidos

1. [Resumen / Abstract](#resumen--abstract)
2. [Introducción](#introducción)
3. [Contexto y justificación del trabajo](#contexto-y-justificación-del-trabajo)
4. [Objetivos](#objetivos)
5. [Datos y fuentes](#datos-y-fuentes)
6. [Metodología](#metodología)
7. [Desarrollo por bloques](#desarrollo-por-bloques)
   - [Bloque 1 — Detección de regímenes](#bloque-1--detección-de-regímenes)
   - [Bloque 2 — Calibración empírica](#bloque-2--calibración-empírica)
   - [Bloque 3 — Motor Monte Carlo (RSJD)](#bloque-3--motor-monte-carlo-rsjd)
   - [Bloque 4 — Motor ABM](#bloque-4--motor-abm)
   - [Bloque 5 — Evaluación financiera](#bloque-5--evaluación-financiera)
8. [Resultados principales](#resultados-principales)
9. [Discusión e interpretación](#discusión-e-interpretación)
10. [Limitaciones](#limitaciones)
11. [Conclusiones](#conclusiones)
12. [Bibliografía](#bibliografía)

---

## Resumen / Abstract

Este repositorio contiene el pipeline computacional completo de la segunda parte de un proyecto de investigación orientado a modelar el precio del petróleo crudo WTI bajo condiciones de estrés geopolítico. El núcleo metodológico integra, en secuencia, cinco bloques: detección de regímenes de mercado mediante un indicador compuesto de estrés, calibración empírica de parámetros de salto a partir del índice GPR de Caldara e Iacoviello (2022), simulación estocástica por Monte Carlo con un modelo de reversión a la media con saltos dependientes del régimen (RSJD), un motor de modelado basado en agentes (ABM) que incorpora impacto de precio a la Kyle (1985), y, finalmente, evaluación financiera de cinco estrategias de inversión alternativas.

El análisis cubre 2.800 observaciones diarias comprendidas entre el 5 de enero de 2015 y el 13 de marzo de 2026. Los regímenes identificados exhiben propiedades estadísticas marcadamente distintas: el régimen de alto estrés presenta una curtosis en exceso de 15,67 frente a 1,76 del régimen de bajo estrés, lo que confirma la necesidad de tratar la dinámica de colas de forma heterogénea. La calibración identifica 37 episodios de choque geopolítico sobre el umbral P90 del GPR (213,69), distribuidos en 130 días de choque. Las simulaciones Monte Carlo reproducen con aceptable fidelidad la frecuencia de saltos (error relativo 6,9 %), aunque muestran divergencias significativas en asimetría y en la proporción de tiempo en régimen de alto estrés. El motor ABM añade una capa microestructural que amplifica los drawdowns máximos respecto al Monte Carlo puro, especialmente en el escenario de baja geopolítica (diferencia de 13,7 puntos porcentuales). La evaluación financiera revela que el Especulador Técnico domina en Sharpe (+0,743) en el escenario base, mientras que el Fondo Geopolítico ofrece protección asimétrica de cola en el escenario de alta geopolítica, con una reducción del drawdown máximo del 72 % frente al inversor pasivo en el escenario base.

**Palabras clave:** petróleo crudo WTI, riesgo geopolítico, regímenes de volatilidad, proceso de difusión con saltos, Monte Carlo, modelado basado en agentes, gestión de riesgo.

---

## Introducción

El precio del petróleo crudo ocupa un lugar singular en la intersección entre los mercados financieros y la geopolítica global. A diferencia de la mayoría de activos financieros, cuya dinámica puede aproximarse razonablemente mediante modelos de movimiento browniano geométrico, el crudo experimenta discontinuidades abruptas generadas por eventos discretos —invasiones militares, sanciones internacionales, decisiones de producción de cárteles— que no son adecuadamente capturados por modelos de volatilidad continua. La literatura académica sobre eficiencia de mercados (Fama, 1970) y sobre procesos de régimen cambiante (Hamilton, 1989) ofrece los fundamentos teóricos para reconocer que los mercados de commodities energéticas pueden operar en estados cualitativamente distintos, con implicaciones directas sobre la distribución de retornos y sobre la óptima estrategia de cobertura.

El período 2021–2026 concentra una densidad inusual de eventos geopolíticos de primer orden: la invasión rusa de Ucrania en febrero de 2022, la escalada de tensiones en Oriente Medio a lo largo de 2025, y un episodio de alta intensidad aún en curso a la fecha de cierre de los datos (febrero–marzo de 2026). Este contexto hace especialmente pertinente la pregunta de investigación central: ¿en qué medida los modelos estocásticos calibrados sobre datos históricos de tensión geopolítica pueden reproducir y anticipar las propiedades estadísticas del mercado del crudo durante episodios de estrés extremo?

Este trabajo no pretende construir un modelo predictivo en sentido operacional, sino un laboratorio de simulación que permita explorar las consecuencias estadísticas y financieras de distintos supuestos sobre la intensidad geopolítica futura. La arquitectura en cinco bloques garantiza que cada componente —detección de regímenes, calibración de parámetros, generación de escenarios, microestructura de mercado y evaluación de estrategias— pueda examinarse de forma modular y replicarse de manera independiente.

---

## Contexto y justificación del trabajo

La relación entre geopolítica y precios del crudo ha sido objeto de estudio sistemático desde al menos los trabajos pioneros sobre los choques del petróleo de la OPEP en los años setenta. Sin embargo, la disponibilidad de índices cuantitativos de riesgo geopolítico de alta frecuencia es relativamente reciente. El GPR de Caldara e Iacoviello (2022) constituye una herramienta de primer orden en este sentido: construido mediante análisis de texto de grandes corpus de artículos de prensa, ofrece una medida diaria de la intensidad del riesgo geopolítico global con cobertura desde 1900, lo que lo convierte en el insumo de calibración más robusto disponible actualmente para este tipo de modelos.

Por otro lado, la modelización del impacto de precio en mercados con fricción ha avanzado considerablemente desde el marco seminal de Kyle (1985), quien formalizó la relación entre el flujo neto de órdenes y el ajuste de precio por parte de los creadores de mercado. La discretización de este mecanismo en un entorno de agentes heterogéneos permite capturar efectos de segunda vuelta que los modelos de ecuaciones diferenciales estocásticas estándar ignoran por construcción: la retroalimentación entre las posiciones de actores estratégicos (productores, especuladores, fondos geopolíticos) y la dinámica de precios resultante.

La justificación metodológica de integrar Monte Carlo y ABM en un mismo pipeline reside en la complementariedad de ambos enfoques. El Monte Carlo, bajo el modelo RSJD, genera distribuciones de precios estadísticamente bien fundamentadas con un número elevado de trayectorias. El ABM, con un número menor de trayectorias pero una riqueza microestructural mayor, permite explorar cómo la heterogeneidad de agentes y la endogeneidad del impacto de precio modifican cuantitativamente los resultados del modelo de reducida forma. La discrepancia entre ambos motores es, en sí misma, informativamente relevante: señala las partes de la distribución de retornos donde la microestructura importa.

---

## Objetivos

El trabajo persigue los siguientes objetivos, ordenados de lo general a lo específico:

Primero, construir un sistema de detección de regímenes de mercado para el crudo WTI que sea robusto, interpretable y calibrado sobre datos fuera de muestra a partir de 2021. Segundo, estimar empíricamente los parámetros de salto (intensidad, media y desviación del tamaño) asociados a episodios de estrés geopolítico extremo, definidos mediante el umbral P90 del índice GPR. Tercero, implementar un motor de simulación Monte Carlo basado en el modelo RSJD que reproduzca con fidelidad estadística documentada las propiedades clave de los retornos del crudo, reconociendo explícitamente las discrepancias cuando estas superen umbrales de tolerancia. Cuarto, construir un motor ABM con cuatro tipos de agentes heterogéneos e impacto de precio endógeno, y comparar sus propiedades distributivas con las del Monte Carlo. Quinto, evaluar financieramente cinco estrategias de inversión bajo múltiples escenarios geopolíticos, contrastando cuatro hipótesis específicas sobre el valor diferencial de la información geopolítica.

---

## Datos y fuentes

El conjunto de datos cubre 2.800 observaciones diarias desde el 5 de enero de 2015 hasta el 13 de marzo de 2026. Las variables incluidas son: el precio spot del crudo WTI y del Brent como referencia de mercado, el índice OVX (CBOE Crude Oil Volatility Index) como medida de volatilidad implícita del crudo, el VIX como indicador de sentimiento de riesgo global, el índice DXY del dólar estadounidense como proxy de condiciones monetarias globales, el índice GPR de Caldara e Iacoviello (2022) como medida cuantitativa del riesgo geopolítico, y el recuento de eventos geopolíticos procedente de la base GDELT como complemento de alta frecuencia al GPR.

El período de calibración operacional, sobre el que se estiman los umbrales de choque y los parámetros de salto, comprende desde el 1 de enero de 2021 hasta el 13 de marzo de 2026. Esta decisión metodológica responde a la necesidad de circunscribir la calibración al entorno de mercado más reciente, caracterizado por una mayor frecuencia e intensidad de eventos geopolíticos que el período anterior. Los parámetros de detección de regímenes (umbrales de los cuantiles P33 y P66 del indicador de estrés compuesto) se estiman sobre el período de entrenamiento 2015–2020 y se aplican fuera de muestra sobre el período operacional.

---

## Metodología

La arquitectura metodológica del pipeline se organiza en cinco bloques secuencialmente dependientes. Los parámetros estimados en cada bloque alimentan el siguiente, lo que impone una disciplina de coherencia interna: ningún bloque puede modificar sus supuestos sin propagar las consecuencias hacia aguas abajo.

El indicador de estrés compuesto que gobierna la clasificación de regímenes combina con pesos fijos la volatilidad realizada a 30 días (peso 60 %) y el índice OVX (peso 40 %):

$$\text{Stress}_t = 0.6 \cdot \sigma^{\text{real}}_{t,30d} + 0.4 \cdot \text{OVX}_t$$

La elección de ponderaciones refleja el mayor contenido informacional de la volatilidad realizada respecto a la volatilidad implícita en horizontes cortos, sin que esta diferencia sea suficientemente pronunciada como para descartar el OVX como señal complementaria.

La dinámica de precios en el bloque Monte Carlo sigue el modelo de reversión a la media con saltos dependientes del régimen (RSJD), que puede escribirse en log-precio como:

$$x_{t+1} = x_t + \mu(s_t) + \kappa(s_t)\bigl(m_0 - x_t\bigr) + \sigma(s_t)\,\varepsilon_t + I_t \cdot Y_t$$

donde $x_t = \log(P_t)$, $s_t \in \{0, 1, 2\}$ indexa el régimen de Markov, $\kappa(s_t)$ es la velocidad de reversión a la media con ancla $m_0 = 4{,}1722$ (equivalente a \$64,86/bbl), $\varepsilon_t \sim \mathcal{N}(0,1)$, $I_t \sim \text{Bernoulli}(\lambda(s_t))$ es el indicador de salto, e $Y_t \sim \mathcal{N}(\mu_J, \sigma_J^2)$ es el tamaño del salto. La cadena de Markov $\{s_t\}$ evoluciona de acuerdo con la matriz de transición estimada empíricamente.

El impacto de precio en el motor ABM sigue la discretización del modelo de Kyle (1985):

$$r_{\text{adj},t} = r_{\text{base},t} + \frac{\lambda}{L_t} \cdot \text{NetFlow}_t$$

donde $\lambda = 0{,}003$ es el coeficiente de impacto de precio, $L_t = \max\!\bigl(0{,}3,\, 1 - 6\sigma_{\text{recent}}\bigr)$ captura el efecto de espiral de liquidez descrito por Brunnermeier y Pedersen (2009), y $\text{NetFlow}_t = \sum_i \text{signal}_{i,t}$ agrega las señales de todos los agentes activos.

La evaluación financiera emplea las métricas estándar de la industria, formalizadas por Sharpe (1966) y Sortino y van der Meer (1991), junto con medidas de riesgo de cola basadas en el CVaR según Rockafellar y Uryasev (2000). La tasa libre de riesgo se fija en un 5 % anual (0,0198 % diario), y el coste de transacción uniforme es de 10 puntos básicos por operación.

---

## Desarrollo por bloques

### Bloque 1 — Detección de regímenes

#### Diseño del indicador de estrés

El primer bloque establece la taxonomía de regímenes sobre la que descansa todo el pipeline. El indicador de estrés compuesto, definido como combinación lineal de la volatilidad realizada a 30 días y el OVX, se discretiza en tres regímenes mediante los cuantiles P33 y P66 estimados sobre el período de entrenamiento 2015–2020. Esta decisión de usar umbrales fijos estimados fuera de muestra —en lugar de re-estimarlos sobre el período completo— es la única forma de garantizar que los regímenes del período 2021–2026 reflejen genuinamente el estado del mercado y no incorporen información futura de forma inadvertida.

Los regímenes resultantes exhiben diferencias sustantivas en sus distribuciones de retorno diario, resumidas en la tabla siguiente.

| Régimen | Días | $\mu_{\text{diario}}$ | $\sigma_{\text{diario}}$ | Asimetría | Curtosis exceso |
|---|---|---|---|---|---|
| `low_stress` | 802 | +0,000169 | 0,01525 | −0,60 | 1,76 |
| `medium_stress` | 1.073 | −0,000241 | 0,02103 | −0,36 | 0,63 |
| `high_stress` | 864 | +0,000037 | 0,04160 | +0,07 | 15,67 |

La figura `fig_regime_overview.png` ofrece la visión longitudinal del indicador de estrés junto con la clasificación de regímenes a lo largo de toda la historia. La figura `fig_regime_return_distributions.png` muestra las distribuciones de retorno por régimen, haciendo visible la diferencia de escala entre las colas del régimen de alto estrés y los demás. La figura `fig_regime_durations.png` ilustra la distribución de duraciones de cada régimen.

![Visión general de regímenes de mercado](outputs/figures/fig_regime_overview.png)

![Distribuciones de retorno por régimen](outputs/figures/fig_regime_return_distributions.png)

![Distribución de duraciones de régimen](outputs/figures/fig_regime_durations.png)

La tabla de retornos merece un análisis cuidadoso. La media de retorno diario es prácticamente nula en los tres regímenes, lo que es coherente con la hipótesis de eficiencia de mercado en su forma débil (Fama, 1970). La diferencia más informativa es la volatilidad: el régimen de alto estrés presenta una $\sigma$ de 4,16 %, que es 2,7 veces la del régimen de bajo estrés (1,53 %). Más significativa aún es la curtosis en exceso del régimen de alto estrés (15,67), que indica una distribución con colas radicalmente más pesadas que la normal y que supera en un orden de magnitud la del régimen de bajo estrés (1,76). La asimetría positiva del régimen de alto estrés (+0,07), frente a las asimetrías negativas de los otros dos regímenes, sugiere que en períodos de máxima tensión los rebotes alcistas extremos son tan frecuentes como las caídas extremas, lo cual es coherente con la dinámica de reversiones rápidas tras colapsos de precio observada empíricamente.

#### Cadena de Markov y probabilidades de transición

La matriz de transición de primer orden, estimada por máxima verosimilitud sobre la secuencia completa de regímenes observados, es:

$$P = \begin{pmatrix} 0{,}9813 & 0{,}0175 & 0{,}0012 \\ 0{,}0130 & 0{,}9692 & 0{,}0177 \\ 0{,}0012 & 0{,}0220 & 0{,}9768 \end{pmatrix}$$

donde las filas corresponden al régimen en $t$ y las columnas al régimen en $t+1$, con orden $\{\text{low}, \text{medium}, \text{high}\}$.

Las probabilidades de permanencia —$p_{\text{stay}} = 0{,}981$ para bajo estrés, $0{,}969$ para estrés medio, $0{,}977$ para alto estrés— indican que los tres regímenes son altamente persistentes. La duración media implícita es de $1/(1 - p_{\text{stay}})$ días: aproximadamente 53 días para bajo estrés, 32 días para estrés medio y 44 días para alto estrés. La asimetría de las transiciones fuera de la diagonal también es relevante: las transiciones directas entre los regímenes extremos (low → high y high → low) tienen probabilidad estimada de apenas 0,12 % y 0,12 % respectivamente, lo que sugiere que los cambios de régimen se producen predominantemente de manera gradual, pasando por el estado intermedio. Este resultado tiene implicaciones directas para la velocidad de respuesta de las estrategias de cobertura geopolítica.

---

### Bloque 2 — Calibración empírica

#### Identificación de episodios de choque

El umbral de choque geopolítico se define como el percentil 90 del índice GPR sobre el período operacional 2021–2026, que toma el valor 213,69. Por encima de este umbral se identifican 37 episodios discretos que suman 130 días de choque. La elección del P90 como umbral responde a un criterio de parsimonia: un umbral más bajo capturaría tensión geopolítica de baja intensidad que no necesariamente genera discontinuidades de precio; uno más alto reduciría la muestra de calibración a un número de eventos insuficiente para la estimación estadística de los parámetros de salto.

Los cinco episodios de mayor intensidad media de GPR se presentan en la tabla siguiente.

| Rango | Período | GPR medio | Retorno acumulado |
|---|---|---|---|
| 1 | 2026-02-24 → 2026-03-13 | 348,2 | +39,5 % |
| 2 | 2022-02-15 → 2022-03-31 | 334,5 | +5,1 % (invasión Rusia-Ucrania) |
| 3 | 2025-06-16 → 2025-06-27 | 317,6 | −10,2 % |
| 4 | 2025-10-03 | 292,3 | +0,6 % |
| 5 | 2022-01-25 → 2022-01-27 | 272,3 | +3,6 % |

La figura `fig_calib_shock_episodes.png` visualiza la distribución temporal de estos episodios sobre la serie del GPR. La figura `fig_calib_return_distributions.png` compara las distribuciones de retorno dentro y fuera de los días de choque. La figura `fig_calib_jump_distribution.png` muestra la distribución empírica de los tamaños de salto y su ajuste normal. La figura `fig_calib_decay_profile.png` examina el perfil de decaimiento de los retornos en los 30 días posteriores a cada choque. La figura `fig_calib_cross_asset_regimes.png` presenta las correlaciones cruzadas entre retorno del WTI y los activos financieros auxiliares, desagregadas por régimen.

![Episodios de choque geopolítico sobre la serie GPR](outputs/figures/fig_calib_shock_episodes.png)

![Distribuciones de retorno: días de choque vs. días normales](outputs/figures/fig_calib_return_distributions.png)

![Distribución empírica de tamaños de salto y ajuste normal](outputs/figures/fig_calib_jump_distribution.png)

![Perfil de decaimiento post-choque (30 días)](outputs/figures/fig_calib_decay_profile.png)

![Correlaciones cruzadas WTI vs. activos auxiliares por régimen](outputs/figures/fig_calib_cross_asset_regimes.png)

Lo más llamativo de la tabla de episodios es la heterogeneidad de las respuestas de precio. El episodio de mayor intensidad (GPR = 348,2, aún en curso en la fecha de corte de los datos) muestra un retorno acumulado de +39,5 %, mientras que el tercer episodio por intensidad (GPR = 317,6) genera un retorno de −10,2 %. El episodio de la invasión rusa de Ucrania, con GPR = 334,5, produce un retorno de tan solo +5,1 % a pesar de ser uno de los choques geopolíticos más severos del período. Esta heterogeneidad sugiere que el nivel del GPR no es un predictor suficiente de la dirección del movimiento de precio, lo que tiene consecuencias directas sobre el diseño de estrategias geopolíticas: la señal de choque identifica episodios de alta volatilidad, pero no necesariamente de dirección definida.

#### Parámetros de salto y correlaciones cruzadas

Los parámetros de salto estimados sobre los días de choque (GPR > P90) son:

$$\mu_J = 0{,}00580 \quad \text{(retorno diario medio en días de choque)}$$
$$\sigma_J = 0{,}03692 \quad \text{(desviación estándar del tamaño del salto)}$$

La intensidad de salto varía significativamente con el régimen: $\lambda_{\text{low}} = 0{,}0641$, $\lambda_{\text{medium}} = 0{,}0765$, $\lambda_{\text{high}} = 0{,}1667$. Esta escalada —en la que el régimen de alto estrés tiene una frecuencia de salto 2,6 veces superior al de bajo estrés— captura la concentración empírica de los choques geopolíticos en períodos de mercado ya perturbado. Es un resultado de retroalimentación positiva: el estrés de mercado eleva la sensibilidad del precio a los choques externos, y los choques externos contribuyen a mantener el mercado en régimen de alto estrés.

El análisis de decaimiento no detecta un perfil exponencial estadísticamente significativo en la ventana de 30 días posterior a los choques. Esta ausencia de decaimiento exponencial distingue al mercado del crudo de los modelos de choque-respuesta habituales en la literatura macroeconómica, y justifica la decisión de modelar la persistencia mediante la cadena de Markov (con $p_{\text{stay}} = 0{,}977$ para el régimen de alto estrés) en lugar de mediante una tasa de decaimiento paramétrica explícita.

Las correlaciones cruzadas por régimen revelan un patrón interesante. En el régimen de bajo estrés, el retorno del WTI presenta correlaciones negativas con OVX (−0,161) y VIX (−0,196), lo que es consistente con el efecto habitual de apetito por el riesgo: cuando la volatilidad baja, el precio del crudo tiende a subir. Sin embargo, en el régimen de alto estrés, la correlación con el OVX se vuelve positiva (+0,114), indicando que en períodos de máxima tensión el mercado experimenta simultaneamente subidas de precio y de volatilidad implícita. La correlación con el DXY es negativa en los tres regímenes (−0,040, −0,072, −0,079), aunque de magnitud modesta, lo que sugiere un efecto dólar presente pero no dominante en el período operacional.

---

### Bloque 3 — Motor Monte Carlo (RSJD)

#### Especificación del modelo y condiciones iniciales

El modelo RSJD implementado en el bloque 3 combina reversión a la media con velocidades dependientes del régimen ($\kappa = 0{,}006$ en bajo estrés, $0{,}004$ en estrés medio, $0{,}002$ en alto estrés), una distribución de retornos de difusión dependiente del régimen, y un proceso de salto de Poisson compuesto cuya intensidad varía con el estado de la cadena de Markov. El ancla de reversión $m_0 = 4{,}1722$ corresponde a un precio de \$64,86 por barril, estimado mediante una media ponderada exponencialmente con horizonte de 180 días congelada en el inicio de la simulación. Las condiciones iniciales son $x_0 = 4{,}5899$ (equivalente a $P_0 = 98{,}48$ USD/bbl) con régimen inicial $s_0 =$ `high_stress` en el escenario base.

Se generan 2.000 trayectorias con horizonte $T = 252$ días bajo tres escenarios: escenario `low_geo` con régimen inicial de bajo estrés y parámetros de salto atenuados ($\lambda \times 0{,}4$, $\mu_J$ y $\sigma_J$ reducidos a la mitad); escenario `base` con parámetros calibrados y régimen inicial de alto estrés; y escenario `high_geo` con intensidades de salto amplificadas ($\lambda_{\text{medium}} \times 1{,}5$, $\lambda_{\text{high}} \times 2{,}5$, $\sigma_J \times 1{,}5$) y una probabilidad de permanencia en alto estrés incrementada en $P_{hh} \times 1{,}03$.

Las figuras `fig_mc_fan_chart.png`, `fig_mc_anchor.png` y `fig_mc_regime_evolution.png` muestran respectivamente la nube de trayectorias simuladas con bandas de confianza, la dinámica de la función de ancla a lo largo de las simulaciones, y la evolución de la distribución de regímenes a lo largo del horizonte de simulación. Las figuras `fig_mc_return_comparison.png`, `fig_mc_jump_frequency.png`, `fig_mc_final_price_dist.png` y `fig_mc_drawdowns.png` comparan las propiedades de los retornos simulados con los históricos, muestran la frecuencia de saltos por trayectoria, presentan la distribución de precios finales y la distribución de drawdowns máximos, respectivamente.

![Fan chart de trayectorias Monte Carlo con bandas de confianza](outputs/figures/fig_mc_fan_chart.png)

![Dinámica del ancla de reversión a lo largo de las simulaciones](outputs/figures/fig_mc_anchor.png)

![Evolución de la distribución de regímenes en el horizonte simulado](outputs/figures/fig_mc_regime_evolution.png)

![Comparación de retornos simulados vs. históricos](outputs/figures/fig_mc_return_comparison.png)

![Frecuencia de saltos por trayectoria](outputs/figures/fig_mc_jump_frequency.png)

![Distribución de precios finales por escenario](outputs/figures/fig_mc_final_price_dist.png)

![Distribución de drawdowns máximos por escenario](outputs/figures/fig_mc_drawdowns.png)

#### Resultados de validación

Los resultados de validación del escenario base, evaluados como error relativo entre la mediana simulada y el valor histórico de referencia, se presentan en la tabla siguiente.

| Estadístico | Error relativo | Diagnóstico |
|---|---|---|
| Volatilidad anualizada | 0,187 | WARN |
| Curtosis en exceso | 0,541 | PASS |
| Asimetría | 1,369 | WARN |
| Drawdown máximo | 0,381 | WARN |
| % tiempo en high_stress | 0,295 | FAIL |
| Frecuencia de saltos | 0,069 | PASS |

El modelo supera la validación en dos dimensiones: la curtosis en exceso (error del 54,1 %, dentro de dos desviaciones típicas del benchmark de comparación) y la frecuencia de saltos (error del 6,9 %, el resultado más satisfactorio del conjunto). Sin embargo, presenta discrepancias notables en otras dimensiones. El estadístico que presenta mayor discrepancia es la asimetría (error del 136,9 %): el modelo genera distribuciones con asimetría positiva mientras que los retornos históricos muestran asimetría negativa. Esta inversión de signo —y no solo de magnitud— en la asimetría simulada es el fallo estructural más relevante del modelo en su configuración actual. La proporción de tiempo en régimen de alto estrés también supera el umbral de aceptación (error del 29,5 %, clasificado como FAIL), lo que sugiere que la cadena de Markov estimada sobre el período completo 2015–2026 sobreestima la persistencia del alto estrés respecto al período de calibración operacional.

---

### Bloque 4 — Motor ABM

#### Arquitectura de agentes

El motor ABM implementa cuatro tipos de agentes heterogéneos, cada uno con una función de señal específica que traduce el estado del mercado en un flujo de órdenes neto. Los agentes operan simultáneamente y su agregación determina el ajuste de precio vía la fórmula de Kyle discretizada.

El Productor OPEC+ genera una señal de reversión a la media proporcional al desvío del log-precio respecto al ancla: $\text{signal} = \kappa_{\text{opec}} \cdot \tanh\bigl(5 \cdot (m_0 - x_t)\bigr)$, con una intensidad amplificada en un 40 % en el régimen de alto estrés. Este agente representa la función estabilizadora de la oferta gestionada por el cártel. El Especulador Técnico opera sobre el momentum a 10 días: $\text{signal} = \tanh(\gamma \cdot \text{momentum}_{10d}) \times \text{stress\_scale} \times \text{vol\_scale}$, donde la escala de estrés se reduce a 0,4 en el régimen de alto estrés, reflejando la tendencia de los operadores técnicos a reducir posicionamiento ante incertidumbre extrema. El Creador de Mercado mantiene un inventario y opera de forma contraria al flujo neto, con liquidez endógena $L_t = \max(0{,}3, 1 - \beta_L \cdot \sigma_{\text{recent}})$ que se contrae cuando la volatilidad reciente es elevada, generando la espiral de liquidez de Brunnermeier y Pedersen (2009). El Fondo Geopolítico toma posiciones largas de tamaño 0,8 cuando se detectan simultáneamente un choque GPR y el régimen de alto estrés, mantiene la posición durante 15 días y ejecuta una salida gradual con factor de decaimiento 0,7 por día.

El pipeline exporta 200 de las 300 trayectorias generadas ($N_{\text{export}} = 200$) para la evaluación financiera del bloque siguiente.

Las figuras `fig_abm_fan_chart.png`, `fig_abm_agent_signals.png`, `fig_abm_flow_liquidity.png`, `fig_abm_agent_pnl.png`, `fig_abm_vol_dd_comparison.png` y `fig_abm_contrafactuals.png` documentan respectivamente las trayectorias simuladas por el ABM, la evolución de las señales individuales de cada agente, la dinámica del flujo neto y la liquidez de mercado, el PnL acumulado de cada agente por escenario, la comparación de volatilidad y drawdown entre ABM y Monte Carlo puro, y los resultados del análisis contrafactual.

![Fan chart de trayectorias ABM por escenario](outputs/figures/fig_abm_fan_chart.png)

![Evolución de señales individuales de cada agente](outputs/figures/fig_abm_agent_signals.png)

![Dinámica del flujo neto y la liquidez de mercado](outputs/figures/fig_abm_flow_liquidity.png)

![PnL acumulado por agente y escenario](outputs/figures/fig_abm_agent_pnl.png)

![Comparación de volatilidad y drawdown: ABM vs. Monte Carlo puro](outputs/figures/fig_abm_vol_dd_comparison.png)

![Resultados del análisis contrafactual por tipo de agente](outputs/figures/fig_abm_contrafactuals.png)

#### Resultados del ABM

Los resultados de PnL mediano por agente y escenario (en porcentaje, horizonte de 252 días) se recogen en la tabla siguiente.

| Escenario | OPEC+ | Técnico | Creador de Mercado | Fondo Geo |
|---|---|---|---|---|
| `low_geo` | +8,95 % | +32,85 % | +18,26 % | −0,44 % |
| `base` | +4,39 % | +23,87 % | +19,41 % | +3,76 % |
| `high_geo` | −9,85 % | +14,08 % | +22,33 % | +32,64 % |

La distribución de resultados es estructuralmente coherente con las características de cada agente. El Fondo Geopolítico muestra la mayor dispersión entre escenarios: desde −0,44 % en el escenario de baja geopolítica hasta +32,64 % en el de alta geopolítica. Esta sensibilidad al escenario confirma el carácter direccional de la estrategia geopolítica y es precisamente lo que la hace interesante como instrumento de cobertura asimétrica. El Creador de Mercado exhibe el comportamiento más estable (+18,26 % a +22,33 %), con un gradiente positivo respecto a la volatilidad del escenario: a mayor volatilidad, mayor captura del diferencial bid-ask. El OPEC+ presenta una inversión de signo entre escenarios: positivo en baja geopolítica (+8,95 %) pero negativo en alta geopolítica (−9,85 %), lo que refleja la incapacidad del agente de reversión a la media para generar alfa cuando el precio se aleja sostenidamente del ancla durante episodios de estrés prolongado.

La comparación ABM versus Monte Carlo base revela que el motor ABM genera drawdowns máximos sistemáticamente más severos que el Monte Carlo puro:

| Escenario | Vol ABM | Vol MC | MaxDD ABM | MaxDD MC |
|---|---|---|---|---|
| `base` | 0,4415 | 0,4398 | −58,96 % | −50,13 % |
| `high_geo` | 0,7117 | 0,7089 | −65,31 % | −63,51 % |
| `low_geo` | 0,3546 | 0,3528 | −58,84 % | −45,09 % |

En términos de volatilidad anualizada, las diferencias son pequeñas (del orden de 0,002 en términos absolutos). Sin embargo, en términos de drawdown máximo la discrepancia es considerable, especialmente en el escenario de baja geopolítica, donde el ABM produce un MaxDD de −58,84 % frente al −45,09 % del Monte Carlo puro, una diferencia de 13,75 puntos porcentuales. Este resultado sugiere que los mecanismos de retroalimentación microestructural —en particular la contracción de liquidez del Creador de Mercado y el efecto rebaño generado por las posiciones del Fondo Geopolítico— producen episodios de caída más pronunciados que los que emergen de una difusión estocástica calibrada sobre parámetros históricos.

#### Análisis contrafactual

El análisis contrafactual, ejecutado para el escenario base con extracción sucesiva de cada tipo de agente, permite aislar la contribución de cada uno sobre las propiedades del mercado.

| Configuración | Vol. anual | MaxDD | PnL Geo (mediano) |
|---|---|---|---|
| Todos los agentes | 0,4415 | −58,96 % | +3,76 % |
| Sin Especulador | 0,4410 | −50,23 % | +2,94 % |
| Sin Creador de Mercado | 0,4412 | −58,28 % | +2,89 % |
| Sin Fondo Geopolítico | 0,4408 | −69,66 % | 0,00 % |
| Monte Carlo puro | 0,4390 | −50,13 % | 0,00 % |

El hallazgo más sorprendente es que la eliminación del Fondo Geopolítico aumenta el drawdown máximo de −58,96 % a −69,66 %, lo que implica que la presencia del agente geopolítico ejerce un efecto moderador sobre las caídas extremas del mercado. Esto es coherente con la mecánica del agente: el Fondo Geopolítico toma posiciones largas durante los choques, lo que inyecta flujo comprador justo cuando el mercado más lo necesita, amortiguando las caídas. La eliminación del Especulador Técnico reduce el drawdown máximo hasta −50,23 %, aproximándose al Monte Carlo puro, lo que sugiere que es el especulador técnico —no el fondo geopolítico— el principal generador de los episodios de caída profunda a través del seguimiento de tendencia.

---

### Bloque 5 — Evaluación financiera

#### Métricas de rendimiento por escenario

El bloque 5 evalúa cinco estrategias sobre las 200 trayectorias exportadas por el ABM, con un coste de transacción uniforme del 0,1 % por operación y una tasa libre de riesgo del 5 % anual. Las estrategias son: el Fondo Geopolítico (señal de choque más régimen), el Especulador Técnico (momentum), el inversor Pasivo (buy and hold), el Predictor Perfecto (benchmark teórico de referencia superior) y la Señal Aleatoria (benchmark inferior de referencia).

Los resultados del escenario base se presentan en la tabla siguiente.

| Estrategia | Sharpe | Sortino | MaxDD | Calmar | VaR 95 % | CVaR 95 % | Hit Ratio | PnL total |
|---|---|---|---|---|---|---|---|---|
| Fondo Geo | −0,361 | −0,520 | −16,59 % | −0,047 | −1,31 % | −2,21 % | 40,5 % | −0,75 % |
| Técnico | +0,743 | +1,119 | −20,15 % | +1,186 | −2,45 % | −3,44 % | 51,2 % | +24,62 % |
| Pasivo | −0,331 | −0,487 | −59,58 % | −0,168 | −4,43 % | −5,90 % | 48,4 % | −9,94 % |
| Pred. Perfecto | +17,838 | +3.528,2 | −0,08 % | +6.434 | +0,12 % | +0,03 % | 98,4 % | +516,2 % |
| Aleatoria | −0,773 | −1,038 | −48,60 % | −0,443 | −3,74 % | −5,45 % | 32,1 % | −21,75 % |

Y los resultados del escenario `high_geo`:

| Estrategia | Sharpe | Sortino | MaxDD | Calmar | VaR 95 % | CVaR 95 % | Hit Ratio | PnL total |
|---|---|---|---|---|---|---|---|---|
| Fondo Geo | +0,299 | +0,478 | −30,99 % | +0,540 | −3,25 % | −5,27 % | 48,4 % | +16,65 % |
| Técnico | +0,324 | +0,450 | −27,79 % | +0,511 | −2,86 % | −4,15 % | 50,8 % | +14,25 % |
| Pasivo | +0,465 | +0,691 | −64,31 % | +0,546 | −6,54 % | −9,29 % | 50,4 % | +36,50 % |
| Pred. Perfecto | +16,900 | +6.473,9 | −0,08 % | +10.214 | +0,17 % | +0,05 % | 98,8 % | +816,0 % |
| Aleatoria | −0,488 | −0,672 | −67,83 % | −0,349 | −5,92 % | −8,74 % | 32,5 % | −21,29 % |

Las figuras `fig_fin_equity_curves.png`, `fig_fin_drawdown_curves.png`, `fig_fin_sharpe_sortino.png`, `fig_fin_pnl_by_regime.png`, `fig_fin_tail_distribution.png`, `fig_fin_error_cost.png` y `fig_fin_var_cvar.png` documentan respectivamente las curvas de equity acumuladas, los perfiles de drawdown, los ratios Sharpe y Sortino comparados, el PnL desagregado por régimen, la distribución de retornos en las colas, el coste de los errores de señal del Fondo Geopolítico, y las medidas VaR y CVaR por estrategia y escenario.

![Curvas de equity acumulada por estrategia y escenario](outputs/figures/fig_fin_equity_curves.png)

![Perfiles de drawdown por estrategia y escenario](outputs/figures/fig_fin_drawdown_curves.png)

![Ratios Sharpe y Sortino comparados por estrategia](outputs/figures/fig_fin_sharpe_sortino.png)

![PnL desagregado por régimen de mercado](outputs/figures/fig_fin_pnl_by_regime.png)

![Distribución de retornos en las colas por estrategia](outputs/figures/fig_fin_tail_distribution.png)

![Coste de errores de señal del Fondo Geopolítico (TP/FP/TN)](outputs/figures/fig_fin_error_cost.png)

![VaR y CVaR al 95 % por estrategia y escenario](outputs/figures/fig_fin_var_cvar.png)

#### PnL por régimen

La desagregación del PnL por régimen en el escenario base ofrece una perspectiva complementaria sobre el origen de las rentabilidades.

| Estrategia | Low stress | Medium stress | High stress |
|---|---|---|---|
| Fondo Geo | −0,745 % | −0,351 % | +1,203 % |
| Técnico | +5,638 % | +13,851 % | +0,870 % |
| Pasivo | −5,858 % | −2,760 % | +5,466 % |
| Pred. Perfecto | +56,675 % | +147,766 % | +282,222 % |
| Aleatoria | −0,828 % | −3,997 % | −8,916 % |

#### Análisis de errores de señal del Fondo Geopolítico

El análisis de señal del Fondo Geopolítico clasifica cada observación en verdadero positivo (TP: posición larga en día de choque), falso positivo (FP: posición larga en día sin choque), verdadero negativo (TN: sin posición en día sin choque), y falso negativo (FN: sin posición en día de choque). Dado que el agente responde sistemáticamente a cualquier señal que supere un umbral de posición de 0,3, la categoría FN es vacía en los tres escenarios, lo que es una propiedad estructural del diseño del agente, no un resultado empírico contingente.

| Escenario | Clase | Observaciones | Frecuencia | PnL medio/día |
|---|---|---|---|---|
| `low_geo` | TP | 1.909 | 3,79 % | +0,0207 % |
| `low_geo` | FP | 6.717 | 13,33 % | −0,0241 % |
| `low_geo` | TN | 41.774 | 82,88 % | 0,000 % |
| `base` | TP | 5.642 | 11,19 % | +0,157 % |
| `base` | FP | 11.322 | 22,46 % | −0,021 % |
| `base` | TN | 33.436 | 66,34 % | 0,000 % |
| `high_geo` | TP | 16.817 | 33,37 % | +0,284 % |
| `high_geo` | FP | 5.961 | 11,83 % | −0,030 % |
| `high_geo` | TN | 27.622 | 54,81 % | 0,000 % |

#### Contraste de hipótesis

Se contrastan cuatro hipótesis mediante la prueba de Mann-Whitney sobre las distribuciones de métricas a lo largo de las trayectorias simuladas.

**H1: El Fondo Geopolítico presenta mayor Sharpe que el inversor pasivo en el escenario `high_geo`.** Esta hipótesis no se confirma en términos de ratio de Sharpe: el Fondo obtiene 0,299 frente a 0,465 del inversor pasivo. Sin embargo, la comparación de drawdown máximo revela una protección asimétrica de considerable magnitud: el MaxDD del Fondo Geopolítico en el escenario base es de −16,59 % frente al −59,58 % del inversor pasivo, una reducción del 72 %. Esta disociación entre Sharpe y drawdown ilustra que el Fondo Geopolítico no es una estrategia de retorno ajustado por riesgo genérico, sino una estrategia de cobertura de cola.

**H2: La ventaja del Fondo Geopolítico se concentra en el régimen de alto estrés.** Esta hipótesis se confirma: el Fondo genera +1,203 % en high stress frente a −0,745 % en low stress (escenario base). La comparación con el inversor pasivo (+5,466 % vs −5,858 %) muestra que ambas estrategias son procíclicas respecto al régimen, pero la magnitud de la oscilación es radicalmente distinta, lo que indica que el Fondo no simplemente replica una exposición larga al crudo.

**H3 (reformulada): El coste de los falsos positivos es inferior al beneficio de los verdaderos positivos.** Dado que FN = 0 en todos los escenarios, la hipótesis original sobre el coste de los falsos negativos no es contrastable. La versión reformulada compara TP y FP: en el escenario base, la ratio TP/|FP| es de +0,157 %/+0,021 % = 7,6x, confirmando que cada día de verdadero positivo genera en expectativa 7,6 veces el coste de un día de falso positivo. Esta ratio cae a 0,86x en el escenario `low_geo` (+0,0207 % vs +0,0241 %), lo que explica el PnL negativo del Fondo en ese escenario.

**H4: El Fondo Geopolítico captura mejor los retornos extremos positivos que la señal aleatoria.** Esta hipótesis se confirma en los tres escenarios: el P95 de la distribución de retornos del Fondo supera al P95 de la distribución aleatoria, lo que indica que la señal geopolítica proporciona acceso selectivo a los episodios de retorno extremo positivo que la estrategia aleatoria no puede capturar sistemáticamente.

---

## Resultados principales

| # | Hallazgo | Dato clave |
|---|---|---|
| 1 | El modelo RSJD reproduce bien la frecuencia de saltos y la curtosis, pero falla en asimetría (error 136,9 %, inversión de signo) y sobreestima el tiempo en alto estrés. | Error frecuencia saltos: 6,9 % ✓ |
| 2 | La microestructura ABM amplifica los drawdowns frente al Monte Carlo puro, especialmente en el escenario de baja geopolítica. | +13,75 pp en `low_geo`; +1,80 pp en `high_geo` |
| 3 | El Especulador Técnico domina en Sharpe (+0,743, escenario base); el Fondo Geopolítico ofrece protección de cola, no alfa genérico. | MaxDD reducido un 72 % vs. inversor pasivo |
| 4 | La señal geopolítica tiene asimetría favorable: cada TP vale 7,6× el coste de un FP, pero la alta tasa de FP (22,46 %) erosiona el PnL en escenarios de baja tensión. | TP/\|FP\| = 7,6× en escenario base |

---

## Discusión e interpretación

**Regímenes.** La alta persistencia ($p_{\text{stay}} > 0{,}97$) implica que las señales de cambio de régimen llegan con retraso, lo que limita su utilidad operacional en tiempo real.

**Perfil post-choque.** La ausencia de decaimiento exponencial estadísticamente significativo podría reflejar baja potencia estadística (37 episodios) más que ineficiencia genuina de mercado.

**ABM vs. Monte Carlo.** La diferencia de 8,8 pp en MaxDD (−58,96 % vs −50,13 %) implica que los modelos de reducida forma subestiman el riesgo de caída al ignorar la retroalimentación entre momentum del especulador técnico y contracción de liquidez del creador de mercado.

**Fondo Geopolítico vs. Pasivo.** El Fondo no supera al Pasivo en Sharpe ni en `high_geo` (+0,299 vs +0,465), porque el Pasivo captura la apreciación de +36,50 % directamente. La ventaja del Fondo es condicional a la métrica: domina en protección de drawdown, no en retorno ajustado por riesgo genérico.

**Especulador Técnico.** Es el resultado más robusto: Sharpe positivo en dos de tres escenarios, mayor PnL en escenario base (+24,62 %), mayor contribución en régimen de estrés medio (+13,85 %). El momentum de mediano plazo es competitivo con independencia del escenario geopolítico.

---

## Limitaciones

1. **Matriz de Markov estimada en muestra completa.** Los umbrales de estrés son out-of-sample (2015–2020), pero la matriz de transición usa el período completo 2015–2026, incorporando información del período operacional.
2. **Muestra de calibración de saltos reducida.** Solo 37 episodios y 130 días de choque hacen que pequeñas variaciones en el umbral P90 o en la regla de agrupación alteren sensiblemente $\mu_J$ y $\sigma_J$.
3. **Fallo en asimetría del RSJD.** El modelo genera asimetría positiva mientras los datos históricos muestran asimetría negativa (las caídas son más abruptas que las subidas), lo que puede subestimar el riesgo de cola bajista.
4. **FN = 0 por diseño en el Fondo Geopolítico.** El agente responde sistemáticamente a toda señal de choque, impidiendo la contrastación directa de H3; la reformulación TP/|FP| es útil pero no equivalente.
5. **Agentes estilizados.** Los cuatro tipos de agente simplifican comportamientos con mayor heterogeneidad real (horizontes múltiples, mandatos variables, acuerdos políticos).
6. **GPR exógeno.** El modelo no captura la retroalimentación entre el precio del crudo y el propio índice GPR (endogeneidad precio–geopolítica).

---

## Conclusiones

El pipeline integra cinco bloques coherentes —detección de regímenes, calibración de saltos GPR, Monte Carlo RSJD, ABM microestructural y evaluación financiera— sobre 2.800 observaciones diarias (2015–2026).

Los resultados clave son:

- **Regímenes bien separados**: el alto estrés exhibe curtosis de 15,67 (9× la del bajo estrés) y $\lambda_{\text{salto}} = 0{,}1667$ (2,6× el bajo estrés).
- **RSJD válido parcialmente**: buena fidelidad en frecuencia de saltos (error 6,9 %) y curtosis; fallo estructural en asimetría (inversión de signo, error 136,9 %).
- **ABM amplifica riesgo de cola**: +8,8 pp en MaxDD respecto al Monte Carlo puro en el escenario base; diferencia máxima en `low_geo` (+13,75 pp).
- **Especulador Técnico**: estrategia más consistente (Sharpe +0,743 en escenario base, PnL +24,62 %).
- **Fondo Geopolítico**: no domina en Sharpe, pero reduce el MaxDD un 72 % frente al inversor pasivo y obtiene +32,64 % en `high_geo`; su valor es la protección de cola, no el alfa genérico.

Las limitaciones principales —fallo en asimetría del RSJD, muestra reducida de episodios de choque, agentes estilizados y GPR exógeno— definen la agenda para trabajo futuro.

---

## Bibliografía

Brunnermeier, M. K., & Pedersen, L. H. (2009). Market liquidity and funding liquidity. *Review of Financial Studies*, 22(6), 2201–2238.

Caldara, D., & Iacoviello, M. (2022). Measuring geopolitical risk. *American Economic Review*, 112(4), 1194–1225.

Fama, E. F. (1970). Efficient capital markets: A review of theory and empirical evidence. *Journal of Finance*, 25(2), 383–417.

Farmer, J. D., & Foley, D. (2009). The economy needs agent-based modelling. *Nature*, 460, 685–686.

Hamilton, J. D. (1989). A new approach to the economic analysis of nonstationary time series and the business cycle. *Econometrica*, 57(2), 357–384.

Kyle, A. S. (1985). Continuous auctions and insider trading. *Econometrica*, 53(6), 1315–1335.

Rockafellar, R. T., & Uryasev, S. (2000). Optimization of conditional value-at-risk. *Journal of Risk*, 2(3), 21–41.

Sharpe, W. F. (1966). Mutual fund performance. *Journal of Business*, 39(1), 119–138.

Sortino, F. A., & van der Meer, R. (1991). Downside risk. *Journal of Portfolio Management*, 17(4), 27–31.

Tesfatsion, L., & Judd, K. L. (Eds.) (2006). *Handbook of computational economics, vol. 2: Agent-based computational economics*. Elsevier.

---

*Fecha de cierre de datos: 13 de marzo de 2026. Notebook: `00_pipeline_completo.ipynb`.*
