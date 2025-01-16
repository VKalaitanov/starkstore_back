import hashlib

txn_id = '67894caa099a68b62b003625'
source_amount = '50.00'
source_currency = 'USD'
status = 'complited'  # Статус платежа
secret_key = 'RZTKyvsBkD_5dIkelHp3xMyRWwNSqXnm_MfxqR20NCY6LK6hoi7T8gVPTBJwgRko'

# Попробуем включить статус в подпись
verification_string = f"{txn_id}{source_amount}{source_currency}{status}{secret_key}"
generated_hash = hashlib.sha1(verification_string.encode()).hexdigest()
print(f"Generated Hash: {generated_hash}")