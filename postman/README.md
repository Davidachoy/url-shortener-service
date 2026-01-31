# Postman Collection

Colección de Postman para probar la API del URL Shortener.

## Archivos

- **`URL_Shortener_API.postman_collection.json`** - Colección con todos los endpoints
- **`Local.postman_environment.json`** - Entorno para desarrollo local (http://localhost:8000)
- **`Production.postman_environment.json`** - Entorno para producción (cambiar dominio)

## Importar en Postman

1. Abrir Postman
2. Click en **Import**
3. Arrastrar los archivos `.json` o seleccionarlos
4. La colección y los entornos aparecerán en tu workspace

## Endpoints incluidos

### Health Check
- **GET** `/health`
- Verificar que la API está funcionando

### Shorten URL - Simple
- **POST** `/api/v1/shorten`
- Body: `{"url": "https://www.google.com"}`
- Acorta una URL con código auto-generado

### Shorten URL - Custom Code
- **POST** `/api/v1/shorten`
- Body: `{"url": "https://github.com", "custom_code": "github"}`
- Acorta una URL con código personalizado

### Shorten URL - With Expiration
- **POST** `/api/v1/shorten`
- Body: `{"url": "https://example.com", "custom_code": "temp", "expires_at": "2026-12-31T23:59:59Z"}`
- Acorta una URL con fecha de expiración

### Shorten URL - Invalid URL
- **POST** `/api/v1/shorten`
- Body: `{"url": "not-a-valid-url"}`
- Test de validación (debe retornar 422)

### Shorten URL - Duplicate Custom Code
- **POST** `/api/v1/shorten`
- Body: `{"url": "https://example.com", "custom_code": "duplicate-test"}`
- Ejecutar 2 veces: segunda debe fallar con 400

### Shorten URL - Reserved Code
- **POST** `/api/v1/shorten`
- Body: `{"url": "https://example.com", "custom_code": "admin"}`
- Intenta usar código reservado (debe retornar 400)

## Uso

1. Seleccionar entorno: **Local** o **Production**
2. Ejecutar requests
3. Ver responses en Postman

## Variables de entorno

La colección usa `{{base_url}}` que se define en los archivos de entorno:
- **Local**: `http://localhost:8000`
- **Production**: Cambiar a tu dominio real

## Antes de probar

Asegúrate de que los servicios estén corriendo:

```bash
./scripts/docker-up.sh
uvicorn app.main:app --reload
```
