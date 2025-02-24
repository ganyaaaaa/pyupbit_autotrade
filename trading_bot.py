import sys
import time
import pyupbit
import sqlite3
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from source.main import Ui_MainWindow  # UI 코드 불러오기

# 🔹 Matplotlib 한글 폰트 설정 (Mac 환경에서는 'AppleGothic', 윈도우에서는 'Malgun Gothic')
plt.rcParams['font.family'] = 'AppleGothic'  # Mac용 폰트 설정

class TradingWorker(QThread):
    """자동매매 실행 (계속 반복)"""
    log_signal = pyqtSignal(str)
    chart_signal = pyqtSignal(pd.DataFrame)

    def __init__(self, ticker, budget, upbit):
        super().__init__()
        self.ticker = ticker
        self.budget = budget
        self.upbit = upbit
        self.running = True

    def run(self):
        """자동매매 지속 실행"""
        while self.running:
            try:
                # ✅ 현재 가격 가져오기
                current_price = pyupbit.get_orderbook(self.ticker)["orderbook_units"][0]["ask_price"]
                target_price = self.get_target_price(self.ticker)
                ema = self.get_ema(self.ticker)

                self.log_signal.emit(f"현재가: {current_price}, 목표가: {target_price}, EMA: {ema}")

                # ✅ 실시간 차트 데이터 가져오기
                df = pyupbit.get_ohlcv(self.ticker, interval="minute1")
                self.chart_signal.emit(df)  # UI 스레드에 데이터 전달

                # ✅ 매수 조건: 목표가 돌파 & 현재 가격이 EMA 위에 있을 때
                if current_price > target_price and current_price > ema:
                    balance = self.budget / current_price
                    order = self.upbit.buy_market_order(self.ticker, self.budget)
                    self.log_signal.emit(f"💰 매수 완료! 가격: {current_price}원")

                    # ✅ 매수 가격 저장
                    bought_price = current_price

                    # ✅ 매도 조건: 3% 수익 or 1.5% 손실
                    target_sell_price = bought_price * 1.03  # 3% 수익
                    stop_loss_price = bought_price * 0.985  # 1.5% 손실

                    # 매도 감시
                    while self.running:
                        current_price = pyupbit.get_orderbook(self.ticker)["orderbook_units"][0]["ask_price"]

                        if current_price >= target_sell_price:
                            order = self.upbit.sell_market_order(self.ticker, balance)
                            self.log_signal.emit(f"✅ 3% 수익 매도 완료! 가격: {current_price}원")
                            break

                        if current_price <= stop_loss_price:
                            order = self.upbit.sell_market_order(self.ticker, balance)
                            self.log_signal.emit(f"❌ 1.5% 손절 매도 완료! 가격: {current_price}원")
                            break

                        time.sleep(1)

                # ✅ 매도 후 다시 새로운 매수 기회 탐색
                self.log_signal.emit("🔄 다음 매매 기회를 찾는 중...")
                time.sleep(10)  # 10초 후 다시 조건 확인

            except Exception as e:
                self.log_signal.emit(f"⚠️ 에러 발생: {e}")

    def get_target_price(self, ticker, k=0.5):
        """변동성 돌파 전략: 목표 매수가 계산"""
        df = pyupbit.get_ohlcv(ticker, interval="day")
        yesterday = df.iloc[-2]
        today_open = df.iloc[-1]['open']
        return today_open + (yesterday['high'] - yesterday['low']) * k

    def get_ema(self, ticker, period=20):
        """EMA(지수 이동 평균) 계산"""
        df = pyupbit.get_ohlcv(ticker, interval="day")
        return df['close'].ewm(span=period).mean().iloc[-1]

    def stop(self):
        """자동매매 중지"""
        self.running = False


class CryptoTradingBot(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # 업비트 API 키
        self.access_key = "YOUR_ACCESS_KEY"
        self.secret_key = "YOUR_SECRET_KEY"
        self.upbit = pyupbit.Upbit(self.access_key, self.secret_key)

        # 기본 매매 설정
        self.ticker = "KRW-BTC"
        self.budget = 10000

        # Matplotlib 그래프 추가
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)

        # 기존 레이아웃 가져오거나 새로 추가
        layout = self.centralwidget.layout()
        if layout is None:
            layout = QVBoxLayout(self.centralwidget)
            self.centralwidget.setLayout(layout)

        layout.addWidget(self.canvas)

        # 버튼 이벤트 연결
        self.start_btn.clicked.connect(self.start_trading)
        self.stop_btn.clicked.connect(self.stop_trading)

        self.worker = None

    def log(self, message):
        """로그 출력"""
        self.log_text.append(message)
        self.log_text.ensureCursorVisible()

    def update_chart(self, df):
        """실시간 차트 업데이트"""
        self.ax.clear()
        self.ax.plot(df.index, df['close'], label="가격")
        self.ax.legend()
        self.canvas.draw()

    def start_trading(self):
        """자동매매 시작"""
        self.ticker = self.input_ticker.text()
        self.budget = float(self.input_budget.text())

        self.worker = TradingWorker(self.ticker, self.budget, self.upbit)
        self.worker.log_signal.connect(self.log)
        self.worker.chart_signal.connect(self.update_chart)  # 차트 업데이트 연결
        self.worker.start()
        self.log("🚀 자동매매 시작!")

    def stop_trading(self):
        """자동매매 정지"""
        if self.worker:
            self.worker.stop()
            self.worker.quit()
            self.worker.wait()
        self.log("🛑 자동매매 중지됨.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    bot = CryptoTradingBot()
    bot.show()
    sys.exit(app.exec_())
