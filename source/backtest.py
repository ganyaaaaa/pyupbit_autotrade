import pyupbit
import pandas as pd

def backtest(ticker, k=0.5):
    """변동성 돌파 전략 백테스팅"""
    df = pyupbit.get_ohlcv(ticker, interval="day")
    df["range"] = df["high"] - df["low"]
    df["target"] = df["open"] + df["range"] * k

    df["buy"] = df["close"] > df["target"]
    df["sell"] = df["close"] < df["open"]

    df["returns"] = df["close"].pct_change() * df["buy"]
    df["cumulative"] = (1 + df["returns"]).cumprod()

    return df[["close", "target", "buy", "sell", "cumulative"]]

if __name__ == "__main__":
    result = backtest("KRW-BTC", k=0.5)
    print(result.tail())  # 최근 5일간 결과 출력
