# 0002 — Varias fuentes de datos detrás de una interfaz común

- **Estado:** Aceptado
- **Fecha:** 2026-10-21

## Contexto

Ninguna fuente gratuita cubre todos los deportes (ver design.md §3.2). Las APIs gratuitas
tienen cuotas pequeñas (≈100 req/día) y algunos deportes, como el boxeo, no tienen
ninguna API confiable.

## Decisión

- Se priorizan las **APIs gratuitas**; el **scraping** se usa solo cuando no hay API.
- Cada fuente se implementa como un adaptador de la interfaz `EventProvider`, que
  devuelve DTOs normalizados. El resto del sistema no sabe de dónde vino un dato.
- La identidad entre fuentes se resuelve con las tablas `*_external_refs`
  (`UNIQUE (source, external_id)`), que hacen idempotente el upsert.
- La ingesta es **según demanda**: solo se sincronizan las competiciones con suscriptores.

## Consecuencias

- ✅ Agregar un deporte o una fuente = un adaptador nuevo (RNF-6).
- ✅ El costo de la ingesta depende del catálogo seguido, no de la cantidad de usuarios.
- ⚠️ Los scrapers son frágiles: necesitan tests con HTML grabado y alertas cuando
  devuelven 0 eventos.
- ⚠️ La resolución de entidades entre fuentes empieza siendo manual.
- ⚠️ Si la app se abre al público, hay que revisar las licencias: el feed iCal
  redistribuye datos de terceros.
