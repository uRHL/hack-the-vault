import sys
import os
sys.path.insert(0, os.path.abspath('../../src'))  # Add our project to the path
import htv
# import constants
# import resources
# import utils


# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = htv.constants.DOCS['PROJECT_NAME']
author = htv.constants.DOCS['AUTHOR']
copyright = f'2025, {author}'
release = htv.constants.VERSION

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = htv.constants.DOCS['EXTENSIONS']

templates_path = ['_templates']
exclude_patterns = []

language = 'en'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
