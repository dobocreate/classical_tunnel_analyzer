"""Streamlit app for Murayama tunnel stability analysis."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.models import (
    TunnelGeometry, SoilParameters, LoadingConditions, 
    MurayamaInput, MurayamaResult
)
from src.murayama import MurayamaCalculator, get_default_presets
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

# Add minimal CSS for section styling
st.markdown("""
<style>
    /* セクションのスタイリング */
    div[data-testid="stVerticalBlock"] > div:has(> div > div > h3) {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'calculate_clicked' not in st.session_state:
    st.session_state.calculate_clicked = False
if 'show_graph' not in st.session_state:
    st.session_state.show_graph = False

# Sidebar navigation
with st.sidebar:
    # App logo and title
    st.markdown(
        """
        <div style="text-align: center; padding: 1rem 0;">
            <h1 style="font-size: 1.5rem; margin: 0;">🚇</h1>
            <h2 style="font-size: 1.2rem; margin: 0;">トンネル安定性解析</h2>
            <p style="font-size: 0.8rem; color: #666; margin: 0.5rem 0;">村山の式による評価</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("---")
    
    # Navigation menu
    st.markdown("### 📍 ナビゲーション")
    page = st.radio(
        "ページを選択してください",
        ["🧮 計算ツール", "📚 理論説明", "📊 物性値の根拠"],
        label_visibility="collapsed"
    )
    
    # Map page names for internal use
    page_map = {
        "🧮 計算ツール": "計算",
        "📚 理論説明": "理論説明",
        "📊 物性値の根拠": "物性値の根拠"
    }
    page = page_map[page]
    
    st.markdown("---")
    
    # Additional information
    st.markdown("### ℹ️ 情報")
    st.info(
        """
        **バージョン**: v0.1  
        **開発**: 2024  
        **手法**: 村山の式 (1984)
        """
    )
    
    # Links section
    st.markdown("### 🔗 リンク")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("[📖 使い方](https://github.com/dobocreate/classical_tunnel_analyzer)")
    with col2:
        st.markdown("[💻 GitHub](https://github.com/dobocreate/classical_tunnel_analyzer)")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; font-size: 0.8rem; color: #666;">
            <p>© 2024 Classical Tunnel Analyzer</p>
            <p>Powered by Streamlit</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# Main page based on selection
if page == "計算":
    # Header with description
    st.title("🧮 計算ツール")
    st.markdown(
        """
        <p style="font-size: 1.1rem; color: #555; margin-bottom: 2rem;">
        村山の式を用いてトンネル切羽の安定性を評価します
        </p>
        """,
        unsafe_allow_html=True
    )
    
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
            # Use container with background color to create box-like appearance
            with st.container():
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
                    r0 = st.number_input(
                        "初期半径 r₀ (m) *", 
                        min_value=0.1, 
                        max_value=20.0, 
                        value=5.0, 
                        step=0.5,
                        help="対数螺旋の初期半径"
                    )
        
        st.markdown("")  # Spacing
        
        # Section 2: Soil Parameters
        with st.container():
            st.markdown("### 2️⃣ 地山物性値")
            with st.container():
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
        
        st.markdown("")  # Spacing
        
        # Section 3: Loading Conditions
        with st.container():
            st.markdown("### 3️⃣ 荷重条件")
            with st.container():
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
        
        st.markdown("")  # Spacing
        
        # Section 4: Advanced Settings
        st.markdown("### 4️⃣ 詳細設定（オプション）")
        with st.expander("詳細パラメータを表示"):
            col1, col2 = st.columns(2)
            with col1:
                max_B = st.number_input(
                    "最大すべり幅 (m)", 
                    min_value=1.0, 
                    max_value=50.0, 
                    value=20.0, 
                    step=1.0,
                    help="解析する最大すべり幅"
                )
                step_B = st.number_input(
                    "すべり幅刻み (m)",
                    min_value=0.01,
                    max_value=1.0,
                    value=0.05,
                    step=0.01,
                    help="B値の計算刻み幅"
                )
            with col2:
                n_divisions = st.number_input(
                    "計算分割数",
                    min_value=10,
                    max_value=1000,
                    value=100,
                    step=10,
                    help="数値積分の分割数"
                )
                max_iterations = st.number_input(
                    "最大反復回数",
                    min_value=10,
                    max_value=1000,
                    value=100,
                    step=10,
                    help="収束計算の最大反復回数"
                )
            
            tolerance = st.number_input(
                "収束判定値",
                min_value=1e-10,
                max_value=0.1,
                value=1e-6,
                format="%.2e",
                help="反復計算の収束判定値"
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
            geometry = TunnelGeometry(height=height, r0=r0)
            soil = SoilParameters(gamma=gamma, c=c, phi=phi)
            loading = LoadingConditions(u=u, sigma_v=sigma_v)
            murayama_input = MurayamaInput(
                geometry=geometry,
                soil=soil,
                loading=loading,
                max_B=max_B if 'max_B' in locals() else 20.0,
                step_B=step_B if 'step_B' in locals() else 0.05,
                n_divisions=n_divisions if 'n_divisions' in locals() else 100,
                max_iterations=max_iterations if 'max_iterations' in locals() else 100,
                tolerance=tolerance if 'tolerance' in locals() else 1e-6
            )
            
            # Calculate
            with st.spinner("計算中..."):
                calculator = MurayamaCalculator(murayama_input)
                result = calculator.calculate_curve()
                
                # Store result in session state
                st.session_state['result'] = result
                st.session_state['input'] = murayama_input
        
        # Display results if available
        if 'result' in st.session_state:
            result = st.session_state['result']
            input_params = st.session_state['input']
            
            # Safety factor evaluation
            st.markdown("#### 安全率評価")
            
            # Calculate safety factor (dummy if not available)
            safety_factor = result.safety_factor if result.safety_factor else (result.P_max / 1000)
            
            # Create columns for safety zones
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("🔴 **危険**")
                st.markdown("Fs < 1.0")
            with col2:
                st.markdown("🟡 **要注意**")
                st.markdown("1.0 ≤ Fs < 1.2")
            with col3:
                st.markdown("🟢 **安全**")
                st.markdown("Fs ≥ 1.2")
            
            # Display safety factor as metric
            st.metric("安全率", f"{safety_factor:.2f}")
            
            # Progress bar for safety factor
            progress_value = min(safety_factor / 3.0, 1.0)
            st.progress(progress_value)
            
            # Safety judgment
            if safety_factor >= 1.2:
                st.success("✅ **切羽は安定しています**")
            elif safety_factor >= 1.0:
                st.warning("⚠️ **要注意**")
            else:
                st.error("❌ **切羽は不安定です**")
            
            # Detailed results
            st.markdown("#### 計算結果の詳細")
            
            result_data = {
                "項目": ["最大抵抗力 (P_max)", "臨界幅 (B_critical)", "安全率 (Fs)"],
                "値": [
                    f"{result.P_max:.1f} kN/m",
                    f"{result.B_critical:.2f} m",
                    f"{safety_factor:.2f}"
                ]
            }
            df_results = pd.DataFrame(result_data)
            st.dataframe(df_results, hide_index=True, use_container_width=True)
            
            st.divider()
            
            # Judgment criteria
            with st.expander("判定基準"):
                st.markdown("""
                - **Fs < 1.0**: 危険（対策必須）
                - **1.0 ≤ Fs < 1.2**: 要注意
                - **Fs ≥ 1.2**: 安全
                - **計算方法**: 村山の式（1984）
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
            
            # P-B curve graph
            if st.session_state.show_graph:
                st.markdown("#### P-B曲線")
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=result.B_values,
                    y=result.P_values,
                    mode='lines',
                    name='P-B曲線',
                    line=dict(color='blue', width=2)
                ))
                fig.add_trace(go.Scatter(
                    x=[result.B_critical],
                    y=[result.P_max],
                    mode='markers',
                    name=f'P_max = {result.P_max:.1f} kN/m',
                    marker=dict(color='red', size=12, symbol='star')
                ))
                fig.update_layout(
                    xaxis_title="すべり幅 B [m]",
                    yaxis_title="抵抗力 P [kN/m]",
                    height=300,
                    margin=dict(l=0, r=0, t=20, b=0)
                )
                st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.info("💡 左側のパラメータを入力して「計算実行」をクリックしてください")

elif page == "理論説明":
    st.title("📚 理論説明")
    st.markdown(
        """
        <p style="font-size: 1.1rem; color: #555; margin-bottom: 2rem;">
        村山の式による切羽安定性評価の理論的背景
        </p>
        """,
        unsafe_allow_html=True
    )
    
    # Theory explanation
    st.markdown("## 1. 村山の式の概要")
    st.markdown("""
    村山の式は、トンネル切羽の安定性を評価するための解析手法で、対数螺旋すべり面を仮定した
    極限平衡法に基づいています。この手法は1984年に村山により提案され、現在でも広く使用されています。
    """)
    
    st.markdown("## 2. 基本仮定")
    st.markdown("""
    - すべり面は対数螺旋形状を仮定
    - 土の破壊基準はMohr-Coulombの破壊基準に従う
    - モーメントの釣り合いを考慮
    - 平面ひずみ状態を仮定
    """)
    
    st.markdown("## 3. 対数螺旋すべり面")
    st.markdown("""
    すべり面の形状は以下の式で表されます：
    
    $$r = r_0 e^{\\theta \\tan \\phi}$$
    
    ここで：
    - $r$: 動径
    - $r_0$: 初期動径
    - $\\theta$: 偏角
    - $\\phi$: 内部摩擦角
    """)
    
    st.markdown("## 4. モーメント平衡式")
    st.markdown("""
    切羽に作用する抵抗力 $P$ は、すべり土塊に作用する力のモーメント平衡から求められます：
    
    $$P \\cdot l_p = W_f \\cdot l_w + \\int_{\\theta_0}^{\\theta_1} r \\cdot c \\cdot \\cos \\phi \\, ds$$
    
    ここで：
    - $P$: 切羽抵抗力
    - $l_p$: 抵抗力の作用点からの距離
    - $W_f$: すべり土塊の重量
    - $l_w$: 重量の作用点からの距離
    - $c$: 粘着力
    """)
    
    st.markdown("## 5. 安全率の定義")
    st.markdown("""
    安全率 $F_s$ は、最大抵抗力と作用土圧の比として定義されます：
    
    $$F_s = \\frac{P_{max}}{P_{required}}$$
    
    一般的な判定基準：
    - $F_s \\geq 1.2$: 安全
    - $1.0 \\leq F_s < 1.2$: 要注意
    - $F_s < 1.0$: 危険（対策必須）
    """)
    
    st.markdown("## 6. 参考文献")
    st.markdown("""
    - 村山元英 (1984): 「トンネル切羽の安定解析法」, 地盤工学会誌
    - 福島啓一 (1994): 『わかりやすいトンネルの力学』, 森北出版
    - 国総研資料第548号 (2015): 「都市トンネル施工における切羽安定管理指針」
    """)

elif page == "物性値の根拠":
    st.title("📊 物性値の根拠")
    st.markdown(
        """
        <p style="font-size: 1.1rem; color: #555; margin-bottom: 2rem;">
        地盤物性値の標準値と決定根拠
        </p>
        """,
        unsafe_allow_html=True
    )
    
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
if page in ["計算", "理論説明", "物性値の根拠"]:
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; padding: 2rem 0; color: #666;">
            <p style="margin: 0;">村山式トンネル安定性解析 v0.1 | 村山 (1984) に基づく</p>
        </div>
        """,
        unsafe_allow_html=True
    )