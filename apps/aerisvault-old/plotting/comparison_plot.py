"""
AerisVault - Comparison Plotting
Create plots comparing multiple simulations.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from ..config import get_settings


class ComparisonPlotter:
    """Create comparative plots for multiple simulations."""
    
    def __init__(self):
        self.settings = get_settings()
    
    def plot_overlay(
        self,
        dfs: List[pd.DataFrame],
        labels: List[str],
        column: str,
        title: Optional[str] = None
    ) -> go.Figure:
        """Overlay multiple simulations on same plot."""
        if title is None:
            title = f"{column} Comparison"
        
        fig = go.Figure()
        colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3']
        
        for idx, (df, label) in enumerate(zip(dfs, labels)):
            color = colors[idx % len(colors)]
            
            fig.add_trace(go.Scatter(
                x=df['time'],
                y=df[column],
                mode='lines',
                name=label,
                line=dict(color=color, width=self.settings.plot_settings.line_width)
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Time (s)",
            yaxis_title=self._get_ylabel(column),
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
    
    def plot_difference(
        self,
        df1: pd.DataFrame,
        df2: pd.DataFrame,
        label1: str,
        label2: str,
        column: str,
        title: Optional[str] = None
    ) -> go.Figure:
        """Plot difference between two simulations."""
        if title is None:
            title = f"{column} Difference: {label2} - {label1}"
        
        # Align time series
        common_time = np.intersect1d(df1['time'], df2['time'])
        df1_aligned = df1[df1['time'].isin(common_time)]
        df2_aligned = df2[df2['time'].isin(common_time)]
        
        difference = df2_aligned[column].values - df1_aligned[column].values
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=common_time,
            y=difference,
            mode='lines',
            name=f'{label2} - {label1}',
            line=dict(color='#636EFA', width=self.settings.plot_settings.line_width)
        ))
        
        # Add zero reference line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        fig.update_layout(
            title=title,
            xaxis_title="Time (s)",
            yaxis_title=f"Δ{column} ({self._get_unit(column)})",
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
    
    def plot_statistics_comparison(
        self,
        stats_df: pd.DataFrame,
        title: str = "Statistical Comparison"
    ) -> go.Figure:
        """Plot comparison of statistics across simulations."""
        fig = go.Figure()
        
        metrics = ['mean', 'std', 'min', 'max', 'rms']
        colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A']
        
        for idx, metric in enumerate(metrics):
            if metric in stats_df.columns:
                fig.add_trace(go.Bar(
                    name=metric.upper(),
                    x=stats_df.index,
                    y=stats_df[metric],
                    marker_color=colors[idx % len(colors)]
                ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Simulation",
            yaxis_title="Value",
            barmode='group',
            template=self.settings.plot_settings.theme,
            width=self.settings.plot_settings.width,
            height=self.settings.plot_settings.height,
            font=dict(size=self.settings.plot_settings.font_size)
        )
        
        return fig
    
    def plot_convergence(
        self,
        convergence_data: Dict,
        title: str = "Convergence Analysis"
    ) -> go.Figure:
        """Plot convergence analysis results."""
        fig = go.Figure()
        
        for column, data in convergence_data.items():
            errors = data['errors']
            fig.add_trace(go.Scatter(
                x=list(range(len(errors))),
                y=errors,
                mode='lines+markers',
                name=column,
                line=dict(width=self.settings.plot_settings.line_width)
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Refinement Level",
            yaxis_title="RMSE",
            yaxis_type="log",
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
    
    def plot_multi_column_comparison(
        self,
        dfs: List[pd.DataFrame],
        labels: List[str],
        columns: List[str],
        title: str = "Multi-Column Comparison"
    ) -> go.Figure:
        """Create subplots comparing multiple columns across simulations."""
        n_cols = len(columns)
        rows = (n_cols + 2) // 3  # 3 columns per row
        cols = min(3, n_cols)
        
        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=columns
        )
        
        colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A']
        
        for col_idx, column in enumerate(columns):
            row = col_idx // 3 + 1
            col = col_idx % 3 + 1
            
            for sim_idx, (df, label) in enumerate(zip(dfs, labels)):
                color = colors[sim_idx % len(colors)]
                
                fig.add_trace(
                    go.Scatter(
                        x=df['time'],
                        y=df[column],
                        mode='lines',
                        name=label,
                        line=dict(color=color, width=2),
                        showlegend=(col_idx == 0)
                    ),
                    row=row,
                    col=col
                )
        
        fig.update_xaxes(title_text="Time (s)")
        fig.update_yaxes(title_text="Value")
        
        fig.update_layout(
            title_text=title,
            height=300 * rows,
            width=self.settings.plot_settings.width,
            font=dict(size=self.settings.plot_settings.font_size)
        )
        
        return fig
    
    def _get_ylabel(self, column: str) -> str:
        """Get appropriate y-axis label for column."""
        if column.startswith('Fp') or column.startswith('Fv'):
            return "Force (N)"
        elif column.startswith('Mp') or column.startswith('Mv'):
            return "Moment (N·m)"
        else:
            return "Value"
    
    def _get_unit(self, column: str) -> str:
        """Get unit for column."""
        if column.startswith('Fp') or column.startswith('Fv'):
            return "N"
        elif column.startswith('Mp') or column.startswith('Mv'):
            return "N·m"
        else:
            return ""
