import requests
import logging

logger = logging.getLogger(__name__)

def test_connection_fixed(token, chat_id):
    """Versión corregida del test de conexión usando requests directamente"""
    try:
        logger.info("🧪 Iniciando test de conexión corregido...")
        
        import time
        
        # Test básico con API de Telegram
        start_time = time.time()
        
        # Verificar bot con getMe
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"❌ Error verificando bot: {response.status_code}")
            logger.error(f"❌ Respuesta: {response.text}")
            return False
        
        bot_info = response.json()
        if not bot_info.get('ok'):
            logger.error(f"❌ Bot no válido: {bot_info}")
            return False
        
        bot_data = bot_info['result']
        verification_time = time.time() - start_time
        logger.info(f"🤖 Bot encontrado: @{bot_data.get('username', 'N/A')} ({bot_data.get('first_name', 'N/A')}) - {verification_time:.2f}s")
        
        # Test de envío de mensaje
        start_time = time.time()
        test_message = "🧪 **Test de Conexión Corregido**\n\nSi recibes este mensaje, Telegram funciona correctamente.\n\n✅ Conexión restablecida"
        
        send_url = f"https://api.telegram.org/bot{token}/sendMessage"
        send_data = {
            'chat_id': chat_id,
            'text': test_message,
            'parse_mode': 'Markdown'
        }
        
        send_response = requests.post(send_url, json=send_data, timeout=15)
        send_time = time.time() - start_time
        
        if send_response.status_code == 200:
            result = send_response.json()
            if result.get('ok'):
                message_id = result['result']['message_id']
                logger.info(f"✅ Test de Telegram exitoso - Mensaje ID: {message_id} - {send_time:.2f}s")
                return True
            else:
                logger.error(f"❌ Error enviando mensaje: {result}")
                return False
        else:
            logger.error(f"❌ Error HTTP enviando mensaje: {send_response.status_code}")
            logger.error(f"❌ Respuesta: {send_response.text}")
            return False
        
    except requests.exceptions.Timeout:
        logger.error("❌ Test de Telegram falló: Timeout de conexión")
        return False
    except requests.exceptions.ConnectionError:
        logger.error("❌ Test de Telegram falló: Error de conexión a internet")
        return False
    except Exception as e:
        logger.error(f"❌ Test de Telegram falló: {e}")
        logger.error(f"❌ Tipo de error: {type(e).__name__}")
        return False


def send_simple_message_fixed(token, chat_id, message):
    """Envía un mensaje simple usando requests directamente"""
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=data, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                logger.info(f"✅ Mensaje enviado - ID: {result['result']['message_id']}")
                return True
            else:
                logger.error(f"❌ Error en respuesta: {result}")
                return False
        else:
            logger.error(f"❌ Error HTTP: {response.status_code}")
            logger.error(f"❌ Respuesta: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje: {e}")
        return False


def send_alert_fixed(token, chat_id, emotion, probability, image_path=None):
    """Envía una alerta usando requests directamente"""
    try:
        logger.info(f"🚨 Enviando alerta: {emotion} ({probability:.2f})")
        
        # Recomendaciones por emoción
        recommendations = {
            'angry': [
                "🚨 Tu perro parece molesto. Aquí algunas recomendaciones:",
                "• Revisa si hay ruidos fuertes que lo estresen",
                "• Verifica que tenga agua fresca y comida",
                "• Dale un espacio tranquilo para calmarse"
            ],
            'sad': [
                "😢 Tu perro se ve triste. Te sugerimos:",
                "• Dedícale tiempo de calidad y caricias",
                "• Sácalo a pasear si es posible",
                "• Revisa si está enfermo o tiene dolor"
            ],
            'happy': [
                "😊 ¡Tu perro está feliz! Esto es genial:",
                "• Continúa con las actividades que lo hacen feliz",
                "• Es un buen momento para entrenamientos positivos"
            ],
            'relaxed': [
                "😌 Tu perro está relajado:",
                "• Es el estado ideal, continúa así",
                "• Mantén el ambiente tranquilo"
            ]
        }
        
        emotion_recs = recommendations.get(emotion, ["• Observa el comportamiento de tu mascota"])
        
        # Crear mensaje
        from datetime import datetime
        message = f"🐕 **ALERTA DE COMPORTAMIENTO**\n\n"
        message += f"Emoción detectada: **{emotion.upper()}** ({probability:.2f})\n"
        message += f"Detectado en el análisis actual.\n\n"
        message += "\n".join(emotion_recs)
        message += f"\n\n📊 Confianza: {probability*100:.1f}%"
        message += f"\n⏰ Hora: {datetime.now().strftime('%H:%M:%S')}"
        
        return send_simple_message_fixed(token, chat_id, message)
        
    except Exception as e:
        logger.error(f"❌ Error enviando alerta: {e}")
        return False


if __name__ == "__main__":
    # Test rápido
    TOKEN = "7668982184:AAEXrM7xx0bDKidNOhyi6xjSNYUNRpvu61U"
    CHAT_ID = "1673887715"
    
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Probando conexión corregida...")
    success = test_connection_fixed(TOKEN, CHAT_ID)
    print(f"Resultado: {'✅ ÉXITO' if success else '❌ FALLO'}")