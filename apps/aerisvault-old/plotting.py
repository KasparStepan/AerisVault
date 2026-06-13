"""
AerisVault - Plotting Utilities
Generated with assistance from Claude Sonnet 4 by Anthropic

Plotly-based interactive plotting for simulation results.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Dict


class ResultPlotter:
    """Creates interactive Plotly charts for simulation results."""
    
    @staticmethod
    def plot_single_drag(df: pd.DataFrame, simulation_name: str) -> go.Figure:
        """
        Plot drag forces for a single simulation.
        
        Args:
            df: DataFrame with time-series data
            simulation_name: Name to display in title
            
        Returns:
            Plotly figure
        """
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Pressure Forces (Fp)", "Viscous Forces (Fv)"),
            vertical_spacing=0.12
        )
        
        # Pressure forces
        fig.add_trace(
            go.Scatter(x=df['time'], y=df['Fpx'], name='Fpx', mode='lines'),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['time'], y=df['Fpy'], name='Fpy', mode='lines'),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['time'], y=df['Fpz'], name='Fpz', mode='lines'),
            row=1, col=1
        )
        
        # Viscous forces
        fig.add_trace(
            go.Scatter(x=df['time'], y=df['Fvx'], name='Fvx', mode='lines'),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['time'], y=df['Fvy'], name='Fvy', mode='lines'),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['time'], y=df['Fvz'], name='Fvz', mode='lines'),
            row=2, col=1
        )
        
        fig.update_xaxes(title_text="Time [s]", row=1, col=1)
        fig.update_xaxes(title_text="Time [s]", row=2, col=1)
        fig.update_yaxes(title_text="Force [N]", row=1, col=1)
        fig.update_yaxes(title_text="Force [N]", row=2, col=1)
        
        fig.update_layout(
            title=f"Drag Forces: {simulation_name}",
            height=700,
            hovermode='x unified'
        )
        
        return fig
    
    @staticmethod
    def plot_comparison(
        data_dict: Dict[str, pd.DataFrame], 
        force_component: str = "Fpz"
    ) -> go.Figure:
        """
        Plot comparison of multiple simulations for a single component.
        
        Args:
            data_dict: {simulation_name: DataFrame}
            force_component: Which force component to compare (e.g., 'Fpz')
            
        Returns:
            Plotly figure
        """
        fig = go.Figure()
        
        for sim_name, df in data_dict.items():
            fig.add_trace(
                go.Scatter(
                    x=df['time'],
                    y=df[force_component],
                    name=sim_name,
                    mode='lines',
                    line=dict(width=2)
                )
            )
        
        fig.update_layout(
            title=f"Comparison: {force_component}",
            xaxis_title="Time [s]",
            yaxis_title=f"{force_component} [N]",
            hovermode='x unified',
            height=600,
            legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99)
        )
        
        return fig
    
    @staticmethod
    def plot_multi_axis_comparison(
        data_dict: Dict[str, pd.DataFrame],
        force_components: List[str]
    ) -> go.Figure:
        """
        Plot comparison with multiple force components in subplots.
        
        Args:
            data_dict: {simulation_name: DataFrame}
            force_components: List of force components to plot (e.g., ['Fpx', 'Fpy', 'Fpz'])
            
        Returns:
            Plotly figure with subplots
        """
        n_components = len(force_components)
        
        # Create subplots (one row per component)
        fig = make_subplots(
            rows=n_components,
            cols=1,
            subplot_titles=[f"{comp}" for comp in force_components],
            vertical_spacing=0.08,
            shared_xaxes=True
        )
        
        # Color palette for simulations
        colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        
        # Add traces for each simulation and component
        for idx, (sim_name, df) in enumerate(data_dict.items()):
            color = colors[idx % len(colors)]
            
            for row_idx, component in enumerate(force_components, start=1):
                show_legend = (row_idx == 1)
                
                fig.add_trace(
                    go.Scatter(
                        x=df['time'],
                        y=df[component],
                        name=sim_name,
                        mode='lines',
                        line=dict(width=2, color=color),
                        legendgroup=sim_name,
                        showlegend=show_legend
                    ),
                    row=row_idx,
                    col=1
                )
        
        # Update axes
        for row_idx, component in enumerate(force_components, start=1):
            fig.update_yaxes(title_text=f"{component} [N]", row=row_idx, col=1)
        
        fig.update_xaxes(title_text="Time [s]", row=n_components, col=1)
        
        # Update layout
        height = max(600, 250 * n_components)
        fig.update_layout(
            title="Multi-Axis Comparison",
            height=height,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    @staticmethod
    def plot_statistical_comparison(
        data_dict: Dict[str, pd.DataFrame],
        force_component: str = "Fpz",
        show_bands: bool = True
    ) -> go.Figure:
        """
        Plot comparison with statistical bands (mean ± std).
        
        Args:
            data_dict: {simulation_name: DataFrame}
            force_component: Which force component to compare
            show_bands: Show standard deviation bands
            
        Returns:
            Plotly figure
        """
        fig = go.Figure()
        
        colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        
        for idx, (sim_name, df) in enumerate(data_dict.items()):
            color = colors[idx % len(colors)]
            
            # Mean line
            fig.add_trace(
                go.Scatter(
                    x=df['time'],
                    y=df[force_component],
                    name=sim_name,
                    mode='lines',
                    line=dict(width=2, color=color)
                )
            )
            
            # Add mean line (horizontal)
            mean_val = df[force_component].mean()
            fig.add_hline(
                y=mean_val,
                line_dash="dash",
                line_color=color,
                opacity=0.5,
                annotation_text=f"{sim_name} mean: {mean_val:.2f}",
                annotation_position="right"
            )
        
        fig.update_layout(
            title=f"Statistical Comparison: {force_component}",
            xaxis_title="Time [s]",
            yaxis_title=f"{force_component} [N]",
            hovermode='x unified',
            height=600,
            legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99)
        )
        
        return fig
