from imports import *

eps = 1e-14

def load_wav(filename):
    y, fs = sf.read(filename)
    if y.ndim > 1:
        y = y.mean(axis=1)
    return y.astype(np.float32), fs

def load_wav_to_dataframe(filename):
    signal, fs = load_wav(filename)
    t = np.arange(len(signal)) / fs
    df = pd.DataFrame({"time_s": t, "amplitude": signal})
    return signal, fs, df

#  MAIN CLASS
class LabAnalyzer:
    def __init__(self, mode="Optimal"):
        base = Path(__file__).resolve().parent

        # Load the main dataset (Optimal or Comparison)
        exp_dir = base / "Experimental Data" / mode
        self.ref_path = exp_dir / "sound_recorded_reference.wav"
        self.sam_path = exp_dir / "sound_recorded_sample.wav"
        self.sweep_path = exp_dir / "sound_played_reference.wav"
        self.ir_ref_path = exp_dir / "impulse_response_reference.wav"
        self.ir_sam_path = exp_dir / "impulse_response_sample.wav"

        # Load reference and sample for the selected mode
        self.sig_ref, self.fs_ref, self.df_ref = load_wav_to_dataframe(self.ref_path)
        self.sig_sam, self.fs_sam, self.df_sam = load_wav_to_dataframe(self.sam_path)

        # Sweep (only needed for transfer function)
        self.sweep, self.fs_sweep = load_wav(self.sweep_path)

        # Load impulse responses
        self.ir_ref, self.fs_ir_ref = load_wav(self.ir_ref_path)
        self.ir_sam, self.fs_ir_sam = load_wav(self.ir_sam_path)

        # Load optimal and comparison reference signals for insertion loss comparison (if available)
        opt_dir = base / "Experimental Data" / "Optimal"
        comp_dir = base / "Experimental Data" / "Comparison"

        self.sig_ref_opt, self.fs_ref_opt, _ = load_wav_to_dataframe(opt_dir / "sound_recorded_reference.wav")
        self.sig_sam_opt, self.fs_sam_opt, _ = load_wav_to_dataframe(opt_dir / "sound_recorded_sample.wav")

        self.sig_ref_comp, self.fs_ref_comp, _ = load_wav_to_dataframe(comp_dir / "sound_recorded_reference.wav")
        self.sig_sam_comp, self.fs_sam_comp, _ = load_wav_to_dataframe(comp_dir / "sound_recorded_sample.wav")

    #  PLOT 1 — WAVEFORM COMPARISON
    def plot_waveform(self):
        fig, ax = plt.subplots(figsize=(12, 5))

        t_ref = np.arange(len(self.sig_ref)) / self.fs_ref
        t_sam = np.arange(len(self.sig_sam)) / self.fs_sam

        ax.plot(t_ref, self.sig_ref, color="blue", label="Reference")
        ax.plot(t_sam, self.sig_sam, color="red", label="Sample")

        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Amplitude")
        ax.set_title("Reference vs Sample – Waveform")
        ax.legend()
        ax.grid(False)
        fig.tight_layout()

        return fig

    #  PLOT 2 — WELCH PSD SPECTRUM
    def plot_welch_spectrum(self):
        f_ref, P_ref = welch(self.sig_ref, self.fs_ref, nperseg=4096)
        f_sam, P_sam = welch(self.sig_sam, self.fs_sam, nperseg=4096)

        mask_ref = (f_ref >= 1) & (f_ref <= 2000)
        mask_sam = (f_sam >= 1) & (f_sam <= 2000)

        ref_dB = 10*np.log10(P_ref[mask_ref] + 1e-12)
        sam_dB = 10*np.log10(P_sam[mask_sam] + 1e-12)

        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(f_ref[mask_ref], ref_dB, color="blue", label="Reference")
        ax.plot(f_sam[mask_sam], sam_dB, color="red", label="Sample")

        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Magnitude (dB)")
        ax.set_title("Spectral Response Comparison (Welch PSD)")
        ax.grid(False)
        ax.set_xlim(200, 2000)
        ax.legend()
        fig.tight_layout()

        return fig

    # PLOT 3 — IMPULSE RESPONSE COMPARISON
    def plot_impulse_response(self):
        # Time axis in milliseconds
        t_ref = np.arange(len(self.ir_ref)) / self.fs_ir_ref * 1000
        t_sam = np.arange(len(self.ir_sam)) / self.fs_ir_sam * 1000

        fig, ax = plt.subplots(figsize=(12, 5))

        ax.plot(t_ref, self.ir_ref, color="blue", label="Reference IR")
        ax.plot(t_sam, self.ir_sam, color="red", label="Sample IR")

        ax.set_xlabel("Time (ms)")
        ax.set_ylabel("Amplitude")
        ax.set_title("Impulse Response Comparison")
        ax.legend()
        ax.grid(False)
        fig.tight_layout()

        return fig

    #  PLOT 4 — INSERTION LOSS
    def plot_insertion_loss(self):
        f_ref, P_ref = welch(self.sig_ref, self.fs_ref, nperseg=4096)
        f_sam, P_sam = welch(self.sig_sam, self.fs_sam, nperseg=4096)

        f_common = np.linspace(max(f_ref.min(), f_sam.min()),
                               min(f_ref.max(), f_sam.max()), 4000)

        P_ref_i = np.interp(f_common, f_ref, P_ref)
        P_sam_i = np.interp(f_common, f_sam, P_sam)

        mag_ref_dB = 10*np.log10(P_ref_i + 1e-12)
        mag_sam_dB = 10*np.log10(P_sam_i + 1e-12)

        IL_dB = mag_ref_dB - mag_sam_dB

        mask = (f_common >= 200) & (f_common <= 2000)

        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(f_common[mask], IL_dB[mask], color="green")

        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Insertion Loss (dB)")
        ax.set_title("Insertion Loss (Welch PSD)")
        ax.grid(False)
        ax.set_xlim(200, 2000)
        ax.axhline(0, color="k", linestyle="--", alpha=0.3)
        fig.tight_layout()

        return fig

    #  PLOT 5 — TRANSFER FUNCTION (PROFESSOR METHOD)
    def build_inverse_filter(self, sweep, fs, f_start, f_end, duration):
        T = duration
        L = np.log(f_end / f_start)
        t = np.arange(int(T * fs)) / fs
        w = np.exp(-t * L / T).astype(np.float32)
        inv = (sweep[::-1] * w).astype(np.float32)
        test = sig.fftconvolve(sweep, inv, mode="full")
        inv /= (np.max(np.abs(test)) + eps)
        return inv

    def compute_impulse_response(self, x, y, inv, fs):
        corr = sig.correlate(y, x, mode="full", method="fft")
        lag = np.argmax(corr) - (len(x) - 1)

        if lag > 0:
            y = y[lag:]
            x = x[:len(y)]
        elif lag < 0:
            x = x[-lag:]
            y = y[:len(x)]

        Lmin = min(len(x), len(y))
        x = x[:Lmin]
        y = y[:Lmin]

        ir_full = sig.fftconvolve(y, inv, mode="full")

        peak = np.argmax(np.abs(ir_full))
        pre = int(0.001 * fs)
        post = int(0.05 * fs)

        start = max(0, peak - pre)
        stop = min(len(ir_full), peak + post)
        ir = ir_full[start:stop]

        fade_len = int(0.01 * fs)
        if fade_len < len(ir):
            fade = np.ones_like(ir)
            fade[-fade_len:] *= np.hanning(2 * fade_len)[-fade_len:]
            ir *= fade

        return ir

    def compute_transfer_function(self, ir, fs):
        nfft = int(2 ** np.ceil(np.log2(len(ir))))
        H = np.fft.rfft(ir, n=nfft)
        f = np.fft.rfftfreq(nfft, 1/fs)
        mag = 20*np.log10(np.abs(H) + eps)
        return f, mag

    def plot_transfer_function(self):
        f_start = 100
        f_end = 2500
        duration = 8.0
        pad = 1.0

        pad_samples = int(pad * self.fs_sweep)
        sweep = self.sweep[pad_samples : pad_samples + int(duration * self.fs_sweep)]

        inv = self.build_inverse_filter(sweep, self.fs_sweep, f_start, f_end, duration)

        ir_ref = self.compute_impulse_response(sweep, self.sig_ref, inv, self.fs_sweep)
        ir_sam = self.compute_impulse_response(sweep, self.sig_sam, inv, self.fs_sweep)

        f_ref, mag_ref = self.compute_transfer_function(ir_ref, self.fs_sweep)
        f_sam, mag_sam = self.compute_transfer_function(ir_sam, self.fs_sweep)

        mask_ref = (f_ref >= 200) & (f_ref <= 2000)
        mask_sam = (f_sam >= 200) & (f_sam <= 2000)

        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(f_ref[mask_ref], mag_ref[mask_ref], color="blue", label="Reference")
        ax.plot(f_sam[mask_sam], mag_sam[mask_sam], color="red", label="Sample")

        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Magnitude (dB)")
        ax.set_title("Spectral Response Comparison (Transfer Function)")
        ax.grid(False)
        ax.set_xlim(200, 2000)
        ax.legend()
        fig.tight_layout()

        return fig

    # PLOT 6 - Compare insertion loss of Optimal and Comparison samples (Plot both lines with legend)
    def plot_insertion_compare(self):
        f_opt_r, P_opt_r = welch(self.sig_ref_opt, self.fs_ref_opt, nperseg=4096)
        f_opt_s, P_opt_s = welch(self.sig_sam_opt, self.fs_sam_opt, nperseg=4096)

        f_cmp_r, P_cmp_r = welch(self.sig_ref_comp, self.fs_ref_comp, nperseg=4096)
        f_cmp_s, P_cmp_s = welch(self.sig_sam_comp, self.fs_sam_comp, nperseg=4096)

        f_common = np.linspace(
            max(f_opt_r.min(), f_cmp_r.min()),
            min(f_opt_r.max(), f_cmp_r.max()),
            4000
        )

        Pr_opt = np.interp(f_common, f_opt_r, P_opt_r)
        Ps_opt = np.interp(f_common, f_opt_s, P_opt_s)
        Pr_cmp = np.interp(f_common, f_cmp_r, P_cmp_r)
        Ps_cmp = np.interp(f_common, f_cmp_s, P_cmp_s)

        IL_opt = 10*np.log10(Pr_opt + 1e-12) - 10*np.log10(Ps_opt + 1e-12)
        IL_cmp = 10*np.log10(Pr_cmp + 1e-12) - 10*np.log10(Ps_cmp + 1e-12)

        mask = (f_common >= 200) & (f_common <= 2000)

        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(f_common[mask], IL_opt[mask], label="Optimal IL", color="blue")
        ax.plot(f_common[mask], IL_cmp[mask], label="Comparison IL", color="red")

        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Insertion Loss (dB)")
        ax.set_title("Insertion Loss Comparison")
        ax.grid(False)
        ax.set_xlim(200, 2000)
        ax.legend()
        fig.tight_layout()

        return fig

if __name__ == "__main__":
    pass
