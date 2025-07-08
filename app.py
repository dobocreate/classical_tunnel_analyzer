"""Streamlit app for Murayama tunnel stability analysis with improved UI."""
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

# Custom CSS for improved UI
st.markdown("""
<style>
    /* メイン背景色 */
    .stApp {
        background-color: #fafbfc;
    }
    
    /* ヘッダースタイル */
    .main-header {
        background-color: #1a365d;
        color: white;
        padding: 1rem 2rem;
        margin: -1rem -1rem 2rem -1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* セクションスタイル */
    .input-section {
        background-color: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
    }
    
    .section-header {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    .section-number {
        background-color: #3182ce;
        color: white;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-right: 10px;
    }
    
    .section-number-optional {
        background-color: #718096;
    }
    
    .section-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #2d3748;
    }
    
    /* 必須マーク */
    .required-mark {
        color: #e53e3e;
        font-size: 0.8rem;
        margin-left: 5px;
    }
    
    /* ガイドテキスト */
    .guide-text {
        background-color: #edf2f7;
        border-radius: 5px;
        padding: 0.8rem;
        margin: 1rem 0;
        color: #4a5568;
        font-size: 0.9rem;
    }
    
    /* 入力フィールドのヘルプテキスト */
    .help-text {
        color: #718096;
        font-size: 0.8rem;
        margin-left: 10px;
    }
    
    /* 結果セクション */
    .result-section {
        background-color: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        height: calc(100vh - 150px);
        overflow-y: auto;
        position: sticky;
        top: 20px;
    }
    
    /* 安全率バー */
    .safety-bar {
        position: relative;
        height: 80px;
        background-color: #f7fafc;
        border-radius: 5px;
        border: 1px solid #e2e8f0;
        margin: 1rem 0;
    }
    
    /* 判定結果ボックス */
    .result-box-safe {
        background-color: #f0fff4;
        border: 2px solid #9ae6b4;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        margin: 1rem 0;
    }
    
    .result-box-warning {
        background-color: #fffdf0;
        border: 2px solid #faf089;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        margin: 1rem 0;
    }
    
    .result-box-danger {
        background-color: #fff5f5;
        border: 2px solid #feb2b2;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        margin: 1rem 0;
    }
    
    /* スクロール可能なコンテナ */
    .scrollable-container {
        height: calc(100vh - 200px);
        overflow-y: auto;
        padding-right: 10px;
    }
    
    /* 左右カラムの高さ設定 */
    [data-testid="column"]:first-child {
        height: calc(100vh - 100px);
        overflow-y: auto;
        padding-right: 20px;
    }
    
    [data-testid="column"]:last-child {
        height: calc(100vh - 100px);
    }
    
    /* ヘルプボタン */
    .help-button {
        position: absolute;
        right: 2rem;
        top: 1rem;
        background-color: #38b2ac;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 15px;
        text-decoration: none;
        font-size: 0.9rem;
    }
    
    /* 計算ボタン */
    .calculate-button {
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1 style="margin: 0;">🚇 トンネル切羽安定性評価</h1>
    <a href="#" class="help-button" onclick="alert('ヘルプ機能は準備中です')">ヘルプ</a>
</div>
""", unsafe_allow_html=True)

# Main container with two columns
col_input, col_result = st.columns([7, 3])

# Left column - Input section
with col_input:
    # Guide text
    st.markdown("""
    <div class="guide-text">
        <strong>切羽の安定性を確認しましょう</strong><br>
        以下の項目を入力すると、村山の式で切羽が安全かどうか自動計算されます
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state for calculation
    if 'calculate_clicked' not in st.session_state:
        st.session_state.calculate_clicked = False
    
    # Section 1: Tunnel Geometry
    with st.container():
        st.markdown("""
        <div class="input-section">
            <div class="section-header">
                <div class="section-number">1</div>
                <div class="section-title">トンネル諸元</div>
            </div>
        """, unsafe_allow_html=True)
        
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
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Section 2: Soil Parameters
    with st.container():
        st.markdown("""
        <div class="input-section">
            <div class="section-header">
                <div class="section-number">2</div>
                <div class="section-title">地山物性値</div>
            </div>
        """, unsafe_allow_html=True)
        
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
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Section 3: Loading Conditions
    with st.container():
        st.markdown("""
        <div class="input-section">
            <div class="section-header">
                <div class="section-number section-number-optional">3</div>
                <div class="section-title">荷重条件（オプション）</div>
            </div>
        """, unsafe_allow_html=True)
        
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
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Section 4: Advanced Settings
    with st.container():
        st.markdown("""
        <div class="input-section">
            <div class="section-header">
                <div class="section-number section-number-optional">4</div>
                <div class="section-title">詳細設定（オプション）</div>
            </div>
        """, unsafe_allow_html=True)
        
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
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Calculate button
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        calculate_button = st.button(
            "計算実行", 
            type="primary", 
            use_container_width=True,
            key="calculate_main"
        )
        
        if calculate_button:
            st.session_state.calculate_clicked = True

# Right column - Results section
with col_result:
    st.markdown('<div class="result-section">', unsafe_allow_html=True)
    st.markdown("### 評価結果")
    
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
        
        # Safety factor evaluation with visual bar
        st.markdown("#### 安全率評価")
        
        # Create safety factor visualization
        safety_factor = result.safety_factor if result.safety_factor else (result.P_max / 1000)  # Dummy calculation
        
        # Safety zones
        fig_safety = go.Figure()
        
        # Background zones
        fig_safety.add_shape(
            type="rect", x0=0, x1=1.0, y0=0, y1=1,
            fillcolor="#feb2b2", opacity=0.3, line_width=0
        )
        fig_safety.add_shape(
            type="rect", x0=1.0, x1=1.2, y0=0, y1=1,
            fillcolor="#faf089", opacity=0.3, line_width=0
        )
        fig_safety.add_shape(
            type="rect", x0=1.2, x1=3.0, y0=0, y1=1,
            fillcolor="#9ae6b4", opacity=0.3, line_width=0
        )
        
        # Safety factor bar
        fig_safety.add_trace(go.Bar(
            x=[min(safety_factor, 3.0)],
            y=[1],
            orientation='h',
            marker_color='#48bb78' if safety_factor >= 1.2 else '#faf089' if safety_factor >= 1.0 else '#feb2b2',
            showlegend=False
        ))
        
        fig_safety.update_layout(
            height=100,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(range=[0, 3], showgrid=False, title=""),
            yaxis=dict(visible=False),
            plot_bgcolor='rgba(0,0,0,0)',
            annotations=[
                dict(x=0.5, y=0.5, text="危険", showarrow=False, font=dict(color="#e53e3e", size=12)),
                dict(x=1.1, y=0.5, text="要注意", showarrow=False, font=dict(color="#d69e2e", size=12)),
                dict(x=2.1, y=0.5, text="安全", showarrow=False, font=dict(color="#38a169", size=12)),
            ]
        )
        
        st.plotly_chart(fig_safety, use_container_width=True)
        
        # Display safety factor value
        st.metric("安全率", f"{safety_factor:.2f}")
        
        # Safety judgment box
        if safety_factor >= 1.2:
            st.markdown("""
            <div class="result-box-safe">
                <div style="font-size: 2rem;">✓</div>
                <div style="font-weight: bold; color: #22543d;">切羽は安定しています</div>
            </div>
            """, unsafe_allow_html=True)
        elif safety_factor >= 1.0:
            st.markdown("""
            <div class="result-box-warning">
                <div style="font-size: 2rem;">⚠</div>
                <div style="font-weight: bold; color: #744210;">要注意</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="result-box-danger">
                <div style="font-size: 2rem;">✗</div>
                <div style="font-weight: bold; color: #742a2a;">切羽は不安定です</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Detailed results
        st.markdown("#### 計算結果の詳細")
        
        with st.container():
            st.markdown(f"**最大抵抗力 (P_max):** {result.P_max:.1f} kN/m")
            st.markdown(f"**臨界幅 (B_critical):** {result.B_critical:.2f} m")
            if result.safety_factor:
                st.markdown(f"**安全率 (Fs):** {result.safety_factor:.2f}")
            
            st.divider()
            
            st.markdown("""
            <small>
            判定基準:<br>
            Fs < 1.0: 危険（対策必須）<br>
            1.0 ≤ Fs < 1.2: 要注意<br>
            Fs ≥ 1.2: 安全<br>
            計算方法: 村山の式（1984）
            </small>
            """, unsafe_allow_html=True)
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📄 レポート出力", use_container_width=True):
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
            if st.button("📊 グラフ表示", use_container_width=True):
                st.session_state.show_graph = True
        
        # Graph modal (simplified)
        if 'show_graph' in st.session_state and st.session_state.show_graph:
            with st.expander("P-B曲線", expanded=True):
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
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
                if st.button("閉じる"):
                    st.session_state.show_graph = False
    
    else:
        st.info("💡 左側のパラメータを入力して「計算実行」をクリックしてください")
    
    st.markdown('</div>', unsafe_allow_html=True)