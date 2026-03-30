# Conclusiones y Resultados Clave — Parte 2
# Geopolítica y Crudo WTI — Simulación Estocástica Multibloque

> Extraído de los notebooks ejecutados: `00_pipeline_completo.ipynb` y `14_financial_evaluation.ipynb`
> Proyecto: Geopolítica Simulación Crudo

---



<!-- Celda 42 -->
### A.2 Interpretación y decisión de parámetros para el simulador

**Hallazgo clave:** El período 2021–2026 muestra drifts positivos en los tres regímenes, incluido el medium_stress (que en el período completo tenía drift negativo de –6%). Esto refleja la recuperación post-COVID y el ciclo alcista de energía 2021–2022. El simulador usará los parámetros del **período operativo 2021–2026** porque:

- Son más representativos del entorno de mercado que el simulador quiere proyectar.
- La diferencia más pronunciada está en el drift, no en la volatilidad (que es estable entre períodos).
- La kurtosis de exceso en high_stress es 1.68 en 2021–2026 vs 15.67 en el período completo (que incluye el evento COVID-19 de abril 2020). El simulador usará el valor del período operativo, ya que el evento COVID es un outlier estructural no representativo de episodios geopolíticos típicos.

---


<!-- Celda 56 -->
---

## G. Resumen de hallazgos y parámetros para el Bloque 3

| Componente | Parámetro | Valor calibrado | Fuente |
|---|---|---|---|
| Drift low stress | μ_ann | +3.6% | Retornos 2021-26, régimen low |
| Drift medium stress | μ_ann | +16.2% | Retornos 2021-26, régimen medium |
| Drift high stress | μ_ann | +18.4% | Retornos 2021-26, régimen high |
| Vol low stress | σ_ann | 24.6% | Retornos 2021-26, régimen low |
| Vol medium stress | σ_ann | 32.3% | Retornos 2021-26, régimen medium |
| Vol high stress | σ_ann | 50.7% | Retornos 2021-26, régimen high |
| Salto μ_J | — | +0.58%/día | Retornos en días GPR>P90 |
| Salto σ_J | — | 3.69%/día | Retornos en días GPR>P90 |
| Intensidad saltos high_stress | λ | Ver JSON | Freq. días shock en régimen |
| Persistencia shock | — | **Markov p_stay=0.977** | Bloque 1 (decay exponencial no detectado) |
| OVX en high_stress | — | 50.2 ± 11.5 | Cross-asset por régimen |
| Prima OVX en shock | — | +30% sobre media | Días GPR>P90 vs media operativa |

### Decisión metodológica clave: modelo de persistencia

El análisis de decay mostró que **no existe un decaimiento exponencial identificable** en los 30 días posteriores al onset de un shock GPR. El perfil de $|r_t|$ es plano y ruidoso, con variabilidad entre episodios alta (IQR amplio). Esto descarta el enfoque de "shock + decaimiento" como mecanismo principal.

**Consecuencia para el Bloque 3:** la persistencia del shock se modela íntegramente mediante la cadena de Markov ($p_{AA} = 0.977$, duración esperada ~43 días). El componente de saltos Jump-Diffusion captura la magnitud del impacto instantáneo, no su decaimiento.

---

**Siguiente:** `03_monte_carlo_engine.py` — motor de simulación Regime-Switching Jump-Diffusion calibrado con estos parámetros.

---


<!-- Celda 87 -->
---

## 10. Conclusiones del bloque y conexión con el Bloque 4 (ABM)

### ¿Qué reproduce bien el motor?

| Característica | Resultado |
|---|---|
| Volatilidad anualizada | Calibrada por régimen, dentro del rango histórico |
| Fat tails | Presentes gracias al componente de saltos (kurt > 0.5) |
| Persistencia de régimen | Cadena de Markov con $P_{ii} \approx 0.97$-$0.99$ |
| Diferencia entre escenarios | Vol(high) > Vol(base) > Vol(low), monotónico |
| Drawdowns plausibles | Dentro del rango percentil histórico |
| No explosión del precio | Reversión parcial impide deriva irreal |

### ¿Qué no pretende capturar?

- **Volatility clustering** (GARCH): la volatilidad dentro de un régimen es constante. El clustering observado históricamente está parcialmente capturado por la persistencia de régimen, no por heterocedasticidad intra-régimen.
- **Correlaciones cross-asset dinámicas**: OVX y DXY son señales externas, no co-simuladas con el precio.
- **Microestructura**: no hay bid-ask, no hay impacto de mercado.

### Conexión con el Bloque 4 (ABM)

Este motor será el **entorno** sobre el que operarán los agentes:

```
Precio WTI simulado = dinámica de fondo (este bloque)
                    + decisiones de agentes (Bloque 4)
```

Los agentes del Bloque 4 recibirán en cada paso:
- El precio actual $P_t$ y log-precio $x_t$
- El régimen actual $s_t$ → condiciona su comportamiento
- Si ocurrió un jump $I_t$ → el Geopolitical Fund reacciona
- La fracción de precio respecto al ancla $(m_0 - x_t)$ → el OPEC+ responde

El motor base proporciona el **proceso de referencia sin agentes** contra el que se medirá el impacto del ABM.

---


<!-- Celda 115 -->
---

## 9. Tabla resumen de métricas

---


<!-- Celda 119 -->
---

## 11. Conclusiones del bloque

### ¿Qué aporta cada agente?

| Agente | Efecto sobre volatilidad | Efecto sobre drawdown | PnL |
|---|---|---|---|
| OPEC+ | Reductor (estabilizador) | Reduce drawdowns en desvíos extremos | Positivo en tendencias bajistas largas |
| Especulador técnico | Amplificador (momentum) | Aumenta drawdowns | Variable; positivo en tendencias claras |
| Market maker | Amortiguador (liquidez) | Reduce impacto puntual | Constante positivo (spread) |
| Fondo geopolítico | Neutral-amplificador | Neutral en media | Depende de persistencia del shock |

### ¿Genera el Fondo Geopolítico alfa real?

Esta es la pregunta central que conecta con la Parte 1. El resultado cuantitativo está en la tabla de PnL:
- En el **escenario base**: el fondo tiene PnL positivo pero Sharpe bajo. La señal existe pero no es suficientemente consistente como para generar alfa significativo.
- En el **escenario de alta tensión**: el PnL sube porque los shocks son más frecuentes y el fondo tiene más oportunidades de entrada.
- Este resultado es **coherente con la Parte 1** (AUC=0.615): hay señal, pero no domina.

### Limitaciones del modelo

1. **Agentes sin aprendizaje**: las reglas son fijas durante toda la simulación.
2. **Sin retroalimentación sobre regímenes**: los agentes modifican el precio pero no el proceso de régimen subyacente.
3. **Liquidez simplificada**: el market maker provee liquidez determinista, sin riesgo de inventario endógeno.
4. **Sin interacción entre agentes**: OPEC+ no observa lo que hace el especulador y viceversa.

Estas limitaciones son explícitas y aceptables en un ABM ligero de portfolio.

### Conexión con el Bloque 5 (evaluación financiera)

Los outputs de este bloque (`abm_paths.parquet`, `abm_agent_pnl.csv`) son los inputs directos del Bloque 5, donde se calcularán:
- VaR/CVaR de las trayectorias ajustadas
- Sharpe y Calmar ratios por agente
- Análisis de escenarios de riesgo extremo

---


<!-- Celda 135 -->
## 6. Tabla resumen de metricas

---


<!-- Celda 154 -->
---

## 12. Conclusiones del bloque

### Resultado central: ¿Tiene valor economico la senal geopolitica?

| Hipotesis | Resultado | Observacion |
|---|---|---|
| **H1**: Geo supera en Sharpe al pasivo en alta tension | **No soportada en Sharpe** | Geo=-0.36 vs Pasivo=-0.33; pero Geo reduce MaxDD un 72% (17% vs 60%) |
| **H2**: Ventaja concentrada en alto estres | **Confirmada** | Geo: +1.2% en high_stress, -0.7% en low_stress. Pasivo: +5.5% vs -5.9% |
| **H3**: Asimetria TP vs FP (FN=0 estructural) | **Confirmada reformulada** | El fondo siempre responde a shocks (FN=0). TP = +0.16%/dia vs FP = -0.02%/dia |
| **H4**: Captura de extremos superior al aleatorio | **Confirmada** | P95 geo > P95 aleatorio en todos los escenarios |

### El verdadero valor del Fondo Geopolitico: reduccion de riesgo

La senal geopolitica no genera alfa Sharpe superior — pero sí genera un perfil de riesgo radicalmente diferente:

| Metrica | Fondo Geo | Pasivo (B&H) | Diferencia |
|---|---|---|---|
| Max Drawdown (base) | -16.6% | -59.6% | **Reduccion del 72%** |
| Sharpe (base) | -0.36 | -0.33 | Similar |
| PnL en high_stress | +1.2% | +5.5% | Pasivo gana mas cuando sube |
| PnL en low_stress | -0.7% | -5.9% | **Geo pierde un 88% menos** |

**Conclusion:** El Fondo Geo es una estrategia de **cobertura asimetrica**. Reduce drasticamente el drawdown maximo a costa de menor participacion en los rebotes. Su valor economico principal no es el alfa, sino la proteccion de capital en caidas.

### Triangulo de coherencia con la Parte 1

- **AUC=0.615** implica precision imperfecta pero recall razonable de los shocks
- El Fondo Geo confirma esto: FN=0 (recall perfecto), FP=22.5% en base (precision imperfecta)
- El ratio TP/|FP| ~ 8x en base indica que cuando la senal es correcta, vale mucho mas que su coste

### Comparacion final de estrategias (escenario base)

| Estrategia | Sharpe | Max DD | Hit Ratio | Veredicto |
|---|---|---|---|---|
| Predictor Perfecto | +17.8 | -0.1% | 98% | Cota superior (oracle) |
| Espec. Tecnico | +0.74 | -20.1% | 51% | Momentum funciona en mercado bajista |
| Pasivo (B&H) | -0.33 | -59.6% | 48% | Riesgo maximo, sin gestion |
| Fondo Geo | -0.36 | -16.6% | 40% | Cobertura: MaxDD reducido 72% |
| Senal Aleatoria | -0.77 | -48.6% | 32% | Peor que pasivo (TC sin valor) |

### Limitaciones

1. **Sin costes de impacto de mercado**: la estrategia geo asume ejecucion sin deslizamiento
2. **Reglas fijas**: los parametros del fondo no se ajustan a las condiciones de mercado
3. **Sin apalancamiento dinamico**: la posicion maxima esta fijada en 0.8
4. **Datos simulados**: los resultados dependen de la calibracion del motor RSJD


---


---

## Evaluación Financiera (14_financial_evaluation.ipynb)

---

## 12. Conclusiones del bloque

### Resultado central: ¿Tiene valor economico la senal geopolitica?

| Hipotesis | Resultado | Observacion |
|---|---|---|
| **H1**: Geo supera en Sharpe al pasivo en alta tension | **No soportada en Sharpe** | Geo=-0.36 vs Pasivo=-0.33; pero Geo reduce MaxDD un 72% (17% vs 60%) |
| **H2**: Ventaja concentrada en alto estres | **Confirmada** | Geo: +1.2% en high_stress, -0.7% en low_stress. Pasivo: +5.5% vs -5.9% |
| **H3**: Asimetria TP vs FP (FN=0 estructural) | **Confirmada reformulada** | El fondo siempre responde a shocks (FN=0). TP = +0.16%/dia vs FP = -0.02%/dia |
| **H4**: Captura de extremos superior al aleatorio | **Confirmada** | P95 geo > P95 aleatorio en todos los escenarios |

### El verdadero valor del Fondo Geopolitico: reduccion de riesgo

La senal geopolitica no genera alfa Sharpe superior — pero sí genera un perfil de riesgo radicalmente diferente:

| Metrica | Fondo Geo | Pasivo (B&H) | Diferencia |
|---|---|---|---|
| Max Drawdown (base) | -16.6% | -59.6% | **Reduccion del 72%** |
| Sharpe (base) | -0.36 | -0.33 | Similar |
| PnL en high_stress | +1.2% | +5.5% | Pasivo gana mas cuando sube |
| PnL en low_stress | -0.7% | -5.9% | **Geo pierde un 88% menos** |

**Conclusion:** El Fondo Geo es una estrategia de **cobertura asimetrica**. Reduce drasticamente el drawdown maximo a costa de menor participacion en los rebotes. Su valor economico principal no es el alfa, sino la proteccion de capital en caidas.

### Triangulo de coherencia con la Parte 1

- **AUC=0.615** implica precision imperfecta pero recall razonable de los shocks
- El Fondo Geo confirma esto: FN=0 (recall perfecto), FP=22.5% en base (precision imperfecta)
- El ratio TP/|FP| ~ 8x en base indica que cuando la senal es correcta, vale mucho mas que su coste

### Comparacion final de estrategias (escenario base)

| Estrategia | Sharpe | Max DD | Hit Ratio | Veredicto |
|---|---|---|---|---|
| Predictor Perfecto | +17.8 | -0.1% | 98% | Cota superior (oracle) |
| Espec. Tecnico | +0.74 | -20.1% | 51% | Momentum funciona en mercado bajista |
| Pasivo (B&H) | -0.33 | -59.6% | 48% | Riesgo maximo, sin gestion |
| Fondo Geo | -0.36 | -16.6% | 40% | Cobertura: MaxDD reducido 72% |
| Senal Aleatoria | -0.77 | -48.6% | 32% | Peor que pasivo (TC sin valor) |

### Limitaciones

1. **Sin costes de impacto de mercado**: la estrategia geo asume ejecucion sin deslizamiento
2. **Reglas fijas**: los parametros del fondo no se ajustan a las condiciones de mercado
3. **Sin apalancamiento dinamico**: la posicion maxima esta fijada en 0.8
4. **Datos simulados**: los resultados dependen de la calibracion del motor RSJD
