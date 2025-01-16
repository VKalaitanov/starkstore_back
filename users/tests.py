import hmac
import hashlib
import json
api_key = 'RZTKyvsBkD_5dIkelHp3xMyRWwNSqXnm_MfxqR20NCY6LK6hoi7T8gVPTBJwgRko'

# Данные, которые отправляются в запросе
data = {
    "id": "6787f7a8086534820002acd8",
    "status": "completed"
}

# Сортируем данные и сериализуем в JSON
serialized_data = json.dumps(data, sort_keys=True).encode()

# Генерируем подпись
signature = hmac.new(
    api_key.encode(),
    msg=serialized_data,
    digestmod=hashlib.sha256
).hexdigest()

print(f"Signature: {signature}")



