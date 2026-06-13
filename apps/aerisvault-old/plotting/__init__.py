"""
AerisVault - Single Simulation Plotting
Create interactive plots for individual simulation results.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
from ..config import get_settings
from ..filters import DataFilter


class SinglePlotter:
    """Create interactive plots for single simulation analysis."""
    
    def __init__(self):
        self.settings = get_settings()
    
    def plot_forces(
        self,
        df: pd.DataFrame,
        components: Optional[List[str]] = None,
        title: str = "Drag Forces",
        enable_filter: Optional[bool] = None,
        filter_params: Optional[Dict[str, Any]] = None,
        annotations: Optional[List[Dict]] = None
    ) -> go.Figure:
        """Plot force components over time."""
        if components is None:
            components = ['Fpx', 'Fpy', 'Fpz']
        
        if enable_filter is None:
            enable_filter = self.settings.filter_settings.enabled_by_default
        
        if filter_params is None:
            filter_params = self._get_default_filter_params()
        
        fig = go.Figure()
        colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A']
        
        for idx, comp in enumerate(components):
            if comp not in df.columns:
                continue
            
            color = colors[idx % len(colors)]
            
            if enable_filter:
                # Original data (dashed)
                fig.add_trace(go.Scatter(
                    x=df['time'],
                    y=df[comp],
                    mode='lines',
                    name=f'{comp} (original)',
                    line=dict(
                        color=color,
                        width=self.settings.plot_settings.line_width,
                        dash=self.settings.plot_settings.original_line_style
                    ),
                    opacity=self.settings.plot_settings.original_line_opacity,
                    showlegend=True
                ))
                
                # Filtered data (solid)
                filter_type = filter_params.get('filter_type', 'savgol')
                params_copy = {k: v for k, v in filter_params.items() if k != 'filter_type'}
                filtered_data = DataFilter.apply_filter(
                    df[comp],
                    df['time'],
                    filter_type,
                    **params_copy
                )
                
                fig.add_trace(go.Scatter(
                    x=df['time'],
                    y=filtered_data,
                    mode='lines',
                    name=f'{comp} (filtered)',
                    line=dict(
                        color=color,
                        width=self.settings.plot_settings.line_width,
                        dash=self.settings.plot_settings.filtered_line_style
                    ),
                    showlegend=True
                ))
            else:
                fig.add_trace(go.Scatter(
                    x=df['time'],
                    y=df[comp],
                    mode='lines',
                    name=comp,
                    line=dict(color=color, width=self.settings.plot_settings.line_width),
                    showlegend=True
                ))
        
        # Add annotations if provided
        if annotations:
            for ann in annotations:
                fig.add_vline(
                    x=ann['time'],
                    line_dash="dash",
                    line_color="gray",
                    annotation_text=ann['label'],
                    annotation_position="top"
                )
        
        fig.update_layout(
            title=title,
            xaxis_title="Time (s)",
            yaxis_title="Force (N)",
            template=self.settings.plot_settings.theme,
            width=self.settings.plot_settings.width,
            height=self.settings.plot_settings.height,
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99
            ),
            font=dict(size=self.settings.plot_settings.font_size)
        )
        
        if self.settings.plot_settings.show_grid:
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        
        return fig
    
    def plot_moments(
        self,
        df: pd.DataFrame,
        components: Optional[List[str]] = None,
        title: str = "Moments",
        enable_filter: Optional[bool] = None,
        filter_params: Optional[Dict[str, Any]] = None,
        annotations: Optional[List[Dict]] = None
    ) -> go.Figure:
        """Plot moment components over time."""
        if components is None:
            components = ['Mpx', 'Mpy', 'Mpz']
        
        if enable_filter is None:
            enable_filter = self.settings.filter_settings.enabled_by_default
        
        if filter_params is None:
            filter_params = self._get_default_filter_params()
        
        fig = go.Figure()
        colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A']
        
        for idx, comp in enumerate(components):
            if comp not in df.columns:
                continue
            
            color = colors[idx % len(colors)]
            
            if enable_filter:
                # Original data
                fig.add_trace(go.Scatter(
                    x=df['time'],
                    y=df[comp],
                    mode='lines',
                    name=f'{comp} (original)',
                    line=dict(
                        color=color,
                        width=self.settings.plot_settings.line_width,
                        dash=self.settings.plot_settings.original_line_style
                    ),
                    opacity=self.settings.plot_settings.original_line_opacity
                ))
                
                # Filtered data
                filter_type = filter_params.get('filter_type', 'savgol')
                params_copy = {k: v for k, v in filter_params.items() if k != 'filter_type'}
                filtered_data = DataFilter.apply_filter(
                    df[comp],
                    df['time'],
                    filter_type,
                    **params_copy
                )
                
                fig.add_trace(go.Scatter(
                    x=df['time'],
                    y=filtered_data,
                    mode='lines',
                    name=f'{comp} (filtered)',
                    line=dict(
                        color=color,
                        width=self.settings.plot_settings.line_width
                    )
                ))
            else:
                fig.add_trace(go.Scatter(
                    x=df['time'],
                    y=df[comp],
                    mode='lines',
                    name=comp,
                    line=dict(color=color, width=self.settings.plot_settings.line_width)
                ))
        
        # Add annotations
        if annotations:
            for ann in annotations:
                fig.add_vline(
                    x=ann['time'],
                    line_dash="dash",
                    line_color="gray",
                    annotation_text=ann['label'],
                    annotation_position="top"
                )
        
        fig.update_layout(
            title=title,
            xaxis_title="Time (s)",
            yaxis_title="Moment (N·m)",
            template=self.settings.plot_settings.theme,
            width=self.settings.plot_settings.width,
            height=self.settings.plot_settings.height,
            hovermode='x unified',
            legend=dict(
                orientation="v",
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99
            ),
            font=dict(size=self.settings.plot_settings.font_size)
        )
        
        if self.settings.plot_settings.show_grid:
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        
        return fig
    
    def plot_resultant_force(
        self,
        df: pd.DataFrame,
        title: str = "Resultant Force Magnitude",
        enable_filter: Optional[bool] = None,
        filter_params: Optional[Dict[str, Any]] = None
    ) -> go.Figure:
        """Plot resultant force magnitude."""
        # Calculate resultant
        resultant = np.sqrt(df['Fpx']**2 + df['Fpy']**2 + df['Fpz']**2)
        
        if enable_filter is None:
            enable_filter = self.settings.filter_settings.enabled_by_default
        
        if filter_params is None:
            filter_params = self._get_default_filter_params()
        
        fig = go.Figure()
        
        if enable_filter:
            # Original
            fig.add_trace(go.Scatter(
                x=df['time'],
                y=resultant,
                mode='lines',
                name='Resultant (original)',
                line=dict(
                    color='#636EFA',
                    width=self.settings.plot_settings.line_width,
                    dash=self.settings.plot_settings.original_line_style
                ),
                opacity=self.settings.plot_settings.original_line_opacity
            ))
            
            # Filtered
            filter_type = filter_params.get('filter_type', 'savgol')
            params_copy = {k: v for k, v in filter_params.items() if k != 'filter_type'}
            filtered = DataFilter.apply_filter(
                resultant,
                df['time'],
                filter_type,
                **params_copy
            )
            
            fig.add_trace(go.Scatter(
                x=df['time'],
                y=filtered,
                mode='lines',
                name='Resultant (filtered)',
                line=dict(color='#636EFA', width=self.settings.plot_settings.line_width)
            ))
        else:
            fig.add_trace(go.Scatter(
                x=df['time'],
                y=resultant,
                mode='lines',
                name='Resultant Force',
                line=dict(color='#636EFA', width=self.settings.plot_settings.line_width)
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Time (s)",
            yaxis_title="Force (N)",
            template=self.settings.plot_settings.theme,
            width=self.settings.plot_settings.width,
            height=self.settings.plot_settings.height,
            hovermode='x unified',
            font=dict(size=self.settings.plot_settings.font_size)
        )
        
        if self.settings.plot_settings.show_grid:
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        
        return fig
    
    def plot_3d_force_trajectory(
        self,
        df: pd.DataFrame,
        title: str = "3D Force Vector Trajectory"
    ) -> go.Figure:
        """Plot 3D trajectory of force vector."""
        fig = go.Figure(data=[go.Scatter3d(
            x=df['Fpx'],
            y=df['Fpy'],
            z=df['Fpz'],
            mode='lines',
            line=dict(
                color=df['time'],
                colorscale='Viridis',
                width=4,
                colorbar=dict(title="Time (s)")
            ),
            text=[f'Time: {t:.3f}s' for t in df['time']],
            hoverinfo='text'
        )])
        
        fig.update_layout(
            title=title,
            scene=dict(
                xaxis_title='Fpx (N)',
                yaxis_title='Fpy (N)',
                zaxis_title='Fpz (N)'
            ),
            width=self.settings.plot_settings.width,
            height=self.settings.plot_settings.height,
            font=dict(size=self.settings.plot_settings.font_size)
        )
        
        return fig
    
    def plot_subplots(
        self,
        df: pd.DataFrame,
        layout: str = '2x2',
        enable_filter: Optional[bool] = None,
        filter_params: Optional[Dict[str, Any]] = None
    ) -> go.Figure:
        """Create subplot layout with multiple plots."""
        if layout == '2x2':
            rows, cols = 2, 2
            subplot_titles = ('Forces X', 'Forces Y', 'Forces Z', 'Resultant')
        elif layout == '3x1':
            rows, cols = 3, 1
            subplot_titles = ('Forces X', 'Forces Y', 'Forces Z')
        else:
            rows, cols = 1, 3
            subplot_titles = ('Forces X', 'Forces Y', 'Forces Z')
        
        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=subplot_titles
        )
        
        if enable_filter is None:
            enable_filter = self.settings.filter_settings.enabled_by_default
        
        if filter_params is None:
            filter_params = self._get_default_filter_params()
        
        components = ['Fpx', 'Fpy', 'Fpz']
        positions = [(1, 1), (1, 2), (2, 1)] if layout == '2x2' else [(i+1, 1) for i in range(3)]
        
        for comp, (row, col) in zip(components, positions):
            if enable_filter:
                # Original
                fig.add_trace(
                    go.Scatter(
                        x=df['time'],
                        y=df[comp],
                        mode='lines',
                        name=f'{comp} (orig)',
                        line=dict(dash='dash'),
                        opacity=0.5,
                        showlegend=False
                    ),
                    row=row, col=col
                )
                
                # Filtered
                filter_type = filter_params.get('filter_type', 'savgol')
                params_copy = {k: v for k, v in filter_params.items() if k != 'filter_type'}
                filtered = DataFilter.apply_filter(df[comp], df['time'], filter_type, **params_copy)
                fig.add_trace(
                    go.Scatter(
                        x=df['time'],
                        y=filtered,
                        mode='lines',
                        name=comp,
                        showlegend=False
                    ),
                    row=row, col=col
                )
            else:
                fig.add_trace(
                    go.Scatter(
                        x=df['time'],
                        y=df[comp],
                        mode='lines',
                        name=comp,
                        showlegend=False
                    ),
                    row=row, col=col
                )
        
        # Add resultant in 4th subplot if 2x2
        if layout == '2x2':
            resultant = np.sqrt(df['Fpx']**2 + df['Fpy']**2 + df['Fpz']**2)
            if enable_filter:
                filtered_res = DataFilter.apply_filter(resultant, df['time'], **filter_params)
                fig.add_trace(
                    go.Scatter(x=df['time'], y=filtered_res, mode='lines', name='Resultant'),
                    row=2, col=2
                )
            else:
                fig.add_trace(
                    go.Scatter(x=df['time'], y=resultant, mode='lines', name='Resultant'),
                    row=2, col=2
                )
        
        fig.update_xaxes(title_text="Time (s)")
        fig.update_yaxes(title_text="Force (N)")
        
        fig.update_layout(
            height=800,
            width=self.settings.plot_settings.width,
            showlegend=False,
            font=dict(size=self.settings.plot_settings.font_size)
        )
        
        return fig
    
    def _get_default_filter_params(self) -> Dict[str, Any]:
        """Get default filter parameters from settings."""
        fs = self.settings.filter_settings
        filter_type = fs.default_filter_type
        
        params = {'filter_type': filter_type}
        
        if filter_type == 'savgol':
            params['window_length'] = fs.savgol_window_length
            params['polyorder'] = fs.savgol_polyorder
        elif filter_type == 'moving_average':
            params['window'] = fs.moving_avg_window
        elif filter_type == 'lowpass':
            params['cutoff_freq'] = fs.lowpass_cutoff_freq
            params['order'] = fs.lowpass_order
        
        return params
