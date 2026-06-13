"""
AerisVault - LS-DYNA Keyword Parser
Parse LS-DYNA keyword files for additional metadata.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional


class LSDynaKeywordParser:
    """Parse LS-DYNA keyword (.k) files."""
    
    @staticmethod
    def parse_keyword_file(filepath: Path) -> Dict:
        """
        Parse LS-DYNA keyword file.
        
        Args:
            filepath: Path to .k file
            
        Returns:
            Dictionary with parsed information
        """
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        parsed = {
            'keywords': [],
            'title': None,
            'control_settings': {},
            'material_count': 0,
            'part_count': 0
        }
        
        # Extract title
        title_match = re.search(r'\*TITLE\s*\n(.+)', content, re.IGNORECASE)
        if title_match:
            parsed['title'] = title_match.group(1).strip()
        
        # Find all keywords
        keywords = re.findall(r'\*([A-Z_]+)', content)
        parsed['keywords'] = list(set(keywords))
        
        # Count materials
        parsed['material_count'] = content.count('*MAT_')
        
        # Count parts
        parsed['part_count'] = content.count('*PART')
        
        # Extract control settings
        control_match = re.search(r'\*CONTROL_TIMESTEP(.*?)(?=\*|\Z)', content, re.DOTALL | re.IGNORECASE)
        if control_match:
            parsed['control_settings']['timestep'] = control_match.group(1).strip()
        
        return parsed
    
    @staticmethod
    def extract_icfd_settings(filepath: Path) -> Dict:
        """Extract ICFD-specific settings from keyword file."""
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        icfd_settings = {}
        
        # Look for ICFD control cards
        icfd_control = re.search(r'\*ICFD_CONTROL.*?(?=\*|\Z)', content, re.DOTALL | re.IGNORECASE)
        if icfd_control:
            icfd_settings['control_card_found'] = True
        
        return icfd_settings
