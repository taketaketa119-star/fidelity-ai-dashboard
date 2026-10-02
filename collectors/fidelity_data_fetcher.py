import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

@dataclass
class StockData:
    ticker: str
    company_name: str
    sector: str
    price: float
    change_pct: float
    market_cap_b: float        # 時価総額 (十億ドル B$)
    pe_ratio: float           # PER
    pb_ratio: float           # PBR
    roe: float                # ROE (%)
    profit_margin: float      # 営業利益率 (%)
    revenue_growth: float     # 売上成長率 (%)
    dividend_yield: float     # 配当利回り (%)
    weight_pct: float         # ファンド推定組み入れ比率 (%)
    history_df: pd.DataFrame  # 株価履歴

class FidelityDataFetcher:
    """
    フィデリティ米国株ファンド主要構成銘柄および関連グローバル銘柄のデータコレクター
    """

    # フィデリティ米国株ファンドの主要組み入れ上位銘柄リスト
    DEFAULT_HOLDINGS = {
        'MSFT': {'name': 'Microsoft Corp', 'sector': 'Information Technology', 'weight': 9.2},
        'AAPL': {'name': 'Apple Inc', 'sector': 'Information Technology', 'weight': 8.5},
        'NVDA': {'name': 'NVIDIA Corp', 'sector': 'Information Technology', 'weight': 7.8},
        'AMZN': {'name': 'Amazon.com Inc', 'sector': 'Consumer Discretionary', 'weight': 6.1},
        'GOOGL': {'name': 'Alphabet Inc (Google)', 'sector': 'Communication Services', 'weight': 5.4},
        'META': {'name': 'Meta Platforms Inc', 'sector': 'Communication Services', 'weight': 4.8},
        'AVGO': {'name': 'Broadcom Inc', 'sector': 'Information Technology', 'weight': 3.5},
        'LLY': {'name': 'Eli Lilly and Co', 'sector': 'Health Care', 'weight': 3.1},
        'BRK-B': {'name': 'Berkshire Hathaway Inc', 'sector': 'Financials', 'weight': 2.9},
        'JPM': {'name': 'JPMorgan Chase & Co', 'sector': 'Financials', 'weight': 2.5},
        'WMT': {'name': 'Walmart Inc', 'sector': 'Consumer Staples', 'weight': 2.1},
        'COST': {'name': 'Costco Wholesale Corp', 'sector': 'Consumer Staples', 'weight': 1.9},
        'V': {'name': 'Visa Inc', 'sector': 'Financials', 'weight': 1.8},
        'TSLA': {'name': 'Tesla Inc', 'sector': 'Consumer Discretionary', 'weight': 1.7},
    }

    def __init__(self):
        pass

    def fetch_all_holdings_data(self) -> List[StockData]:
        """
        全構成銘柄のリアルタイムデータおよび財務データを一括取得
        """
        results = []
        for ticker, meta in FidelityDataFetcher.DEFAULT_HOLDINGS.items():
            stock_data = FidelityDataFetcher.fetch_single_stock(ticker, meta)
            results.append(stock_data)
        return results

    @staticmethod
    def fetch_single_stock(ticker: str, meta: dict = None) -> StockData:
        """
        個別銘柄のデータ取得
        """
        if meta is None:
            meta = FidelityDataFetcher.DEFAULT_HOLDINGS.get(
                ticker, {'name': ticker, 'sector': 'Technology/Other', 'weight': 1.0}
            )

        try:
            t = yf.Ticker(ticker)
            info = t.info or {}
            hist = t.history(period="1y")

            if hist.empty:
                return FidelityDataFetcher._generate_fallback_stock(ticker, meta)

            price = float(info.get('currentPrice') or info.get('regularMarketPrice') or hist['Close'].iloc[-1])
            prev_price = float(hist['Close'].iloc[-2]) if len(hist) > 1 else price
            change_pct = ((price - prev_price) / prev_price) * 100.0

            market_cap_b = float(info.get('marketCap') or 1e11) / 1e9
            pe = float(info.get('trailingPE') or info.get('forwardPE') or 25.0)
            pb = float(info.get('priceToBook') or 5.0)
            roe = float(info.get('returnOnEquity') or 0.20) * 100.0
            margin = float(info.get('operatingMargins') or info.get('profitMargins') or 0.22) * 100.0
            rev_growth = float(info.get('revenueGrowth') or 0.12) * 100.0
            div_yield = float(info.get('dividendYield') or 0.01) * 100.0

            hist_df = hist.reset_index()
            hist_df.columns = [c.lower() for c in hist_df.columns]

            return StockData(
                ticker=ticker,
                company_name=meta['name'],
                sector=meta['sector'],
                price=round(price, 2),
                change_pct=round(change_pct, 2),
                market_cap_b=round(market_cap_b, 1),
                pe_ratio=round(pe, 1),
                pb_ratio=round(pb, 1),
                roe=round(roe, 1),
                profit_margin=round(margin, 1),
                revenue_growth=round(rev_growth, 1),
                dividend_yield=round(div_yield, 2),
                weight_pct=meta['weight'],
                history_df=hist_df
            )
        except Exception as e:
            print(f"yfinance fetch error for {ticker}: {e}")
            return FidelityDataFetcher._generate_fallback_stock(ticker, meta)

    @staticmethod
    def _generate_fallback_stock(ticker: str, meta: dict) -> StockData:
        """
        フォールバック用の疑似銘柄データ
        """
        end_date = datetime.now()
        dates = [end_date - timedelta(days=i) for i in range(365, -1, -1)]
        np.random.seed(abs(hash(ticker)) % 1000)
        
        base_price = 200.0
        returns = np.random.normal(0.0005, 0.015, len(dates))
        prices = base_price * np.exp(np.cumsum(returns))
        
        hist_df = pd.DataFrame({
            'date': dates,
            'open': prices * 0.995,
            'high': prices * 1.01,
            'low': prices * 0.99,
            'close': prices,
            'volume': np.random.randint(1000000, 50000000, len(dates))
        })

        return StockData(
            ticker=ticker,
            company_name=meta['name'],
            sector=meta['sector'],
            price=round(float(prices[-1]), 2),
            change_pct=round(float(np.random.normal(0.5, 1.2)), 2),
            market_cap_b=round(float(np.random.uniform(200, 3000)), 1),
            pe_ratio=round(float(np.random.uniform(18, 45)), 1),
            pb_ratio=round(float(np.random.uniform(3, 15)), 1),
            roe=round(float(np.random.uniform(15, 45)), 1),
            profit_margin=round(float(np.random.uniform(15, 35)), 1),
            revenue_growth=round(float(np.random.uniform(5, 30)), 1),
            dividend_yield=round(float(np.random.uniform(0.0, 2.5)), 2),
            weight_pct=meta['weight'],
            history_df=hist_df
        )

    @staticmethod
    def fetch_benchmark_index_history() -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        ベンチマーク比較用の S&P500 (SPY) および NASDAQ100 (QQQ) データ取得
        """
        try:
            spy = yf.Ticker("SPY").history(period="1y").reset_index()
            qqq = yf.Ticker("QQQ").history(period="1y").reset_index()
            spy.columns = [c.lower() for c in spy.columns]
            qqq.columns = [c.lower() for c in qqq.columns]
            return spy, qqq
        except Exception as e:
            print(f"yfinance benchmark error: {e}")
            # Fallback
            dates = [datetime.now() - timedelta(days=i) for i in range(365, -1, -1)]
            np.random.seed(101)
            p_spy = 500.0 * np.exp(np.cumsum(np.random.normal(0.0004, 0.008, len(dates))))
            p_qqq = 450.0 * np.exp(np.cumsum(np.random.normal(0.0006, 0.012, len(dates))))
            df_spy = pd.DataFrame({'date': dates, 'close': p_spy})
            df_qqq = pd.DataFrame({'date': dates, 'close': p_qqq})
            return df_spy, df_qqq
