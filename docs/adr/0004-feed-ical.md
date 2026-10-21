# 0004 — Feed iCal con token privado y caché por TTL

- **Estado:** Aceptado
- **Fecha:** 2026-10-21

## Contexto

El usuario quiere ver sus eventos en Google Calendar o Apple Calendar. Esos clientes se
suscriben a una URL `.ics` (RFC 5545) y la vuelven a pedir periódicamente, **sin**
enviar credenciales.

## Decisión

- Cada usuario tiene un `ical_token` aleatorio (≥ 32 bytes, `secrets.token_urlsafe`),
  único y revocable. URL: `GET /calendar/{ical_token}.ics`.
- Cada evento usa un `UID` estable (derivado de `events.id`), así un cambio de hora
  **actualiza** el evento en el calendario en vez de duplicarlo.
- Horas en UTC; los eventos `date_only` se publican como eventos de todo el día.
- La respuesta se guarda en caché en Redis con **TTL de 1 hora**, sin invalidación explícita.
- El feed se construye en la misma fase que el calendario web, porque usan la misma consulta.

## Consecuencias

- ✅ Funciona con cualquier cliente de calendario, sin app propia.
- ✅ El costo por consulta es bajo; la caché absorbe las consultas repetidas.
- ⚠️ La URL **es** la credencial: si se filtra, cualquiera ve el calendario (que no
  contiene datos sensibles). Mitigación: poder regenerar el token.
- ⚠️ Retraso total = sincronización diaria + TTL + intervalo de refresco del cliente
  (Google: hasta ~24 h). Es aceptable según RNF-1; si no alcanza, la solución son las
  notificaciones push, no achicar el TTL.
