from imports import *

class SpectraReader:
    def __init__(self, file_path, tol=1e-6, min_freq=200, max_freq=2000):
        self.file_path = Path(file_path)
        self.tol = tol
        self.min_freq = min_freq
        self.max_freq = max_freq

        self.title = self._make_title()

        self.simple_title = " ".join(re.findall(r"[\d.]+|mm", self.title))

        self.groups = self._read_file()
        self.gaps = self.detect_band_gaps()

    def _make_title(self):
        name = self.file_path.stem
        name = name.replace('_', ' ').replace('-', ' ')
        name = name.replace('mm', ' mm')
        return name.capitalize()

    def _detect_encoding(self):
        with open(self.file_path, 'rb') as f:
            return chardet.detect(f.read())['encoding']

    def _find_data_start(self, encoding):
        with open(self.file_path, 'r', encoding=encoding) as f:
            for i, line in enumerate(f):
                if line.strip() and line.strip()[0].isdigit():
                    return i
        raise ValueError("No numeric data found in the file.")

    def _read_file(self):
        encoding = self._detect_encoding()
        start_row = self._find_data_start(encoding)

        df = pd.read_csv(
            self.file_path,
            skiprows=start_row,
            sep=r'\s+',
            header=None,
            encoding=encoding
        )
        df.columns = ['kxa (rad)', 'Frequency (Hz)']

        group_id = (df['kxa (rad)'] == 0).cumsum()
        grouped = [
            g.reset_index(drop=True)
            for _, g in df.groupby(group_id)
            if len(g) > 3
        ]

        filtered_groups = []
        for g in grouped:
            g_filtered = g[(g['Frequency (Hz)'] >= self.min_freq) & (g['Frequency (Hz)'] <= self.max_freq)]
            if len(g_filtered) > 0:
                filtered_groups.append(g_filtered.reset_index(drop=True))

        return filtered_groups

    def detect_band_gaps(self):
        band_edges = []

        for group in self.groups:
            f = group['Frequency (Hz)'].values
            band_edges.append((f.min(), f.max()))

        band_edges.append((self.min_freq, self.min_freq))
        band_edges.append((self.max_freq, self.max_freq))
        band_edges.sort(key=lambda x: x[0])

        gaps = []
        for (low1, high1), (low2, high2) in zip(band_edges[:-1], band_edges[1:]):
            if low2 - high1 > self.tol:
                gaps.append((high1, low2))

        gaps_clipped = [
            (max(self.min_freq, g[0]), min(self.max_freq, g[1]))
            for g in gaps
            if g[1] > self.min_freq and g[0] < self.max_freq
        ]
        return gaps_clipped

    def total_band_gap(self):
        return sum(g[1] - g[0] for g in self.gaps)

    def plot(self, ax=None):
        fig_created = False
        if ax is None:
            fig, ax = plt.subplots(figsize=(8, 6))
            fig_created = True

        x_min = min(g['kxa (rad)'].min() for g in self.groups)
        x_max = max(g['kxa (rad)'].max() for g in self.groups)

        ax.axhspan(self.min_freq, self.max_freq, color='grey', alpha=0.25, zorder=0)

        for group in self.groups:
            ax.plot(group['kxa (rad)'], group['Frequency (Hz)'],
                    color='black', linewidth=1, zorder=2)

        for gap_start, gap_end in self.gaps:
            ax.axhspan(gap_start, gap_end, color='white', alpha=0.999, zorder=1)
            ax.hlines([gap_start, gap_end], x_min, x_max,
                      linestyles='dotted', colors='red', linewidth=1)

        ax.hlines([self.min_freq, self.max_freq], x_min, x_max,
                  linestyles='solid', colors='blue', linewidth=1, label='Freq limits')

        ax.set_xlabel(r'$k_x a_x$ (rad)')
        ax.set_ylabel('Frequency (Hz)')
        ax.set_title(self.title)
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(self.min_freq, self.max_freq)
        ax.legend()
        if fig_created:
            plt.tight_layout()
            plt.show()

    def extract_thickness(self):
        for token in self.file_path.stem.split():
            if 'mm' in token:
                return float(token.replace('mm', ''))
        raise ValueError("Thickness not found in filename.")


if __name__ == "__main__":
    pass