from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from collectors.fidelity_data_fetcher import StockData

@dataclass
class AIScoreResult:
    stock: StockData
    total_score: float          # 0 - 100
    growth_score: float         # 0 - 25
    profitability_score: float  # 0 - 25
    moat_score: float           # 0 - 25
    valuation_score: float      # 0 - 25
    barbell_type: str           # 🚀 AI・メガテック成長株 vs 🛡️ キャッシュフロー・ディフェンシブ株
    ai_rating: str              # 🟢 Strong Buy / 🟢 Buy / 🟡 Hold / 🔴 Caution
    key_strengths: List[str]    # 強み
    risk_factors: List[str]     # リスク要因
    ai_summary: str             # AI要約コメント

class FidelityAIEngine:
    """
    元フィデリティ ポール・サイ氏のフレームワークに基づく AI スコアリング＆銘柄分析エンジン
    """

    # 各セクター/銘柄の推定 Moat (競合優位性) 定義
    MOAT_SCORES = {
        'MSFT': (24.0, "OS・クラウド(Azure)・Officeの強力なロックインとAI独占権"),
        'AAPL': (24.5, "Appleエコシステム・ブランド力・圧倒的ハードウェア粗利"),
        'NVDA': (24.8, "CUDAエコシステムとAI半導体・GPUマーケットシェア90%以上"),
        'AMZN': (23.5, "AWSのクラウドシェア首位と物流ネットワークの圧倒的規模"),
        'GOOGL': (23.8, "検索・YouTube・Androidのグローバルインフラ・AI研究開発"),
        'META': (22.5, "Instagram・WhatsApp・Facebookの30億人ネットワーク効果"),
        'AVGO': (22.0, "通信・AIアクセラレータ向けカスタムカスタムチップの独占的ポジション"),
        'LLY': (24.0, "GLP-1肥満症薬・新薬パイプラインの特許障壁と爆発的成長"),
        'BRK-B': (23.0, "ウォーレン・バフェットの圧倒的資本力・保険フロート・分散ポートフォリオ"),
        'JPM': (22.5, "米国最大手メガバンクの資本効率・金利環境・預金基盤"),
        'WMT': (21.5, "全米最大の小売店舗網・価格支配力・EC成長"),
        'COST': (23.0, "会員制ビジネスモデルの異常に高い顧客維持率(90%以上)と粗利率"),
        'V': (24.2, "世界最大の決済ネットワーク・限界費用ゼロの決済インフラ"),
        'TSLA': (21.0, "EVシェア・自動運転(FSD)データ・スーパーチャージャー網"),
    }

    @staticmethod
    def evaluate_stock(stock: StockData) -> AIScoreResult:
        """
        1銘柄のAIスコア算出および分析
        """
        # 1. 成長性スコア (0-25)
        rev_g = stock.revenue_growth
        if rev_g >= 25.0:
            growth_score = 25.0
        elif rev_g >= 15.0:
            growth_score = 20.0 + (rev_g - 15.0) * 0.5
        elif rev_g >= 5.0:
            growth_score = 12.0 + (rev_g - 5.0) * 0.8
        elif rev_g >= 0:
            growth_score = 8.0 + rev_g * 0.8
        else:
            growth_score = max(0.0, 8.0 + rev_g * 0.5)

        # 2. 収益性スコア (0-25)
        roe = stock.roe
        margin = stock.profit_margin
        profitability_score = min(12.5, max(0.0, roe * 0.4)) + min(12.5, max(0.0, margin * 0.4))

        # 3. Moat (競合優位性) スコア (0-25)
        moat_info = FidelityAIEngine.MOAT_SCORES.get(
            stock.ticker, (20.0, "確固たる事業基盤と業界優位性")
        )
        moat_score = moat_info[0]
        moat_desc = moat_info[1]

        # 4. バリュエーション/効率性スコア (0-25)
        pe = stock.pe_ratio
        if pe <= 0:
            val_score = 5.0
        elif pe < 20.0:
            val_score = 25.0
        elif pe < 35.0:
            val_score = 25.0 - (pe - 20.0) * 0.6
        elif pe < 60.0:
            val_score = 16.0 - (pe - 35.0) * 0.3
        else:
            val_score = max(5.0, 8.5 - (pe - 60.0) * 0.1)

        total_score = round(growth_score + profitability_score + moat_score + val_score, 1)

        # AI シグナル判定
        if total_score >= 80.0:
            ai_rating = "🟢 Strong Buy"
        elif total_score >= 70.0:
            ai_rating = "🟢 Buy"
        elif total_score >= 58.0:
            ai_rating = "🟡 Hold"
        else:
            ai_rating = "🔴 Caution"

        # ポール・サイ式 バーベル分類
        if stock.sector in ['Information Technology', 'Communication Services'] or rev_g > 15.0:
            barbell_type = "🚀 AI・メガテック成長株 (Growth)"
        else:
            barbell_type = "🛡️ キャッシュフロー・ディフェンシブ株 (Value/Defensive)"

        # 強み & リスク要因
        strengths = []
        if roe > 25.0: strengths.append(f"高い資本効率 (ROE: {roe:.1f}%)")
        if margin > 20.0: strengths.append(f"強固な営業利益率 ({margin:.1f}%)")
        if rev_g > 12.0: strengths.append(f"高成長モメンタム (売上増率: {rev_g:.1f}%)")
        strengths.append(f"Moat要因: {moat_desc}")

        risks = []
        if pe > 35.0: risks.append(f"バリュエーション高値警戒 (PER: {pe:.1f}倍)")
        if rev_g < 3.0: risks.append(f"売上成長の鈍化 (売上増率: {rev_g:.1f}%)")
        if stock.dividend_yield == 0: risks.append("無配によるインカム保護なし")

        # AI 要約文
        ai_summary = (
            f"【AIスコア: {total_score}/100 | {ai_rating}】\n"
            f"{stock.company_name} ({stock.ticker}) は【{barbell_type}】に分類されます。"
            f"ROE {roe:.1f}% と営業利益率 {margin:.1f}% により業界トップクラスの収益性を維持。"
            f"{moat_desc}。バリュエーション（PER {pe:.1f}倍）とのバランスを考慮した保有が推奨されます。"
        )

        return AIScoreResult(
            stock=stock,
            total_score=total_score,
            growth_score=round(growth_score, 1),
            profitability_score=round(profitability_score, 1),
            moat_score=round(moat_score, 1),
            valuation_score=round(val_score, 1),
            barbell_type=barbell_type,
            ai_rating=ai_rating,
            key_strengths=strengths,
            risk_factors=risks,
            ai_summary=ai_summary
        )

    @staticmethod
    def evaluate_all(stocks: List[StockData]) -> List[AIScoreResult]:
        """
        全銘柄のAI評価を実行しスコア順にソート
        """
        results = [FidelityAIEngine.evaluate_stock(s) for s in stocks]
        results.sort(key=lambda x: -x.total_score)
        return results
