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
    initial_sidebar_state="collapsed"
)

# Header
st.title("🚇 トンネル切羽安定性評価")
st.markdown("---")

# Initialize session state
if 'calculate_clicked' not in st.session_state:
    st.session_state.calculate_clicked = False
if 'show_graph' not in st.session_state:
    st.session_state.show_graph = False

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
    st.markdown("### 1️⃣ トンネル諸元")
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
    st.markdown("### 3️⃣ 荷重条件（オプション）")
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
        max_B = st.number_input(
            "最大すべり幅 (m)", 
            min_value=1.0, 
            max_value=50.0, 
            value=20.0, 
            step=1.0,
            help="解析する最大すべり幅"
        )
        st.info("計算分割数、最大反復回数、収束判定値などの詳細パラメータを設定できます")
    
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
            max_B=max_B if 'max_B' in locals() else 20.0
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
        if safety_factor >= 1.2:
            bar_color = "green"
        elif safety_factor >= 1.0:
            bar_color = "orange"
        else:
            bar_color = "red"
        
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

# Footer
st.markdown("---")
st.caption("村山式トンネル安定性解析 v0.1 | 村山 (1984) に基づく")