# 0003 — Una sola tabla `competitors` para equipos e individuos

- **Estado:** Aceptado
- **Fecha:** 2026-10-21

## Contexto

El modelo v1 tenía `teams` y `players` separados, y `event_participants` apuntaba a
cualquiera de los dos con `participant_type` + `participant_id`, sin clave foránea. La base
de datos no podía garantizar que el participante existiera, y las suscripciones
necesitaban columnas `team_id` y `player_id` en paralelo.

## Decisión

Una tabla `competitors` con `kind = team | individual`. `event_participants.competitor_id`
y `subscriptions.competitor_id` son claves foráneas reales. La relación jugador ↔ equipo
se modela aparte con `competitor_memberships`, temporal (`valid_from`/`valid_to`),
después del MVP (design.md §4.6).

## Alternativas consideradas

- **Mantener tablas separadas con FKs opcionales** (`team_id`, `player_id` + `CHECK`):
  tiene integridad, pero cada filtro y cada consulta se duplica por tipo de competidor.
- **Herencia de tablas** (una tabla base + `teams`/`players` con su id): más fiel al
  dominio, pero agrega joins y complejidad en el ORM que el MVP no necesita.

## Consecuencias

- ✅ Integridad referencial en participantes y suscripciones.
- ✅ "Seguir a X" es igual para Barcelona, Djokovic o Verstappen.
- ✅ Dobles en tenis y piloto ↔ escudería en F1 encajan con las pertenencias.
- ⚠️ Los atributos propios de un tipo (por ejemplo, la mano hábil de un tenista) no
  tienen columna; si hacen falta, irán en una tabla de detalle por tipo.
