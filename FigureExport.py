from imports import *

class ExportFigureWindow:
    def __init__(self, parent, figure):
        self.parent = parent
        self.original_fig = figure

        self.has_quadmesh = any(
            isinstance(coll, QuadMesh)
            for ax in figure.axes
            for coll in ax.collections
        )

        # Clone figure if not heatmap
        self.fig = figure if self.has_quadmesh else self.clone_figure(figure)

        # Tk window
        self.window = tk.Toplevel(parent)
        self.window.title("Export Figure")
        self.window.geometry("900x700")

        self._build_controls()
        self._build_preview()
        self.update_preview()

    # ---------------- Clone Figure ----------------
    def clone_figure(self, fig):
        old_ax = fig.axes[0]
        new_fig = plt.Figure(figsize=fig.get_size_inches())
        new_ax = new_fig.add_subplot(111)

        # --- Clone lines ---
        for line in old_ax.get_lines():
            new_ax.add_line(Line2D(
                line.get_xdata(),
                line.get_ydata(),
                color=line.get_color(),
                linewidth=line.get_linewidth(),
                linestyle=line.get_linestyle(),
                marker=line.get_marker(),
                markersize=line.get_markersize(),
                label=line.get_label(),
                zorder=line.get_zorder()
            ))

        # --- Clone collections ---
        for coll in old_ax.collections:
            if isinstance(coll, QuadMesh):
                continue  # skip heatmaps (already handled)
            elif isinstance(coll, PathCollection):
                offsets = coll.get_offsets()
                if len(offsets) == 0:
                    continue
                new_ax.scatter(
                    offsets[:, 0],
                    offsets[:, 1],
                    s=coll.get_sizes(),
                    c=coll.get_facecolor(),
                    label=coll.get_label(),
                    zorder=coll.get_zorder()
                )
            elif isinstance(coll, PolyCollection):
                # axhspan / fill_between / masks
                for path in coll.get_paths():
                    new_poly = PolyCollection([path.vertices],
                                              facecolor=coll.get_facecolor(),
                                              alpha=coll.get_alpha(),
                                              zorder=coll.get_zorder())
                    new_ax.add_collection(new_poly)
            elif isinstance(coll, LineCollection):
                # hlines / vlines
                segments = coll.get_segments()
                lc = LineCollection(
                    segments,
                    colors=coll.get_colors(),
                    linewidths=coll.get_linewidths(),
                    linestyles=coll.get_linestyles(),
                    zorder=coll.get_zorder(),
                    alpha=coll.get_alpha()
                )
                new_ax.add_collection(lc)

        # --- Axis labels, limits, grid, legend ---
        new_ax.set_title(old_ax.get_title())
        new_ax.set_xlabel(old_ax.get_xlabel())
        new_ax.set_ylabel(old_ax.get_ylabel())
        new_ax.set_xlim(old_ax.get_xlim())
        new_ax.set_ylim(old_ax.get_ylim())
        # Copy grid state safely
        grid_visible = any(line.get_visible() for line in old_ax.get_xgridlines())
        new_ax.grid(grid_visible)
        if old_ax.get_legend():
            new_ax.legend()

        return new_fig

    # ---------------- Controls ----------------
    def _build_controls(self):
        frame = tk.Frame(self.window)
        frame.pack(fill=tk.X, padx=10, pady=10)

        # DPI
        tk.Label(frame, text="DPI:").grid(row=0, column=0)
        self.dpi_var = tk.IntVar(value=300)
        dpi_entry = tk.Entry(frame, textvariable=self.dpi_var, width=6)
        dpi_entry.grid(row=0, column=1)

        # Width / Height
        tk.Label(frame, text="Width:").grid(row=1, column=0)
        tk.Label(frame, text="Height:").grid(row=1, column=2)
        self.w_var = tk.DoubleVar(value=8)
        self.h_var = tk.DoubleVar(value=6)
        w_entry = tk.Entry(frame, textvariable=self.w_var, width=6)
        w_entry.grid(row=1, column=1)
        h_entry = tk.Entry(frame, textvariable=self.h_var, width=6)
        h_entry.grid(row=1, column=3)

        # Axis limits
        tk.Label(frame, text="X-lim:").grid(row=2, column=0)
        tk.Label(frame, text="Y-lim:").grid(row=3, column=0)
        self.xmin = tk.DoubleVar()
        self.xmax = tk.DoubleVar()
        self.ymin = tk.DoubleVar()
        self.ymax = tk.DoubleVar()
        xmin_entry = tk.Entry(frame, textvariable=self.xmin, width=6)
        xmin_entry.grid(row=2, column=1)
        xmax_entry = tk.Entry(frame, textvariable=self.xmax, width=6)
        xmax_entry.grid(row=2, column=2)
        ymin_entry = tk.Entry(frame, textvariable=self.ymin, width=6)
        ymin_entry.grid(row=3, column=1)
        ymax_entry = tk.Entry(frame, textvariable=self.ymax, width=6)
        ymax_entry.grid(row=3, column=2)

        # Toggles
        self.grid_var = tk.BooleanVar(value=True)
        self.legend_var = tk.BooleanVar(value=True)
        self.title_var = tk.BooleanVar(value=True)
        tk.Checkbutton(frame, text="Grid", variable=self.grid_var, command=self.update_preview).grid(row=4, column=0)
        tk.Checkbutton(frame, text="Legend", variable=self.legend_var, command=self.update_preview).grid(row=4, column=1)
        tk.Checkbutton(frame, text="Title", variable=self.title_var, command=self.update_preview).grid(row=4, column=2)

        # Title / Axis labels
        tk.Label(frame, text="Title Text:").grid(row=5, column=0)
        self.title_text = tk.StringVar(value=self.fig.axes[0].get_title())
        title_entry = tk.Entry(frame, textvariable=self.title_text, width=30)
        title_entry.grid(row=5, column=1, columnspan=3)

        tk.Label(frame, text="X Label:").grid(row=6, column=0)
        tk.Label(frame, text="Y Label:").grid(row=7, column=0)
        self.xlabel_text = tk.StringVar(value=self.fig.axes[0].get_xlabel())
        self.ylabel_text = tk.StringVar(value=self.fig.axes[0].get_ylabel())
        xlabel_entry = tk.Entry(frame, textvariable=self.xlabel_text, width=30)
        xlabel_entry.grid(row=6, column=1, columnspan=3)
        ylabel_entry = tk.Entry(frame, textvariable=self.ylabel_text, width=30)
        ylabel_entry.grid(row=7, column=1, columnspan=3)

        # Buttons
        tk.Button(frame, text="Save", command=self.save).grid(row=8, column=0, pady=10)
        tk.Button(frame, text="Cancel", command=self.window.destroy).grid(row=8, column=1)

        # Bind updates
        entries = [dpi_entry, w_entry, h_entry,
                   xmin_entry, xmax_entry, ymin_entry, ymax_entry,
                   title_entry, xlabel_entry, ylabel_entry]
        for entry in entries:
            entry.bind("<Return>", lambda e, s=self: s.update_preview())
            entry.bind("<FocusOut>", lambda e, s=self: s.update_preview())

    # ---------------- Preview ----------------
    def _build_preview(self):
        self.preview_frame = tk.Frame(self.window)
        self.preview_frame.pack(fill=tk.BOTH, expand=True)
        self.preview_frame.bind("<Configure>", lambda e: self.update_preview())

    def update_preview(self):
        for w in self.preview_frame.winfo_children():
            w.destroy()

        preview_fig = self.clone_figure(self.fig) if not self.has_quadmesh else self.fig
        ax = preview_fig.axes[0]

        # Axis limits
        if self.xmin.get() or self.xmax.get():
            ax.set_xlim(self.xmin.get(), self.xmax.get())
        if self.ymin.get() or self.ymax.get():
            ax.set_ylim(self.ymin.get(), self.ymax.get())

        # Grid / Title / Labels / Legend
        ax.grid(self.grid_var.get())
        ax.set_title(self.title_text.get() if self.title_var.get() else "")
        ax.set_xlabel(self.xlabel_text.get())
        ax.set_ylabel(self.ylabel_text.get())
        if self.legend_var.get() and ax.get_legend_handles_labels()[0]:
            ax.legend()
        elif ax.get_legend():
            ax.get_legend().remove()

        # Embed figure in canvas
        canvas = FigureCanvasTkAgg(preview_fig, master=self.preview_frame)
        canvas.draw()

        widget = canvas.get_tk_widget()
        widget.pack(expand=True)
        widget.update_idletasks()

        # Maintain aspect ratio
        canvas_width = self.preview_frame.winfo_width()
        canvas_height = self.preview_frame.winfo_height()
        fig_ratio = self.w_var.get() / self.h_var.get()
        canvas_ratio = canvas_width / canvas_height

        if canvas_ratio > fig_ratio:
            display_width = int(canvas_height * fig_ratio)
            display_height = canvas_height
        else:
            display_width = canvas_width
            display_height = int(canvas_width / fig_ratio)

        widget.config(width=display_width, height=display_height)

    # ---------------- Save ----------------
    def save(self):
        file_path = filedialog.asksaveasfilename(
            title="Save Figure",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("PDF", "*.pdf")]
        )
        if not file_path:
            return

        # Set exact size and DPI
        self.fig.set_size_inches(self.w_var.get(), self.h_var.get())
        self.fig.savefig(file_path, dpi=self.dpi_var.get(), bbox_inches="tight")
        self.window.destroy()


if __name__ == "__main__":
    pass