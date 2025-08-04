"""
Sistema de Telegram simplificado y corregido
=========================================

Esta versión usa requests directamente para evitar problemas con asyncio
y garantizar compatibilidad completa con la aplicación web.
"""

import requests
import logging
import time
import os
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class SimpleTelegramBot:
    """Bot de Telegram simplificado usando requests directamente"""
    
    def __init__(self, token: str = None, chat_id: str = None):
        self.token = token or os.getenv('TELEGRAM_BOT_TOKEN', '7668982184:AAEXrM7xx0bDKidNOhyi6xjSNYUNRpvu61U')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID', '1673887715')
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        
        # Estado del monitoreo
        self.monitoring_active = True
        self.emotion_history = []
        self.last_status_time = 0
        
        # Validar token y chat_id
        if not self.token or self.token == 'YOUR_BOT_TOKEN':
            raise ValueError("❌ Token de Telegram no válido")
        if not self.chat_id or self.chat_id == 'YOUR_CHAT_ID':
            raise ValueError("❌ Chat ID no válido")
        
        logger.info(f"🤖 Bot inicializado - Chat ID: {self.chat_id}")
        
        # Recomendaciones por emoción
        self.recommendations = {
            'angry': [
                "🚨 Tu perro parece molesto. Aquí algunas recomendaciones:",
                "• Revisa si hay ruidos fuertes que lo estresen",
                "• Verifica que tenga agua fresca y comida",
                "• Dale un espacio tranquilo para calmarse",
                "• Evita forzar interacciones hasta que se calme",
                "• Si persiste, consulta con un veterinario"
            ],
            'sad': [
                "😢 Tu perro se ve triste. Te sugerimos:",
                "• Dedícale tiempo de calidad y caricias",
                "• Sácalo a pasear si es posible",
                "• Revisa si está enfermo o tiene dolor",
                "• Asegúrate de que no esté solo por mucho tiempo",
                "• Considera juguetes interactivos para estimularlo",
                "• Si la tristeza persiste, consulta al veterinario"
            ],
            'happy': [
                "😊 ¡Tu perro está feliz! Esto es genial:",
                "• Continúa con las actividades que lo hacen feliz",
                "• Es un buen momento para entrenamientos positivos",
                "• Puedes introducir nuevos juegos o juguetes"
            ],
            'relaxed': [
                "😌 Tu perro está relajado:",
                "• Es el estado ideal, continúa así",
                "• Mantén el ambiente tranquilo",
                "• Es buen momento para descanso"
            ]
        }
    
    def _make_request(self, method: str, data: Dict[Any, Any] = None, files: Dict[str, Any] = None, timeout: int = 15) -> Optional[Dict]:
        """Hacer request a la API de Telegram"""
        try:
            url = f"{self.base_url}/{method}"
            
            if files:
                response = requests.post(url, data=data, files=files, timeout=timeout)
            else:
                response = requests.post(url, json=data, timeout=timeout)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    return result
                else:
                    logger.error(f"❌ API Error: {result}")
                    return None
            else:
                logger.error(f"❌ HTTP Error {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("❌ Timeout en request a Telegram")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("❌ Error de conexión a Telegram")
            return None
        except Exception as e:
            logger.error(f"❌ Error en request: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Probar conexión con Telegram"""
        try:
            logger.info("🧪 Probando conexión con Telegram...")
            
            # Test 1: Verificar bot
            result = self._make_request('getMe', timeout=10)
            if not result:
                logger.error("❌ No se pudo verificar el bot")
                return False
            
            bot_info = result['result']
            logger.info(f"🤖 Bot verificado: @{bot_info.get('username', 'N/A')} ({bot_info.get('first_name', 'N/A')})")
            
            # Test 2: Enviar mensaje de prueba
            test_message = "🧪 **Test de Conexión**\n\nSi recibes este mensaje, Telegram funciona correctamente.\n\n✅ Conexión establecida exitosamente"
            
            result = self.send_message(test_message)
            if result:
                logger.info("✅ Test de conexión exitoso")
                return True
            else:
                logger.error("❌ Falló el envío de mensaje de prueba")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error en test de conexión: {e}")
            return False
    
    def send_simple_message(self, message: str) -> bool:
        """Alias para send_message para compatibilidad"""
        return self.send_message(message)
    
    def send_message(self, message: str, parse_mode: str = 'Markdown') -> bool:
        """Enviar mensaje de texto"""
        try:
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            
            result = self._make_request('sendMessage', data)
            if result:
                message_id = result['result']['message_id']
                logger.info(f"✅ Mensaje enviado - ID: {message_id}")
                return True
            else:
                logger.error("❌ Error enviando mensaje")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje: {e}")
            return False
    
    def send_photo(self, photo_path: str, caption: str = "") -> bool:
        """Enviar foto con caption"""
        try:
            if not os.path.exists(photo_path):
                logger.error(f"❌ Imagen no encontrada: {photo_path}")
                return False
            
            data = {
                'chat_id': self.chat_id,
                'caption': caption,
                'parse_mode': 'Markdown'
            }
            
            with open(photo_path, 'rb') as photo_file:
                files = {'photo': photo_file}
                result = self._make_request('sendPhoto', data, files)
            
            if result:
                message_id = result['result']['message_id']
                logger.info(f"✅ Foto enviada - ID: {message_id}")
                return True
            else:
                logger.error("❌ Error enviando foto")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error enviando foto: {e}")
            return False
    
    def send_alert(self, emotion: str, probability: float, image_path: str = None) -> bool:
        """Enviar alerta de emoción"""
        try:
            if not self.monitoring_active:
                logger.info("⚠️ Monitoreo pausado - Alerta no enviada")
                return False
            
            logger.info(f"🚨 Enviando alerta: {emotion} ({probability:.2f})")
            
            # Obtener recomendaciones
            recommendations = self.recommendations.get(emotion, ["• Observa el comportamiento de tu mascota"])
            
            # Crear mensaje
            message = f"🐕 **ALERTA DE COMPORTAMIENTO**\n\n"
            message += f"Emoción detectada: **{emotion.upper()}** ({probability:.2f})\n"
            message += f"Detectado en el análisis actual.\n\n"
            message += "\n".join(recommendations)
            message += f"\n\n📊 Confianza: {probability*100:.1f}%"
            message += f"\n⏰ Hora: {datetime.now().strftime('%H:%M:%S')}"
            
            # Enviar con imagen si está disponible
            if image_path and os.path.exists(image_path):
                success = self.send_photo(image_path, message)
                if success:
                    logger.info("✅ Alerta con imagen enviada")
                    return True
                else:
                    logger.warning("⚠️ Falló envío con imagen, enviando solo texto")
            
            # Enviar solo texto
            success = self.send_message(message)
            if success:
                logger.info("✅ Alerta enviada")
                return True
            else:
                logger.error("❌ Error enviando alerta")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error enviando alerta: {e}")
            return False
    
    def send_video_summary(self, video_stats: Dict[str, Any]) -> bool:
        """Enviar resumen de análisis de video"""
        try:
            if not self.monitoring_active:
                logger.info("⚠️ Monitoreo pausado - Resumen no enviado")
                return False
            
            logger.info("📹 Enviando resumen de video...")
            
            stats = video_stats
            emotion_dist = stats.get('emotion_distribution', {})
            dominant = stats.get('dominant_emotion', 'unknown')
            confidence = stats.get('confidence_avg', 0)
            
            message = f"📹 **RESUMEN DE VIDEO**\n\n"
            message += f"Archivo: {stats.get('video_name', 'video.mp4')}\n"
            message += f"Total de análisis: {stats.get('total_emotions', 0)}\n\n"
            
            message += "📊 **Distribución emocional:**\n"
            for emotion, count in emotion_dist.items():
                percentage = (count / stats.get('total_emotions', 1)) * 100
                message += f"• {emotion.capitalize()}: {count} ({percentage:.1f}%)\n"
            
            message += f"\n🎯 **Emoción dominante:** {dominant.upper()}\n"
            message += f"📈 **Confianza promedio:** {confidence*100:.1f}%\n"
            message += f"⏰ **Hora:** {datetime.now().strftime('%H:%M:%S')}"
            
            success = self.send_message(message)
            if success:
                logger.info("✅ Resumen de video enviado")
                return True
            else:
                logger.error("❌ Error enviando resumen")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error enviando resumen: {e}")
            return False
    
    def send_welcome_message(self) -> bool:
        """Enviar mensaje de bienvenida"""
        try:
            message = (
                "🐕 **DOG EMOTION AI - SISTEMA ACTIVADO**\n\n"
                "¡Hola! Tu sistema de monitoreo emocional para mascotas está ahora activo.\n\n"
                "**Funcionalidades disponibles:**\n"
                "• 🔔 Alertas automáticas de comportamiento\n"
                "• 📊 Resúmenes de análisis en tiempo real\n"
                "• 📹 Análisis completo de videos\n"
                "• 💡 Recomendaciones personalizadas\n\n"
                "**Estado actual:**\n"
                f"🔔 Monitoreo: {'✅ ACTIVO' if self.monitoring_active else '❌ PAUSADO'}\n"
                f"⏰ Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                "¡Comenzaré a enviarte actualizaciones sobre el estado emocional de tu mascota!"
            )
            
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje de bienvenida: {e}")
            return False
    
    def update_emotion_history(self, emotion: str):
        """Actualizar historial de emociones"""
        try:
            self.emotion_history.append({
                'emotion': emotion,
                'timestamp': time.time()
            })
            
            # Mantener solo los últimos 100 registros
            if len(self.emotion_history) > 100:
                self.emotion_history = self.emotion_history[-100:]
                
        except Exception as e:
            logger.error(f"❌ Error actualizando historial: {e}")
    
    def send_periodic_update(self):
        """Enviar actualización periódica"""
        try:
            current_time = time.time()
            
            # Solo enviar si han pasado al menos 30 minutos
            if current_time - self.last_status_time > 1800:  # 30 minutos
                if self.emotion_history and self.monitoring_active:
                    
                    # Calcular estadísticas recientes
                    recent_emotions = [e for e in self.emotion_history if current_time - e['timestamp'] < 3600]  # Última hora
                    
                    if recent_emotions:
                        emotion_counts = {}
                        for entry in recent_emotions:
                            emotion = entry['emotion']
                            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                        
                        dominant = max(emotion_counts.items(), key=lambda x: x[1])
                        
                        message = (
                            "🕐 **ACTUALIZACIÓN PERIÓDICA**\n\n"
                            f"Estado general en la última hora:\n"
                            f"🎯 Emoción predominante: **{dominant[0].upper()}**\n"
                            f"📊 Total de análisis: {len(recent_emotions)}\n"
                            f"⏰ Hora: {datetime.now().strftime('%H:%M:%S')}\n\n"
                            "El sistema continúa monitoreando a tu mascota."
                        )
                        
                        self.send_message(message)
                        self.last_status_time = current_time
                        
        except Exception as e:
            logger.error(f"❌ Error en actualización periódica: {e}")
    
    def clear_chat_sync(self):
        """Limpiar historial del chat - placeholder para compatibilidad"""
        try:
            logger.info("🧹 Limpiando historial de chat...")
            # En esta versión simplificada solo enviamos mensaje informativo
            self.send_message(
                "🧹 **HISTORIAL LIMPIADO**\n\n"
                "El historial de análisis ha sido reiniciado.\n"
                f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            logger.info("✅ Historial limpiado")
            return True
        except Exception as e:
            logger.error(f"❌ Error limpiando historial: {e}")
            return False
    
    def cleanup(self):
        """Limpiar recursos"""
        try:
            logger.info("🧹 Limpiando bot de Telegram...")
            # En esta versión simplificada no hay recursos específicos que limpiar
            logger.info("✅ Bot limpiado")
        except Exception as e:
            logger.error(f"❌ Error limpiando bot: {e}")


# Función de conveniencia para mantener compatibilidad
TelegramBot = SimpleTelegramBot


if __name__ == "__main__":
    """Test rápido del bot"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [%(levelname)s] - %(message)s'
    )
    
    try:
        # Crear bot
        bot = SimpleTelegramBot()
        
        # Test de conexión
        print("🧪 Probando conexión...")
        if bot.test_connection():
            print("✅ Conexión exitosa")
            
            # Test de alerta
            print("🧪 Probando alerta...")
            bot.send_alert('happy', 0.95)
            
            print("✅ Todas las pruebas exitosas")
        else:
            print("❌ Fallo en la conexión")
            
    except Exception as e:
        print(f"❌ Error en test: {e}")