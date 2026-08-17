# blockchain_client.py
import requests
import time
import json
from datetime import datetime, timedelta
import config

class BlockchainClient:
    def __init__(self):
        self.tronscan_api_key = config.TRONSCAN_API_KEY
        self.etherscan_api_key = config.ETHERSCAN_API_KEY
        self.bscscan_api_key = config.BSCSCAN_API_KEY
        
        # Contadores para rate limiting
        self.last_call_time = 0
        self.calls_today = 0
        self.last_reset_date = datetime.now().date()
        
        # Límites desde config
        self.max_calls_per_second = config.MAX_CALLS_PER_SECOND  # 5
        self.max_calls_per_day = config.MAX_CALLS_PER_DAY  # 100000

    def _rate_limit(self):
        """Aplica límite de 5 llamadas por segundo y 100,000 por día."""
        now = datetime.now()
        # Reset diario
        if now.date() != self.last_reset_date:
            self.calls_today = 0
            self.last_reset_date = now.date()
        
        # Verificar límite diario
        if self.calls_today >= self.max_calls_per_day:
            raise Exception(f"Límite diario de API ({self.max_calls_per_day}) alcanzado. Espera hasta mañana.")
        
        # Verificar límite por segundo
        elapsed = time.time() - self.last_call_time
        if elapsed < (1.0 / self.max_calls_per_second):
            time.sleep((1.0 / self.max_calls_per_second) - elapsed + 0.05)  # +0.05 de margen
        
        self.last_call_time = time.time()
        self.calls_today += 1

    # =====================================================
    # TRONSCAN (TRC20, TRX, USDT)
    # =====================================================
    def get_trx_account_info(self, address):
        """Obtiene saldo de TRX y USDT (TRC20) de una dirección."""
        self._rate_limit()
        url = f"https://api.tronscan.org/api/account?address={address}"
        headers = {"TRON-PRO-API-KEY": self.tronscan_api_key}
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                # Extraer saldo TRX y tokens
                balance_trx = data.get('balance', 0) / 1_000_000  # TRX tiene 6 decimales
                tokens = data.get('trc20token_balances', [])
                usdt_balance = 0
                for token in tokens:
                    if token.get('symbol') == 'USDT':
                        usdt_balance = int(token.get('balance', 0)) / 1_000_000
                return {
                    'address': address,
                    'trx_balance': balance_trx,
                    'usdt_balance': usdt_balance,
                    'total_volume': data.get('total_volume', 0) / 1_000_000,
                    'tx_count': data.get('total_tx', 0)
                }
        except Exception as e:
            print(f"⚠️ Error consultando Tronscan: {e}")
        return None

    def get_trx_transactions(self, address, limit=20):
        """Obtiene las últimas transacciones de una dirección."""
        self._rate_limit()
        url = f"https://api.tronscan.org/api/transaction?address={address}&limit={limit}"
        headers = {"TRON-PRO-API-KEY": self.tronscan_api_key}
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('data', [])
        except Exception as e:
            print(f"⚠️ Error obteniendo transacciones: {e}")
        return []

    # =====================================================
    # ETHERSCAN (Ethereum)
    # =====================================================
    def get_eth_balance(self, address):
        """Obtiene saldo de ETH de una dirección."""
        self._rate_limit()
        url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={self.etherscan_api_key}"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('status') == '1':
                    balance_wei = int(data.get('result', 0))
                    return balance_wei / 1_000_000_000_000_000_000  # Wei → ETH
        except Exception as e:
            print(f"⚠️ Error consultando Etherscan: {e}")
        return None

    # =====================================================
    # BSCSCAN (Binance Smart Chain)
    # =====================================================
    def get_bsc_balance(self, address):
        """Obtiene saldo de BNB de una dirección."""
        self._rate_limit()
        url = f"https://api.bscscan.com/api?module=account&action=balance&address={address}&tag=latest&apikey={self.bscscan_api_key}"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('status') == '1':
                    balance_wei = int(data.get('result', 0))
                    return balance_wei / 1_000_000_000_000_000_000  # Wei → BNB
        except Exception as e:
            print(f"⚠️ Error consultando BscScan: {e}")
        return None

    # =====================================================
    # DETECCIÓN DE PATRONES DE LAVADO (Heurística básica)
    # =====================================================
    def detect_laundering_patterns(self, address, transactions):
        """Analiza transacciones para detectar patrones de lavado."""
        patterns = []
        
        if not transactions:
            return patterns
        
        # 1. Spreading: muchas salidas pequeñas desde una sola entrada grande
        inflows = [tx for tx in transactions if tx.get('to') == address]  # recibidos
        outflows = [tx for tx in transactions if tx.get('from') == address]  # enviados
        
        if len(inflows) == 1 and len(outflows) > 10:
            # Una sola entrada grande, muchas salidas pequeñas
            total_in = sum(float(tx.get('amount', 0)) for tx in inflows)
            avg_out = sum(float(tx.get('amount', 0)) for tx in outflows) / len(outflows) if outflows else 0
            if avg_out < total_in * 0.1:  # cada salida es <10% de la entrada
                patterns.append("SPREADING: Una gran entrada dividida en muchas salidas pequeñas (pitufeo).")
        
        # 2. Consolidation: muchas entradas, una sola salida grande
        if len(inflows) > 10 and len(outflows) == 1:
            total_in = sum(float(tx.get('amount', 0)) for tx in inflows)
            total_out = sum(float(tx.get('amount', 0)) for tx in outflows)
            if total_out > total_in * 0.9:  # casi todo sale en una transacción
                patterns.append("CONSOLIDATION: Múltiples entradas convergen en una única salida (cuenta concentradora).")
        
        # 3. Dusting: transacciones de montos muy pequeños (ej. 0.0001 TRX)
        dust_txs = [tx for tx in transactions if float(tx.get('amount', 0)) < 0.001]
        if len(dust_txs) > 5:
            patterns.append(f"DUSTING: {len(dust_txs)} transacciones de montos muy pequeños (posible enmascaramiento).")
        
        return patterns

    # =====================================================
    # FUNCIÓN MAESTRA: analizar una dirección completa
    # =====================================================
    def analyze_address(self, address, blockchain='tron'):
        """
        Analiza una dirección de blockchain y devuelve un resumen con:
        - Balance
        - Volumen total
        - Últimas transacciones
        - Patrones de lavado
        """
        result = {
            'address': address,
            'blockchain': blockchain,
            'balance': None,
            'total_volume': None,
            'tx_count': None,
            'transactions': [],
            'patterns': [],
            'timestamp': datetime.now().isoformat()
        }
        
        if blockchain.lower() == 'tron':
            info = self.get_trx_account_info(address)
            if info:
                result['balance'] = info.get('trx_balance', 0)
                result['total_volume'] = info.get('total_volume', 0)
                result['tx_count'] = info.get('tx_count', 0)
                # Obtener transacciones para patrones
                txs = self.get_trx_transactions(address, limit=50)
                result['transactions'] = txs
                result['patterns'] = self.detect_laundering_patterns(address, txs)
        elif blockchain.lower() == 'ethereum':
            balance = self.get_eth_balance(address)
            if balance is not None:
                result['balance'] = balance
                # Etherscan no da transacciones fácilmente sin otra API, dejamos solo balance
        elif blockchain.lower() == 'bsc':
            balance = self.get_bsc_balance(address)
            if balance is not None:
                result['balance'] = balance
        
        return result
