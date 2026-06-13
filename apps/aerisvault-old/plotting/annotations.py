"""
AerisVault - Plot Export
Export plots to various formats.
"""

import plotly.graph_objects as go
from pathlib import Path
from typing import Optional, Literal
import io


class PlotExporter:
    """Export Plotly figures to various formats."""
    
    @staticmethod
    def export_static_image(
        fig: go.Figure,
        filepath: Path,
        format: Literal['png', 'svg', 'pdf', 'eps'] = 'png',
        width: Optional[int] = None,
        height: Optional[int] = None,
        scale: float = 2.0
    ):
        """
        Export figure as static image.
        
        Args:
            fig: Plotly figure
            filepath: Output file path
            format: Image format
            width: Image width in pixels
            height: Image height in pixels
            scale: Scale factor for resolution
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        fig.write_image(
            str(filepath),
            format=format,
            width=width,
            height=height,
            scale=scale
        )
    
    @staticmethod
    def export_html(
        fig: go.Figure,
        filepath: Path,
        include_plotlyjs: bool = True,
        auto_open: bool = False
    ):
        """
        Export figure as interactive HTML.
        
        Args:
            fig: Plotly figure
            filepath: Output file path
            include_plotlyjs: Include Plotly.js in HTML
            auto_open: Open in browser after export
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        fig.write_html(
            str(filepath),
            include_plotlyjs=include_plotlyjs,
            auto_open=auto_open
        )
    
    @staticmethod
    def to_bytes(
        fig: go.Figure,
        format: Literal['png', 'svg', 'pdf'] = 'png',
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> bytes:
        """Export figure to bytes (for in-memory operations)."""
        return fig.to_image(
            format=format,
            width=width,
            height=height
        )
