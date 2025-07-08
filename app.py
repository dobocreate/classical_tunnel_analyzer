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

# Title and description
st.title("🚇 村山式トンネル安定性評価")
st.markdown("""
このアプリケーションは村山法を用いてトンネル切羽の安定性を評価します。
トンネル形状と地盤パラメータを入力して、抵抗力曲線と最大抵抗力を計算します。
""")

# Sidebar inputs
st.sidebar.header("入力パラメータ")

# Preset selection
st.sidebar.subheader("地盤プリセット")
presets = get_default_presets()
preset_names = ["カスタム"] + [p.name for p in presets]
selected_preset = st.sidebar.selectbox("地盤タイプを選択", preset_names)

# Initialize default values
if selected_preset != "カスタム":
    preset = next(p for p in presets if p.name == selected_preset)
    default_gamma = preset.soil.gamma
    default_c = preset.soil.c
    default_phi = preset.soil.phi
    default_u = preset.typical_loading.u
    default_sigma_v = preset.typical_loading.sigma_v
else:
    default_gamma = 20.0
    default_c = 30.0
    default_phi = 30.0
    default_u = 0.0
    default_sigma_v = 0.0

# Tunnel geometry inputs
st.sidebar.subheader("トンネル形状")
height = st.sidebar.number_input(
    "トンネル切羽高さ H [m]", 
    min_value=0.1, 
    max_value=50.0, 
    value=10.0, 
    step=0.5,
    help="トンネル切羽の高さ"
)
r0 = st.sidebar.number_input(
    "初期半径 r₀ [m]", 
    min_value=0.1, 
    max_value=20.0, 
    value=5.0, 
    step=0.5,
    help="対数螺旋の初期半径"
)

# Soil parameter inputs
st.sidebar.subheader("地盤パラメータ")
gamma = st.sidebar.slider(
    "単位体積重量 γ [kN/m³]", 
    min_value=10.0, 
    max_value=30.0, 
    value=default_gamma, 
    step=0.5,
    help="地盤の有効単位体積重量"
)
c = st.sidebar.slider(
    "粘着力 c [kPa]", 
    min_value=0.0, 
    max_value=200.0, 
    value=default_c, 
    step=5.0,
    help="地盤の粘着力"
)
phi = st.sidebar.slider(
    "内部摩擦角 φ [°]", 
    min_value=0.0, 
    max_value=60.0, 
    value=default_phi, 
    step=1.0,
    help="地盤の内部摩擦角"
)

# Loading conditions
st.sidebar.subheader("荷重条件")
u = st.sidebar.number_input(
    "水圧 u [kPa]", 
    min_value=0.0, 
    max_value=1000.0, 
    value=default_u, 
    step=10.0,
    help="間隙水圧"
)
sigma_v = st.sidebar.number_input(
    "上載荷重 σᵥ [kPa]", 
    min_value=0.0, 
    max_value=5000.0, 
    value=default_sigma_v, 
    step=50.0,
    help="鉛直上載荷重"
)

# Analysis parameters
st.sidebar.subheader("解析設定")
max_B = st.sidebar.number_input(
    "最大すべり幅 [m]", 
    min_value=1.0, 
    max_value=50.0, 
    value=20.0, 
    step=1.0
)

# Create input objects
geometry = TunnelGeometry(height=height, r0=r0)
soil = SoilParameters(gamma=gamma, c=c, phi=phi)
loading = LoadingConditions(u=u, sigma_v=sigma_v)
murayama_input = MurayamaInput(
    geometry=geometry,
    soil=soil,
    loading=loading,
    max_B=max_B
)

# Calculate button
if st.sidebar.button("計算実行", type="primary", use_container_width=True):
    with st.spinner("計算中..."):
        # Perform calculation
        calculator = MurayamaCalculator(murayama_input)
        result = calculator.calculate_curve()
        
        # Store result in session state
        st.session_state['result'] = result
        st.session_state['input'] = murayama_input

# Main area - Results display
if 'result' in st.session_state:
    result = st.session_state['result']
    input_params = st.session_state['input']
    
    # Create columns for layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Plot P-B curve
        st.subheader("P-B曲線（抵抗力 vs すべり幅）")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=result.B_values,
            y=result.P_values,
            mode='lines',
            name='P-B曲線',
            line=dict(color='blue', width=2)
        ))
        
        # Add maximum point
        fig.add_trace(go.Scatter(
            x=[result.B_critical],
            y=[result.P_max],
            mode='markers',
            name=f'最大抵抗力 P_max = {result.P_max:.1f} kN/m',
            marker=dict(color='red', size=12, symbol='star')
        ))
        
        fig.update_layout(
            xaxis_title="すべり幅 B [m]",
            yaxis_title="抵抗力 P [kN/m]",
            hovermode='closest',
            showlegend=True,
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Display key results
        st.subheader("結果の概要")
        
        st.metric("最大抵抗力 P_max", f"{result.P_max:.1f} kN/m")
        st.metric("臨界幅 B_critical", f"{result.B_critical:.2f} m")
        
        if result.safety_factor:
            st.metric("安全率", f"{result.safety_factor:.2f}")
            
            # Safety assessment
            if result.safety_factor >= 1.5:
                st.success("✅ 安全 (FS ≥ 1.5)")
            elif result.safety_factor >= 1.2:
                st.warning("⚠️ 要注意 (1.2 ≤ FS < 1.5)")
            else:
                st.error("❌ 危険 (FS < 1.2)")
        
        # Input parameters summary
        st.subheader("入力パラメータ")
        params_df = pd.DataFrame({
            'パラメータ': ['H [m]', 'r₀ [m]', 'γ [kN/m³]', 'c [kPa]', 'φ [°]', 'u [kPa]', 'σᵥ [kPa]'],
            '値': [
                input_params.geometry.height,
                input_params.geometry.r0,
                input_params.soil.gamma,
                input_params.soil.c,
                input_params.soil.phi,
                input_params.loading.u,
                input_params.loading.sigma_v
            ]
        })
        st.dataframe(params_df, hide_index=True)
    
    # Export options
    st.subheader("結果のエクスポート")
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV export
        csv_data = pd.DataFrame({
            'B [m]': result.B_values,
            'P [kN/m]': result.P_values
        })
        csv_string = csv_data.to_csv(index=False)
        st.download_button(
            label="CSVダウンロード",
            data=csv_string,
            file_name="murayama_results.csv",
            mime="text/csv"
        )
    
    with col2:
        # PDF Report generation
        if st.button("PDFレポート生成"):
            with st.spinner("PDFレポートを生成中..."):
                report_gen = ReportGenerator(input_params, result)
                pdf_bytes = report_gen.generate_pdf()
                
                st.download_button(
                    label="PDFレポートダウンロード",
                    data=pdf_bytes,
                    file_name=f"murayama_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )

else:
    # No results yet
    st.info("👈 サイドバーにパラメータを入力し、「計算実行」をクリックして解析を開始してください。")
    
    # Show example image or description
    st.subheader("村山法について")
    st.markdown("""
    村山法は以下を考慮してトンネル切羽の安定性を解析します：
    - 対数螺旋破壊面
    - すべり土塊のモーメント均衡
    - 地盤の粘着力と摩擦
    - 水圧の影響
    - 外部荷重条件
    
    この手法は、すべり幅Bの関数として必要抵抗力Pを計算し、
    切羽が提供できる最大抵抗力P_maxを決定します。
    """)

# Footer
st.markdown("---")
st.caption("村山式トンネル安定性解析 v0.1 | 村山 (1984) に基づく")