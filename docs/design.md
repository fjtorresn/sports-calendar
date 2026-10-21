# Sports Calendar — Documento de diseño

> Estado: **borrador** · Última actualización: 2026-10-21

Este documento describe qué construimos, por qué y cómo. Las decisiones puntuales
se registran como ADRs en [`docs/adr/`](adr/).

---

## 1. Problema y objetivo

Seguir varios deportes a la vez hace fácil perderse partidos o competiciones.
Sports Calendar permite que cada usuario defina **suscripciones** (por ejemplo,
*Fútbol – FC Barcelona – Champions League* o *Tenis – Novak Djokovic*) y obtenga
un **calendario personalizado** con todos los eventos que coinciden, visible en la
web, en la app móvil y en su calendario habitual (Google / Apple) vía feed iCal.

## 2. Requisitos

> _Pendiente — se completa en la siguiente iteración._

### 2.1 Funcionales
### 2.2 No funcionales (escala, disponibilidad, frescura de datos)
### 2.3 Fuera de alcance (por ahora)

---

## 3. Fuentes de datos

### 3.1 Deportes en alcance

Fútbol, tenis, básquet, Fórmula 1, boxeo, MMA, NFL. La lista crecerá, así que la
arquitectura debe permitir **agregar un deporte o una fuente sin tocar el resto
del sistema** (ver §3.4).

### 3.2 Hallazgos de la investigación (oct 2026)

> ⚠️ Los planes gratuitos cambian seguido. Todo lo marcado como _"sin verificar"_
> se confirma con una cuenta y una llamada real antes de escribir el adaptador.

| Deporte | Candidata principal (gratis) | Alternativa | Observaciones |
|---|---|---|---|
| **Fútbol** | [football-data.org](https://www.football-data.org/pricing) — 12 competiciones gratis (incluye Champions, las 5 grandes ligas y el Mundial), 10 req/min | [API-Football](https://www.api-football.com/news/post/how-to-get-started-with-api-football-the-complete-beginners-guide) (API-Sports) — ~1200 ligas, 100 req/día | El plan gratuito de football-data entrega los datos con retraso; para un calendario no importa. Cobertura de temporadas de API-Football: _sin verificar_ |
| **F1** | [Jolpica-F1](https://docs.fastf1.dev/api_reference/jolpica.html) — sucesor de Ergast, abierto, 4 req/s y 500 req/h | API-Sports Formula-1 | Es la mejor situación de todas: abierta, estable y con muchos datos |
| **Básquet** | API-Basketball (API-Sports) — 100 req/día, NBA y ligas internacionales | API de ESPN no oficial | La de ESPN no tiene documentación ni términos de uso: solo como respaldo |
| **NFL** | API-American-Football (API-Sports) — 100 req/día | API de ESPN no oficial, [TheSportsDB](https://www.thesportsdb.com/pricing) | |
| **Tenis** | [Live Tennis API](https://duckdb.org/community_extensions/extensions/livetennis) — 100 req/día (_sin verificar_) | API-Tennis, scraping | Es el deporte más difícil de cubrir gratis. Hay que probar la calidad de los datos antes de decidir |
| **MMA** | [TheSportsDB](https://www.thesportsdb.com/season/4443-ufc/2026&view=1) — UFC, 30 req/min | API-Sports MMA, [UFCalendar](https://www.ufcalendar.com/developers/mma-api) (pago, ~USD 19/mes) | Otras promotoras (PFL, ONE) tienen menos cobertura gratis |
| **Boxeo** | ❌ No encontramos una API gratuita confiable | Scraping (revisar los términos de uso de cada sitio) | Candidato natural para el primer adaptador de scraping |
| **Respaldo general** | TheSportsDB — muchos deportes, plan gratuito con resultados limitados | [sporting-events.org](https://sporting-events.org/data/) — descargas CSV/JSON gratuitas, piden atribución | Útil para llenar huecos y para cargar el catálogo inicial |

### 3.3 Lo que la investigación implica para el diseño

1. **Ninguna fuente cubre todo.** Vamos a convivir con varias fuentes desde el día
   uno, así que el patrón *Adapter* (§3.4) no es opcional.
2. **Las cuotas son pequeñas (≈100 req/día por API).** La ingesta tiene que
   **cuidar ese presupuesto**:
   - Los calendarios cambian poco: alcanza con sincronizar 1 a 4 veces al día,
     y con más frecuencia solo cerca de la fecha del evento.
   - Pedir los partidos **por competición o temporada**, no uno por uno.
   - **Ingesta según demanda:** solo se sincronizan las competiciones que al menos
     un usuario sigue. Así el costo depende del catálogo seguido, no de la cantidad
     de usuarios.
3. **La misma entidad llega desde varias fuentes.** "FC Barcelona" en
   football-data y en API-Football tiene IDs distintos. Hace falta una tabla de
   mapeo `external_ids (entity_type, entity_id, source, external_id)` en vez de
   una sola columna `external_id`. Esto es **resolución de entidades**, y se
   empieza a mano: cuando dos fuentes no coinciden, se mapea manualmente.
4. **Prioridad entre fuentes.** Si dos fuentes traen el mismo evento, se define
   por deporte cuál manda (por ejemplo, football-data sobre API-Football para las
   12 competiciones que cubre).
5. **Licencias.** Para uso personal, el plan gratuito alcanza. Si la app se vuelve
   pública, el feed iCal **redistribuye** los datos, y hay que revisar los términos
   de cada fuente antes de abrirla al público.

### 3.4 Patrón de ingesta (borrador)

```
   ┌──────────────────────┐
   │ FootballDataProvider │──┐
   ├──────────────────────┤  │   fetch_events(competition, season)
   │ JolpicaF1Provider    │──┼──────────────────────────────────►  DTOs normalizados
   ├──────────────────────┤  │                                         │
   │ BoxingScraper        │──┘                                         ▼
   └──────────────────────┘                          resolución de entidades (external_ids)
                                                                       │
                                                                       ▼
                                                     upsert idempotente  →  PostgreSQL
```

Cada fuente implementa la misma interfaz (`EventProvider`). El resto del sistema
(API, calendario, iCal) **no sabe** de qué fuente vino cada evento.

---

## 4. Modelo de datos v2

> _Pendiente._

## 5. Arquitectura

> _Pendiente._

## 6. Estimación de carga

> _Pendiente — incluir el cálculo para 1000 usuarios (< 1 req/s de iCal)._

## 7. Plan por fases

> _Pendiente._
