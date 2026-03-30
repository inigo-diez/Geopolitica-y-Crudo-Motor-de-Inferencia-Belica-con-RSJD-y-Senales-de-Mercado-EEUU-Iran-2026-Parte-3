# INTELLIGENCE BRIEF - Crudo, Geopolitica y Mercados Financieros

**Fecha:** 23 marzo 2026
**Fuentes:** Polymarket API + Modelo GPR->WTI (Partes 1+2) + Datos intradiarios
**Evento ancla:** 11:05 UTC (07:05 ET) - Trump publica en Truth Social sobre 'conversaciones productivas' con Iran

---

## SITUACION ACTUAL

- **WTI**: Abrio $99, minimo $84 (+17.4% intradiario), cierre $86
- **Evento ancla**: Trump anuncia pausa de 5 dias en ataques y "conversaciones productivas" con Iran
- **Iran desmiente** cualquier contacto. Incertidumbre maxima.
- **Perfil actual**: 6 de 8 dimensiones activas -> ESTRES EXTREMO
- **GPR actual**: 248.8% (P97.8th historico, umbral modelo: 120)
- **OVX actual**: 91.8% (P98.6th historico, umbral modelo: 40)

---

## SENIALES POLYMARKET POR ACTIVO Y CONVICCION

- **[descontado >90%]**    -> Will there be no change in Fed interest rates after the April 2026 meeting? (95.3%); Will Crude Oil (CL) hit (LOW) $90 by end of June? (91.5%); Will annual inflation increase by ≥2.8% in March? (96.8%)
- **[muy probable 75-90%]** -> Will Crude Oil (CL) hit (LOW) $90 by end of March? (86.8%); Will Iran take military action against a Gulf State on March 22, 2026? (85.0%); Military action against Iran continues through March 31, 2026? (78.5%)
- **[probable 60-75%]**    -> Will Iran conduct a military action against Israel on March 25, 2026? (74.0%); US x Iran ceasefire by June 30? (68.5%); Iran x Israel/US conflict ends by June 30? (73.5%)
- **[cola <60%]**          -> Will Bitcoin reach $150,000 in March? (0.1%); Will the Iranian regime fall by March 31? (1.8%); US forces enter Iran by March 31? (13.5%)

---

## INFERENCIAS DEL MODELO - CRUDO

**Escenarios dentro del dominio:**
  [VERDE] **WTI > $105** (Poly: 41.0%, Conf: Alta)
    Historico: WTI supero $100 en el 5.4% de dias historicos (545/10119). Durante crisis de oferta geopolitica (202
    Modelo   : Modelo Parte 1: AUC=0.615. Con OVX>P90 + GPR>120 la probabilidad de high_stress_day sube sustancialm
  [AMARILLO] **WTI cae < $90 (fin de marzo)** (Poly: 86.8%, Conf: Media)
    Historico: WTI ya toco $84.37 hoy intradiario. Cerro ~$88. El mercado YA ha visto WTI por debajo de $90 hoy. Co
    Modelo   : El modelo de Parte 1 (recall=0.92) habria marcado hoy como high_stress_day. La cadena de Markov (Par
  [VERDE] **Ormuz cerrado hasta abril** (Poly: 55.5%, Conf: Media)
    Historico: El dataset cubre episodios de tension en Ormuz (2011-2012, 2019 ataques a tankers). En esos episodio
    Modelo   : El modelo de Parte 1 usa GDELT para capturar estos eventos via GoldsteinScale y event_count. En la P

**Escenarios fuera del dominio:**
  [ROJO] **WTI > $150** (Poly: 1.6%, Conf: Muy baja / OOD)
    Historico: WTI nunca supero $147 historicamente (max dataset: $145.3 en julio 2008). Ese pico fue POR DEMANDA (
    Modelo   : El modelo de Parte 1 fue entrenado con datos hasta 2026. Max WTI en training: $123.64. $150 esta fue
  [ROJO] **Ormuz cerrado hasta junio** (Poly: 27.0%, Conf: Muy baja / OOD)
    Historico: 90+ dias consecutivos con extreme_event_dummy=1 nunca ocurrio en el dataset (2010-2026). El maximo s
    Modelo   : EXTRAPOLACION FUERA DE DOMINIO. El modelo de Parte 1 nunca vio un episodio de >30 dias de cierre tot
  [ROJO] **Fuerzas USA entran en Iran (fin de marzo)** (Poly: 13.5%, Conf: Muy baja / OOD)
    Historico: El dataset incluye la invasion de Irak 2003: WTI subio +30% en 3 meses previos y luego BAJO tras el 
    Modelo   : PARCIALMENTE FUERA DE DOMINIO. El modelo fue entrenado con amenazas geopoliticas pero no con invasio
  [ROJO] **Oro cae durante la guerra (paradoja safe haven)** (Poly: 17.4%, Conf: Muy baja / OOD)
    Historico: En el dataset (2010-2026), en todos los episodios de GPR>200 el oro subio. La correlacion oro-GPR en
    Modelo   : El modelo de Parte 1 no incluye oro como variable. El modelo no puede predecir el comportamiento del
  [ROJO] **Bitcoin como refugio geopolitico** (Poly: 84.0%, Conf: Muy baja / OOD)
    Historico: Bitcoin no existe como clase de activo relevante en la mayor parte del dataset (2010-2016). Su compo
    Modelo   : COMPLETAMENTE FUERA DEL DOMINIO DEL MODELO. Bitcoin no es una variable en el modelo de Parte 1 ni en

---

## INFERENCIAS DEL MODELO - ACTIVOS FINANCIEROS

  [AMARILLO] **Cese el fuego EEUU-Iran antes del 15 abril** (Poly: 39.5%, Conf: Media)
    Historico: El dataset incluye el acuerdo nuclear Iran-Obama (2015) donde el GPR cayo ~30% en un mes y WTI no su
    Modelo   : El modelo de Parte 1 no modela resoluciones diplomaticas — solo detecta el estado actual. Si se prod
  [VERDE] **Fed pausa en abril (sin cambio de tipos)** (Poly: 95.3%, Conf: Alta)
    Historico: En todos los episodios de shock energetico del dataset donde la Fed tenia doble mandato bajo tension
    Modelo   : El modelo de Parte 1 no incluye variables de politica monetaria directamente. Pero el canal de trans
  [AMARILLO] **Recesion EEUU en 2026** (Poly: 31.5%, Conf: Baja)
    Historico: El dataset incluye las recesiones de 2008-09 y 2020. En ambos casos, WTI cayo >50% durante la recesi
    Modelo   : La señal del modelo es contradictoria para este escenario: GPR alto → modelo predice high_stress_day
  [AMARILLO] **S&P 500 entra en bear market (-20% desde maximo)** (Poly: 12.0%, Conf: Media)
    Historico: El dataset incluye bear markets en 2020 (-34% en 5 semanas) y 2022 (-25% en 9 meses). En ambos casos
    Modelo   : El modelo de Parte 1 no incluye S&P como variable predictora. Pero la transmision es critica: GPR↑ →

---

## DICTAMEN DE LAS PARTES 1 Y 2 SOBRE LAS APUESTAS

*Parte 1 construyo un clasificador RandomForest (AUC=0.615, recall=0.918) entrenado sobre 15 variables macro para predecir regimenes de alta volatilidad en el crudo. Parte 2 calibro un modelo RSJD (Regime-Switching Jump-Diffusion) que estima la dinamica de precio en regimenes de estres (drift=+18.4%, vol=50.7%). El dictamen clasifica cada apuesta segun el respaldo empirico e inferencial de ambos modelos.*

### Verde - Validado por historico y modelo
  [VERDE] **WTI > $105** (Poly: 41.0%, Conf: Alta)
    Historico: WTI supero $100 en el 5.4% de dias historicos (545/10119). Durante crisis de oferta geopolitica (202
    Modelo   : Modelo Parte 1: AUC=0.615. Con OVX>P90 + GPR>120 la probabilidad de high_stress_day sube sustancialm
  [VERDE] **Ormuz cerrado hasta abril** (Poly: 55.5%, Conf: Media)
    Historico: El dataset cubre episodios de tension en Ormuz (2011-2012, 2019 ataques a tankers). En esos episodio
    Modelo   : El modelo de Parte 1 usa GDELT para capturar estos eventos via GoldsteinScale y event_count. En la P
  [VERDE] **Fed pausa en abril (sin cambio de tipos)** (Poly: 95.3%, Conf: Alta)
    Historico: En todos los episodios de shock energetico del dataset donde la Fed tenia doble mandato bajo tension
    Modelo   : El modelo de Parte 1 no incluye variables de politica monetaria directamente. Pero el canal de trans

### Amarillo - Señal parcial / mixta
  [AMARILLO] **WTI cae < $90 (fin de marzo)** (Poly: 86.8%, Conf: Media)
    Historico: WTI ya toco $84.37 hoy intradiario. Cerro ~$88. El mercado YA ha visto WTI por debajo de $90 hoy. Co
    Modelo   : El modelo de Parte 1 (recall=0.92) habria marcado hoy como high_stress_day. La cadena de Markov (Par
  [AMARILLO] **Cese el fuego EEUU-Iran antes del 15 abril** (Poly: 39.5%, Conf: Media)
    Historico: El dataset incluye el acuerdo nuclear Iran-Obama (2015) donde el GPR cayo ~30% en un mes y WTI no su
    Modelo   : El modelo de Parte 1 no modela resoluciones diplomaticas — solo detecta el estado actual. Si se prod
  [AMARILLO] **Recesion EEUU en 2026** (Poly: 31.5%, Conf: Baja)
    Historico: El dataset incluye las recesiones de 2008-09 y 2020. En ambos casos, WTI cayo >50% durante la recesi
    Modelo   : La señal del modelo es contradictoria para este escenario: GPR alto → modelo predice high_stress_day
  [AMARILLO] **S&P 500 entra en bear market (-20% desde maximo)** (Poly: 12.0%, Conf: Media)
    Historico: El dataset incluye bear markets en 2020 (-34% en 5 semanas) y 2022 (-25% en 9 meses). En ambos casos
    Modelo   : El modelo de Parte 1 no incluye S&P como variable predictora. Pero la transmision es critica: GPR↑ →

### Rojo - Fuera de dominio / no respaldado
  [ROJO] **WTI > $150** (Poly: 1.6%, Conf: Muy baja / OOD)
    Historico: WTI nunca supero $147 historicamente (max dataset: $145.3 en julio 2008). Ese pico fue POR DEMANDA (
    Modelo   : El modelo de Parte 1 fue entrenado con datos hasta 2026. Max WTI en training: $123.64. $150 esta fue
  [ROJO] **Ormuz cerrado hasta junio** (Poly: 27.0%, Conf: Muy baja / OOD)
    Historico: 90+ dias consecutivos con extreme_event_dummy=1 nunca ocurrio en el dataset (2010-2026). El maximo s
    Modelo   : EXTRAPOLACION FUERA DE DOMINIO. El modelo de Parte 1 nunca vio un episodio de >30 dias de cierre tot
  [ROJO] **Fuerzas USA entran en Iran (fin de marzo)** (Poly: 13.5%, Conf: Muy baja / OOD)
    Historico: El dataset incluye la invasion de Irak 2003: WTI subio +30% en 3 meses previos y luego BAJO tras el 
    Modelo   : PARCIALMENTE FUERA DE DOMINIO. El modelo fue entrenado con amenazas geopoliticas pero no con invasio
  [ROJO] **Oro cae durante la guerra (paradoja safe haven)** (Poly: 17.4%, Conf: Muy baja / OOD)
    Historico: En el dataset (2010-2026), en todos los episodios de GPR>200 el oro subio. La correlacion oro-GPR en
    Modelo   : El modelo de Parte 1 no incluye oro como variable. El modelo no puede predecir el comportamiento del
  [ROJO] **Bitcoin como refugio geopolitico** (Poly: 84.0%, Conf: Muy baja / OOD)
    Historico: Bitcoin no existe como clase de activo relevante en la mayor parte del dataset (2010-2016). Su compo
    Modelo   : COMPLETAMENTE FUERA DEL DOMINIO DEL MODELO. Bitcoin no es una variable en el modelo de Parte 1 ni en

---

## DIVERGENCIAS CLAVE

- **Lo que Polymarket prica que el modelo no puede validar**: WTI > $150, Ormuz cerrado hasta junio, Fuerzas USA entran en Iran (fin de marzo)
- **Lo que el modelo sugiere que Polymarket no descuenta**: WTI cae < $90 (fin de marzo): modelo sugiere El modelo de Parte 1 (recall=0.92) habria marcado hoy como high_stress_day. La c...
- **El factor Trump**: Variable exogena no modelable que movio WTI +17.4% en menos de 60 minutos. Ningun modelo basado en series temporales puede capturar el riesgo de declaracion de un actor politico unico en tiempo real.

---

## TABLA DE CONTAGIO SISTEMICO

| Canal | Cadena | Modelado | Observado hoy | Divergencia |
|-------|--------|----------|---------------|-------------|
| Canal 1 — Inflacion-Tipos-Renta Variable | GPR↑ → OVX↑ → WTI↑ → IPC↑ → Fed pausa → yields↑ → S&P↓ | SI | WTI↑ (con swing -14% hoy), TNX↑, S&P↓ leve pero NO crash | S&P mas resiliente de lo esperado. El mercado descuenta resolucion rap |
| Canal 2 — Safe Haven Paradox | GPR↑ → WTI↑ → IPC↑ → tipos reales↑ → ORO↓ (a pesar del riesg | NO | Oro↓ intradiario (-8.8%), recuperacion parcial a cierre. Pla | La paradoja se materializo hoy. Canal de tipos reales domino sobre can |
| Canal 3 — Risk-off Selectivo | GPR↑ → VIX↑ → S&P↓ → BTC↑ (activos fuera del sistema financi | NO | BTC SUBIO mientras WTI caia. Posible desacoplamiento del per | Primera vez (potencialmente) que BTC actua como refugio durante crisis |
| Canal 4 — Equity Energetico Desacoplado | WTI↑ → revenues de XOM/CVX↑ → equity energetico outperforms  | SI | Confirmado. XOM y CVX son los principales ganadores del shoc | Sin divergencia. El canal funciona exactamente como predice el modelo. |
| Canal 5 — Factor Trump (no modelable) | Post en red social → expectativa diplomatica → WTI -14% en 5 | NO | El mayor swing intradiario de WTI registrado. Causado por un | DIVERGENCIA MAXIMA. El modelo no puede anticipar, detectar ni modelar  |

---

## CONCLUSION

El episodio del 23 de marzo de 2026 combina un shock energetico estructural (guerra EEUU-Iran, Estrecho de Ormuz bloqueado, WTI +44% YTD) con un canal politico intradiario que reescribe el precio en tiempo real. El historico empirico y los modelos de las Partes 1 y 2 siguen siendo utiles para ordenar escenarios y discriminar que apuestas estan respaldadas por precedentes, pero no sustituyen el juicio cuando aparecen variables exogenas de alta velocidad como un post en Truth Social.

Este brief no es una prediccion: es una lectura argumentada del momento mas inestable del mercado del crudo en decadas, separando cuidadosamente senal historica, lectura del modelo y ruido politico.
