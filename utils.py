import base64
import time
import logging

import requests
import urllib3
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

KEY = 'ilyB29ZdruuQjC45JhBBR7o2Z8WJ26Vg'.encode()
IV = 'JUMxvVMmszqUTeKn'.encode()


def my_requester(method, **kwargs):
    retry_times = 3
    timeout = 5
    if 'timeout' in kwargs:
        timeout = kwargs.pop('timeout', 5)
    verify = False
    if 'verify' in kwargs:
        verify = kwargs.pop('verify', False)

    while retry_times > 0:
        try:
            resp = requests.request(method, timeout=timeout, verify=verify, **kwargs)
            resp.raise_for_status()
            return resp
        except Exception as e:
            retry_times -= 1
            time.sleep(0.5)
            logging.error(f'Request failed: {e}, retrying...')

    logging.error('Request failed after retrying')
    return None


def encrypt_data(data):
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    padded_data = pad(data.encode(), AES.block_size)
    return base64.b64encode(cipher.encrypt(padded_data))


def decrypt_data(encrypted_data):
    decipher = AES.new(KEY, AES.MODE_CBC, IV)
    decrypted_data = unpad(decipher.decrypt(base64.b64decode(encrypted_data)), AES.block_size)
    return decrypted_data.decode()
