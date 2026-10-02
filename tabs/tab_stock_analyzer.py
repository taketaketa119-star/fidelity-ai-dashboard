import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from collectors.fidelity_data_fetcher import FidelityDataFetcher, StockData
from analyzers.fidelity_ai_engine import FidelityAIEngine, AIScoreResult

def render_stock_analyzer_tab():
    st.markdown("### 🔬 AI個別銘柄ディープアナライザー")
    st.caption("ポール・サイ式分析フレームワークに基づく、財務健全性・ROE分解・競合優位性(Moat)・株価チャートの可視化")

    ai_results: list[AIScoreResult] = st.session_state.get('fidelity_ai_results', [])

    if not ai_results:
        fetcher = FidelityDataFetcher()
        stocks = fetcher.fetch_all_holdings_data()
        ai_results = FidelityAIEngine.evaluate_all(stocks)
        st.session_state['fidelity_ai_results'] = ai_results

    ticker_list = [r.stock.ticker for r in ai_results]

    col_sel1, col_sel2 = st.columns([1, 2])
    with col_sel1:
        selected_ticker = st.selectbox("分析対象銘柄を選択", ticker_list, index=0)

    selected_result = next((r for r in ai_results if r.stock.ticker == selected_ticker), ai_results[0])
    s = selected_result.stock

    st.divider()

    # ── ヘッダー部 ──
    h_col1, h_col2, h_col3 = st.columns([2, 1, 1])
    with h_col1:
        st.title(f"{s.company_name} ({s.ticker})")
        st.caption(f"セクター: **{s.sector}** | バーベル分類: **{selected_result.barbell_type}** | 時価総額: **${s.market_cap_b:.1f}B (約{s.market_cap_b*150/1000:.1f}兆円)**")
    with h_col2:
        score_color = "#00c853" if selected_result.total_score >= 80 else ("#ffd600" if selected_result.total_score >= 65 else "#ff1744")
        st.markdown(
            f"<h4>AI 総合スコア</h4><h1 style='color:{score_color};margin:0;'>{selected_result.total_score} <span style='font-size:0.4em;'>/100</span></h1>"
            f"<b>{selected_result.ai_rating}</b>",
            unsafe_allow_html=True
        )
    with h_col3:
        st.metric("💵 現在株価", f"${s.price:.2f}", delta=f"{s.change_pct:+.2f}%")
        st.metric("📊 PER / PBR", f"{s.pe_ratio}倍 / {s.pb_ratio}倍")

    # ── 2カラム：株価チャート & AIアナリストプロンプト ──
    ch_col, ai_col = st.columns([1, 1])

    with ch_col:
        st.markdown("##### 📈 1年間の株価・出来高推移")
        df_h = s.history_df

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.7, 0.3])
        fig.add_trace(go.Scatter(x=df_h['date'], y=df_h['close'], mode='lines', name='株価($)', line=dict(color='#00c853', width=2)), row=1, col=1)
        fig.add_trace(go.Bar(x=df_h['date'], y=df_h['volume'], name='出来高', marker_color='rgba(100, 100, 100, 0.4)'), row=2, col=1)
        fig.update_layout(height=380, margin=dict(t=20, b=10), showlegend=False, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

    with ai_col:
        st.markdown("##### 🤖 AI ディープアナリスト判定")
        st.info(selected_result.ai_summary)

        st.markdown("##### 🏰 Moat (競合優位性) 定性分析")
        moat_score = selected_result.moat_score
        st.progress(moat_score / 25.0, text=f"Moat スコア: {moat_score} / 25.0")
        for strength in selected_result.key_strengths:
            st.markdown(f"🔹 {strength}")

    st.divider()

    # ── 3カラム：財務指標メトリクス ＆ ROE分析 ──
    st.markdown("##### 📊 財務ファンダメンタルズ＆デュポン分析")
    
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("🎯 ROE (自己資本利益率)", f"{s.roe:.1f}%", help="高いほど資本効率が良い (20%以上で非常に優秀)")
    with m2:
        st.metric("💰 営業利益率", f"{s.profit_margin:.1f}%", help="本業の稼ぐ力 (20%以上で高収益構造)")
    with m3:
        st.metric("🚀 売上成長率 (YoY)", f"{s.revenue_growth:+.1f}%", help="トップラインの成長スピード")
    with m4:
        st.metric("💵 配当利回り", f"{s.dividend_yield:.2f}%", help="年間配当還元率")

    # デュポン分析ビジュアル
    st.markdown("##### ⚙️ ROEデュポン分解ビジュアル (簡易モデル)")
    d_col1, d_col2, d_col3 = st.columns(3)
    with d_col1:
        st.markdown(
            f"<div style='border:1px solid #444;padding:12px;border-radius:6px;text-align:center;'>"
            f"<b>① 収益性 (売上高純利益率)</b><br>"
            f"<h3 style='color:#00c853;'>{s.profit_margin * 0.85:.1f}%</h3>"
            f"<span style='font-size:0.8em;color:#aaa;'>製品・サービスの付加価値</span></div>",
            unsafe_allow_html=True
        )
    with d_col2:
        st.markdown(
            f"<div style='border:1px solid #444;padding:12px;border-radius:6px;text-align:center;'>"
            f"<b>② 効率性 (総資産回転率)</b><br>"
            f"<h3 style='color:#ffd600;'>{max(0.4, min(1.5, s.revenue_growth / 20.0 + 0.5)):.2f} 回</h3>"
            f"<span style='font-size:0.8em;color:#aaa;'>資産の運用スピード</span></div>",
            unsafe_allow_html=True
        )
    with d_col3:
        st.markdown(
            f"<div style='border:1px solid #444;padding:12px;border-radius:6px;text-align:center;'>"
            f"<b>③ 財務レバレッジ</b><br>"
            f"<h3 style='color:#00e5ff;'>{max(1.2, min(3.5, s.pb_ratio / 2.0)):.2f} 倍</h3>"
            f"<span style='font-size:0.8em;color:#aaa;'>自己資本に対する総資産の比率</span></div>",
            unsafe_allow_html=True
        )

    # ── ポール・サイ式 AI分析プロンプト出力 ──
    st.divider()
    with st.expander("📝 ポール・サイ式 AI分析プロンプト・チェックリスト (プロ仕様)"):
        st.markdown(f"""
```markdown
# 銘柄分析プロンプト: {s.ticker} ({s.company_name})
- 分析日付: {pd.Timestamp.now().strftime('%Y-%m-%d')}
- セクター: {s.sector}

## 1. 財務ファンダメンタルズ
- PER: {s.pe_ratio}倍 | PBR: {s.pb_ratio}倍
- ROE: {s.roe}% | 営業利益率: {s.profit_margin}%
- 売上成長率: {s.revenue_growth}%

## 2. 競争優位性 (Moat) チェック
- {selected_result.key_strengths[0] if selected_result.key_strengths else 'N/A'}

## 3. バーベル戦略における判定
- 分類: {selected_result.barbell_type}
- AI総合評価: {selected_result.total_score}点 ({selected_result.ai_rating})
```
        """)
