import requests
import time
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Конфиг ---
BLOCKCHAIN_API_URL = "https://api.blockchair.com/bitcoin/transactions"
CHECK_INTERVAL = 60  # секунд между проверками
THRESHOLD_USD = 1_000_000  # Сумма транзакции для оповещения
EXCHANGE_RATE_API = "https://api.coindesk.com/v1/bpi/currentprice/USD.json"

def get_btc_usd_rate():
    """Получить текущий курс BTC/USD"""
    try:
        resp = requests.get(EXCHANGE_RATE_API, timeout=5)
        data = resp.json()
        return float(data["bpi"]["USD"]["rate"].replace(",", ""))
    except Exception as e:
        logging.error(f"Ошибка получения курса BTC/USD: {e}")
        return None

def get_recent_transactions():
    """Получить последние транзакции в сети Биткоин"""
    try:
        resp = requests.get(BLOCKCHAIN_API_URL, timeout=5)
        data = resp.json()
        return data.get("data", [])
    except Exception as e:
        logging.error(f"Ошибка получения транзакций: {e}")
        return []

def filter_large_transactions(transactions, btc_usd_rate):
    """Отфильтровать транзакции больше порога"""
    large_tx = []
    for tx in transactions:
        total_btc = sum([out["value"] for out in tx.get("outputs", [])]) / 1e8
        total_usd = total_btc * btc_usd_rate
        if total_usd >= THRESHOLD_USD:
            large_tx.append({
                "hash": tx.get("hash"),
                "btc": total_btc,
                "usd": total_usd,
                "time": tx.get("time")
            })
    return large_tx

def notify_large_transaction(tx):
    """Выводит информацию о крупной транзакции"""
    logging.info(
        f"🐋 Обнаружена крупная транзакция!\n"
        f"Hash: {tx['hash']}\n"
        f"Сумма: {tx['btc']:.4f} BTC (~${tx['usd']:,.2f})\n"
        f"Время: {tx['time']}"
    )

def run_watcher():
    """Запуск основного цикла наблюдателя"""
    logging.info("🚀 Запуск Whale Watcher...")
    while True:
        rate = get_btc_usd_rate()
        if rate:
            txs = get_recent_transactions()
            large_txs = filter_large_transactions(txs, rate)
            for tx in large_txs:
                notify_large_transaction(tx)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run_watcher()
