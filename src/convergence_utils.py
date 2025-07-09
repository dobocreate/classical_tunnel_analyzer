"""Utilities for convergence visualization and analysis."""
import plotly.graph_objects as go
import numpy as np
from typing import Dict, List, Optional
import streamlit as st


def create_convergence_history_plot(convergence_sample: List[Dict], 
                                  tolerance: float) -> go.Figure:
    """
    Create plot showing convergence history of the solver.
    
    Args:
        convergence_sample: List of convergence data from fsolve
        tolerance: Convergence tolerance value
        
    Returns:
        Plotly figure showing convergence history
    """
    if not convergence_sample:
        return go.Figure()
    
    iterations = [d['iteration'] for d in convergence_sample]
    errors = [d['error'] for d in convergence_sample]
    
    fig = go.Figure()
    
    # Add error history
    fig.add_trace(go.Scatter(
        x=iterations,
        y=errors,
        mode='lines+markers',
        name='誤差 (残差ノルム)',
        line=dict(color='blue', width=2),
        marker=dict(size=6)
    ))
    
    # Add tolerance line
    fig.add_trace(go.Scatter(
        x=[iterations[0], iterations[-1]],
        y=[tolerance, tolerance],
        mode='lines',
        name=f'収束判定値 ({tolerance:.1e})',
        line=dict(color='red', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title="反復計算の収束履歴",
        xaxis_title="反復回数",
        yaxis_title="誤差 (残差ノルム)",
        yaxis_type="log",  # Log scale for better visualization
        plot_bgcolor='white',
        hovermode='x unified',
        height=400
    )
    
    return fig


def create_convergence_statistics_plot(successful_convergences: List[Dict]) -> go.Figure:
    """
    Create plot showing convergence statistics across all x_i values.
    
    Args:
        successful_convergences: List of convergence data for each x_i
        
    Returns:
        Plotly figure showing convergence statistics
    """
    if not successful_convergences:
        return go.Figure()
    
    x_values = [d['x_i'] for d in successful_convergences]
    iterations = [d['iterations'] for d in successful_convergences]
    
    fig = go.Figure()
    
    # Bar chart of iterations needed
    fig.add_trace(go.Bar(
        x=x_values,
        y=iterations,
        name='反復回数',
        marker=dict(
            color=iterations,
            colorscale='Blues',
            showscale=True,
            colorbar=dict(title="反復回数")
        )
    ))
    
    fig.update_layout(
        title="各すべり面位置での収束性能",
        xaxis_title="すべり面始点位置 x_i (m)",
        yaxis_title="収束までの反復回数",
        plot_bgcolor='white',
        height=400
    )
    
    return fig


def show_calculation_progress(placeholder, status_data: Dict):
    """
    Display real-time calculation progress.
    
    Args:
        placeholder: Streamlit placeholder for updates
        status_data: Dictionary with progress information
    """
    with placeholder.container():
        # Progress bar
        progress = status_data.get('progress', 0)
        st.progress(progress, text=f"計算進捗: {progress:.0%}")
        
        # Status metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "現在の探索位置",
                f"{status_data.get('x_i', 0):.1f} m"
            )
        
        with col2:
            st.metric(
                "収束成功",
                f"{status_data.get('successful', 0)} 点",
                delta=f"+{status_data.get('successful', 0)}"
            )
        
        with col3:
            st.metric(
                "収束失敗",
                f"{status_data.get('failed', 0)} 点",
                delta=f"+{status_data.get('failed', 0)}" if status_data.get('failed', 0) > 0 else None,
                delta_color="inverse"
            )
        
        with col4:
            successful = status_data.get('successful', 0)
            failed = status_data.get('failed', 0)
            total = successful + failed
            
            if total > 0:
                success_rate = (successful / total) * 100
                rate_text = f"{success_rate:.1f}%"
            else:
                rate_text = "--"  # まだ計算が始まっていない
            
            st.metric(
                "収束率",
                rate_text
            )
        
        # Visual status indicator
        if status_data.get('status') == 'calculating':
            st.info("🔄 幾何形状を計算中...")
        elif status_data.get('status') == 'completed':
            st.success("✅ 計算完了！")


def create_convergence_summary_table(result) -> Dict:
    """
    Create summary statistics for convergence performance.
    
    Args:
        result: MurayamaResult object
        
    Returns:
        Dictionary with summary statistics
    """
    if not result.convergence_info:
        return {}
    
    conv_info = result.convergence_info
    successful = conv_info.get('successful_convergences', [])
    
    if successful:
        iterations_list = [s['iterations'] for s in successful]
        avg_iterations = np.mean(iterations_list)
        max_iterations = np.max(iterations_list)
        min_iterations = np.min(iterations_list)
    else:
        avg_iterations = max_iterations = min_iterations = 0
    
    return {
        "総探索点数": conv_info.get('total_points', 0),
        "収束成功点数": conv_info.get('successful_points', 0),
        "収束失敗点数": conv_info.get('convergence_failures', 0),
        "収束率": f"{conv_info.get('convergence_rate', 0):.1f}%",
        "平均反復回数": f"{avg_iterations:.1f}",
        "最大反復回数": max_iterations,
        "最小反復回数": min_iterations
    }