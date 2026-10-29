"""
Downloads historical prices and calculates the basic statistics quants look at first:
returns, volatility, drawdown, Sharpe ratio, and correlations.
"""

import argparse
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf

TRADING_DAYS = 252  # amount trading days in a year


def load_prices(tickers, years):
    data = yf.download(tickers, period=f"{years}y", auto_adjust=True, progress=False)
    prices = data["Close"]
    if isinstance(prices, pd.Series):  # single ticker comes back as a Series
        prices = prices.to_frame(name=tickers[0])
    return prices.dropna(how="all").ffill().dropna()


def daily_returns(prices):
    return prices.pct_change().dropna()

def annualized_return(returns):
    total_growth = (1 + returns).prod()
    return total_growth ** (TRADING_DAYS / len(returns)) - 1

def annualized_volatility(returns):
    return returns.std() * np.sqrt(TRADING_DAYS)

def sharpe_ratio(returns, risk_free=0.0):
    return (annualized_return(returns) - risk_free) / annualized_volatility(returns)

def drawdown(prices):
    running_peak = prices.cummax()
    return prices / running_peak - 1

def summary_table(prices):
    rets = daily_returns(prices)
    return pd.DataFrame({
        "Ann. Return": annualized_return(rets),
        "Ann. Volatility": annualized_volatility(rets),
        "Sharpe": sharpe_ratio(rets),
        "Max Drawdown": drawdown(prices).min(),
    })


def plot_dashboard(prices):
    rets = daily_returns(prices)
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))

    # Growth of $1, so stocks with different price levels are comparable
    (prices / prices.iloc[0]).plot(ax=axes[0, 0], title="Growth of $1")
    axes[0, 0].set_ylabel("Multiple of starting value")

    # Rolling 30-day volatility, annualized
    rolling_vol = rets.rolling(30).std() * np.sqrt(TRADING_DAYS)
    rolling_vol.plot(ax=axes[0, 1], title="Rolling 30-Day Volatility (annualized)")

    # Drawdowns
    drawdown(prices).plot(ax=axes[1, 0], title="Drawdown from Peak")
    axes[1, 0].set_ylabel("Drawdown")

    # Correlation heatmap (only meaningful with 2+ tickers)
    ax = axes[1, 1]
    if prices.shape[1] > 1:
        corr = rets.corr()
        im = ax.imshow(corr, vmin=-1, vmax=1, cmap="coolwarm")
        ax.set_xticks(range(len(corr)), corr.columns, rotation=45)
        ax.set_yticks(range(len(corr)), corr.columns)
        for i in range(len(corr)):
            for j in range(len(corr)):
                ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center")
        fig.colorbar(im, ax=ax)
        ax.set_title("Return Correlations")
    else:
        ax.text(0.5, 0.5, "Add 2+ tickers\nto see correlations", ha="center", va="center")
        ax.axis("off")

    plt.tight_layout()
    plt.show()

def main():
    parser = argparse.ArgumentParser(description="Simple stock data explorer")
    parser.add_argument("tickers", nargs="*", help="e.g. AVGO, NVDA, AAOI")
    parser.add_argument("--years", type=int, default=None, help="years of history")
    args = parser.parse_args()

    # Ask for tickers if none were passed on the command line
    if args.tickers:
        tickers = [t.upper() for t in args.tickers]
    else:
        raw = input("Enter tickers separated by spaces or commas (e.g. AAPL MSFT NVDA): ")
        tickers = [t.strip().upper() for t in raw.replace(",", " ").split()]
        if not tickers:
            print("No tickers entered.")
            return

    # Ask for years if not already passed
    if args.years is None:
        raw_years = input("How many years of history? [default 5]: ").strip()
        years = int(raw_years) if raw_years.isdigit() else 5
    else:
        years = args.years

    prices = load_prices(tickers, years)

    print(f"\nLoaded {len(prices)} trading days: "
          f"{prices.index[0].date()} to {prices.index[-1].date()}\n")
    print(summary_table(prices).to_string(float_format=lambda x: f"{x:.3f}"))

    plot_dashboard(prices)


if __name__ == "__main__":
    main()
