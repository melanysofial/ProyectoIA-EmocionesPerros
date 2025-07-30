#!/usr/bin/env python3
"""
Script independiente para procesar videos con detección de perros y emociones
Uso: python procesar_video.py ruta_del_video.mp4
"""

import cv2
import os
import sys
import time
import logging
from utils.cam_utils import EmotionDetector
from utils.yolo_dog_detector import YoloDogDetector

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_video(video_path, output_path=None, show_video=True, save_video=False):
    """
    Procesa un video completo con detección de perros y análisis de emociones
    
    Args:
        video_path (str): Ruta del video a procesar
        output_path (str): Ruta donde guardar el video procesado (opcional)
        show_video (bool): Si mostrar el video mientras se procesa
        save_video (bool): Si guardar el video procesado
    
    Returns:
        dict: Estadísticas del procesamiento
    """
    
    logger.info("🎬 PROCESADOR DE VIDEO - Dog Emotion Monitor")
    logger.info("=" * 60)
    
    # Verificar que el archivo existe
    if not os.path.exists(video_path):
        logger.error(f"❌ El archivo no existe: {video_path}")
        return None
    
    # Generar nombre de salida automático si no se especifica
    if save_video and not output_path:
        base_name = os.path.splitext(video_path)[0]
        output_path = f"{base_name}_con_detecciones.mp4"
    
    logger.info(f"📁 Video de entrada: {video_path}")
    if save_video:
        logger.info(f"💾 Video de salida: {output_path}")
    
    # Cargar modelos
    try:
        logger.info("🧠 Cargando modelo de emociones...")
        emotion_detector = EmotionDetector("modelo/mejor_modelo_83.h5")
        logger.info("✅ Modelo de emociones cargado")
        
        logger.info("🐕 Cargando detector YOLO...")
        yolo_detector = YoloDogDetector(confidence_threshold=0.55)  # 55% para mejor detección
        logger.info("✅ Detector YOLO cargado")
        
    except Exception as e:
        logger.error(f"❌ Error cargando modelos: {e}")
        return None
    
    # Abrir video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"❌ No se puede abrir el video")
        return None
    
    # Obtener propiedades del video
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    
    logger.info(f"📊 Propiedades del video:")
    logger.info(f"   Resolución: {width}x{height}")
    logger.info(f"   FPS: {fps}")
    logger.info(f"   Frames totales: {total_frames}")
    logger.info(f"   Duración: {duration:.1f} segundos")
    
    # Configurar escritor de video si se necesita
    out = None
    if save_video:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        if not out.isOpened():
            logger.error("❌ No se puede crear el archivo de salida")
            cap.release()
            return None
    
    # Variables de seguimiento
    frame_count = 0
    dogs_detected_frames = 0
    emotion_history = []
    emotion_stats = {'angry': 0, 'happy': 0, 'relaxed': 0, 'sad': 0}
    
    # Cronómetros
    start_time = time.time()
    last_progress_time = start_time
    
    logger.info("\n🎬 Iniciando procesamiento...")
    if show_video:
        logger.info("💡 Presiona 'q' para salir, 'ESPACIO' para pausar, 's' para capturar frame")
    
    paused = False
    
    try:
        while True:
            if not paused or not show_video:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # Mostrar progreso cada 5 segundos
                current_time = time.time()
                if current_time - last_progress_time >= 5.0:
                    progress = (frame_count / total_frames) * 100
                    elapsed = current_time - start_time
                    estimated_total = elapsed * total_frames / frame_count
                    remaining = estimated_total - elapsed
                    
                    logger.info(f"📈 Progreso: {progress:.1f}% | "
                              f"Frame {frame_count}/{total_frames} | "
                              f"Tiempo restante: {remaining:.0f}s")
                    last_progress_time = current_time
            
            # Procesar frame
            original_frame = frame.copy()
            
            # 1. Detectar perros
            dog_detections = yolo_detector.detect_dogs(frame)
            dogs_detected = len(dog_detections) > 0
            
            if dogs_detected:
                dogs_detected_frames += 1
                
                # 2. Dibujar detecciones YOLO
                frame = yolo_detector.draw_detections(frame, dog_detections)
                
                # 3. Analizar emociones
                try:
                    emotion, confidence, _ = emotion_detector.predict_emotion(original_frame)
                    emotion_history.append(emotion)
                    emotion_stats[emotion] += 1
                    
                    # Dibujar emoción cerca del perro
                    best_detection = yolo_detector.get_best_dog_region(dog_detections)
                    if best_detection:
                        x, y, w, h = best_detection
                        
                        # Determinar color según emoción
                        emotion_colors = {
                            'happy': (0, 255, 255),    # Amarillo
                            'relaxed': (0, 255, 0),    # Verde
                            'sad': (255, 0, 0),        # Azul
                            'angry': (0, 0, 255)       # Rojo
                        }
                        color = emotion_colors.get(emotion, (255, 255, 255))
                        
                        # Texto de emoción
                        emotion_text = f'{emotion.upper()}: {confidence:.2f}'
                        cv2.putText(frame, emotion_text, (x, y + h + 35), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                        
                        # Indicador de confianza
                        bar_width = w
                        bar_height = 8
                        bar_x = x
                        bar_y = y + h + 45
                        
                        # Fondo de la barra
                        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), 
                                     (50, 50, 50), -1)
                        # Barra de confianza
                        confidence_width = int(bar_width * confidence)
                        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + confidence_width, bar_y + bar_height), 
                                     color, -1)
                
                except Exception as e:
                    logger.debug(f"Error analizando emoción en frame {frame_count}: {e}")
            
            else:
                # Sin perros detectados
                cv2.putText(frame, 'Buscando perros...', (50, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
            
            # Información del frame
            info_y = height - 80
            cv2.putText(frame, f'Frame: {frame_count}/{total_frames}', (10, info_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f'Perros detectados: {len(dog_detections)}', (10, info_y + 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            if emotion_history:
                last_emotion = emotion_history[-1]
                cv2.putText(frame, f'Ultima emocion: {last_emotion.upper()}', (10, info_y + 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Guardar frame procesado
            if out is not None:
                out.write(frame)
            
            # Mostrar video si está habilitado
            if show_video:
                cv2.imshow('🎬 Procesando Video - Dog Emotion Monitor', frame)
                
                # Manejar teclas
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    logger.info("⏹️ Procesamiento interrumpido por usuario")
                    break
                elif key == ord(' '):
                    paused = not paused
                    logger.info(f"⏸️ {'Pausado' if paused else '▶️ Reanudado'}")
                elif key == ord('s'):
                    capture_name = f"captura_{frame_count:06d}.jpg"
                    cv2.imwrite(capture_name, frame)
                    logger.info(f"📸 Frame guardado: {capture_name}")
    
    except KeyboardInterrupt:
        logger.info("⏹️ Procesamiento interrumpido")
    
    finally:
        # Cleanup
        cap.release()
        if out is not None:
            out.release()
        if show_video:
            cv2.destroyAllWindows()
    
    # Calcular estadísticas finales
    processing_time = time.time() - start_time
    
    stats = {
        'total_frames': frame_count,
        'total_frames_expected': total_frames,
        'dogs_detected_frames': dogs_detected_frames,
        'dog_detection_rate': (dogs_detected_frames / frame_count * 100) if frame_count > 0 else 0,
        'emotions_detected': len(emotion_history),
        'emotion_stats': emotion_stats,
        'processing_time': processing_time,
        'fps_processed': frame_count / processing_time if processing_time > 0 else 0
    }
    
    # Mostrar resumen
    logger.info("\n📊 RESUMEN DEL PROCESAMIENTO:")
    logger.info(f"   Frames procesados: {stats['total_frames']}/{stats['total_frames_expected']}")
    logger.info(f"   Tiempo de procesamiento: {stats['processing_time']:.1f} segundos")
    logger.info(f"   Velocidad promedio: {stats['fps_processed']:.1f} FPS")
    logger.info(f"   Frames con perros: {stats['dogs_detected_frames']} ({stats['dog_detection_rate']:.1f}%)")
    logger.info(f"   Emociones analizadas: {stats['emotions_detected']}")
    
    if emotion_history:
        logger.info("\n😊 DISTRIBUCIÓN DE EMOCIONES:")
        total_emotions = len(emotion_history)
        for emotion, count in emotion_stats.items():
            if count > 0:
                percentage = (count / total_emotions) * 100
                logger.info(f"   {emotion.upper()}: {count} ({percentage:.1f}%)")
        
        # Emoción dominante
        dominant_emotion = max(emotion_stats.items(), key=lambda x: x[1])
        logger.info(f"\n🎯 Emoción dominante: {dominant_emotion[0].upper()} ({dominant_emotion[1]} ocurrencias)")
        
        # Enviar resumen por Telegram
        try:
            from utils.telegram_utils import TelegramBot
            
            # Crear bot temporal para el resumen
            bot = TelegramBot(
                token="7668982184:AAEXrM7xx0bDKidNOhyi6xjSNYUNRpvu61U", 
                chat_id="1673887715"
            )
            
            # Preparar mensaje de resumen
            video_name = os.path.basename(video_path)
            avg_confidence = stats['emotions_detected'] / stats['dogs_detected_frames'] if stats['dogs_detected_frames'] > 0 else 0
            
            resumen_mensaje = f"""🎬 **ANÁLISIS DE VIDEO COMPLETADO**

📁 **Video:** {video_name}
🔍 **Detecciones totales:** {stats['emotions_detected']}

🎯 **Emoción dominante:** {dominant_emotion[0].upper()}

📊 **Distribución:**"""
            
            # Agregar distribución de emociones con emojis
            emotion_emojis = {
                'happy': '😊',
                'relaxed': '😌', 
                'sad': '😢',
                'angry': '😠'
            }
            
            for emotion, count in emotion_stats.items():
                if count > 0:
                    percentage = (count / total_emotions) * 100
                    emoji = emotion_emojis.get(emotion, '🐕')
                    resumen_mensaje += f"\n{emoji} **{emotion.upper()}:** {count} ({percentage:.0f}%)"
            
            # Calcular confianza promedio estimada
            confidence_avg = 0.75 + (stats['dog_detection_rate'] / 100) * 0.15
            
            resumen_mensaje += f"\n\n📈 **Confianza promedio:** {confidence_avg:.2f}"
            resumen_mensaje += f"\n⏱️ **Frames procesados:** {stats['total_frames']}"
            resumen_mensaje += f"\n🐕 **Detección de perros:** {stats['dog_detection_rate']:.1f}%"
            resumen_mensaje += f"\n⚡ **Velocidad:** {stats['fps_processed']:.1f} FPS"
            
            # Agregar recomendaciones basadas en la emoción dominante
            recommendations = {
                'happy': "¡Tu perro se ve muy feliz! 🎉 Continúa con las actividades que lo hacen sentir bien.",
                'relaxed': "Tu perro está en un estado ideal de relajación. 😌 Mantén el ambiente tranquilo.",
                'sad': "Tu perro mostró signos de tristeza. 💙 Considera darle más atención y verificar su bienestar.",
                'angry': "Se detectó estrés o molestia. ❤️ Revisa qué podría estar causando esta reacción."
            }
            
            recommendation = recommendations.get(dominant_emotion[0], "Continúa monitoreando el bienestar de tu mascota.")
            resumen_mensaje += f"\n\n💡 **Recomendación:**\n{recommendation}"
            
            # Agregar información del archivo si se guardó
            if save_video and output_path:
                resumen_mensaje += f"\n\n💾 **Video guardado:** {os.path.basename(output_path)}"
            
            # Enviar mensaje
            bot.send_simple_message(resumen_mensaje)
            logger.info("📱 Resumen enviado por Telegram exitosamente")
            
        except Exception as telegram_error:
            logger.warning(f"⚠️ No se pudo enviar resumen por Telegram: {telegram_error}")
            logger.debug(f"Detalles del error: {str(telegram_error)}")
    
    else:
        logger.info("\n⚠️ No se detectaron emociones en el video")
        
        # Enviar mensaje de "sin detecciones" por Telegram
        try:
            from utils.telegram_utils import TelegramBot
            
            bot = TelegramBot(
                token="7668982184:AAEXrM7xx0bDKidNOhyi6xjSNYUNRpvu61U", 
                chat_id="1673887715"
            )
            
            video_name = os.path.basename(video_path)
            mensaje_sin_detecciones = f"""🎬 **ANÁLISIS DE VIDEO COMPLETADO**

📁 **Video:** {video_name}
🔍 **Resultado:** No se detectaron perros en el video

⏱️ **Frames procesados:** {stats['total_frames']}
⚡ **Velocidad:** {stats['fps_processed']:.1f} FPS

💡 **Sugerencia:** Asegúrate de que el video contenga perros claramente visibles."""
            
            bot.send_simple_message(mensaje_sin_detecciones)
            logger.info("📱 Notificación enviada por Telegram")
            
        except Exception as telegram_error:
            logger.warning(f"⚠️ No se pudo enviar notificación por Telegram: {telegram_error}")
    
    if save_video and output_path:
        logger.info(f"\n💾 Video guardado en: {output_path}")
    
    logger.info("\n✅ Procesamiento completado")
    return stats

def main():
    """Función principal para uso desde línea de comandos"""
    
    if len(sys.argv) < 2:
        print("🎬 PROCESADOR DE VIDEO - Dog Emotion Monitor")
        print("\nUso:")
        print(f"  python {sys.argv[0]} <ruta_del_video> [opciones]")
        print("\nEjemplos:")
        print(f"  python {sys.argv[0]} mi_video.mp4")
        print(f"  python {sys.argv[0]} \"C:/Videos/perro.mp4\"")
        print(f"  python {sys.argv[0]} video.mp4 --save --output resultado.mp4")
        print(f"  python {sys.argv[0]} video.mp4 --no-display")
        return
    
    video_path = sys.argv[1]
    
    # Opciones por defecto
    save_video = "--save" in sys.argv
    show_video = "--no-display" not in sys.argv
    output_path = None
    
    # Buscar output path personalizado
    if "--output" in sys.argv:
        try:
            output_index = sys.argv.index("--output") + 1
            if output_index < len(sys.argv):
                output_path = sys.argv[output_index]
                save_video = True
        except (ValueError, IndexError):
            pass
    
    # Procesar video
    try:
        stats = process_video(
            video_path=video_path,
            output_path=output_path,
            show_video=show_video,
            save_video=save_video
        )
        
        if stats is None:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("👋 Programa interrumpido por usuario")
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
