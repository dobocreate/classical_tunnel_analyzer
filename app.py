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
    page_title="Murayama Tunnel Stability Analysis",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("🚇 Murayama Tunnel Stability Evaluation")
st.markdown("""
This application evaluates tunnel face stability using Murayama's method.
Input tunnel geometry and soil parameters to calculate the resistance force curve and maximum resistance.
""")

# Sidebar inputs
st.sidebar.header("Input Parameters")

# Preset selection
st.sidebar.subheader("Soil Presets")
presets = get_default_presets()
preset_names = ["Custom"] + [p.name for p in presets]
selected_preset = st.sidebar.selectbox("Select soil type", preset_names)

# Initialize default values
if selected_preset != "Custom":
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
st.sidebar.subheader("Tunnel Geometry")
height = st.sidebar.number_input(
    "Tunnel face height H [m]", 
    min_value=0.1, 
    max_value=50.0, 
    value=10.0, 
    step=0.5,
    help="Height of the tunnel face"
)
r0 = st.sidebar.number_input(
    "Initial radius r₀ [m]", 
    min_value=0.1, 
    max_value=20.0, 
    value=5.0, 
    step=0.5,
    help="Initial radius for logarithmic spiral"
)

# Soil parameter inputs
st.sidebar.subheader("Soil Parameters")
gamma = st.sidebar.slider(
    "Unit weight γ [kN/m³]", 
    min_value=10.0, 
    max_value=30.0, 
    value=default_gamma, 
    step=0.5,
    help="Effective unit weight of soil"
)
c = st.sidebar.slider(
    "Cohesion c [kPa]", 
    min_value=0.0, 
    max_value=200.0, 
    value=default_c, 
    step=5.0,
    help="Soil cohesion"
)
phi = st.sidebar.slider(
    "Friction angle φ [°]", 
    min_value=0.0, 
    max_value=60.0, 
    value=default_phi, 
    step=1.0,
    help="Internal friction angle"
)

# Loading conditions
st.sidebar.subheader("Loading Conditions")
u = st.sidebar.number_input(
    "Water pressure u [kPa]", 
    min_value=0.0, 
    max_value=1000.0, 
    value=default_u, 
    step=10.0,
    help="Pore water pressure"
)
sigma_v = st.sidebar.number_input(
    "Surcharge σᵥ [kPa]", 
    min_value=0.0, 
    max_value=5000.0, 
    value=default_sigma_v, 
    step=50.0,
    help="Vertical surcharge load"
)

# Analysis parameters
st.sidebar.subheader("Analysis Settings")
max_B = st.sidebar.number_input(
    "Maximum sliding width [m]", 
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
if st.sidebar.button("Calculate", type="primary", use_container_width=True):
    with st.spinner("Calculating..."):
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
        st.subheader("P-B Curve (Resistance Force vs Sliding Width)")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=result.B_values,
            y=result.P_values,
            mode='lines',
            name='P-B Curve',
            line=dict(color='blue', width=2)
        ))
        
        # Add maximum point
        fig.add_trace(go.Scatter(
            x=[result.B_critical],
            y=[result.P_max],
            mode='markers',
            name=f'P_max = {result.P_max:.1f} kN/m',
            marker=dict(color='red', size=12, symbol='star')
        ))
        
        fig.update_layout(
            xaxis_title="Sliding Width B [m]",
            yaxis_title="Resistance Force P [kN/m]",
            hovermode='closest',
            showlegend=True,
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Display key results
        st.subheader("Results Summary")
        
        st.metric("Maximum Resistance P_max", f"{result.P_max:.1f} kN/m")
        st.metric("Critical Width B_critical", f"{result.B_critical:.2f} m")
        
        if result.safety_factor:
            st.metric("Safety Factor", f"{result.safety_factor:.2f}")
            
            # Safety assessment
            if result.safety_factor >= 1.5:
                st.success("✅ Safe (FS ≥ 1.5)")
            elif result.safety_factor >= 1.2:
                st.warning("⚠️ Marginal (1.2 ≤ FS < 1.5)")
            else:
                st.error("❌ Unsafe (FS < 1.2)")
        
        # Input parameters summary
        st.subheader("Input Parameters")
        params_df = pd.DataFrame({
            'Parameter': ['H [m]', 'r₀ [m]', 'γ [kN/m³]', 'c [kPa]', 'φ [°]', 'u [kPa]', 'σᵥ [kPa]'],
            'Value': [
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
    st.subheader("Export Results")
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV export
        csv_data = pd.DataFrame({
            'B [m]': result.B_values,
            'P [kN/m]': result.P_values
        })
        csv_string = csv_data.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv_string,
            file_name="murayama_results.csv",
            mime="text/csv"
        )
    
    with col2:
        # PDF Report generation
        if st.button("Generate PDF Report"):
            with st.spinner("Generating PDF report..."):
                report_gen = ReportGenerator(input_params, result)
                pdf_bytes = report_gen.generate_pdf()
                
                st.download_button(
                    label="Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"murayama_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )

else:
    # No results yet
    st.info("👈 Please input parameters in the sidebar and click 'Calculate' to start the analysis.")
    
    # Show example image or description
    st.subheader("About Murayama's Method")
    st.markdown("""
    Murayama's method analyzes tunnel face stability by considering:
    - Logarithmic spiral failure surface
    - Moment equilibrium of the sliding mass
    - Soil cohesion and friction
    - Water pressure effects
    - External loading conditions
    
    The method calculates the required resistance force P as a function of sliding width B,
    and determines the maximum resistance P_max that the face can provide.
    """)

# Footer
st.markdown("---")
st.caption("Murayama Tunnel Stability Analysis v0.1 | Based on Murayama (1984)")