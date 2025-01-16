import hashlib
import hmac
import urllib.parse

def verify_callback_data(post_data, secret_key):
    if 'verify_hash' not in post_data:
        return False

    # Извлекаем verify_hash
    verify_hash = post_data['verify_hash']
    del post_data['verify_hash']  # Убираем verify_hash из данных

    # Сортируем данные по ключам
    sorted_post_data = {k: post_data[k] for k in sorted(post_data.keys())}

    # Преобразуем некоторые поля в строки
    if 'expire_utc' in sorted_post_data:
        sorted_post_data['expire_utc'] = str(sorted_post_data['expire_utc'])

    if 'tx_urls' in sorted_post_data:
        sorted_post_data['tx_urls'] = urllib.parse.unquote(sorted_post_data['tx_urls'])

    # Сериализация данных
    post_string = str(sorted_post_data)

    # Генерация подписи с помощью HMAC-SHA1
    check_key = hmac.new(secret_key.encode(), post_string.encode(), hashlib.sha1).hexdigest()

    # Сравниваем с полученной подписью
    if check_key != verify_hash:
        return False

    return True
