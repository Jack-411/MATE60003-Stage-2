from imports import *

from SpectraReader import SpectraReader
from BandGapAnalyzer import BandGapAnalyzer
from Heatmap import HeatmapGenerator
from LabAnalyzer import LabAnalyzer
from FigureExport import ExportFigureWindow

def add_canvas_to_frame(fig, frame):
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, anchor="center")
    return canvas


class BandGapGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Lab Analyser")
        self.master.geometry("950x650")

        self.folder = None
        self.analyzer = None
        self.spectrum_objects = []
        self.current_figure = None

        self.selected_mode = tk.StringVar(value="Trend")
        self.selected_spectrum = tk.StringVar()
        self.fit_plot = tk.BooleanVar(value=True)
        self.show_choices = tk.BooleanVar(value=False)
        self.audio_mode = tk.StringVar(value="Optimal")
        self.audio_plot_type = tk.StringVar(value="Waveform")
        self.selected_folder = tk.StringVar()

        self.preloaded_folders = {
            "Thickness (inner radius adjusted)": (
                Path("inner thickness"),
                "Thickness (inner radius adjusted) (outer kept at 58) (mm)"
            ),
            "Thickness (outer radius adjusted)": (
                Path("outer thickness"),
                "Thickness (outer radius adjusted) (inner kept at 30) (mm)"
            ),
            "Separation (D)": (
                Path("separation"),
                "Separation (D) (mm)"
            ),
            "Slit (W)": (
                Path("slit"),
                "Slit (W) (mm)"
            )
        }

        self._build_gui()

        first = list(self.preloaded_folders.keys())[0]
        self.selected_folder.set(first)
        self._preloaded_folder_changed(first)

    def _build_gui(self):
        mode_frame = tk.Frame(self.master)
        mode_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(mode_frame, text="View:").pack(side=tk.LEFT)

        ttk.OptionMenu(
            mode_frame,
            self.selected_mode,
            "Trend",
            "Trend",
            "Heatmap",
            "Audio Analysis",
            command=self._mode_changed
        ).pack(side=tk.LEFT, padx=5)

        self.mode_controls_container = tk.Frame(self.master)
        self.mode_controls_container.pack(fill=tk.X, padx=5, pady=5)

        self.trend_frame = self._build_trend_controls(self.mode_controls_container)
        self.heatmap_frame = self._build_heatmap_controls(self.mode_controls_container)
        self.audio_frame = self._build_audio_controls(self.mode_controls_container)

        self.plot_container = tk.Frame(self.master)
        self.plot_container.pack(fill=tk.BOTH, expand=True)

        self.plot_frame = tk.Frame(self.plot_container)
        self.plot_frame.pack(fill=tk.BOTH, expand=True)

        self.plot_container.pack_propagate(False)

        bottom = tk.Frame(self.master)
        bottom.pack(fill=tk.X, pady=5)
        tk.Button(bottom, text="Save Figure", command=self.save_current_figure).pack()

        self._mode_changed("Trend")

    def _build_trend_controls(self, parent):
        frame = tk.Frame(parent)

        tk.Label(frame, text="Dataset:").pack(side=tk.LEFT, padx=5)
        ttk.OptionMenu(
            frame,
            self.selected_folder,
            list(self.preloaded_folders.keys())[0],
            *self.preloaded_folders.keys(),
            command=self._preloaded_folder_changed
        ).pack(side=tk.LEFT, padx=5)

        tk.Checkbutton(
            frame,
            text="Polynomial Fit",
            variable=self.fit_plot,
            command=self._display_bandgap_plot
        ).pack(side=tk.LEFT, padx=5)

        tk.Label(frame, text="Spectrum:").pack(side=tk.LEFT)
        self.spectrum_dropdown = ttk.OptionMenu(frame, self.selected_spectrum, "")
        self.spectrum_dropdown.pack(side=tk.LEFT, padx=5)

        return frame

    def _build_heatmap_controls(self, parent):
        frame = tk.Frame(parent)

        tk.Checkbutton(
            frame,
            text="Show Choices",
            variable=self.show_choices,
            command=self.show_heatmap
        ).pack(side=tk.LEFT, padx=5)

        return frame

    def _build_audio_controls(self, parent):
        frame = tk.Frame(parent)

        tk.Label(frame, text="Audio Mode:").pack(side=tk.LEFT)
        ttk.OptionMenu(
            frame,
            self.audio_mode,
            "Optimal",
            "Optimal",
            "Comparison"
        ).pack(side=tk.LEFT, padx=5)

        tk.Label(frame, text="Plot Type:").pack(side=tk.LEFT)
        audio_options = [
            "Waveform",
            "Welch Spectrum",
            "Impulse Response",
            "Insertion Loss",
            "Transfer Function"
        ]
        ttk.OptionMenu(
            frame,
            self.audio_plot_type,
            audio_options[0],
            *audio_options
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(frame, text="Show Audio Plot", command=self.show_audio_plot).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Show IL Comparison", command=self.get_insertion_loss).pack(side=tk.LEFT, padx=5)

        return frame

    def _mode_changed(self, mode):
        for f in (self.trend_frame, self.heatmap_frame, self.audio_frame):
            f.pack_forget()

        if mode == "Trend":
            self.trend_frame.pack(fill=tk.X)
            self._display_bandgap_plot()

        elif mode == "Heatmap":
            self.heatmap_frame.pack(fill=tk.X)
            self.show_heatmap()

        elif mode == "Audio Analysis":
            self.audio_frame.pack(fill=tk.X)
            self.show_audio_plot()

    def _preloaded_folder_changed(self, display_name):
        folder_path, param_name = self.preloaded_folders[display_name]
        if folder_path.exists():
            self.load_folder(folder_path, param_name)

    def load_folder(self, folder_path, param_name):
        self.folder = folder_path
        self.analyzer = BandGapAnalyzer(folder_path, param_name, plot_spectra=False)

        self.spectrum_objects.clear()
        for file in self.folder.glob("*.txt"):
            spec = SpectraReader(file)
            spec.simple_title = " ".join(re.findall(r"[\d.]+|mm", spec.title))
            self.spectrum_objects.append(spec)

        self.spectrum_objects.sort(key=lambda s: float(re.findall(r"[\d.]+", s.simple_title)[0]))

        menu = self.spectrum_dropdown["menu"]
        menu.delete(0, "end")
        for i, spec in enumerate(self.spectrum_objects):
            menu.add_command(label=spec.simple_title, command=lambda idx=i: self.select_spectrum_by_index(idx))

        if self.spectrum_objects:
            self.selected_spectrum.set(self.spectrum_objects[0].simple_title)

        self._display_bandgap_plot()

    def select_spectrum_by_index(self, idx):
        spec = self.spectrum_objects[idx]
        self.selected_spectrum.set(spec.simple_title)
        self.plot_selected_spectrum()

    def _display_bandgap_plot(self):
        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        if self.analyzer is None:
            return

        fig = plt.Figure(figsize=(8, 6))
        ax = fig.add_subplot(111)
        self.current_figure = fig

        x = self.analyzer.data[self.analyzer.param_name].values
        y = self.analyzer.data["Total Band Gap (Hz)"].values

        ax.scatter(x, y, color="blue")

        if self.fit_plot.get():
            best_degree, best_coeffs, best_r2 = self.analyzer.best_fit()
            x_smooth = np.linspace(x.min(), x.max(), 200)
            y_smooth = np.polyval(best_coeffs, x_smooth)
            ax.plot(x_smooth, y_smooth, "r--")

        ax.set_xlabel(self.analyzer.param_name)
        ax.set_ylabel("Total Band Gap (Hz)")
        ax.set_title(f"Band Gap vs {self.analyzer.param_name}")
        fig.tight_layout()

        add_canvas_to_frame(fig, self.plot_frame)

    def plot_selected_spectrum(self):
        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        selected_title = self.selected_spectrum.get()
        spec = next((s for s in self.spectrum_objects if s.simple_title == selected_title), None)
        if spec is None:
            return

        fig, ax = plt.subplots(figsize=(7, 4))
        spec.plot(ax=ax)
        self.current_figure = fig

        add_canvas_to_frame(fig, self.plot_frame)

    def show_heatmap(self):
        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        generator = HeatmapGenerator()
        fig = generator.get_figure(show_choices=self.show_choices.get())
        self.current_figure = fig

        add_canvas_to_frame(fig, self.plot_frame)

    def show_audio_plot(self):
        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        analyzer = LabAnalyzer(mode=self.audio_mode.get())
        plot_map = {
            "Waveform": analyzer.plot_waveform,
            "Welch Spectrum": analyzer.plot_welch_spectrum,
            "Impulse Response": analyzer.plot_impulse_response,
            "Insertion Loss": analyzer.plot_insertion_loss,
            "Transfer Function": analyzer.plot_transfer_function
        }

        fig = plot_map[self.audio_plot_type.get()]()
        self.current_figure = fig

        add_canvas_to_frame(fig, self.plot_frame)

    def get_insertion_loss(self):
        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        analyzer = LabAnalyzer(mode=self.audio_mode.get())
        fig = analyzer.plot_insertion_compare()
        self.current_figure = fig

        add_canvas_to_frame(fig, self.plot_frame)

    def save_current_figure(self):
        if self.current_figure is None:
            messagebox.showwarning("No Figure", "There is no figure to save.")
            return
    
        ExportFigureWindow(self.master, self.current_figure)

if __name__ == "__main__":
    pass