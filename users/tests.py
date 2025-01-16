import hashlib

txn_id = '67893e1e0ae97e06de014686'
source_amount = '50.00'
source_currency = 'USD'
secret_key = 'RZTKyvsBkD_5dIkelHp3xMyRWwNSqXnm_MfxqR20NCY6LK6hoi7T8gVPTBJwgRko'  # Заменить на свой ключ

# Формирование строки
verification_string = f"{txn_id}{source_amount}{source_currency}{secret_key}"

# Генерация хэша
generated_hash = hashlib.sha1(verification_string.encode()).hexdigest()
print(f"Generated Hash: {generated_hash}")