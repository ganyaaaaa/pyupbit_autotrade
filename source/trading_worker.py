import time
import pyupbit
import pandas as pd
from PyQt5.QtCore import QThread, pyqtSignal


class TradingWorker(QThread):
    """자동매매 실행 (특정 조건 충족 시 매수)"""
    log_signal = pyqtSignal(str)
    chart_signal = pyqtSignal(pd.DataFrame, float, float, float, float)

    def __init__(self, ticker, budget, upbit):
        super().__init__()
        self.ticker = ticker
        self.budget = budget
        self.upbit = upbit
        self.running = True

    def run(self):
        """자동매매 실행 (특정 조건 충족 시 매수)"""
        try:
            balance = self.upbit.get_balance("KRW")
            self.log_signal.emit(f"💰 현재 원화 잔고: {balance}원")

            while self.running:
                df = pyupbit.get_ohlcv(self.ticker, interval="minute5")  # 5분봉 데이터 가져오기
                df['EMA5'] = df['close'].ewm(span=5, adjust=False).mean()  # 5분봉 EMA(5) 계산

                current_price = pyupbit.get_orderbook(self.ticker)["orderbook_units"][0]["ask_price"]
                ema5 = df['EMA5'].iloc[-1]

                self.log_signal.emit(f"📊 현재 가격: {current_price}원 | EMA(5): {ema5}원")

                if current_price > ema5:  # 조건: 현재 가격이 EMA(5)보다 높으면 매수
                    self.log_signal.emit(f"✅ 매수 조건 충족! {self.ticker} 시장가 매수 진행")
                    order = self.upbit.buy_market_order(self.ticker, self.budget)
                    self.log_signal.emit(f"🛠 매수 응답: {order}")

                    coin_balance = self.upbit.get_balance(self.ticker)
                    krw_balance = self.upbit.get_balance("KRW")
                    self.log_signal.emit(f"🪙 {self.ticker} 보유량: {coin_balance}, 남은 원화 잔고: {krw_balance}원")

                    bought_price = current_price
                    target_sell_price = bought_price * 1.03
                    stop_loss_price = bought_price * 0.985

                    # 매도 감시 루프 시작
                    while self.running:
                        current_price = pyupbit.get_orderbook(self.ticker)["orderbook_units"][0]["ask_price"]

                        df = pyupbit.get_ohlcv(self.ticker, interval="minute1")
                        self.chart_signal.emit(df, current_price, bought_price, target_sell_price, stop_loss_price)

                        if current_price >= target_sell_price:
                            order = self.upbit.sell_market_order(self.ticker, coin_balance)
                            self.log_signal.emit(f"✅ 3% 수익 매도 완료! 가격: {current_price}원")
                            return

                        if current_price <= stop_loss_price:
                            order = self.upbit.sell_market_order(self.ticker, coin_balance)
                            self.log_signal.emit(f"❌ 1.5% 손절 매도 완료! 가격: {current_price}원")
                            return

                        time.sleep(1)

                time.sleep(5)  # 5초 후 다시 확인

        except Exception as e:
            self.log_signal.emit(f"⚠️ 에러 발생: {e}")

    def stop(self):
        """자동매매 중지"""
        self.running = False
