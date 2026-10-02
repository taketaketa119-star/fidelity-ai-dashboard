"""
フィデリティ米国株ファンド AI分析ダッシュボード
(Fidelity US Equity AI Analytics Dashboard)

YouTube動画『元フィデリティが、「フィデリティ米国株ファンド」を、AIで分析してみた！【WORLD MARKETZ】ポール・サイさん』のフレームワークに基づく分析システム
起動: streamlit run app.py --server.port 8504
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from tabs.tab_fund_scoreboard import render_fund_scoreboard_tab
from tabs.tab_stock_analyzer import render_stock_analyzer_tab
from tabs.tab_benchmark_compare import render_benchmark_compare_tab
from tabs.tab_portfolio_ideas import render_portfolio_ideas_tab

# ── ページ設定 ──
st.set_page_config(
    page_title='Fidelity US Equity AI Dashboard',
    page_icon='🇺🇸',
    layout='wide',
    initial_sidebar_state='collapsed',
)

# ── カスタムCSS ──
st.markdown("""
<style>
    /* 全体的なスタイル */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        font-weight: 600;
    }
    /* メトリクスの調整 */
    [data-testid="stMetricValue"] {
        font-size: 1.3rem;
    }
</style>
""", unsafe_allow_html=True)

# ── ヘッダー ──
st.title('🇺🇸 フィデリティ米国株ファンド AI分析ダッシュボード')
st.caption('元フィデリティ ポール・サイ氏の分析メソッドに基づく AI銘柄スコアリング & アクティブ vs S&P500 対比システム')
st.divider()

# ── サイドバー ──
st.sidebar.title('⚙️ 設定 & 情報')
st.sidebar.markdown('### 📊 分析対象ファンド')
st.sidebar.info('・ **Fidelity US Equity Fund** Top Holdings\n・ 米国主要アクティブ＆メガテック構成銘柄')

st.sidebar.markdown('---')
st.sidebar.markdown('### 💡 分析フレームワーク')
st.sidebar.markdown(
    '1. **AI 100点スコアリング**: 成長性・収益性・Moat(優位性)・バリュエーション\n'
    '2. **バーベル戦略**: 🚀高成長株 × 🛡️高キャッシュフロー株\n'
    '3. **アクティブ vs S&P500/NASDAQ100 対比**\n'
    '4. **AI民主化リサーチ**'
)

last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.sidebar.markdown(f"🕐 最終データ同期: **{last_update}**")

# ── メインタブ ──
tab1, tab2, tab3, tab4 = st.tabs([
    '🏆 AIスコアボード',
    '🔬 AI個別銘柄ディープアナライザー',
    '⚖️ アクティブ vs S&P500 比較',
    '💡 AIポートフォリオ＆売買アイデア',
])

with tab1:
    try:
        render_fund_scoreboard_tab()
    except Exception as e:
        st.error(f"AIスコアボード タブでエラーが発生しました: {e}")
        import traceback
        st.code(traceback.format_exc())

with tab2:
    try:
        render_stock_analyzer_tab()
    except Exception as e:
        st.error(f"AIディープアナライザー タブでエラーが発生しました: {e}")
        import traceback
        st.code(traceback.format_exc())

with tab3:
    try:
        render_benchmark_compare_tab()
    except Exception as e:
        st.error(f"アクティブ vs S&P500 比較 タブでエラーが発生しました: {e}")
        import traceback
        st.code(traceback.format_exc())

with tab4:
    try:
        render_portfolio_ideas_tab()
    except Exception as e:
        st.error(f"AIポートフォリオ＆売買アイデア タブでエラーが発生しました: {e}")
        import traceback
        st.code(traceback.format_exc())
