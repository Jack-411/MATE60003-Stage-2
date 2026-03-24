from imports import *

class HeatmapGenerator:

    def __init__(self, data_dir=None):
        base_dir = Path(__file__).resolve().parent
        if data_dir is None:
            self.data_dir = base_dir / "Heatmap"
        else:
            self.data_dir = Path(data_dir)

        self.C_SOUND = 343.0
        self.R_MM = 53.0
        self.R_back = 59.0
        self.R_M = self.R_MM / 1000.0

        self.df = None
        self._build_dataframe()

        raw_points = np.column_stack([
            self.df["w_over_R"].values,
            self.df["d_over_R"].values
        ])

        self.raw_tree = cKDTree(raw_points)
        self.raw_values = self.df["total_band_gap"].values

    def _parse_dw(self, filepath):
        filepath = Path(filepath)
        base = filepath.name
        pattern = r"d\s*=\s*([0-9]*\.?[0-9]+)\s*mm\s*w\s*=\s*([0-9]*\.?[0-9]+)\s*mm"
        m = re.search(pattern, base)
        if not m:
            raise ValueError(f"Cannot parse d and w from filename: {base}")
        return float(m.group(1)), float(m.group(2))

    def _load_band_data(self, filepath):
        filepath = Path(filepath)
        data = np.loadtxt(filepath, comments='%')

        if data.ndim == 1:
            data = data.reshape(-1, 2)

        k = data[:, 0]
        f = data[:, 1]

        mask = (~np.isnan(f)) & (k > 0.3)
        return k[mask], f[mask]

    def _split_into_bands(self, k, f):
        bands = []
        start = 0
        for i in range(1, len(k)):
            if k[i] < k[i - 1]:
                bands.append((k[start:i], f[start:i]))
                start = i
        if start < len(k):
            bands.append((k[start:], f[start:]))
        return bands

    def _compute_total_gap(self, bands):
        ranges = []
        for _, f_band in bands:
            ranges.append((np.min(f_band), np.max(f_band)))

        ranges.sort(key=lambda x: x[0])

        total_gap = 0.0
        for i in range(len(ranges) - 1):
            gap = ranges[i + 1][0] - ranges[i][1]
            if gap > 0:
                total_gap += gap

        return total_gap

    def _build_dataframe(self):

        records = []

        txt_files = list(self.data_dir.glob("*.txt"))

        for filepath in txt_files:
            try:
                d_mm, w_mm = self._parse_dw(filepath)
            except ValueError:
                continue

            k, f = self._load_band_data(filepath)
            if len(k) == 0:
                continue

            bands = self._split_into_bands(k, f)
            raw_gap = self._compute_total_gap(bands)

            total_gap = 2 * np.pi * raw_gap * self.R_M / self.C_SOUND

            records.append({
                "d_over_R": d_mm / self.R_MM,
                "w_over_R": w_mm / self.R_MM,
                "total_band_gap": total_gap,
                "raw_gap": raw_gap
            })

        self.df = pd.DataFrame(records)

    def create_base_figure(self):
        x = self.df["w_over_R"].values
        y = self.df["d_over_R"].values
        z = self.df["total_band_gap"].values

        # Create grid
        x_grid = np.linspace(x.min(), x.max(), 300)
        y_grid = np.linspace(y.min(), y.max(), 300)
        Xg, Yg = np.meshgrid(x_grid, y_grid)

        # RBF interpolation
        rbf = Rbf(x, y, z, function='multiquadric', smooth=0.1)
        Zg = rbf(Xg, Yg)

        fig, ax = plt.subplots(figsize=(6, 5))
        cf = ax.pcolormesh(Xg, Yg, Zg, shading="nearest", cmap=plt.cm.turbo)
        fig.colorbar(cf, ax=ax, label="Normalised band gap")

        ax.set_xlabel(r"$w/R$")
        ax.set_ylabel(r"$d/R$")
        ax.set_title("Total Band Gap Heatmap (RBF Smoothed)")

        return fig, ax, Xg, Yg, Zg, x_grid, y_grid

    def create_crosshair(self, ax, x0, y0):
        vline = ax.axvline(x0, color="white", lw=0.8, alpha=0.7, zorder=5000)
        hline = ax.axhline(y0, color="white", lw=0.8, alpha=0.7, zorder=5000)
        vline.set_visible(False)
        hline.set_visible(False)
        return vline, hline

    def create_tooltip(self, fig):
        annot = fig.text(
            0, 0, "",
            ha="left",
            va="bottom",
            fontsize=9,
            bbox=dict(boxstyle="round", fc="white", ec="black", alpha=0.9),
            zorder=9999
        )
        annot.set_visible(False)
        return annot
    
    def connect_hover(self, fig, ax, vline, hline, annot, Xg, Yg, Zg, x_grid, y_grid):
        def on_move(event):
            if not event.inaxes:
                annot.set_visible(False)
                vline.set_visible(False)
                hline.set_visible(False)
                fig.canvas.draw_idle()
                return
    
            vline.set_visible(True)
            hline.set_visible(True)
    
            vline.set_xdata([event.xdata, event.xdata])
            hline.set_ydata([event.ydata, event.ydata])
    
            ix = np.searchsorted(x_grid, event.xdata)
            iy = np.searchsorted(y_grid, event.ydata)
    
            if 0 <= ix < Xg.shape[1] and 0 <= iy < Xg.shape[0]:
                w_val = Xg[iy, ix]
                d_val = Yg[iy, ix]
                gap_val = Zg[iy, ix]
    
                W_mm = w_val * self.R_back
                D_mm = d_val * self.R_back
                raw_gap_interp = gap_val * self.C_SOUND / (2 * np.pi * self.R_M)
    
                fig_x, fig_y = ax.transData.transform((event.xdata, event.ydata))
                fig_x, fig_y = fig.transFigure.inverted().transform((fig_x, fig_y))
    
                annot.set_position((fig_x, fig_y))
                annot.set_text(
                    f"Normalised:\n"
                    f"  w/R = {w_val:.3f}\n"
                    f"  d/R = {d_val:.3f}\n"
                    f"  Gap = {gap_val:.4f}\n\n"
                    f"Original data:\n"
                    f"  w = {W_mm:.1f} mm\n"
                    f"  d = {D_mm:.1f} mm\n"
                    f"  Raw Gap = {raw_gap_interp:.2f} MHz"
                )
                annot.set_visible(True)
    
            fig.canvas.draw_idle()
    
        fig.canvas.mpl_connect("motion_notify_event", on_move)
    
    def add_choice_markers(self, ax):
        ax.plot(1.50, 2.15, 'wo', markersize=8, markeredgecolor='black', zorder=3000)
        ax.text(
            1.50, 2.15, "Best",
            color='white', fontsize=10, ha='center', va='bottom',
            weight='bold', bbox=dict(boxstyle="round,pad=0.2", fc="black", alpha=0.6),
            zorder=3000
        )
    
        ax.plot(0.40, 1.90, 'wo', markersize=8, markeredgecolor='black', zorder=3000)
        ax.text(
            0.40, 1.90, "Worst",
            color='white', fontsize=10, ha='center', va='bottom',
            weight='bold', bbox=dict(boxstyle="round,pad=0.2", fc="black", alpha=0.6),
            zorder=3000
        )
    
    def get_figure(self, show_choices=False):
        fig, ax, Xg, Yg, Zg, x_grid, y_grid = self.create_base_figure()
        vline, hline = self.create_crosshair(ax, x_grid[0], y_grid[0])
        annot = self.create_tooltip(fig)
        self.connect_hover(fig, ax, vline, hline, annot, Xg, Yg, Zg, x_grid, y_grid)
    
        if show_choices:
            self.add_choice_markers(ax)
    
        fig.tight_layout()
        return fig

if __name__ == "__main__":
    pass