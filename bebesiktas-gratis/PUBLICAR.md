# Bebesiktas Futsal — versión independiente, grupo B

## Estado de esta copia

Esta carpeta contiene el código fuente corregido para 2.ª División, Grupo B, temporada 2026–2027, con datos municipales oficiales hasta la jornada 4 (15/11/2026). **Todavía no está desplegada**. No modifica la web actual de ChatGPT Sites ni conserva automáticamente su URL.

## Datos incorporados

- Clasificación oficial completa de los 12 equipos.
- Resultado oficial Sporting de Majadahonda 5–8 Bebesiktas (jornada 4).
- Calendario de los 22 encuentros de Bebesiktas, con horarios y pistas publicados.
- Partidos anteriores sin marcador individual publicado marcados como “resultado no publicado”, sin inventar marcadores.
- Los dos encuentros frente a Taberna El Farol marcados como excluidos/pendientes según la nota municipal de exclusión desde jornada 1.
- Los siete goleadores oficiales de Bebesiktas, con 13 goles en total.
- Panel de administración y sistema de sincronización protegidos por secretos.

Fuentes municipales consultadas el 16/11/2026:
- Calendario: https://deportes.majadahonda.org/documents/146024/154919/03-%2BCalendario%2BFUTBOL%2BSALA%2B2%C2%AA%2BDivisi%C3%B3n%2C%2BGrupo%2BB.pdf/c2a1b68d-8232-19c4-9ed1-abf0b89229c9?version=1.1
- Resultados/clasificación: https://deportes.majadahonda.org/documents/146024/155055/03-%2BF%C3%BAtbol%2BSala%2B2%C2%AA%2BDIVISION%2B-%2BGrupo%2BB.pdf/41564fb0-9ac5-8054-953f-7b45c72bf738?version=1.4
- Goleadores: https://deportes.majadahonda.org/documents/146024/155059/03-%2BM%C3%A1ximos%2BGOLEADORES%2B2%C2%AA%2BDivisi%C3%B3n%2B-%2BGrupo%2BB.pdf/fdb4fca3-a65d-7123-2c2d-2090affd2dcf?version=1.3

## Publicación gratuita desde ordenador

Requiere Node.js 20 o posterior, una cuenta gratuita de Cloudflare y una cuenta gratuita de GitHub. No compartas contraseñas, tokens ni claves en el chat.

1. Descomprime la carpeta `bebesiktas-gratis`.
2. Abre una terminal dentro de esa carpeta y ejecuta `npx wrangler@4 login`.
3. Crea una base de datos D1: `npx wrangler@4 d1 create bebesiktas-data`.
4. Copia el `database_id` que devuelve Cloudflare en `wrangler.jsonc`, sustituyendo `REEMPLAZAR_CON_EL_ID_DE_TU_BASE`.
5. Ejecuta `npx wrangler@4 d1 execute bebesiktas-data --remote --file=schema.sql`.
6. Ejecuta `npx wrangler@4 deploy`.
7. Configura los secretos con `npx wrangler@4 secret put ADMIN_PASSWORD`, `npx wrangler@4 secret put SESSION_KEY` y `npx wrangler@4 secret put SYNC_TOKEN`. Usa valores distintos y privados; la contraseña debe tener al menos 12 caracteres y los otros dos secretos al menos 32.
8. Abre la dirección `workers.dev` que entrega Cloudflare y comprueba `/api/state` y `/admin`.

No actives planes de pago ni facturación. Si Cloudflare te pide añadir un método de pago, detente.

## Revisión automática

El flujo de GitHub Actions se programa dos veces al día, a las 08:00 y 20:00 UTC. En horario peninsular de invierno equivale a 09:00 y 21:00; durante el horario de verano se desplaza una hora. GitHub Actions no permite programar directamente con zona horaria Europe/Madrid. GitHub puede retrasar o desactivar tareas programadas si el repositorio público no tiene actividad durante 60 días.

Para activarlo:
1. Crea un repositorio público en GitHub y sube el contenido de esta carpeta, incluida `.github/workflows/actualizar.yml`.
2. En Settings → Secrets and variables → Actions añade `APP_URL` como variable con la URL HTTPS de Cloudflare.
3. Añade `SYNC_TOKEN` como secreto con exactamente el mismo valor que configuraste en Cloudflare.
4. En Actions ejecuta “Revisar liga municipal” con “Run workflow”.
5. Comprueba que termina correctamente y que cambia la fecha de última revisión en la app.

El lector verifica que los tres PDF corresponden a 2026–2027 y al grupo B, y que contienen 12 equipos, 22 partidos y goleadores coherentes. Si la fuente falla o los documentos no pasan las validaciones, conserva los últimos datos válidos.

## Importante sobre la URL actual

El despliegue de esta copia en Cloudflare generará una dirección nueva `workers.dev`. No modifica automáticamente `https://bebesiktas-futsal.belen-hormaechea.chatgpt.site/`. Para conservar la URL de ChatGPT Sites necesitamos recuperar el editor/proyecto original o disponer de una opción de dominio personalizado que permita apuntar el dominio; no se debe prometer que esta copia puede sobrescribir Sites.
