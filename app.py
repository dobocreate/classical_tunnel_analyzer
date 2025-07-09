"""Streamlit app for Murayama tunnel stability analysis."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.models import (
    TunnelGeometry, SoilParameters, LoadingConditions, 
    MurayamaInput, MurayamaResult, SurchargeMethod
)
from src.murayama_new import ImprovedMurayamaCalculator
from src.murayama import get_default_presets
from src.report_generator import ReportGenerator, generate_markdown_report
import io
import base64
from datetime import datetime


# Page configuration
st.set_page_config(
    page_title="村山式トンネル安定性解析",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add CSS for section styling
st.markdown("""
<style>
    /* expanderのスタイル調整 */
    div[data-testid="stExpander"] {
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
    }
    
    /* セクション用expanderのスタイル */
    .section-expander + div[data-testid="stExpander"] > details > summary {
        padding: 0 !important;
        min-height: 0 !important;
    }
    
    .section-expander + div[data-testid="stExpander"] > details > summary > svg {
        display: none !important;
    }
    
    .section-expander + div[data-testid="stExpander"] > details > div {
        padding-top: 1rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'calculate_clicked' not in st.session_state:
    st.session_state.calculate_clicked = False
if 'show_graph' not in st.session_state:
    st.session_state.show_graph = False
if 'page' not in st.session_state:
    st.session_state.page = "計算"

# Custom CSS for button styling
st.markdown("""
<style>
    /* サイドバーボタンのスタイル */
    div[data-testid="stSidebar"] button {
        width: 100%;
        text-align: left;
        border: none;
        padding: 0.5rem 1rem;
        margin: 0.25rem 0;
        border-radius: 0.5rem;
        transition: background-color 0.3s;
    }
    
    /* アクティブなボタンのスタイル */
    div[data-testid="stSidebar"] button:hover {
        background-color: rgba(28, 131, 225, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
with st.sidebar:
    # 計算ツールボタン
    if st.button("🧮 計算ツール", use_container_width=True, type="primary" if st.session_state.page == "計算" else "secondary"):
        st.session_state.page = "計算"
        st.rerun()
    
    # 理論説明ボタン
    if st.button("📚 理論説明", use_container_width=True, type="primary" if st.session_state.page == "理論説明" else "secondary"):
        st.session_state.page = "理論説明"
        st.rerun()
    
    # 物性値の根拠ボタン
    if st.button("📊 物性値の根拠", use_container_width=True, type="primary" if st.session_state.page == "物性値の根拠" else "secondary"):
        st.session_state.page = "物性値の根拠"
        st.rerun()

# Get current page from session state
page = st.session_state.page

# Main page based on selection
if page == "計算":
    # Header
    st.title("🧮 トンネルの安定計算")
    st.markdown("村山の式を用いてトンネル切羽の安定性を評価します")
    
    # Main container with two columns
    col_input, col_result = st.columns([2, 1])
    
    # Left column - Input section
    with col_input:
        # Guide text
        with st.container():
            st.info("""
            **切羽の安定性を確認しましょう**  
            以下の項目を入力すると、村山の式で切羽が安全かどうか自動計算されます
            """)
        
        # Section 1: Tunnel Geometry
        with st.container():
            st.markdown("### 1️⃣ トンネル諸元")
            # Use an expander that's always expanded and can't be collapsed
            st.markdown('<div class="section-expander">', unsafe_allow_html=True)
            expander1 = st.expander("", expanded=True)
            with expander1:
                col1, col2 = st.columns(2)
                with col1:
                    height = st.number_input(
                        "トンネル切羽高さ H (m) *", 
                        min_value=0.1, 
                        max_value=50.0, 
                        value=10.0, 
                        step=0.5,
                        help="トンネル切羽の高さ（通常: 8〜12m）"
                    )
                with col2:
                    tunnel_depth = st.number_input(
                        "土被り D_t (m) *", 
                        min_value=0.0, 
                        max_value=100.0, 
                        value=10.0, 
                        step=0.5,
                        help="トンネル天端の土被り深さ"
                    )
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("")  # Spacing
        
        # Section 2: Soil Parameters
        with st.container():
            st.markdown("### 2️⃣ 地山物性値")
            st.markdown('<div class="section-expander">', unsafe_allow_html=True)
            expander2 = st.expander("", expanded=True)
            with expander2:
                # Preset selection
                presets = get_default_presets()
                preset_names = ["カスタム"] + [p.name for p in presets]
                selected_preset = st.selectbox("地盤タイプを選択", preset_names)
                
                # Initialize default values
                if selected_preset != "カスタム":
                    preset = next(p for p in presets if p.name == selected_preset)
                    default_gamma = preset.soil.gamma
                    default_c = preset.soil.c
                    default_phi = preset.soil.phi
                else:
                    default_gamma = 20.0
                    default_c = 30.0
                    default_phi = 30.0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    c = st.number_input(
                        "粘着力 c (kPa) *", 
                        min_value=0.0, 
                        max_value=200.0, 
                        value=default_c, 
                        step=5.0,
                        help="地盤の粘着力"
                    )
                with col2:
                    phi = st.number_input(
                        "内部摩擦角 φ (°) *", 
                        min_value=0.0, 
                        max_value=60.0, 
                        value=default_phi, 
                        step=1.0,
                        help="地盤の内部摩擦角"
                    )
                with col3:
                    gamma = st.number_input(
                        "単位体積重量 γ (kN/m³) *", 
                        min_value=10.0, 
                        max_value=30.0, 
                        value=default_gamma, 
                        step=0.5,
                        help="地盤の有効単位体積重量"
                    )
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("")  # Spacing
        
        # Section 3: Loading Conditions
        with st.container():
            st.markdown("### 3️⃣ 荷重条件")
            st.markdown('<div class="section-expander">', unsafe_allow_html=True)
            expander3 = st.expander("", expanded=True)
            with expander3:
                col1, col2 = st.columns(2)
                with col1:
                    u = st.number_input(
                        "水圧 u (kPa)", 
                        min_value=0.0, 
                        max_value=1000.0, 
                        value=0.0, 
                        step=10.0,
                        help="間隙水圧（通常: 0）"
                    )
                with col2:
                    sigma_v = st.number_input(
                        "上載荷重 σᵥ (kPa)", 
                        min_value=0.0, 
                        max_value=5000.0, 
                        value=0.0, 
                        step=50.0,
                        help="鉛直上載荷重（通常: 0）"
                    )
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("")  # Spacing
        
        # Section 4: Advanced Settings
        st.markdown("### 4️⃣ 詳細設定（オプション）")
        with st.expander("詳細パラメータを表示"):
            col1, col2 = st.columns(2)
            with col1:
                x_start = st.number_input(
                    "探索開始位置 (m)", 
                    min_value=-20.0, 
                    max_value=0.0, 
                    value=-10.0, 
                    step=0.5,
                    help="すべり面始点の探索開始位置（トンネル中心からの水平距離）"
                )
                x_end = st.number_input(
                    "探索終了位置 (m)",
                    min_value=0.0,
                    max_value=20.0,
                    value=10.0,
                    step=0.5,
                    help="すべり面始点の探索終了位置"
                )
            with col2:
                x_step = st.number_input(
                    "探索刻み幅 (m)",
                    min_value=0.1,
                    max_value=2.0,
                    value=0.5,
                    step=0.1,
                    help="探索の刻み幅"
                )
            
            col1, col2 = st.columns(2)
            with col1:
                max_iterations = st.number_input(
                    "最大反復回数",
                    min_value=10,
                    max_value=1000,
                    value=100,
                    step=10,
                    help="収束計算の最大反復回数"
                )
            with col2:
                tolerance = st.number_input(
                    "収束判定値",
                    min_value=1e-10,
                    max_value=0.1,
                    value=1e-6,
                    format="%.2e",
                    help="反復計算の収束判定値"
                )
            
            # Surcharge calculation method selection
            st.markdown("#### 上載荷重計算方法")
            surcharge_method = st.selectbox(
                "計算方法を選択",
                options=[SurchargeMethod.SIMPLE.value, SurchargeMethod.TERZAGHI.value],
                index=0,
                help="簡易法：土被り分の重量、テルツァギー：アーチング効果を考慮"
            )
        
        # Calculate button
        st.markdown("")  # Spacing
        col1, col2, col3 = st.columns([3, 2, 3])
        with col2:
            calculate_button = st.button(
                "計算実行", 
                type="primary", 
                use_container_width=True
            )
            
            if calculate_button:
                st.session_state.calculate_clicked = True
    
    # Right column - Results section
    with col_result:
        st.markdown("### 📊 評価結果")
        
        # Perform calculation if button was clicked
        if st.session_state.calculate_clicked:
            # Create input objects
            geometry = TunnelGeometry(height=height, tunnel_depth=tunnel_depth)
            soil = SoilParameters(gamma=gamma, c=c, phi=phi)
            loading = LoadingConditions(u=u, sigma_v=sigma_v)
            # Convert surcharge method string to enum
            surcharge_method_enum = SurchargeMethod.SIMPLE
            if 'surcharge_method' in locals():
                if surcharge_method == SurchargeMethod.TERZAGHI.value:
                    surcharge_method_enum = SurchargeMethod.TERZAGHI
            
            murayama_input = MurayamaInput(
                geometry=geometry,
                soil=soil,
                loading=loading,
                x_start=x_start if 'x_start' in locals() else -10.0,
                x_end=x_end if 'x_end' in locals() else 10.0,
                x_step=x_step if 'x_step' in locals() else 0.5,
                n_divisions=100,  # Fixed value for scipy.quad
                max_iterations=max_iterations if 'max_iterations' in locals() else 100,
                tolerance=tolerance if 'tolerance' in locals() else 1e-6,
                surcharge_method=surcharge_method_enum
            )
            
            # Calculate using improved algorithm
            with st.spinner("計算中..."):
                calculator = ImprovedMurayamaCalculator(murayama_input)
                result = calculator.calculate_stability()
                
                # Store result in session state
                st.session_state['result'] = result
                st.session_state['input'] = murayama_input
        
        # Display results if available
        if 'result' in st.session_state:
            result = st.session_state['result']
            input_params = st.session_state['input']
            
            # Safety factor evaluation
            st.markdown("#### 安全率評価")
            
            # Display required support pressure
            st.metric("必要支保圧力", f"{result.P_max:.1f} kN/m²")
            
            # Safety evaluation based on support pressure
            if result.P_max < 50:
                st.success("✅ **切羽は安定しています**")
                st.markdown("必要支保圧力が小さく、切羽は自立可能です。")
            elif result.P_max < 100:
                st.warning("⚠️ **軽微な支保が必要**")
                st.markdown("一定の支保圧力が必要です。")
            else:
                st.error("❌ **強固な支保が必要**")
                st.markdown("大きな支保圧力が必要です。適切な対策を検討してください。")
            
            # Detailed results
            st.markdown("#### 計算結果の詳細")
            
            # Get calculation method from session state
            calc_method = "簡易法"
            if 'input' in st.session_state:
                if st.session_state['input'].surcharge_method == SurchargeMethod.TERZAGHI:
                    calc_method = "テルツァギー"
            
            # Add convergence info if available
            convergence_rate = "100%"
            if result.convergence_info and 'convergence_rate' in result.convergence_info:
                convergence_rate = f"{result.convergence_info['convergence_rate']:.1f}%"
            
            result_data = {
                "項目": ["最大必要支保圧力", "危険すべり面位置", "計算点数", "収束率", "上載荷重計算"],
                "値": [
                    f"{result.P_max:.1f} kN/m²",
                    f"{result.x_critical:.2f} m",
                    f"{len(result.x_values)} 点",
                    convergence_rate,
                    calc_method
                ]
            }
            df_results = pd.DataFrame(result_data)
            st.dataframe(df_results, hide_index=True, use_container_width=True)
            
            st.divider()
            
            # Judgment criteria
            with st.expander("判定基準"):
                st.markdown("""
                - **P < 50 kN/m²**: 切羽は安定
                - **50 ≤ P < 100 kN/m²**: 軽微な支保が必要
                - **P ≥ 100 kN/m²**: 強固な支保が必要
                - **計算方法**: 改良版村山の式
                """)
            
            # Action buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📄 レポート", use_container_width=True):
                    with st.spinner("レポートを生成中..."):
                        report_gen = ReportGenerator(input_params, result)
                        pdf_bytes = report_gen.generate_pdf()
                        
                        st.download_button(
                            label="PDFダウンロード",
                            data=pdf_bytes,
                            file_name=f"murayama_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf"
                        )
            
            with col2:
                if st.button("📊 グラフ", use_container_width=True):
                    st.session_state.show_graph = not st.session_state.show_graph
            
            # P-x curve graph
            if st.session_state.show_graph:
                st.markdown("#### P-x曲線（必要支保圧力分布）")
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=result.x_values,
                    y=result.P_values,
                    mode='lines',
                    name='P-x曲線',
                    line=dict(color='blue', width=2)
                ))
                fig.add_trace(go.Scatter(
                    x=[result.x_critical],
                    y=[result.P_max],
                    mode='markers',
                    name=f'P_max = {result.P_max:.1f} kN/m²',
                    marker=dict(color='red', size=12, symbol='star')
                ))
                fig.update_layout(
                    xaxis_title="すべり面始点位置 x [m]",
                    yaxis_title="必要支保圧力 P [kN/m²]",
                    height=300,
                    margin=dict(l=0, r=0, t=20, b=0)
                )
                st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.info("💡 左側のパラメータを入力して「計算実行」をクリックしてください")

elif page == "理論説明":
    st.title("📚 理論説明")
    st.markdown("改良版村山の式による切羽安定性評価の理論的背景")
    
    # Theory explanation
    st.markdown("## 1. 村山の式の概要")
    st.markdown("""
    村山の式は、トンネル切羽の安定性を評価するための解析手法で、対数螺旋すべり面を仮定した
    極限平衡法に基づいています。この手法は1984年に村山により提案され、現在でも広く使用されています。
    
    本システムでは、より厳密な幾何学的条件と力学的平衡を考慮した改良版を実装しています。
    """)
    
    st.markdown("## 2. 基本仮定")
    st.markdown("""
    改良版では以下の仮定を採用しています：
    
    - すべり面は対数螺旋形状を仮定
    - 土の破壊基準はMohr-Coulombの破壊基準に従う
    - すべり土塊の重心まわりのモーメント平衡を考慮
    - 平面ひずみ状態を仮定
    - すべり面始点は切羽天端（地表面）に位置
    - すべり面終点での角度条件を満足
    """)
    
    st.markdown("## 3. 対数螺旋すべり面の幾何学")
    st.markdown("""
    ### 3.1 すべり面の方程式
    
    対数螺旋の極座標表示：
    $$r = r_0 e^{\\theta \\tan \\phi}$$
    
    ここで：
    - $r$: 中心Oからの動径
    - $r_0$: 基準動径
    - $\\theta$: 偏角
    - $\\phi$: 内部摩擦角
    
    ### 3.2 幾何学的拘束条件
    
    1. **すべり面始点の条件**
       - 位置: $(x_i, D_t + H)$ 
       - $x_i$: トンネル中心からの水平距離（探索パラメータ）
       - $D_t$: 土被り深さ
       - $H$: トンネル高さ
    
    2. **中心Oの位置**
       - 点$i$を通り、水平線から$(180° - \\phi)$の角度を持つ直線上
    
    3. **終点での角度条件**
       - すべり面がトンネル底面と交わる点での角度: $\\delta = 45° - \\phi/2$
    """)
    
    st.markdown("## 4. 力学的平衡")
    st.markdown("""
    ### 4.1 作用力
    
    すべり土塊に作用する力：
    
    1. **すべり土塊の重量 $W_h$**
       $$W_h = \\gamma \\cdot A_h$$
       - $\\gamma$: 土の単位体積重量
       - $A_h$: すべり土塊の断面積（数値積分により算定）
    
    2. **上載荷重 $Q$**
       
       **簡易法**：
       $$Q = \\gamma \\cdot B_s \\cdot D_t$$
       
       **テルツァギーの土圧理論**：
       $$p_v = \\frac{B_s \\cdot \\gamma - 2c}{2K \\tan\\delta} \\left(1 - e^{-2K \\tan\\delta \\frac{D_t}{B_s}}\\right)$$
       $$Q = p_v \\cdot B_s$$
       
       ここで：
       - $B_s$: すべり土塊の地表面での幅
       - $K$: 土圧係数（ランキンの主働土圧係数）
       - $\\delta$: 側壁摩擦角（通常 $\\delta = \\phi$）
    
    3. **粘着力によるモーメント $M_c$**
       $$M_c = \\frac{c}{2\\tan\\phi}(r_i^2 - r_d^2)$$
       - $c$: 粘着力
       - $r_i, r_d$: 始点・終点での動径
    
    ### 4.2 モーメント平衡式
    
    中心Oまわりのモーメント平衡：
    $$P \\cdot l_p + M_c = W_h \\cdot l_w + Q \\cdot l_Q$$
    
    必要支保圧力：
    $$P = \\frac{W_h \\cdot l_w + Q \\cdot l_Q - M_c}{l_p \\cdot H}$$
    
    ここで $l_p, l_w, l_Q$ は各力の中心Oからの腕の長さ
    """)
    
    st.markdown("## 5. 計算アルゴリズム")
    st.markdown("""
    ### 5.1 探索手順
    
    1. **探索範囲の設定**
       - $x_i \\in [x_{start}, x_{end}]$ の範囲で探索
       - 刻み幅: $\\Delta x = x_{step}$
    
    2. **各位置での計算**
       - 幾何学的形状の決定（非線形連立方程式）
       - 作用力の計算（数値積分）
       - モーメント平衡から必要支保圧力を算定
    
    3. **最大値の探索**
       - 全ての $x_i$ に対する $P$ から最大値 $P_{max}$ を特定
       - 対応する位置を危険すべり面位置 $x_{critical}$ として記録
    
    ### 5.2 数値計算手法
    
    - **非線形方程式**: SciPy の `fsolve` を使用
      - 最大反復回数とで収束性を制御
      - 収束判定値で計算精度を調整
    - **数値積分**: SciPy の `quad` を使用（自動適応分割）
    - **収束判定**: ユーザー指定の判定値（デフォルト: $10^{-6}$）
    """)
    
    st.markdown("## 6. 必要支保圧力の評価")
    st.markdown("""
    ### 6.1 判定基準
    
    計算された最大必要支保圧力 $P_{max}$ により切羽の安定性を評価：
    
    | 必要支保圧力 | 判定 | 推奨対策 |
    |:---:|:---:|:---|
    | $P_{max} < 50 kN/m²$ | **安定** 🟢 | 支保不要または軽微な支保 |
    | $50 \\leq P_{max} < 100 kN/m²$ | **要注意** 🟡 | 吹付けコンクリート等の軽微な支保 |
    | $P_{max} \\geq 100 kN/m²$ | **不安定** 🔴 | 鋼製支保工等の強固な支保 |
    
    ### 6.2 支保工の選定
    
    必要支保圧力に応じて適切な支保工を選定：
    - 吹付けコンクリート
    - 鋼製支保工
    - ロックボルト
    - 注入工法
    - これらの組み合わせ
    """)
    
    st.markdown("## 7. 上載荷重計算方法の選択")
    st.markdown("""
    ### 7.1 簡易法
    
    単純に土被り分の重量を考慮：
    - 計算が簡単
    - 保守的な評価（安全側）
    - アーチング効果を無視
    
    ### 7.2 テルツァギーの土圧理論
    
    地盤のアーチング効果を考慮：
    - より現実的な荷重評価
    - すべり土塊幅が小さいほど荷重が軽減
    - 粘着力の効果も考慮
    
    **選択の指針**：
    - 初期検討や保守的評価が必要な場合：簡易法
    - より詳細な検討や経済的設計が必要な場合：テルツァギー法
    """)
    
    st.markdown("## 8. 改良版の特徴")
    st.markdown("""
    従来の村山の式からの主な改良点：
    
    1. **より厳密な幾何学的条件**
       - すべり面始点位置の系統的な探索
       - 終点での角度条件の厳密な適用
    
    2. **精密な力学計算**
       - 数値積分による正確な断面積算定
       - 上載荷重計算方法の選択機能
       - より正確なモーメント腕の計算
    
    3. **実用的な出力**
       - 必要支保圧力による直接的な評価
       - 危険すべり面位置の特定
       - 支保工選定への直接的な指標
    """)
    
    st.markdown("## 9. 参考文献")
    st.markdown("""
    - 村山元英 (1984): 「トンネル切羽の安定解析法」, 地盤工学会誌
    - Terzaghi, K. (1943): "Theoretical Soil Mechanics", John Wiley & Sons
    - 福島啓一 (1994): 『わかりやすいトンネルの力学』, 森北出版
    - 土木学会 (2016): 『トンネル標準示方書［山岳工法編］・同解説』
    - 国総研資料第548号 (2015): 「都市トンネル施工における切羽安定管理指針」
    """)

elif page == "物性値の根拠":
    st.title("📊 物性値の根拠")
    st.markdown("地盤物性値の標準値と決定根拠")
    
    st.markdown("## 1. 地盤種別ごとの標準物性値")
    
    # Create dataframe for soil properties
    soil_data = {
        "地盤種別": ["砂質土（密）", "砂質土（緩）", "粘性土（硬）", "粘性土（軟）", "砂礫", "シルト質砂"],
        "単位体積重量 γ (kN/m³)": [20.0, 18.0, 19.0, 17.0, 21.0, 19.0],
        "粘着力 c (kPa)": [0.0, 0.0, 50.0, 25.0, 0.0, 10.0],
        "内部摩擦角 φ (°)": [35.0, 30.0, 0.0, 0.0, 40.0, 28.0],
        "N値の目安": ["30-50", "10-30", "15-30", "4-15", ">50", "10-30"]
    }
    df_soil = pd.DataFrame(soil_data)
    st.dataframe(df_soil, hide_index=True)
    
    st.markdown("## 2. 物性値の決定根拠")
    
    st.markdown("### 2.1 単位体積重量 (γ)")
    st.markdown("""
    単位体積重量は以下の要因により決定されます：
    - 土粒子の密度
    - 間隙比
    - 飽和度
    
    **一般的な範囲**：
    - 砂質土: 17-21 kN/m³
    - 粘性土: 16-20 kN/m³
    - 砂礫: 20-22 kN/m³
    """)
    
    st.markdown("### 2.2 粘着力 (c)")
    st.markdown("""
    粘着力は土粒子間の結合力を表し、主に粘性土で発現します：
    
    **粘性土の粘着力とN値の関係（Terzaghi & Peck）**：
    - c ≈ 12.5N (kPa)
    
    **砂質土**：
    - 通常 c = 0 と仮定
    - セメンテーションがある場合は若干の粘着力を考慮
    """)
    
    st.markdown("### 2.3 内部摩擦角 (φ)")
    st.markdown("""
    内部摩擦角は土粒子間の摩擦抵抗を表します：
    
    **砂質土の内部摩擦角とN値の関係（大崎の式）**：
    - φ = √(20N) + 15 (°)
    
    **相対密度との関係**：
    - 緩い砂: φ = 28-32°
    - 中密な砂: φ = 32-36°
    - 密な砂: φ = 36-41°
    """)
    
    st.markdown("## 3. 安全側の設計値の選定")
    st.markdown("""
    実際の設計では、以下の点を考慮して安全側の値を選定します：
    
    1. **変動係数の考慮**
       - 粘着力: CV = 0.3-0.5
       - 内部摩擦角: CV = 0.1-0.2
    
    2. **設計用値の算定**
       - 特性値 = 平均値 - 0.5×標準偏差
       - 設計値 = 特性値 / 部分安全係数
    
    3. **部分安全係数**
       - 粘着力: γc = 1.2-1.5
       - tanφ: γφ = 1.1-1.3
    """)
    
    st.markdown("## 4. 参考基準")
    st.markdown("""
    - 道路橋示方書・同解説 Ⅳ下部構造編（日本道路協会）
    - 鉄道構造物等設計標準・同解説 基礎構造物（鉄道総合技術研究所）
    - 建築基礎構造設計指針（日本建築学会）
    - 各種土質試験結果のデータベース
    """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; padding: 1rem 0; color: #666; font-size: 0.9rem;">
        村山式トンネル安定性解析 v0.2 | 改良版村山の式
    </div>
    """,
    unsafe_allow_html=True
)