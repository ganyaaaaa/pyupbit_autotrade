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
from PyQt5.QtWidgets import QLabel, QMessageBox
from PyQt5 import QtCore
from source.backtest import backtest
from source.trading_worker import TradingWorker  # ✅ TradingWorker import

# 🔹 Matplotlib 한글 폰트 설정 (Mac 환경에서는 'AppleGothic', 윈도우에서는 'Malgun Gothic')
plt.rcParams['font.family'] = 'AppleGothic'  # Mac용 폰트 설정


class CryptoTradingBot(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # 업비트 API 키
        load_dotenv()
        self.access_key = os.getenv("ACCESS_KEY")
        self.secret_key = os.getenv("PRIVATE_KEY")
        self.upbit = pyupbit.Upbit(self.access_key, self.secret_key)

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

        # ✅ 여러 종목을 관리할 딕셔너리
        self.workers = {}

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
        """자동매매 시작 (여러 종목 지원)"""
        ticker = self.input_ticker.text()
        budget = float(self.input_budget.text())

        # ✅ 🔹 백테스트 실행
        self.log(f"📊 {ticker} 변동성 돌파 전략 백테스트 실행 중...")
        backtest_result = backtest(ticker, k=0.5)

        # ✅ 백테스트 마지막 누적 수익률 확인
        latest_cumulative = backtest_result["cumulative"].iloc[-1]
        self.log(f"📈 {ticker} 최근 백테스트 누적 수익률: {latest_cumulative:.4f}")

        # ✅ 수익률이 일정 이상이면 매매 진행 (예: 1.02 이상이면 매매 진행)
        if latest_cumulative >= 1.02:
            self.log(f"✅ {ticker} 백테스트 결과가 양호하여 자동매매를 시작합니다!")

            # ✅ 새로운 TradingWorker 생성 후 딕셔너리에 저장
            worker = TradingWorker(ticker, budget, self.upbit)
            worker.log_signal.connect(self.log)
            worker.chart_signal.connect(self.update_chart)

            self.workers[ticker] = worker  # 여러 종목을 관리할 수 있도록 딕셔너리에 저장
            worker.start()
        else:
            self.log(f"❌ {ticker} 백테스트 결과가 좋지 않아 자동매매를 취소합니다.")
            QMessageBox.warning(self, "자동매매 취소", f"{ticker} 백테스트 결과가 양호하지 않습니다. 매매를 취소합니다.")

    def stop_trading(self):
        """자동매매 정지 (여러 종목 지원)"""
        ticker = self.input_ticker.text()  # 중지할 종목 선택

        if ticker in self.workers:
            self.workers[ticker].stop()
            self.workers[ticker].quit()
            self.workers[ticker].wait()
            del self.workers[ticker]  # 종료된 종목 제거
            self.log(f"🛑 {ticker} 자동매매 중지됨.")
        else:
            self.log(f"⚠️ {ticker} 자동매매가 실행 중이 아닙니다.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    bot = CryptoTradingBot()
    bot.show()
    sys.exit(app.exec_())
