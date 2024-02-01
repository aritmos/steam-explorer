# --- Setup ---

"""
Common setup script for all of the notebooks
Don't forget to add the following lines after running this script:
> %load_ext sql
> %sql engine
> %config SqlMagic.autopandas = True
"""

# --- Notebook Module Imports ---

import os
import sys                                             
sys.path.append(os.path.abspath(os.path.join('../..')))
from config import Config

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import sqlalchemy

# --- DB Connection ---

config = Config()
engine = sqlalchemy.create_engine(config.db_uri)

# --- MyST Markdown ---

# custom class to eliminate quotes in glued string types 
class StrFmt:
    def __init__(self, s: str):
        self.inner = s

    def __repr__(self):
        return self.inner

def fmt(s: str | int | float) -> StrFmt:
    if isinstance(s, str):
        return StrFmt(s)
    if isinstance(s, int | float):
        return StrFmt(f"{s:,}")
    raise Exception("unreachable")

# --- Glueing ---
# Wrappers for `myst_nb.glue` that only take variable names in the local scope

from myst_nb import glue as myst_glue
from IPython.core.magic import register_line_magic
import ast

def glue_core(line: str, display: bool) -> None:
    # execute the line (so the variable can be used later)
    exec(line, get_ipython().user_ns)

    # glue the assigned variables
    line_ast = ast.parse(line, mode="exec")
    target = line_ast.body[0].targets[0]
    
    if isinstance(target, ast.Name):
        # single variable assignment
        var_name = target.id
        var_value = get_ipython().user_ns[var_name]
        myst_glue(var_name, var_value, display)
        
    elif isinstance(target, ast.Tuple) or isinstance(target, ast.List):
        # destructured variable assignment
        var_names = [element.id for element in target.elts]
        var_values = [get_ipython().user_ns[var_name] for var_name in var_names]

        for var_name, var_value in zip(var_names, var_values):
            myst_glue(var_name, var_value, display)

# `glue` does not display the value
@register_line_magic
def glue(line: str) -> None:
   glue_core(line, False)

# `glued` (glue-display) displays the value
@register_line_magic
def glued(line: str) -> None:
    glue_core(line, True)

get_ipython().register_magic_function(glue, magic_kind='line')
get_ipython().register_magic_function(glued, magic_kind='line')

# --- Plotting ---

# https://stackoverflow.com/questions/26085867/matplotlib-font-not-found
# font_path = '/usr/share/fonts/HelveticaNeue/HelveticaNeue.ttf'  # Replace with the actual path
plt.rcParams['font.family'] = 'Helvetica Neue'

blue = "#064A75"
palette_blue_yellow = "blend:#7AB,#EDA"

from matplotlib.colors import LinearSegmentedColormap
colors = ("#ffffff", blue)
bool_blue_cmap = LinearSegmentedColormap.from_list('BinaryTiffanyBlue', colors, len(colors))
