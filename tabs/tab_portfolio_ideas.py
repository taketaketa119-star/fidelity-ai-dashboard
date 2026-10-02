import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from collectors.fidelity_data_fetcher import FidelityDataFetcher
from analyzers.fidelity_ai_engine import AIScoreResult

def render_portfolio_ideas_tab():
    st.markdown("### 💡 AIポートフォリオ＆売買アイデア")
    st.caption("AIスコアとポール・サイ式『バーベル戦略』に基づくユーザー目的別の最適ポートフォリオ提案")

    ai_results: list[AIScoreResult] = st.session_state.get('fidelity_ai_results', [])

    if not ai_results:
        fetcher = FidelityDataFetcher()
        stocks = fetcher.fetch_all_holdings_data()
        ai_results = FidelityAIEngine.evaluate_all(stocks)
        st.session_state['fidelity_ai_results'] = ai_results

    # ── 1. ポートフォリオ戦略モデルの選択 ──
    st.markdown("##### 🎯 あなたの投資目標を選択してください")
    
    col_str1, col_str2, col_str3 = st.columns(3)
    
    with col_str1:
        st.markdown(
            "<div style='border:2px solid #00c853;padding:16px;border-radius:8px;background:rgba(0,200,83,0.05);'>"
            "<h4>🚀 積極成長型 (Aggressive)</h4>"
            "<p style='font-size:0.85em;color:#aaa;'>AIインフラ・メガテック・高成長銘柄を中心にリターンを最大化。</p></div>",
            unsafe_allow_html=True
        )
    with col_str2:
        st.markdown(
            "<div style='border:2px solid #00e5ff;padding:16px;border-radius:8px;background:rgba(0,229,255,0.05);'>"
            "<h4>⚖️ バランス・バーベル型 (Barbell)</h4>"
            "<p style='font-size:0.85em;color:#aaa;'>成長株 60% × 強固キャッシュフロー株 40% の最適バランス構成。</p></div>",
            unsafe_allow_html=True
        )
    with col_str3:
        st.markdown(
            "<div style='border:2px solid #ffd600;padding:16px;border-radius:8px;background:rgba(255,214,0,0.05);'>"
            "<h4>🛡️ クオリティ・ディフェンシブ型</h4>"
            "<p style='font-size:0.85em;color:#aaa;'>圧倒的Moatと連続最高益を誇る財務健全銘柄で低ボラ運用。</p></div>",
            unsafe_allow_html=True
        )

    selected_model = st.selectbox(
        "提案を表示するポートフォリオモデル",
        ["⚖️ バランス・バーベル型 (Barbell Core)", "🚀 積極成長型 (Aggressive Growth)", "🛡️ クオリティ・ディフェンシブ型 (Quality Defensive)"]
    )

    st.divider()

    # ── 2. 選択モデルの組み入れ構成比率 ──
    if "Aggressive" in selected_model:
        model_name = "積極成長型ポートフォリオ"
        model_alloc = {'NVDA': 25, 'MSFT': 20, 'AMZN': 15, 'AVGO': 15, 'META': 15, 'GOOGL': 10}
    elif "Quality" in selected_model:
        model_name = "クオリティ・ディフェンシブ型ポートフォリオ"
        model_alloc = {'BRK-B': 25, 'JPM': 20, 'WMT': 20, 'COST': 20, 'V': 15}
    else:
        model_name = "バランス・バーベル型ポートフォリオ"
        model_alloc = {'MSFT': 20, 'AAPL': 15, 'LLY': 15, 'COST': 15, 'BRK-B': 15, 'JPM': 10, 'NVDA': 10}

    col_pie, col_details = st.columns([1, 1])

    with col_pie:
        st.markdown(f"##### 📊 {model_name} の推奨銘柄配分")
        df_pie = pd.DataFrame([
            {'ticker': t, 'weight': w} for t, w in model_alloc.items()
        ])
        fig_pie = px.pie(
            df_pie, names='ticker', values='weight',
            title=f"{model_name} 構成比率",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_pie.update_layout(height=340, margin=dict(t=30, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_details:
        st.markdown(f"##### 📋 構成銘柄のAIスコア & 期待リターン")
        for t, w in model_alloc.items():
            r = next((res for res in ai_results if res.stock.ticker == t), None)
            if r:
                st.markdown(
                    f"・ **{t}** ({r.stock.company_name}): 比率 **{w}%** | "
                    f"AIスコア **{r.total_score}点** ({r.ai_rating}) | "
                    f"PER: {r.stock.pe_ratio}倍"
                )

    # ── 3. AIによる今月の具体的一括アクション指示 ──
    st.divider()
    st.markdown("##### ⚡ 今月のAIトレーディング・アクション指示")

    col_act1, col_act2 = st.columns(2)

    with col_act1:
        st.success("🟢 **【強気エントリー推奨銘柄】**")
        top_buys = [r for r in ai_results if r.total_score >= 80.0][:3]
        for b in top_buys:
            st.markdown(
                f"- **{b.stock.ticker}** ({b.stock.company_name}): スコア **{b.total_score}点**\n"
                f"  - 理由: {b.key_strengths[0] if b.key_strengths else '高いファンダメンタルズ'}"
            )

    with col_act2:
        st.warning("🟡 **【利益確定・バランス調整おすすめ銘柄】**")
        cautions = [r for r in ai_results if r.stock.pe_ratio > 38.0 or r.total_score < 65.0][:3]
        for c in cautions:
            st.markdown(
                f"- **{c.stock.ticker}** ({c.stock.company_name}): PER **{c.stock.pe_ratio}倍**\n"
                f"  - 理由: {c.risk_factors[0] if c.risk_factors else '過熱気味バリュエーション'}"
            )

    # ── 4. ポール・サイ式 個人投資家へのガイドライン ──
    st.divider()
    st.info("""
💡 **【ポール・サイ式: 個人投資家のAI活用メソッド】**
1. **情報格差の解消**: 従来ウォール街の機関投資家だけが独占していた企業分析・決算要約を、AIを使って数分で個人で実行する。
2. **感情の排除**: 投機的なSNSの熱狂に惑わされず、ROE・利益率・Moat（競合優位性）の定量的スコアに基づいて冷静に判断する。
3. **バーベル戦略の実践**: 一方の極である超高成長（AI・半導体）と、もう一方の極である強固な現金流出入（ヘルスケア・メガバンク・生活必需品）を組み合わせ、市場暴落時にもビクともしないポートフォリオを構築する。
    """)
