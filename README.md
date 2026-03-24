# 📦 MATE60003 Stage 2 Data Visualiser Guide

A compact python project that analyses the simulation (COMSOL Multiphysics) and tested data that:
- Visualises all data in plots
- Uses Gaussian Blur to create the heatmap
- Audio analyses
- All figures are available to be locally saved at a report level quality

---

## 🏁 Pre-requests
All the site-packages required are listed in:
```bash
imports.py
```

Check `pypi.org` regarding the names of the required site packages:

for Python 2.x or below:
```bash
pip install <name>
```

for Python 3.x:
```bash
pip3 install <name>
```

---

## 🧑‍💻 Usage
Literally run the `main.py`:

for Python 2.x or below:
```bash
python main.py
```

for Python 3.x:
```bash
python3 main.py
```

A GUI will pop out with a plotted trend plot.

---

## 🚀 Features
### 1. Trend
For all the controlled variable simulation data, polynomial fits are applied, this can be turned off by the box on the top, the band gap plot at each point are available in the drop-down menu titled **Spectrum**, by choosing different parameters in the drop-down menu called **Dataset**, different absorption patterns can be seen.
### 2. Heatmap
The heatmap is designed specifically for the separation d and the slit w. Hovering the cursor on the plot will show the live data of the absorption, with the parameters. The choices of the best combination and a worse combination for comparison can be illustrated by ticking the box **Show Choices**
### 3. Audio Analysis
Similar to others, different choices of the plots can be shown
### 4. Save Figures
All figures displayed in the GUI can be saved locally by clicking the **Save Figure** button at the bottom of the window, you can change:
- DPI
- limits of x/y axes
- Height and Width
- Grid
- Legend
- Show or hide the titles
- Texts of the title
- Labels of the axes

---

## 💡 Notes
- This Python project was built and tested under the Python versions `3.11` and `3.12` **only**
- This project was only tested with macOS 26 (Tahoe), glitches on other operating systems might happen

---

## 📝 Known Issues
- The save figure function for heatmap does not work with the current version
