from rest_framework.views import APIView
from rest_framework.response import Response # La usamos para los errores
from django.http import HttpResponse # La usamos para la respuesta de imagen
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rembg import remove
from PIL import Image
from io import BytesIO
import base64
import os
import tempfile
import traceback
import numpy as np
from moviepy import *
from moviepy import vfx
from moviepy.video.VideoClip import ImageClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
import time



from django.conf import settings
import tempfile
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(BASE_DIR, "media", "videos")  # por ejemplo: ./media/videos

class BaseRemoveBackgroundView(APIView):
    """
    Vista base para eliminar el fondo de una imagen.
    Encapsula la lógica común para la validación de archivos y el manejo de errores.
    """
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        if 'file' not in request.data:
            return Response({"error": "No se proporcionó ningún archivo"}, status=status.HTTP_400_BAD_REQUEST)

        file_obj = request.data['file']

        try:
            input_image_bytes = file_obj.read()
            
            # Procesar la imagen
            output_image_bytes = self.process_image(input_image_bytes)

            # Crear una respuesta HTTP con la imagen procesada
            response = HttpResponse(output_image_bytes, content_type='image/png')
            response['Content-Disposition'] = 'attachment; filename="no-bg.png"'
            
            return response
        except Exception as e:
            return Response({"error": f"Error al procesar la imagen: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def process_image(self, image_bytes):
        """
        Procesa la imagen. Este método está diseñado para ser sobrescrito
        por subclases si necesitan realizar un procesamiento adicional.
        """
        # Usar rembg para quitar el fondo
        return remove(image_bytes)


class RemoveBackgroundView(BaseRemoveBackgroundView):
    """
    Una vista que simplemente elimina el fondo de una imagen usando la lógica base.
    """
    pass


class RemoveBackgroundView2(BaseRemoveBackgroundView):
    """
    Una vista que elimina el fondo, lo reemplaza con una imagen fija
    y devuelve un objeto JSON con dos imágenes:
    1. La imagen sin fondo.
    2. La imagen con el nuevo fondo y un video de transición.
    Ambas imágenes se devuelven codificadas en base64.
    """
    def post(self, request, *args, **kwargs):
        if 'file' not in request.data:
            return Response({"error": "No se proporcionó ningún archivo"}, status=status.HTTP_400_BAD_REQUEST)

        file_obj = request.data['file']

        try:
            input_image_bytes = file_obj.read()

            # 1. Quitar el fondo usando la lógica de la clase base
            no_bg_image_bytes = super().process_image(input_image_bytes)

            # --- 2. Proceso adicional: añadir un nuevo fondo desde un archivo ---

            # Abrir la imagen original para obtener sus dimensiones
            original_image = Image.open(BytesIO(input_image_bytes))
            # Abrir la imagen sin fondo para pegarla
            no_bg_image = Image.open(BytesIO(no_bg_image_bytes))

            # Cargar la imagen de fondo desde el servidor.
            # **NOTA**: Asegúrate de que esta ruta sea correcta y que la imagen exista.
            # Por ejemplo, crea una carpeta 'static/images' en la raíz de tu proyecto Django.
            background_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'forest.jpg')

            if not os.path.exists(background_path):
                error_msg = f"La imagen de fondo no se encuentra en la ruta esperada: {background_path}"
                print(error_msg) # Log to console for debugging
                return Response({"error": error_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            background_image = Image.open(background_path).convert("RGBA")

            # Adaptar el tamaño del fondo al de la imagen original
            background_image_resized = background_image.resize(original_image.size)

            # Pegar la imagen sin fondo sobre el nuevo fondo
            background_image_resized.paste(no_bg_image, (0, 0), no_bg_image)

            # Guardar la imagen final con el nuevo fondo en un buffer de bytes
            final_image_buffer = BytesIO()
            background_image_resized.save(final_image_buffer, format='PNG')
            image_with_new_bg_bytes = final_image_buffer.getvalue()

            # --- 3. Proceso adicional: Crear un video de transición ---

            # Convertir imágenes a formato que moviepy pueda usar (arrays de numpy en RGB)
            original_np = np.array(original_image.convert("RGB"))
            final_np = np.array(background_image_resized.convert("RGB"))

            # Crear clips de imagen con una duración de 5 segundos
            duration = 5
            original_clip = ImageClip(original_np).with_duration(duration)
            final_clip = ImageClip(final_np).with_duration(8)
            # Obtén el tamaño del video
            video_size = original_clip.size  # (width, height)

            # Define una función de posición que baja la imagen desde arriba
            def vertical_wipe(t):
                # t es el tiempo en segundos
                if t < duration:

                    y = -video_size[1] + (video_size[1] * t / duration)
                else:
                    y=0
                return (0, y)

            # Aplica la animación de entrada
            final_clip = final_clip.with_position(vertical_wipe)

            # Combina los clips
            video = CompositeVideoClip([original_clip, final_clip])

            # original_clip = original_clip.with_effects([vfx.FadeOut(duration)])
            # final_clip = final_clip.with_effects([vfx.FadeIn(duration)])


            # # Crear la transición de fundido cruzado (crossfade)
            # video = CompositeVideoClip([original_clip, final_clip])

            filename = f"transicion_{int(time.time())}.mp4"
            output_path = os.path.join(output_dir, filename)


            # Escribir el video en un archivo temporal para obtener sus bytes
            # Escribir el archivo directamente en la ruta deseada
            video.write_videofile(
                output_path,
                codec='libx264',
                audio=False,
                fps=24,
                logger=None
            )

            # Leer los bytes si los necesitas
            with open(output_path, "rb") as f:
                video_bytes = f.read()


            # --- 4. Codificar todo para la respuesta JSON ---
            no_bg_base64 = base64.b64encode(no_bg_image_bytes).decode('utf-8')
            with_new_bg_base64 = base64.b64encode(image_with_new_bg_bytes).decode('utf-8')
            video_base64 = base64.b64encode(video_bytes).decode('utf-8')

            # 5. Crear la respuesta JSON, añadiendo el prefijo Data URL para uso directo en el frontend.
            data = {
                "image_no_bg": f"data:image/png;base64,{no_bg_base64}",
                "image_with_new_bg": f"data:image/png;base64,{with_new_bg_base64}",
                "transition_video": f"data:video/mp4;base64,{video_base64}"
            }

            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            # Imprimimos el traceback completo en la consola para una mejor depuración
            print("--- Ha ocurrido un error en la vista ---")
            traceback.print_exc()
            print("------------------------------------")
            return Response({"error": f"Error al procesar la imagen: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JurassicExplorerView(APIView):
    """
    Vista para generar explorador del Jurásico con video animado
    Recibe una imagen desde el frontend, genera la imagen del explorador del Jurásico y crea un video de transición
    """
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        if 'file' not in request.data:
            return Response({"error": "No se proporcionó ningún archivo"}, status=status.HTTP_400_BAD_REQUEST)

        file_obj = request.data['file']

        try:
            # Leer los bytes de la imagen
            input_image_bytes = file_obj.read()
            
            # Procesar la imagen usando la funcionalidad del script
            jurassic_image_bytes = self.generate_jurassic_explorer(input_image_bytes)
            
            if jurassic_image_bytes is None:
                return Response({"error": "No se pudo generar la imagen del explorador del Jurásico"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Agregar logos a la imagen del explorador del Jurásico
            jurassic_image_with_logos = self.add_logos_to_image(jurassic_image_bytes)

            # --- Crear video de transición optimizado ---
            original_image = Image.open(BytesIO(input_image_bytes))
            jurassic_image = Image.open(BytesIO(jurassic_image_with_logos))

            # Convertir imágenes a formato que moviepy pueda usar (arrays de numpy en RGB)
            original_np = np.array(original_image.convert("RGB"))
            jurassic_np = np.array(jurassic_image.convert("RGB"))

            # Crear clips de imagen con duración optimizada
            duration = 5
            original_clip = ImageClip(original_np).with_duration(duration)
            jurassic_clip = ImageClip(jurassic_np).with_duration(8)
            
            # Obtener el tamaño del video
            video_size = original_clip.size

            # Función de posición optimizada para la animación
            def vertical_wipe(t):
                if t < duration:
                    y = -video_size[1] + (video_size[1] * t / duration)
                else:
                    y = 0
                return (0, y)

            # Aplicar la animación de entrada
            jurassic_clip = jurassic_clip.with_position(vertical_wipe)

            # Combinar los clips
            video = CompositeVideoClip([original_clip, jurassic_clip])

            # Generar nombre de archivo único
            filename = f"jurassic_transicion_{int(time.time())}.mp4"
            output_path = os.path.join(output_dir, filename)

            # Escribir el video con configuración optimizada
            video.write_videofile(
                output_path,
                codec='libx264',
                audio=False,
                fps=24,
                logger=None,
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )

            # Leer los bytes del video
            with open(output_path, "rb") as f:
                video_bytes = f.read()

            # Codificar todo para la respuesta JSON
            original_base64 = base64.b64encode(input_image_bytes).decode('utf-8')
            jurassic_base64 = base64.b64encode(jurassic_image_with_logos).decode('utf-8')
            video_base64 = base64.b64encode(video_bytes).decode('utf-8')

            # Crear la respuesta JSON
            data = {
                "image_no_bg": f"data:image/jpeg;base64,{original_base64}",
                "image_with_new_bg": f"data:image/png;base64,{jurassic_base64}",
                "transition_video": f"data:video/mp4;base64,{video_base64}"
            }

            return Response(data, status=status.HTTP_200_OK)
            
        except Exception as e:
            print("--- Error en JurassicExplorerView ---")
            traceback.print_exc()
            print("------------------------------------")
            return Response({"error": f"Error al procesar la imagen: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def add_logos_to_image(self, image_bytes):
        """
        Agrega los logos de Titan en las esquinas superiores de la imagen
        """
        try:
            # Abrir la imagen principal
            main_image = Image.open(BytesIO(image_bytes)).convert("RGBA")
            main_width, main_height = main_image.size
            
            # Calcular el tamaño de los logos (10% del ancho de la imagen, máximo 150px)
            logo_size = min(int(main_width * 0.5), 330)
            
            # Rutas de los logos
            logo1_path = os.path.join(BASE_DIR, "media", "images", "lgo2titan.png")
            logo2_path = os.path.join(BASE_DIR, "media", "images", "lgo1titan.png")
            
            # Verificar que los logos existan
            if not os.path.exists(logo1_path) or not os.path.exists(logo2_path):
                print("⚠️ No se encontraron los logos, retornando imagen sin logos")
                return image_bytes
            
            # Cargar y redimensionar los logos
            logo1 = Image.open(logo1_path).convert("RGBA")
            logo2 = Image.open(logo2_path).convert("RGBA")
            
            # Redimensionar manteniendo la proporción
            logo1.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)
            logo2.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Crear una copia de la imagen principal para no modificar la original
            result_image = main_image.copy()
            
            # Posiciones de los logos (esquinas superiores con margen)
            margin = 20
            logo1_position = (margin, main_height - logo1.height - margin) # Esquina inferior izquierda
            logo2_position = (main_width - logo2.width - margin, margin)  # Esquina superior derecha
            
            # Pegar los logos en la imagen principal
            result_image.paste(logo1, logo1_position, logo1)
            result_image.paste(logo2, logo2_position, logo2)
            
            # Convertir de vuelta a bytes
            output_buffer = BytesIO()
            result_image.save(output_buffer, format='PNG')
            return output_buffer.getvalue()
            
        except Exception as e:
            print(f"⚠️ Error al agregar logos: {e}")
            # Si hay error, retornar la imagen original sin logos
            return image_bytes

    def generate_jurassic_explorer(self, image_bytes):
        """
        Genera explorador del Jurásico usando la funcionalidad del script original
        Optimizado para mejor rendimiento y manejo de errores
        """
        try:
            # Importar la librería
            from google import genai
            from google.genai import types
            
            print("✅ Librería google-genai importada correctamente")
            
            # Crear cliente
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                print("❌ No se encontró GOOGLE_API_KEY")
                return None
            
            client = genai.Client(api_key=api_key)
            print("✅ Cliente creado correctamente")
            
            # Crear archivo temporal con la imagen recibida
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_file.write(image_bytes)
                temp_file_path = temp_file.name
            
            try:
                print("📸 Imagen temporal creada")
                
                # Modelo optimizado
                model = "gemini-2.5-flash-image-preview"
                
                # Subir la imagen
                print("📤 Subiendo imagen temporal...")
                uploaded_file = client.files.upload(file=temp_file_path)
                print("✅ Imagen subida correctamente")
                
                # Prompt optimizado y más conciso
                prompt = """Analiza esta imagen y transforma EXACTAMENTE el rostro y pose de TODAS las personas manteniendo 100% fiel cada rostro original (ojos, nariz, boca, forma de cara, expresión, edad, género). CONSERVA las poses, posturas y posiciones corporales originales. Viste a cada persona con trajes de explorador del Jurásico (chaqueta de cuero marrón, botas altas, sombrero de explorador, cinturón con herramientas) manteniendo su pose original. Fondo: período Jurásico con dinosaurios, vegetación prehistórica y volcanes. Si hay múltiples personas, mantén la misma composición espacial original. Iluminación dramática y cinematográfica. Estilo realista como película de aventuras."""
                
                print("🎯 Generando explorador del Jurásico...")
                
                # Configuración optimizada
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
                    response_modalities=["IMAGE", "TEXT"],
                )
                
                # Procesar la respuesta de manera más eficiente
                for chunk in client.models.generate_content_stream(
                    model=model,
                    contents=contents,
                    config=generate_content_config,
                ):
                    # Verificación optimizada
                    if not (chunk.candidates and 
                           chunk.candidates[0].content and 
                           chunk.candidates[0].content.parts):
                        continue
                    
                    part = chunk.candidates[0].content.parts[0]
                    
                    # Verificar si hay datos de imagen
                    if (part.inline_data and 
                        part.inline_data.data):
                        print("✅ ¡Explorador del Jurásico generado exitosamente!")
                        return part.inline_data.data
                    
                    # Log de texto si existe
                    if hasattr(chunk, 'text') and chunk.text:
                        print(f"📝 Texto generado: {chunk.text}")
                
                print("⚠️ No se generó imagen en la respuesta")
                return None
                
            finally:
                # Limpiar archivo temporal de manera segura
                try:
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                        print("🗑️ Archivo temporal eliminado")
                except OSError as e:
                    print(f"⚠️ Error al eliminar archivo temporal: {e}")
                
        except ImportError as e:
            print(f"❌ Error de importación: {e}")
            print("Instala la librería: pip install google-genai")
            return None
        except Exception as e:
            print(f"❌ Error en generate_jurassic_explorer: {e}")
            return None
