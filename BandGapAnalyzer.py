from imports import *

from SpectraReader import SpectraReader

class BandGapAnalyzer:
    def __init__(self, folder: str, param_name: str, plot_spectra: bool = False):
        """
        folder: str, path to folder containing TXT files
        param_name: str, name of the physical variable (e.g., 'Thickness (mm)')
        plot_spectra: bool, whether to plot individual spectra
        """
        self.folder = Path(folder)
        self.param_name = param_name
        self.plot_spectra = plot_spectra
        self.data = None
        self._collect_data()

    def _collect_data(self, display_data: bool = False):
        """Scan folder, read spectra, and compute total band gaps."""
        records = []
        for file in self.folder.glob('*.txt'):
            spec = SpectraReader(file)
            if self.plot_spectra:
                spec.plot()
            # Parameter extraction logic (can adjust per variable type)
            param_value = spec.extract_thickness()  # modify if needed for separation/slit
            records.append({
                self.param_name: param_value,
                'Total Band Gap (Hz)': spec.total_band_gap()
            })
        self.data = pd.DataFrame(records).sort_values(self.param_name).reset_index(drop=True)
        if display_data:
            display(self.data)

    def best_fit(self, degrees=(1, 2, 3)):
        """Compute polynomial fit and return best degree based on R²."""
        x = self.data[self.param_name].values
        y = self.data['Total Band Gap (Hz)'].values

        best_r2 = -np.inf
        best_degree = None
        best_coeffs = None
        best_y_fit = None

        for deg in degrees:
            coeffs = np.polyfit(x, y, deg)
            y_fit = np.polyval(coeffs, x)
            r2 = r2_score(y, y_fit)
            if r2 > best_r2:
                best_r2 = r2
                best_degree = deg
                best_coeffs = coeffs
                best_y_fit = y_fit

        return best_degree, best_coeffs, best_r2

    def plot(self, ax=None, show_plot=True, fit_plot=True):
        if self.data is None or self.data.empty:
            raise ValueError("No data available to plot.")
    
        x = self.data[self.param_name].values
        y = self.data['Total Band Gap (Hz)'].values
    
        if ax is None:
            fig, ax = plt.subplots(figsize=(8, 6))
    
        ax.clear()
        ax.scatter(x, y, color='blue', label='Simulation data')
    
        if fit_plot:
            best_degree, best_coeffs, best_r2 = self.best_fit()
            x_smooth = np.linspace(x.min(), x.max(), 200)
            y_smooth = np.polyval(best_coeffs, x_smooth)
            ax.plot(x_smooth, y_smooth, color='red', linestyle='--',
                    label=f'Polynomial fit (deg {best_degree}, R²={best_r2:.3f})')
    
        ax.set_xlabel(self.param_name)
        ax.set_ylabel('Total Band Gap (Hz)')
        ax.set_title(f'Band Gap vs {self.param_name}')
        ax.legend()
        ax.figure.tight_layout()

if __name__ == "__main__":
    pass