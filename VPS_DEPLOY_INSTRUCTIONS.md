# Guía de Despliegue en VPS

Esta guía describe cómo desplegar el backend (FastAPI) y la base de datos (PostgreSQL) usando Docker Compose en tu servidor VPS.

## Requisitos previos en el VPS
1. **Docker y Docker Compose**: Deben estar instalados en el servidor.
2. **Git**: Para clonar este repositorio (o puedes subir los archivos vía SFTP).

## Pasos

### 1. Preparar el código en el VPS
Clona tu repositorio o copia los archivos de la carpeta `bienestar-docente-server` y el archivo `docker-compose.yml` a tu servidor.

```bash
git clone <tu-url-del-repositorio> bienestar-docente
cd bienestar-docente
```

### 2. Configurar las Variables de Entorno
Copia el archivo de ejemplo y crea tu propio `.env`.

```bash
cp .env.example .env
```

Edita el archivo `.env` (`nano .env` o `vim .env`) y rellena los valores:
- `FRONTEND_URL`: La URL pública de tu frontend en Netlify (ej: `https://tu-sitio.netlify.app`). Esto es crucial para los CORS.
- `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET`: Las credenciales de Google OAuth.
- `SECRET_KEY`: Una cadena segura aleatoria (puedes generar una ejecutando `openssl rand -hex 32` en tu terminal).

### 3. Levantar los Servicios
Ejecuta Docker Compose para construir la imagen del backend y levantar el backend junto con la base de datos PostgreSQL.

```bash
docker-compose up -d --build
```

- `-d`: Corre en modo *detached* (en segundo plano).
- `--build`: Fuerza a Docker a construir la imagen de FastAPI (útil para que tome los últimos cambios del código).

### 4. Verificar el funcionamiento
Puedes ver si los contenedores están corriendo con:
```bash
docker-compose ps
```

También puedes revisar los logs si algo falla:
```bash
docker-compose logs -f
```

Tu API debería estar disponible en el puerto `8000` de tu VPS (ej. `http://<ip-del-vps>:8000/`).

### Consideraciones extra para producción
- **Dominio y HTTPS**: Se recomienda encarecidamente poner un Proxy Inverso (como **Nginx** o **Caddy**) delante de tu puerto `8000` para poder asignarle un dominio (ej: `api.tusitio.com`) y proveer HTTPS (certificados SSL gratuitos con Let's Encrypt). Netlify requerirá que tu backend tenga HTTPS (conexiones seguras) o los navegadores bloquearán las peticiones.
