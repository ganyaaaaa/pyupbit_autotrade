import pyupbit
import pandas as pd

def backtest(ticker, k=0.5):
    """변동성 돌파 전략 백테스팅"""
    df = pyupbit.get_ohlcv(ticker, interval="day")
    df["range"] = df["high"] - df["low"]
    df["target"] = df["open"] + df["range"] * k

    df["buy"] = df["high"] > df["target"]  # 🔹 고가 기준으로 목표가 돌파 여부 확인
    df["take_profit"] = df["high"] >= df["target"] * 1.03  # 3% 익절
    df["stop_loss"] = df["low"] <= df["target"] * 0.985  # 1.5% 손절
    df["sell"] = df["take_profit"] | df["stop_loss"]

    df["returns"] = df["close"].pct_change() * df["buy"]
    df["cumulative"] = (1 + df["returns"]).cumprod()

    return df[["close", "target", "buy", "sell", "cumulative"]]

if __name__ == "__main__":
    result = backtest("KRW-BTC", k=0.5)
    print(result.tail())  # 최근 5일간 결과 출력
