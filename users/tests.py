import hashlib


def generate_signature():
    """
    Генерация подписи для проверки вебхуков.
    """
    txn_id = '6789577a0c83e016f90577a2'
    source_amount = '0.00001006'
    source_currency = 'USD'
    secret_key = 'RZTKyvsBkD_5dIkelHp3xMyRWwNSqXnm_MfxqR20NCY6LK6hoi7T8gVPTBJwgRko'

    # Формируем строку для подписи в порядке Plisio
    verification_string = f"{txn_id}:{source_amount}:{source_currency}:{secret_key}"


    # Генерация HMAC с использованием SHA-1
    signature = hashlib.sha1(verification_string.encode()).hexdigest()


    return signature

print(generate_signature())