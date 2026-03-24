# File & data handling
from pathlib import Path
import pandas as pd
import numpy as np
import soundfile as sf 
import scipy.signal as sig 
from scipy.signal import welch
import chardet

# Plotting
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.collections import Collection, QuadMesh, PathCollection, PolyCollection, LineCollection
from matplotlib.patches import Polygon, Rectangle
from matplotlib.lines import Line2D
from PIL import Image, ImageTk
from scipy.ndimage import gaussian_filter
from scipy.interpolate import Rbf
from scipy.spatial import cKDTree
import copy
import ctypes

# Machine learning metrics
from sklearn.metrics import r2_score
from sklearn.neighbors import KNeighborsRegressor

# Jupyter display (optional)
from IPython.display import display

# GUI
import tkinter as tk
from tkinter import ttk, BooleanVar, filedialog
from tkinter import messagebox
import mplcursors

# System operations
import os
import sys
import re
import shutil
import functools

if __name__ == "__main__":
    pass