import yfinance as yf
import matplotlib.pyplot as plt
import ta

# 분석할 종목
ticker = "satl"

# 데이터 가져오기
stock = yf.Ticker(ticker)
data = stock.history(period="6mo")

# 지표 계산
data["MA5"] = data["Close"].rolling(5).mean()
data["MA20"] = data["Close"].rolling(20).mean()
data["RSI"] = ta.momentum.RSIIndicator(data["Close"]).rsi()

macd = ta.trend.MACD(data["Close"])
data["MACD"] = macd.macd()
data["MACD_signal"] = macd.macd_signal()

bb = ta.volatility.BollingerBands(data["Close"])
data["BB_upper"] = bb.bollinger_hband()
data["BB_lower"] = bb.bollinger_lband()

data["VOL_MA"] = data["Volume"].rolling(20).mean()

# 매수/매도 신호 판단
data["signal"] = ""
for i in range(1, len(data)):
    buy_score = 0
    sell_score = 0

    if data["MA5"].iloc[i] > data["MA20"].iloc[i] and data["MA5"].iloc[i-1] <= data["MA20"].iloc[i-1]:
        buy_score += 1
    if data["MA5"].iloc[i] < data["MA20"].iloc[i] and data["MA5"].iloc[i-1] >= data["MA20"].iloc[i-1]:
        sell_score += 1

    if data["RSI"].iloc[i] < 30:
        buy_score += 1
    if data["RSI"].iloc[i] > 70:
        sell_score += 1

    if data["MACD"].iloc[i] > data["MACD_signal"].iloc[i] and data["MACD"].iloc[i-1] <= data["MACD_signal"].iloc[i-1]:
        buy_score += 1
    if data["MACD"].iloc[i] < data["MACD_signal"].iloc[i] and data["MACD"].iloc[i-1] >= data["MACD_signal"].iloc[i-1]:
        sell_score += 1

    if data["Close"].iloc[i] < data["BB_lower"].iloc[i]:
        buy_score += 1
    if data["Close"].iloc[i] > data["BB_upper"].iloc[i]:
        sell_score += 1

    if data["Volume"].iloc[i] > data["VOL_MA"].iloc[i] * 2:
        if data["Close"].iloc[i] > data["Close"].iloc[i-1]:
            buy_score += 1
        else:
            sell_score += 1

    if buy_score >= 2:
        data.loc[data.index[i], "signal"] = "BUY"
    elif sell_score >= 2:
        data.loc[data.index[i], "signal"] = "SELL"

# 차트
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), gridspec_kw={'height_ratios': [3, 1]})

ax1.plot(data.index, data["Close"], label="Price", color="black", linewidth=1.5)
ax1.plot(data.index, data["MA5"], label="MA5", color="blue", linewidth=1)
ax1.plot(data.index, data["MA20"], label="MA20", color="orange", linewidth=1)
ax1.plot(data.index, data["BB_upper"], label="BB Upper", color="gray", linestyle="--", linewidth=0.8)
ax1.plot(data.index, data["BB_lower"], label="BB Lower", color="gray", linestyle="--", linewidth=0.8)

buy_signals = data[data["signal"] == "BUY"]
sell_signals = data[data["signal"] == "SELL"]
ax1.scatter(buy_signals.index, buy_signals["Close"], marker="^", color="red", s=100, zorder=5, label="BUY")
ax1.scatter(sell_signals.index, sell_signals["Close"], marker="v", color="blue", s=100, zorder=5, label="SELL")

ax1.set_title(f"{ticker} Analysis Chart")
ax1.set_ylabel("Price ($)")
ax1.legend(loc="upper left")
ax1.grid(True, alpha=0.3)

ax2.plot(data.index, data["RSI"], color="purple", linewidth=1)
ax2.axhline(70, color="red", linestyle="--", linewidth=0.8)
ax2.axhline(30, color="blue", linestyle="--", linewidth=0.8)
ax2.fill_between(data.index, data["RSI"], 70, where=(data["RSI"] >= 70), color="red", alpha=0.3)
ax2.fill_between(data.index, data["RSI"], 30, where=(data["RSI"] <= 30), color="blue", alpha=0.3)
ax2.set_title("RSI")
ax2.set_ylabel("RSI")
ax2.set_ylim(0, 100)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# 최근 신호 출력
print(f"\n=== {ticker} Recent Signals ===")
signals = data[data["signal"] != ""].tail(5)
for i, row in signals.iterrows():
    print(f"{i.date()} | {row['signal']} | Price: ${row['Close']:.2f}")