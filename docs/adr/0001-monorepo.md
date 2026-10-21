# 0001 — Monorepo para backend, web y mobile

- **Estado:** Aceptado
- **Fecha:** 2026-10-21

## Contexto

El proyecto empezó en dos repos (`sports-calendar-backend` y `sports-calendar-frontend`).
El plan incluye web y app móvil, que van a consumir la misma API. El desarrollo lo hace
una sola persona.

## Decisión

Un único repositorio `sports-calendar` con `backend/` (Python) y `frontend/`
(Turborepo: `apps/web`, `apps/mobile`, `packages/*`). Los repos originales se importaron
con `git subtree add`, conservando su historial.

## Consecuencias

- ✅ Un cambio en la API y en sus clientes va en un mismo commit o PR.
- ✅ `packages/api-client`, generado desde el OpenAPI de FastAPI, lo comparten web y
  mobile; si cambia el contrato, el TypeScript falla al compilar.
- ✅ Un solo enlace de portafolio que muestra el sistema completo.
- ⚠️ El CI necesita filtros por ruta para no correr los tests de Python cuando solo
  cambia el frontend, y al revés.
- ⚠️ Los commits importados conservan las rutas originales; para seguir un archivo
  a través de la migración se usa `git log --follow`.
- La estructura del repo **no afecta** la escala en tiempo de ejecución: cada componente
  se despliega por separado.
