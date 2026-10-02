import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from collectors.fidelity_data_fetcher import FidelityDataFetcher, StockData
from analyzers.fidelity_ai_engine import FidelityAIEngine, AIScoreResult

def render_fund_scoreboard_tab():
    st.markdown("### 🏆 フィデリティ米国株ファンド AIスコアボード")
    st.caption("ファンド組み入れ主要銘柄のAI総合評価 (100点満点) ・成長性・収益性・Moat（競合優位性）のリアルタイムランキング")

    # データ取得・計算
    if 'fidelity_stocks' not in st.session_state or st.button("🔄 AIスコア再計算", key="refresh_scoreboard"):
        with st.spinner("🤖 米国主要銘柄データとAIスコアを計算中..."):
            fetcher = FidelityDataFetcher()
            stocks = fetcher.fetch_all_holdings_data()
            ai_results = FidelityAIEngine.evaluate_all(stocks)
            st.session_state['fidelity_stocks'] = stocks
            st.session_state['fidelity_ai_results'] = ai_results

    ai_results: list[AIScoreResult] = st.session_state.get('fidelity_ai_results', [])

    if not ai_results:
        st.warning("データが取得できませんでした。再計算ボタンを押してください。")
        return

    # ── フィルター ──
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        category_filter = st.radio(
            "銘柄カテゴリー絞り込み",
            ['すべて', '🚀 AI・メガテック成長株 (Growth)', '🛡️ キャッシュフロー・ディフェンシブ株 (Value/Defensive)'],
            horizontal=True
        )

    filtered_results = ai_results
    if category_filter == '🚀 AI・メガテック成長株 (Growth)':
        filtered_results = [r for r in ai_results if 'Growth' in r.barbell_type]
    elif category_filter == '🛡️ キャッシュフロー・ディフェンシブ株 (Value/Defensive)':
        filtered_results = [r for r in ai_results if 'Value' in r.barbell_type or 'Defensive' in r.barbell_type]

    # ── トップ概要メトリクス ──
    top1 = filtered_results[0] if filtered_results else None
    avg_score = sum(r.total_score for r in ai_results) / len(ai_results) if ai_results else 0
    high_rating_count = sum(1 for r in ai_results if 'Strong' in r.ai_rating or 'Buy' in r.ai_rating)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("🥇 AI最高評価銘柄", f"{top1.stock.ticker} ({top1.total_score}点)" if top1 else "N/A")
    with m2:
        st.metric("📊 平均AIスコア", f"{avg_score:.1f} / 100")
    with m3:
        st.metric("🟢 強気(Buy)評価銘柄数", f"{high_rating_count} / {len(ai_results)} 銘柄")
    with m4:
        st.metric("💼 分析対象ファンド", "Fidelity US Equity Fund Top Holdings")

    st.divider()

    # ── ビジュアルチャート: セクターツリーマップ & AIスコア順 ──
    ch_col1, ch_col2 = st.columns([1, 1])

    with ch_col1:
        st.markdown("##### 🗺️ ファンド組み入れ比率 & セクターツリーマップ")
        df_tree = pd.DataFrame([
            {
                'ticker': r.stock.ticker,
                'company': r.stock.company_name,
                'sector': r.stock.sector,
                'weight': r.stock.weight_pct,
                'score': r.total_score
            }
            for r in ai_results
        ])
        fig_tree = px.treemap(
            df_tree,
            path=['sector', 'ticker'],
            values='weight',
            color='score',
            color_continuous_scale='RdYlGn',
            range_color=[50, 95],
            title="セクター別組み入れ比率 (カラー: AIスコア)"
        )
        fig_tree.update_layout(height=350, margin=dict(t=30, b=10))
        st.plotly_chart(fig_tree, use_container_width=True)

    with ch_col2:
        st.markdown("##### 📊 AI総合スコア ランキング")
        df_bar = pd.DataFrame([
            {
                'ticker': r.stock.ticker,
                'score': r.total_score,
                'rating': r.ai_rating
            }
            for r in filtered_results
        ])
        fig_bar = px.bar(
            df_bar,
            x='score',
            y='ticker',
            orientation='h',
            color='score',
            color_continuous_scale='Viridis',
            title="AIスコア比較 (100点満点)"
        )
        fig_bar.update_layout(height=350, margin=dict(t=30, b=10), yaxis=dict(autorange='reversed'))
        st.plotly_chart(fig_bar, use_container_width=True)

    # ── AIスコアボード カード一覧 ──
    st.divider()
    st.markdown("##### 📋 AI評価カード＆スコア内訳")

    for r in filtered_results:
        s = r.stock
        score_color = "#00c853" if r.total_score >= 80 else ("#ffd600" if r.total_score >= 65 else "#ff1744")
        
        with st.container(border=True):
            card_hdr1, card_hdr2, card_hdr3 = st.columns([2, 1, 1])
            with card_hdr1:
                st.markdown(
                    f"### **{s.ticker}** - {s.company_name} "
                    f"<span style='font-size:0.7em;color:#888;'>({s.sector})</span>",
                    unsafe_allow_html=True
                )
                st.caption(f"{r.barbell_type} | 推定組入比率: **{s.weight_pct}%**")
            with card_hdr2:
                st.markdown(
                    f"<h2 style='color:{score_color};margin:0;'>{r.total_score} <span style='font-size:0.5em;'>/100</span></h2>"
                    f"<b>{r.ai_rating}</b>",
                    unsafe_allow_html=True
                )
            with card_hdr3:
                st.markdown(f"**現在値**: ${s.price:.2f} ({s.change_pct:+.2f}%)")
                st.markdown(f"**PER**: {s.pe_ratio}倍 | **ROE**: {s.roe}%")

            # 4要素スコアゲージ
            sc1, sc2, sc3, sc4 = st.columns(4)
            with sc1: st.progress(r.growth_score / 25.0, text=f"成長性: {r.growth_score}/25")
            with sc2: st.progress(r.profitability_score / 25.0, text=f"収益性: {r.profitability_score}/25")
            with sc3: st.progress(r.moat_score / 25.0, text=f"Moat優位性: {r.moat_score}/25")
            with sc4: st.progress(r.valuation_score / 25.0, text=f"割安性/安定: {r.valuation_score}/25")

            with st.expander("🤖 AIアナリスト要約 & 強み・リスク"):
                st.markdown(f"**【AI要約】**\n{r.ai_summary}")
                c_str, c_risk = st.columns(2)
                with c_str:
                    st.markdown("**強み (Strengths)**")
                    for st_item in r.key_strengths:
                        st.markdown(f"✅ {st_item}")
                with c_risk:
                    st.markdown("**リスク要因 (Risks)**")
                    for rk_item in r.risk_factors:
                        st.markdown(f"⚠️ {rk_item}")

    # ── データ一覧テーブル ──
    st.divider()
    with st.expander("📊 全組み入れ銘柄 財務・データ一覧"):
        df_table = pd.DataFrame([
            {
                'ティッカー': r.stock.ticker,
                '企業名': r.stock.company_name,
                'セクター': r.stock.sector,
                'AIスコア': r.total_score,
                'AI評価': r.ai_rating,
                '組入比率': f"{r.stock.weight_pct}%",
                '株価($)': r.stock.price,
                '前日比(%)': r.stock.change_pct,
                'PER(倍)': r.stock.pe_ratio,
                'ROE(%)': r.stock.roe,
                '営業利益率(%)': r.stock.profit_margin,
                '売上成長率(%)': r.stock.revenue_growth,
            }
            for r in ai_results
        ])
        st.dataframe(df_table, use_container_width=True, hide_index=True)
