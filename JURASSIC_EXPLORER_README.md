# Explorador del Jurásico - Nueva Funcionalidad Django

## Descripción
Se ha agregado una nueva funcionalidad a tu proyecto Django que integra el script `jurassic_explorer_final.py` para generar imágenes de exploradores del Jurásico.

## Nueva Ruta
- **URL**: `/api/jurassic-explorer/`
- **Método**: POST
- **Parámetro**: `file` (imagen en formato multipart/form-data)

## Configuración Requerida

### 1. Variables de Entorno
Crea un archivo `.env` en la raíz del proyecto con tu API key de Google:

```env
GOOGLE_API_KEY=tu_api_key_aqui
```

Para obtener tu API key:
1. Ve a [Google AI Studio](https://aistudio.google.com/)
2. Crea una cuenta o inicia sesión
3. Genera una nueva API key
4. Copia la key al archivo `.env`

### 2. Dependencias
Asegúrate de tener instalada la librería `google-genai`:

```bash
pip install google-genai
```

## Uso

### Desde el Frontend (JavaScript)
```javascript
const formData = new FormData();
formData.append('file', imageFile); // imageFile es un objeto File

fetch('/api/jurassic-explorer/', {
    method: 'POST',
    body: formData
})
.then(response => {
    if (response.ok) {
        return response.blob();
    }
    throw new Error('Error en el procesamiento');
})
.then(blob => {
    // Crear URL para mostrar la imagen
    const imageUrl = URL.createObjectURL(blob);
    const img = document.createElement('img');
    img.src = imageUrl;
    document.body.appendChild(img);
})
.catch(error => {
    console.error('Error:', error);
});
```

### Desde cURL
```bash
curl -X POST \
  -F "file=@tu_imagen.jpg" \
  http://localhost:8000/api/jurassic-explorer/ \
  --output jurassic_explorer.png
```

## Funcionalidad
La nueva vista:
1. Recibe una imagen desde el frontend
2. Crea un archivo temporal con la imagen
3. Sube la imagen a Google AI usando la API de Gemini
4. Genera una nueva imagen con el estilo de explorador del Jurásico
5. Devuelve la imagen procesada como respuesta HTTP
6. Limpia los archivos temporales

## Características
- Mantiene los rostros originales de las personas
- Conserva las poses y posturas originales
- Viste a las personas como exploradores del Jurásico
- Coloca un fondo prehistórico con dinosaurios
- Estilo cinematográfico y realista

## Archivos Modificados
- `api/views.py`: Agregada la clase `JurassicExplorerView`
- `api/urls.py`: Agregada la ruta `/jurassic-explorer/`

## Notas
- La funcionalidad original del script `jurassic_explorer_final.py` se mantiene intacta
- No se han modificado las rutas existentes
- La nueva funcionalidad es completamente independiente
