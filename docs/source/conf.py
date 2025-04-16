"""
Sphinx configuration for LogFlow documentation.
"""
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('../..'))

# Project information
project = 'LogFlow'
copyright = '2025, OpenHands'
author = 'OpenHands'
version = '0.1.0'
release = '0.1.0'

# General configuration
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
]

templates_path = ['_templates']
exclude_patterns = []
language = 'pt_BR'

# HTML output
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_title = f"{project} {version}"

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_use_keyword = True
napoleon_custom_sections = None