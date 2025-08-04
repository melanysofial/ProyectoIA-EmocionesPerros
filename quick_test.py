#!/usr/bin/env python3
"""Prueba rápida de conexión con tus credenciales"""

import requests
import time

# TUS CREDENCIALES
TOKEN = "7565394500:AAEqYMlT4mQFGTlL8slsSrlrst3MZmeMzIg"
CHAT_ID = "1846987938"

print("🧪 PRUEBA RÁPIDA DE TELEGRAM")
print(f"Token: {TOKEN[:20]}...")
print(f"Chat ID: {CHAT_ID}")
print("-" * 40)

# Test 1: Verificar bot
print("1️⃣ Verificando bot...")
url = f"https://api.telegram.org/bot{TOKEN}/getMe"
response = requests.get(url, timeout=10)

if response.status_code == 200:
    data = response.json()
    if data['ok']:
        bot_info = data['result']
        print(f"✅ Bot: @{bot_info['username']} ({bot_info['first_name']})")
    else:
        print(f"❌ Error: {data}")
else:
    print(f"❌ HTTP {response.status_code}: {response.text}")

# Test 2: Enviar mensaje
print("\n2️⃣ Enviando mensaje de prueba...")
message = "🐕 **DOG EMOTION AI**\n\n✅ Conexión establecida correctamente con tus credenciales!\n\nEl sistema está listo para funcionar."

send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
send_data = {
    'chat_id': CHAT_ID,
    'text': message,
    'parse_mode': 'Markdown'
}

send_response = requests.post(send_url, json=send_data, timeout=15)

if send_response.status_code == 200:
    result = send_response.json()
    if result['ok']:
        print(f"✅ Mensaje enviado - ID: {result['result']['message_id']}")
        print("🎉 TODO FUNCIONA CORRECTAMENTE!")
    else:
        print(f"❌ Error: {result}")
else:
    print(f"❌ HTTP {send_response.status_code}: {send_response.text}")

print("\n✨ Ahora puedes ejecutar 'python main.py' con confianza")