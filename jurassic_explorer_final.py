#!/usr/bin/env python3
"""
Generador de explorador del Jurásico usando el script que funcionaba
"""

import base64
import mimetypes
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def save_binary_file(file_name, data):
    """Guarda archivo binario en carpeta específica"""
    # Crear carpeta si no existe
    output_folder = "jurassic_images"
    os.makedirs(output_folder, exist_ok=True)
    
    # Ruta completa del archivo
    full_path = os.path.join(output_folder, file_name)
    
    f = open(full_path, "wb")
    f.write(data)
    f.close()
    print(f"💾 Archivo guardado: {full_path}")

def generate_jurassic_explorer():
    """Genera explorador del Jurásico usando el método que funcionaba"""
    
    try:
        # Importar la librería
        from google import genai
        from google.genai import types
        
        print("✅ Librería google-genai importada correctamente")
        
        # Crear cliente
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("❌ No se encontró GOOGLE_API_KEY")
            return
        
        client = genai.Client(api_key=api_key)
        print("✅ Cliente creado correctamente")
        
        # Verificar que existe la imagen
        if not os.path.exists("test.jpg"):
            print("❌ No se encontró test.jpg")
            return
        
        print("📸 Imagen test.jpg encontrada")
        
        # Modelo que soporta imágenes
        model = "gemini-2.5-flash-image-preview"
        
        # Subir la imagen primero
        print("📤 Subiendo imagen test.jpg...")
        uploaded_file = client.files.upload(file="test.jpg")
        print("✅ Imagen subida correctamente")
        
        # Prompt mejorado para manejar múltiples personas y mantener poses originales
        prompt = "Analiza esta imagen y toma EXACTAMENTE el rostro y la pose de TODAS las personas que aparezcan. CRÍTICO: Mantén 100% fiel cada rostro original - ojos, nariz, boca, forma de la cara, expresión facial, edad y género de cada persona. MANTÉN EXACTAMENTE las poses, posturas y posiciones corporales que tienen en la imagen original. Viste a cada persona con trajes de explorador del Jurásico (chaqueta de cuero marrón, botas altas, sombrero de explorador, cinturón con herramientas) pero conservando su pose original. Coloca el fondo en el período Jurásico con dinosaurios, vegetación prehistórica y volcanes. Si hay múltiples personas, mantén la misma composición y disposición espacial que en la imagen original. Iluminación dramática que destaque a todas las personas. Estilo realista y cinematográfico, como una película de aventuras. Cada persona debe verse como un héroe explorador del Jurásico manteniendo su pose característica."
        
        print("🎯 Generando explorador del Jurásico con rostro de test.jpg...")
        print(f"📝 Prompt: Tomar rostro de test.jpg y crear explorador del Jurásico")
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                    types.Part.from_uri(
                        file_uri=uploaded_file.uri,
                        mime_type="image/jpeg"
                    )
                ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            response_modalities=[
                "IMAGE",
                "TEXT",
            ],
        )
        
        file_index = 0
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if (
                chunk.candidates is None
                or chunk.candidates[0].content is None
                or chunk.candidates[0].content.parts is None
            ):
                continue
                
            if chunk.candidates[0].content.parts[0].inline_data and chunk.candidates[0].content.parts[0].inline_data.data:
                file_name = "final.png"
                file_index += 1
                inline_data = chunk.candidates[0].content.parts[0].inline_data
                data_buffer = inline_data.data
                save_binary_file(file_name, data_buffer)
            else:
                if hasattr(chunk, 'text') and chunk.text:
                    print(f"📝 Texto generado: {chunk.text}")
        
        print("✅ ¡Explorador del Jurásico generado exitosamente!")
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("Instala la librería: pip install google-genai")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🦕 Generador de Explorador del Jurásico (Método que Funciona)")
    print("=" * 60)
    generate_jurassic_explorer()
