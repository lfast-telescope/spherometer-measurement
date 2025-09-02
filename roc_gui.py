import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
from LFAST_wavefront_utils import process_spherometer_concentric

def polar_roc_measurement(csv_file, spherometer_diameter, object_diameter,
                          measurement_radius, number_of_pixels,
                          crop_clear_aperture, concave, sag_unit):
    cropped_data, smoothed_data, mirror_extent = process_spherometer_concentric(
        csv_file,
        measurement_radius=measurement_radius,
        spherometer_diameter=spherometer_diameter,
        object_diameter=object_diameter,
        number_of_pixels=number_of_pixels,
        crop_clear_aperture=crop_clear_aperture,
        sag_unit=sag_unit)

    roc = 25.4 * (
        (spherometer_diameter ** 2 / 4 + smoothed_data ** 2) /
        (2 * np.abs(smoothed_data)) +
        (0.25 / 2 if concave else -0.25 / 2)
    )
    return np.flip(roc, 0), np.flip(smoothed_data, 0)

class RocGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Surface ROC GUI")
        self.geometry("800x600")

        self.loaded_path = None
        self.roc = None
        self.smoothed = None

        self.ctrl = ttk.Frame(self)
        self.ctrl.pack(side=tk.TOP, fill=tk.X, pady=5)

        ttk.Button(self.ctrl, text="Load CSV", command=self.load_csv).grid(row=0, column=0, padx=5)
        ttk.Button(self.ctrl, text="Plot", command=self.plot_data).grid(row=0, column=1, padx=5)

        ttk.Label(self.ctrl, text="Sphero Diam:").grid(row=0, column=2)
        self.var_sphero = tk.DoubleVar(value=11.5)
        ttk.Entry(self.ctrl, width=5, textvariable=self.var_sphero).grid(row=0, column=3)

        ttk.Label(self.ctrl, text="Obj Diam:").grid(row=0, column=4)
        self.var_obj = tk.DoubleVar(value=32)
        ttk.Entry(self.ctrl, width=5, textvariable=self.var_obj).grid(row=0, column=5)

        ttk.Label(self.ctrl, text="Pixels:").grid(row=0, column=6)
        self.var_pix = tk.IntVar(value=100)
        ttk.Entry(self.ctrl, width=5, textvariable=self.var_pix).grid(row=0, column=7)

        self.var_crop = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.ctrl, text="Crop", variable=self.var_crop).grid(row=0, column=8)

        options = ["Concave", "Convex"]
        self.var_shape = tk.StringVar(value=options[0])
        ttk.Label(self.ctrl, text="Shape:").grid(row=0, column=9, padx=(10,2))
        ttk.OptionMenu(self.ctrl, self.var_shape, self.var_shape.get(), *options).grid(row=0, column=10)

        self.rad_entries = []
        ttk.Label(self.ctrl, text="Radii (in):").grid(row=0, column=11)
        for i in range(5):
            e = ttk.Entry(self.ctrl, width=5)
            e.grid(row=1+i, column=11, padx=2)
            self.rad_entries.append(e)
        # Pre-fill defaults:
        for ent, val in zip(self.rad_entries, ["11.875", "8.5", "5.25", "2", ""]):
            ent.insert(0, val)

        self.frame_plot = ttk.Frame(self)
        self.frame_plot.pack(fill=tk.BOTH, expand=True)
        self.canvas = None
        self.toolbar = None


    def load_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if path:
            self.loaded_path = path
            ttk.Label(self.ctrl, text=f"Loaded: {os.path.basename(path)}", foreground="blue")\
                .grid(row=1, column=0, columnspan=4, sticky='w')

    def plot_data(self):
        if not self.loaded_path:
            messagebox.showwarning("No file", "Please load a CSV first.")
            return

        # Parse measurement radii
        rads = []
        for e in self.rad_entries:
            txt = e.get().strip()
            if txt:
                try:
                    rads.append(float(txt))
                except ValueError:
                    messagebox.showerror("Invalid input", f"'{txt}' is not a number.")
                    return
        if not (1 <= len(rads) <= 5):
            messagebox.showerror("Invalid input", "Enter between 1 and 5 radii.")
            return

        roc, smoothed = polar_roc_measurement(
            csv_file=self.loaded_path,
            spherometer_diameter=self.var_sphero.get(),
            object_diameter=self.var_obj.get(),
            measurement_radius=rads,
            number_of_pixels=self.var_pix.get(),
            crop_clear_aperture=self.var_crop.get(),
            concave=(self.var_shape.get() == "Concave"),
            sag_unit='mm'
        )

        self.roc, self.smoothed = roc, smoothed
        self.show_plot()

    def show_plot(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()


        fig = Figure(figsize=(5, 5), dpi=100)
        ax = fig.add_subplot(111)
        im = ax.imshow(self.roc, cmap='viridis_r')
        fig.colorbar(im, ax=ax, label='ROC (mm)')
        fig.suptitle('Surface has mean ROC=' + str(int(np.nanmean(self.roc)))+ 'mm')
        cs = ax.contour(self.roc, colors='k', levels=6, alpha=0.35)
        ax.set_xticks([]);
        ax.set_yticks([])
        ax.set_xlabel(str(int(np.mean(np.diff(cs.levels)))) + 'mm contours')

        self.canvas = FigureCanvasTkAgg(fig, master=self.frame_plot)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        if self.toolbar is None:
            self.toolbar = NavigationToolbar2Tk(self.canvas, self.frame_plot)
            self.toolbar.update()


#%%
if __name__ == "__main__":
    app = RocGui()
    app.mainloop()
