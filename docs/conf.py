# USD-Bio Sphinx Configuration

import os
import sys

# Project information
project = 'USD-Bio'
copyright = '2025, RIKEN, PRIMe'
author = 'Eliott Jacopin'
release = '0.1.0'

# General configuration
extensions = [
    'breathe',
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Breathe configuration
breathe_projects = {
    "usd-bio": "doxygen_output/xml/"
}
breathe_default_project = "usd-bio"

# HTML output options
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_theme_options = {
    'navigation_depth': 4,
}

# Source file encoding
source_suffix = '.rst'
master_doc = 'index'
