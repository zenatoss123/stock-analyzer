import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta

st.set_page_config(page_title="Stock Signal Analyzer", layout="wide")
st.title("📈 Stock Signal Analyzer")

ticker = st.text_input("Enter Ticker Symbol", value="TSLA").upper()
period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y"], index=2)

if st.button("Analyze"):
    with st.spinner("Fetching data..."):
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)

        if data.empty:
            st.error("No data found. Check the ticker symbol.")
        else:
            # 지표 계산
            data["MA5"] = data["Close"].rolling(5).mean()
            data["MA20"] = data["Close"].rolling(20).mean()
            data["RSI"] = ta.momentum.RSIIndicator(data["Close"]).rsi()

            macd = ta.trend.MACD(data["Close"])
            data["MACD"] = macd.macd()
            data["MACD_signal"] = macd.macd_signal()
            data["MACD_hist"] = macd.macd_diff()

            bb = ta.volatility.BollingerBands(data["Close"])
            data["BB_upper"] = bb.bollinger_hband()
            data["BB_lower"] = bb.bollinger_lband()

            data["OBV"] = ta.volume.OnBalanceVolumeIndicator(data["Close"], data["Volume"]).on_balance_volume()
            data["Williams_R"] = ta.momentum.WilliamsRIndicator(data["High"], data["Low"], data["Close"]).williams_r()

            stoch = ta.momentum.StochasticOscillator(data["High"], data["Low"], data["Close"])
            data["Stoch_K"] = stoch.stoch()
            data["Stoch_D"] = stoch.stoch_signal()

            data["VOL_MA"] = data["Volume"].rolling(20).mean()

            # 신호 판단
            data["signal"] = ""
            data["buy_score"] = 0
            data["sell_score"] = 0

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

                if data["Williams_R"].iloc[i] < -80:
                    buy_score += 1
                if data["Williams_R"].iloc[i] > -20:
                    sell_score += 1

                if data["Stoch_K"].iloc[i] < 20 and data["Stoch_K"].iloc[i] > data["Stoch_D"].iloc[i]:
                    buy_score += 1
                if data["Stoch_K"].iloc[i] > 80 and data["Stoch_K"].iloc[i] < data["Stoch_D"].iloc[i]:
                    sell_score += 1

                if data["OBV"].iloc[i] > data["OBV"].iloc[i-1]:
                    buy_score += 1
                else:
                    sell_score += 1

                if data["Volume"].iloc[i] > data["VOL_MA"].iloc[i] * 2:
                    if data["Close"].iloc[i] > data["Close"].iloc[i-1]:
                        buy_score += 1
                    else:
                        sell_score += 1

                data.loc[data.index[i], "buy_score"] = buy_score
                data.loc[data.index[i], "sell_score"] = sell_score

                if buy_score >= 3:
                    data.loc[data.index[i], "signal"] = "BUY"
                elif sell_score >= 3:
                    data.loc[data.index[i], "signal"] = "SELL"

            # 차트
            fig = make_subplots(
                rows=5, cols=1,
                shared_xaxes=True,
                row_heights=[0.4, 0.15, 0.15, 0.15, 0.15],
                vertical_spacing=0.03,
                subplot_titles=(f"{ticker} Price", "MACD", "RSI", "Williams %R / Stochastic", "OBV")
            )

            fig.add_trace(go.Scatter(x=data.index, y=data["BB_upper"], name="BB Upper", line=dict(color="lightgray", dash="dash", width=0.8), showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data["BB_lower"], name="BB Lower", line=dict(color="lightgray", dash="dash", width=0.8), fill="tonexty", fillcolor="rgba(200,200,200,0.1)", showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data["Close"], name="Price", line=dict(color="black", width=1.5)), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data["MA5"], name="MA5", line=dict(color="blue", width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data["MA20"], name="MA20", line=dict(color="orange", width=1)), row=1, col=1)

            buy_data = data[data["signal"] == "BUY"]
            sell_data = data[data["signal"] == "SELL"]
            fig.add_trace(go.Scatter(x=buy_data.index, y=buy_data["Close"], mode="markers", name="BUY", marker=dict(symbol="triangle-up", size=14, color="red")), row=1, col=1)
            fig.add_trace(go.Scatter(x=sell_data.index, y=sell_data["Close"], mode="markers", name="SELL", marker=dict(symbol="triangle-down", size=14, color="blue")), row=1, col=1)

            colors = ["green" if v >= 0 else "red" for v in data["MACD_hist"]]
            fig.add_trace(go.Bar(x=data.index, y=data["MACD_hist"], name="MACD Hist", marker_color=colors, showlegend=False), row=2, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data["MACD"], name="MACD", line=dict(color="blue", width=1)), row=2, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data["MACD_signal"], name="Signal", line=dict(color="orange", width=1)), row=2, col=1)

            fig.add_trace(go.Scatter(x=data.index, y=data["RSI"], name="RSI", line=dict(color="purple", width=1)), row=3, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="blue", row=3, col=1)

            fig.add_trace(go.Scatter(x=data.index, y=data["Williams_R"], name="Williams %R", line=dict(color="brown", width=1)), row=4, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data["Stoch_K"], name="Stoch K", line=dict(color="green", width=1)), row=4, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data["Stoch_D"], name="Stoch D", line=dict(color="red", width=1, dash="dash")), row=4, col=1)

            fig.add_trace(go.Scatter(x=data.index, y=data["OBV"], name="OBV", line=dict(color="teal", width=1)), row=5, col=1)

            fig.update_layout(height=1000, title=f"{ticker} Full Analysis", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # 최근 신호 테이블
            st.subheader("Recent Signals")
            signals = data[data["signal"] != ""][["Close", "signal", "buy_score", "sell_score"]].tail(10)
            if signals.empty:
                st.info("No signals found. Try a longer period!")
            else:
                st.dataframe(signals)

            # 현재 지표 요약
            st.subheader("Current Indicators")
            latest = data.iloc[-1]
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("RSI", f"{latest['RSI']:.1f}", delta="Oversold" if latest['RSI'] < 30 else ("Overbought" if latest['RSI'] > 70 else "Normal"))
            col2.metric("Williams %R", f"{latest['Williams_R']:.1f}")
            col3.metric("Stoch K", f"{latest['Stoch_K']:.1f}")
            col4.metric("MACD", f"{latest['MACD']:.2f}")