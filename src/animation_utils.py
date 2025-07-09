"""Animation utilities for visualizing calculation progress."""
import plotly.graph_objects as go
import numpy as np
from typing import Dict, List
import streamlit as st


def create_slip_surface_animation(animation_frames: List[Dict], 
                                 geometry_params: Dict,
                                 show_realtime: bool = False) -> go.Figure:
    """
    Create animated visualization of slip surface exploration.
    
    Args:
        animation_frames: List of frame data from calculation
        geometry_params: Tunnel geometry parameters
        show_realtime: If True, return figure for real-time updates
        
    Returns:
        Plotly figure with animation
    """
    if not animation_frames:
        return go.Figure()
    
    H = geometry_params['height']
    D_t = geometry_params['tunnel_depth']
    
    # Create figure
    fig = go.Figure()
    
    # Set up layout
    fig.update_layout(
        title="すべり面探索アニメーション",
        xaxis=dict(
            title="水平距離 (m)",
            range=[-15, 15],
            zeroline=True,
            zerolinecolor='black',
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title="深度 (m)",
            range=[-5, D_t + H + 5],
            zeroline=True,
            zerolinecolor='black',
            gridcolor='lightgray',
            scaleanchor="x",
            scaleratio=1
        ),
        plot_bgcolor='white',
        width=800,
        height=600
    )
    
    # Add static elements (tunnel outline)
    # Tunnel face
    fig.add_shape(
        type="rect",
        x0=-0.5, x1=0.5,
        y0=D_t, y1=D_t + H,
        line=dict(color="black", width=3),
        fillcolor="lightgray",
        opacity=0.3
    )
    
    # Ground surface
    fig.add_shape(
        type="line",
        x0=-15, x1=15,
        y0=D_t + H, y1=D_t + H,
        line=dict(color="brown", width=2, dash="dash")
    )
    
    # Add annotation for ground surface
    fig.add_annotation(
        x=12, y=D_t + H + 0.5,
        text="地表面",
        showarrow=False,
        font=dict(color="brown")
    )
    
    if show_realtime:
        # For real-time updates, return base figure
        return fig
    
    # Create animation frames
    frames = []
    for i, frame_data in enumerate(animation_frames):
        frame_traces = []
        
        # Draw all previous slip surfaces in light gray
        for j in range(i + 1):
            slip_surface = create_slip_surface_trace(
                animation_frames[j]['geometry'],
                D_t, H,
                color='lightgray' if j < i else ('red' if animation_frames[j]['is_critical'] else 'blue'),
                width=1 if j < i else 2,
                name=f"x_i = {animation_frames[j]['x_i']:.1f}m"
            )
            frame_traces.append(slip_surface)
        
        # Add P value annotation for current surface
        frame_traces.append(go.Scatter(
            x=[animation_frames[i]['x_i']],
            y=[D_t + H + 2],
            mode='text',
            text=[f"P = {animation_frames[i]['P']:.1f} kPa"],
            textposition="top center",
            showlegend=False
        ))
        
        frames.append(go.Frame(
            data=frame_traces,
            name=str(i),
            traces=list(range(len(frame_traces)))
        ))
    
    # Add initial data
    if animation_frames:
        initial_surface = create_slip_surface_trace(
            animation_frames[0]['geometry'],
            D_t, H,
            color='blue',
            width=2,
            name=f"x_i = {animation_frames[0]['x_i']:.1f}m"
        )
        fig.add_trace(initial_surface)
    
    # Add play/pause buttons only if there are frames
    if frames and len(frames) > 0:
        fig.update_layout(
        updatemenus=[{
            'type': 'buttons',
            'showactive': False,
            'buttons': [
                {
                    'label': '▶ 再生',
                    'method': 'animate',
                    'args': [None, {
                        'frame': {'duration': 500, 'redraw': True},
                        'fromcurrent': True,
                        'mode': 'immediate'
                    }]
                },
                {
                    'label': '⏸ 一時停止',
                    'method': 'animate',
                    'args': [[None], {
                        'frame': {'duration': 0, 'redraw': False},
                        'mode': 'immediate'
                    }]
                }
            ],
            'x': 0.1,
            'y': 1.1
        }],
        sliders=[{
            'active': 0,
            'yanchor': 'top',
            'xanchor': 'left',
            'currentvalue': {
                'font': {'size': 16},
                'prefix': '探索位置: ',
                'visible': True,
                'xanchor': 'right'
            },
            'pad': {'b': 10, 't': 50},
            'len': 0.9,
            'x': 0.1,
            'y': 0,
            'steps': [
                {
                    'args': [[f'{i}'], {
                        'frame': {'duration': 0, 'redraw': True},
                        'mode': 'immediate'
                    }],
                    'label': f'{frame["x_i"]:.1f}m',
                    'method': 'animate'
                }
                for i, frame in enumerate(animation_frames)
            ]
        }],
            frames=frames
        )
    else:
        # If no frames, just return the static figure
        pass
    
    return fig


def create_slip_surface_trace(geometry: Dict, D_t: float, H: float, 
                             color: str = 'blue', width: int = 2,
                             name: str = '') -> go.Scatter:
    """
    Create a plotly trace for a slip surface.
    
    Args:
        geometry: Slip surface geometry data
        D_t: Tunnel depth
        H: Tunnel height
        color: Line color
        width: Line width
        name: Trace name
        
    Returns:
        Plotly scatter trace
    """
    # Generate points along the logarithmic spiral
    theta_i = geometry['theta_i']
    theta_d = geometry['theta_d']
    r_i = geometry['r_i']
    O_x = geometry['center']['x']
    O_y = geometry['center']['y']
    
    # Create theta array
    theta_array = np.linspace(theta_d, theta_i, 50)
    
    # For simplified visualization, approximate with circular arc
    r_array = np.linspace(geometry['r_d'], r_i, 50)
    
    # Convert to x, y coordinates
    x_array = O_x + r_array * np.cos(theta_array)
    y_array = O_y + r_array * np.sin(theta_array)
    
    # Clip to valid region (above tunnel bottom)
    valid_mask = y_array >= D_t
    x_array = x_array[valid_mask]
    y_array = y_array[valid_mask]
    
    return go.Scatter(
        x=x_array,
        y=y_array,
        mode='lines',
        line=dict(color=color, width=width),
        name=name,
        showlegend=True if name else False
    )


def create_convergence_plot(x_values: List[float], P_values: List[float],
                          x_critical: float, P_max: float) -> go.Figure:
    """
    Create plot showing P values vs x_i with critical point highlighted.
    
    Args:
        x_values: List of x_i values
        P_values: List of corresponding P values
        x_critical: Critical x_i value
        P_max: Maximum P value
        
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    # Add P vs x curve
    fig.add_trace(go.Scatter(
        x=x_values,
        y=P_values,
        mode='lines+markers',
        name='必要抑え力 P',
        line=dict(color='blue', width=2),
        marker=dict(size=6)
    ))
    
    # Highlight critical point
    fig.add_trace(go.Scatter(
        x=[x_critical],
        y=[P_max],
        mode='markers',
        name='最大値（危険すべり面）',
        marker=dict(
            size=12,
            color='red',
            symbol='star'
        )
    ))
    
    # Add annotation
    fig.add_annotation(
        x=x_critical,
        y=P_max,
        text=f'最大 P = {P_max:.1f} kPa<br>x = {x_critical:.1f} m',
        showarrow=True,
        arrowhead=2,
        ax=30,
        ay=-40,
        bordercolor='red',
        borderwidth=1,
        bgcolor='white'
    )
    
    fig.update_layout(
        title="すべり面位置と必要抑え力の関係",
        xaxis_title="すべり面始点位置 x_i (m)",
        yaxis_title="必要抑え力 P (kPa)",
        hovermode='x unified',
        plot_bgcolor='white',
        gridcolor='lightgray'
    )
    
    return fig