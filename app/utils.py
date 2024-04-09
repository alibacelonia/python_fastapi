from passlib.context import CryptContext
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.hazmat.backends import default_backend
from base64 import b64encode
import os

def encrypt(key, plaintext):
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    padder = PKCS7(128).padder()
    padded_plaintext = padder.update(plaintext.encode("utf-8")) + padder.finalize()

    ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()
    return b64encode(iv + ciphertext).decode("utf-8")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)


# currency_data.py

def get_currency():
    currency_data = [
        {"Country": "Australia", "Currency": "Dollar", "Code": "AUD", "Symbol": "$"},
        {"Country": "Brazil", "Currency": "Real", "Code": "BRL", "Symbol": "R$"},
        {"Country": "Bulgaria", "Currency": "Lev", "Code": "BGN", "Symbol": "лв"},
        {"Country": "Canada", "Currency": "Dollar", "Code": "CAD", "Symbol": "$"},
        {"Country": "China", "Currency": "Yan Renmibi", "Code": "CNY", "Symbol": "¥"},
        {"Country": "Croatia", "Currency": "Kuna", "Code": "HRK", "Symbol": "kn"},
        {"Country": "Cyprus", "Currency": "Pound", "Code": "CYP", "Symbol": "£"},
        {"Country": "Czech Republic", "Currency": "Kroner", "Code": "CZK", "Symbol": "Kč"},
        {"Country": "Denmark", "Currency": "Kroner", "Code": "DKK", "Symbol": "kr"},
        {"Country": "Estonia", "Currency": "Kroon", "Code": "EEK", "Symbol": "kr"},
        {"Country": "Euro zone", "Currency": "Euro", "Code": "EUR", "Symbol": "€"},
        {"Country": "Hong Kong", "Currency": "Dollar", "Code": "HKD", "Symbol": "HK$"},
        {"Country": "Hungary", "Currency": "Forint", "Code": "HUF", "Symbol": "Ft"},
        {"Country": "Iceland", "Currency": "Króna", "Code": "ISK", "Symbol": "kr"},
        {"Country": "Indonesia", "Currency": "Rupiah", "Code": "IDR", "Symbol": "Rp"},
        {"Country": "Japan", "Currency": "Yen", "Code": "JPY", "Symbol": "¥"},
        {"Country": "Korea", "Currency": "Won", "Code": "KRW", "Symbol": "₩"},
        {"Country": "Latvia", "Currency": "Lats", "Code": "LVL", "Symbol": "Ls"},
        {"Country": "Lithuania", "Currency": "Litas", "Code": "LTL", "Symbol": "Lt"},
        {"Country": "Malaysia", "Currency": "Dollar (Ringgit)", "Code": "MYR", "Symbol": "RM"},
        {"Country": "Malta", "Currency": "Lire", "Code": "MTL", "Symbol": "₤"},
        {"Country": "New Zealand", "Currency": "Dollar", "Code": "NZD", "Symbol": "$"},
        {"Country": "Norway", "Currency": "Kroner", "Code": "NOK", "Symbol": "kr"},
        {"Country": "Philippines", "Currency": "Peso", "Code": "PHP", "Symbol": "₱"},
        {"Country": "Poland", "Currency": "Zloty", "Code": "PLN", "Symbol": "zł"},
        {"Country": "Romania", "Currency": "Leu", "Code": "RON", "Symbol": "lei"},
        {"Country": "Russia", "Currency": "Rubles", "Code": "RUB", "Symbol": "₽"},
        {"Country": "Singapore", "Currency": "Dollar", "Code": "SGD", "Symbol": "S$"},
        {"Country": "Slovakia", "Currency": "Kroner", "Code": "SKK", "Symbol": "Sk"},
        {"Country": "Slovenia", "Currency": "Tolar", "Code": "SIT", "Symbol": "SIT"},
        {"Country": "South Africa", "Currency": "Rand", "Code": "ZAR", "Symbol": "R"},
        {"Country": "Sweden", "Currency": "Kroner", "Code": "SEK", "Symbol": "kr"},
        {"Country": "Switzerland", "Currency": "Franc", "Code": "CHF", "Symbol": "CHF"},
        {"Country": "Thailand", "Currency": "Baht", "Code": "THB", "Symbol": "฿"},
        {"Country": "Turkey", "Currency": "Lire", "Code": "TRY", "Symbol": "₺"},
        {"Country": "United Kingdom", "Currency": "Pound", "Code": "GBP", "Symbol": "£"},
        {"Country": "USA", "Currency": "Dollar", "Code": "USD", "Symbol": "$"},
    ]

    return currency_data
