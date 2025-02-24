import sys
import time
import pyupbit
import sqlite3
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal
from dotenv import load_dotenv
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from source.main import Ui_MainWindow  # UI 코드 불러오기
import os
from PyQt5.QtWidgets import QLabel
from PyQt5 import QtCore

# 🔹 Matplotlib 한글 폰트 설정 (Mac 환경에서는 'AppleGothic', 윈도우에서는 'Malgun Gothic')
plt.rcParams['font.family'] = 'Malgun Gothic'  # Mac용 폰트 설정

class TradingWorker(QThread):
    """자동매매 실행 (즉시 매수 후 매도 감시)"""
    log_signal = pyqtSignal(str)
    chart_signal = pyqtSignal(pd.DataFrame, float, float, float, float)  # ✅ 매수/매도가 추가

    def __init__(self, ticker, budget, upbit):
        super().__init__()
        self.ticker = ticker
        self.budget = budget
        self.upbit = upbit
        self.running = True  # ✅ 실행 상태 변수 추가

    def run(self):
        """자동매매 즉시 실행"""
        try:
            balance = self.upbit.get_balance("KRW")  # 현재 원화 잔고 조회
            self.log_signal.emit(f"💰 현재 원화 잔고: {balance}원")

            # ✅ 현재 가격 가져오기
            current_price = pyupbit.get_orderbook(self.ticker)["orderbook_units"][0]["ask_price"]

            # ✅ 즉시 매수 실행
            order = self.upbit.buy_market_order(self.ticker, self.budget)
            self.log_signal.emit(f"🛠 매수 응답: {order}")

            # ✅ 매수 후 잔고 확인
            coin_balance = self.upbit.get_balance(self.ticker)
            krw_balance = self.upbit.get_balance("KRW")
            self.log_signal.emit(f"🪙 현재 {self.ticker} 보유량: {coin_balance}, 남은 원화 잔고: {krw_balance}원")

            bought_price = current_price
            target_sell_price = bought_price * 1.03
            stop_loss_price = bought_price * 0.985

            while self.running:
                current_price = pyupbit.get_orderbook(self.ticker)["orderbook_units"][0]["ask_price"]

                # ✅ 실시간 차트 + 현재 가격 업데이트
                df = pyupbit.get_ohlcv(self.ticker, interval="minute1")
                self.chart_signal.emit(df, current_price, bought_price, target_sell_price, stop_loss_price)

                if current_price >= target_sell_price:
                    order = self.upbit.sell_market_order(self.ticker, coin_balance)
                    self.log_signal.emit(f"✅ 3% 수익 매도 완료! 가격: {current_price}원")
                    break

                if current_price <= stop_loss_price:
                    order = self.upbit.sell_market_order(self.ticker, coin_balance)
                    self.log_signal.emit(f"❌ 1.5% 손절 매도 완료! 가격: {current_price}원")
                    break

                time.sleep(1)

        except Exception as e:
            self.log_signal.emit(f"⚠️ 에러 발생: {e}")


    def stop(self):
        """자동매매 중지"""
        self.running = False

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
        load_dotenv()
        self.access_key = os.getenv("ACCESS_KEY")
        self.secret_key = os.getenv("PRIVATE_KEY")
        self.upbit = pyupbit.Upbit(self.access_key, self.secret_key)

        # 기본 매매 설정
        self.ticker = "KRW-BTC"
        self.budget = 10000

        # Matplotlib 그래프 추가
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)

        # ✅ 현재 가격 표시할 QLabel 추가
        self.price_label = QLabel("현재 가격: - 원", self)
        self.price_label.setAlignment(QtCore.Qt.AlignRight)

        # ✅ 매수 가격 및 목표 매도가격 QLabel 추가
        self.buy_price_label = QLabel("매수가격: - 원", self)
        self.sell_target_label = QLabel("목표 매도가격 (3% 수익): - 원", self)
        self.stop_loss_label = QLabel("목표 매도가격 (1.5% 손절): - 원", self)

        # 기존 레이아웃 가져오거나 새로 추가
        layout = self.centralwidget.layout()
        if layout is None:
            layout = QVBoxLayout(self.centralwidget)
            self.centralwidget.setLayout(layout)

        # ✅ 그래프 위에 현재 가격 & 매매 정보 QLabel 추가
        layout.addWidget(self.price_label)
        layout.addWidget(self.buy_price_label)
        layout.addWidget(self.sell_target_label)
        layout.addWidget(self.stop_loss_label)
        layout.addWidget(self.canvas)

        # 버튼 이벤트 연결
        self.start_btn.clicked.connect(self.start_trading)
        self.stop_btn.clicked.connect(self.stop_trading)

        self.worker = None

    def log(self, message):
        """로그 출력"""
        self.log_text.append(message)
        self.log_text.ensureCursorVisible()

    def update_chart(self, df, price, buy_price=None, target_price=None, stop_loss_price=None):
        """실시간 차트 업데이트 + 현재 가격 및 매매 정보 표시"""
        self.ax.clear()
        self.ax.plot(df.index, df['close'], label="가격")
        self.ax.legend()
        self.canvas.draw()

        # ✅ 현재 가격 업데이트
        self.price_label.setText(f"현재 가격: {price:,.0f} 원")

        # ✅ 매수가, 목표가, 손절가 업데이트
        if buy_price:
            self.buy_price_label.setText(f"매수가격: {buy_price:,.0f} 원")
        if target_price:
            self.sell_target_label.setText(f"목표 매도가격 (3% 수익): {target_price:,.0f} 원")
        if stop_loss_price:
            self.stop_loss_label.setText(f"목표 매도가격 (1.5% 손절): {stop_loss_price:,.0f} 원")

    def start_trading(self):
        """자동매매 시작"""
        self.ticker = self.input_ticker.text()
        self.budget = float(self.input_budget.text())

        self.worker = TradingWorker(self.ticker, self.budget, self.upbit)
        self.worker.log_signal.connect(self.log)
        self.worker.chart_signal.connect(self.update_chart)  # ✅ 차트 & 가격 업데이트 연결
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
