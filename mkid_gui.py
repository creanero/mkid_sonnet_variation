"""
A small tkinter GUI for building and visualising an MKID circuit with the
classes in mkids.py.

  * Every numeric geometry parameter is exposed as a spinbox, pre-filled with
    the values from the example case at the bottom of mkids.py.
  * Spinbox step sizes follow the Box scale parameters: x-direction parameters
    step by x_scale, y-direction parameters by y_scale, counts (turns,
    num_fingers) step by 1, and -- as requested -- the inductor breadth steps
    by the larger of x_scale / y_scale. The steps update live when you change a
    scale.
  * The MKID polygons and ports are drawn with matplotlib, embedded in the
    window, exactly as in the commented plotting block of mkids.py: the ground
    plane in Reds, the capacitor in Blues, the inductor in Greens, and the
    ports as goldenrod squares. (The y-axis is inverted so the layout reads
    top-down, the way Sonnet displays it; remove the invert_yaxis() call if you
    want the raw orientation of the commented example.)

Run it with:  python mkid_gui.py

IMPORTANT -- mkids.py must be importable without side effects. The demo block
at the bottom of mkids.py (everything from `metals = MetalList()` onward, which
also writes ~/test/mkid_sonnet_variation/test_full.son) runs on import. Wrap
that block in `if __name__ == "__main__":` (or remove it) so that
`from mkids import ...` below does not execute it.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np

from mkids import (MetalList, Metal, Box, Dielectric, GroundPlane,
                   Capacitor, Inductor, Circuit, Geometry, Mkid)


# --------------------------------------------------------------------------- #
# Parameter specification
#
# (key, label, group, default, step_type, is_int)
#   step_type drives the spinbox increment:
#     "x"       -> Box.x_scale            (x-direction dimensions)
#     "y"       -> Box.y_scale            (y-direction dimensions)
#     "breadth" -> max(x_scale, y_scale)  (the inductor breadth, as requested)
#     "count"   -> 1                      (integer counts)
#     "scale"   -> 0.1                    (the cell-size parameters themselves)
#
# Defaults are taken verbatim from the example case at the bottom of mkids.py.
# --------------------------------------------------------------------------- #
SPEC = [
    # Box
    ("box_x_size",      "Size in x",      "MKID", 500.0, "x",     False),
    ("box_y_size",      "Size in y",      "MKID", 500.0, "y",     False),
    ("box_x_scale",     "x unit cell",     "MKID", 1.0,   "scale", False),
    ("box_y_scale",     "y unit cell",     "MKID", 1.0,   "scale", False),
    # Ground plane
    ("gp_top_b",        "Top Bar",       "Ground Plane", 152.0, "y", False),  # 500 - 348
    ("gp_res_yl",       "Resonator length (y)",      "Ground Plane", 175.0, "y", False),  # 348 - 173
    ("gp_side_b",       "Side Bar",      "Ground Plane", 12.0,  "x", False),
    ("gp_near_b",       "Near Bar",      "Ground Plane", 12.0,  "y", False),
    ("gp_feed_b",       "Feedline",      "Ground Plane", 35.0,  "y", False),
    ("gp_oppo_b",       "Opposite Bar",      "Ground Plane", 25.0,  "y", False),
    ("gp_feed_s",       "Feedline Spacing",      "Ground Plane", 5.0,   "y", False),
    # Capacitor
    ("cap_num_fingers", "Number of Fingers", "Capacitor", 27,    "count", True),
    ("cap_finger_p",    "Finger Pitch",    "Capacitor", 4.0,   "y",     False),
    ("cap_finger_b",    "Finger Breadth",    "Capacitor", 2.0,   "y",     False),
    ("cap_finger_l",    "Finger Length",    "Capacitor", 450.0, "x",     False),
    ("cap_finger_lf",   "Final Finger Length",   "Capacitor", 84.0,  "x",     False),
    ("cap_side_b",      "Breadth of Side Bars",      "Capacitor", 7.0,   "x",     False),
    ("cap_top_b",       "Breadth of Top Bar",       "Capacitor", 10.0,  "y",     False),
    ("cap_transfer_b",  "Breadth of Transfer Bar",  "Capacitor", 5.0,   "y",     False),
    ("cap_transfer_0",  "Start Transfer Bar",  "Capacitor", 250.0, "x",     False),
    ("cir_cap_dx",      "Ground Plane spacing (x)",      "Capacitor", 4.0, "x", False),
    ("cir_cap_dy",      "Ground Plane spacing (y)",      "Capacitor", 4.0, "y", False),
    # Inductor
    ("ind_turns",       "Turns",       "Inductor", 5,    "count",   True),
    ("ind_breadth",     "Breadth",     "Inductor", 1.0,  "breadth", False),
    ("ind_space",       "Space",       "Inductor", 1.0,  "y",       False),
    ("ind_length",      "Length",      "Inductor", 20.0, "x",       False),
    ("cap_ij_start",    "Junction",    "Inductor", 240.0, "x",     False),
    # Circuit
]

GROUPS = ["MKID", "Ground Plane", "Capacitor", "Inductor"]

# metals and dielectrics are not exposed as sliders (they do not affect the
# visual layout); they use the example-case defaults when a .son is exported.


def _cmap(name):
    """Return a matplotlib colormap by name, across matplotlib versions."""
    try:
        return matplotlib.colormaps[name]          # matplotlib >= 3.5
    except Exception:                              # pragma: no cover
        from matplotlib import cm
        return cm.get_cmap(name)


def build_mkid(v):
    """
    Build the full MKID from a dict of parameter values (keyed as in SPEC) and
    return (mkid, circuit, capacitor, inductor, ground_plane).

    This mirrors the example case in mkids.py exactly: the ground plane takes
    its size from the (scale-snapped) box, the capacitor is built without an
    explicit ij_end (the Circuit resolves it), and the Circuit positions the
    capacitor and inductor before generate() is called.
    """
    box = Box(x_size=v["box_x_size"], y_size=v["box_y_size"],
              x_scale=v["box_x_scale"], y_scale=v["box_y_scale"])

    metals = MetalList()
    metals.add_metal(Metal.superconductor())

    dielectrics = [
        Dielectric(name="Unnamed", thickness=200.0, erel=1.0, mrel=1.0),
        Dielectric(name="Sapphire", thickness=450.0, erel=9.3, mrel=1.0,
                   anisotropic=True, erel_2=11.5),
    ]

    ground_plane = GroundPlane(
        x_size=float(box.safe_x_size), y_size=float(box.safe_y_size),
        top_b=v["gp_top_b"], res_yl=v["gp_res_yl"], side_b=v["gp_side_b"],
        near_b=v["gp_near_b"], feed_b=v["gp_feed_b"], oppo_b=v["gp_oppo_b"],
        feed_s=v["gp_feed_s"], start_polygon_id=100)

    capacitor = Capacitor(
        finger_p=v["cap_finger_p"], finger_b=v["cap_finger_b"],
        finger_l=v["cap_finger_l"], num_fingers=int(v["cap_num_fingers"]),
        finger_lf=v["cap_finger_lf"], side_b=v["cap_side_b"], top_b=v["cap_top_b"],
        transfer_b=v["cap_transfer_b"], transfer_0=v["cap_transfer_0"],
        ij_start=v["cap_ij_start"])

    inductor = Inductor(turns=int(v["ind_turns"]), breadth=v["ind_breadth"],
                        space=v["ind_space"], length=v["ind_length"])

    circuit = Circuit(ground_plane=ground_plane, capacitor=capacitor,
                      inductor=inductor, cap_dx=v["cir_cap_dx"], cap_dy=v["cir_cap_dy"])
    circuit.generate()

    geometry = Geometry(metal_list=metals, box=box, dielectrics=dielectrics, circuit=circuit)
    mkid = Mkid(geometry)
    return mkid, circuit, capacitor, inductor, ground_plane


class MkidGUI:
    def __init__(self, root):
        self.root = root
        self.vars = {}        # key -> tk variable
        self.spinboxes = {}   # key -> Spinbox widget
        self.hints = {}       # key -> hint Label (shows the live step size)
        self._mkid = None     # most recently built Mkid (for saving)

        for key, label, group, default, step_type, is_int in SPEC:
            self.vars[key] = tk.IntVar(value=default) if is_int else tk.DoubleVar(value=default)

        main = ttk.Frame(root, padding=8)
        main.pack(fill=tk.BOTH, expand=True)
        main.columnconfigure(0, weight=0)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        self._build_controls(main)
        self._build_plot(main)
        self._build_statusbar(root)

        self._update_steps()
        self._redraw()

    # ------------------------------------------------------------------ #
    # Layout
    # ------------------------------------------------------------------ #
    def _build_controls(self, parent):
        left = ttk.Frame(parent)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 8))

        notebook = ttk.Notebook(left)
        notebook.pack(fill=tk.BOTH, expand=True)

        for group in GROUPS:
            tab = ttk.Frame(notebook, padding=10)
            notebook.add(tab, text=group)
            tab.columnconfigure(1, weight=1)
            row = 0
            for key, label, grp, default, step_type, is_int in SPEC:
                if grp != group:
                    continue
                ttk.Label(tab, text=label).grid(row=row, column=0, sticky="w",
                                                padx=(0, 8), pady=3)
                sb = tk.Spinbox(tab, textvariable=self.vars[key], width=12,
                                from_=self._lo(step_type), to=self._hi(step_type),
                                increment=self._step_for(step_type),
                                command=self._on_change)
                sb.grid(row=row, column=1, sticky="ew", pady=3)
                sb.bind("<Return>", self._on_change)
                self.spinboxes[key] = sb
                hint = ttk.Label(tab, text=self._hint(step_type), foreground="#888888")
                hint.grid(row=row, column=2, sticky="w", padx=(8, 0))
                self.hints[key] = hint
                row += 1

        buttons = ttk.Frame(left, padding=(0, 8, 0, 0))
        buttons.pack(fill=tk.X)
        ttk.Button(buttons, text="Update plot", command=self._on_change).pack(fill=tk.X, pady=2)
        ttk.Button(buttons, text="Reset to defaults", command=self._reset).pack(fill=tk.X, pady=2)
        ttk.Button(buttons, text="Save .son\u2026", command=self._save_son).pack(fill=tk.X, pady=2)

    def _build_plot(self, parent):
        right = ttk.Frame(parent)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        self.fig = Figure(figsize=(6.5, 6.5), dpi=100)
        self.ax = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        toolbar_frame = ttk.Frame(right)
        toolbar_frame.grid(row=1, column=0, sticky="ew")
        NavigationToolbar2Tk(self.canvas, toolbar_frame)

    def _build_statusbar(self, root):
        self.status = ttk.Label(root, anchor="w", padding=(8, 4))
        self.status.pack(fill=tk.X, side=tk.BOTTOM)

    # ------------------------------------------------------------------ #
    # Step-size handling
    # ------------------------------------------------------------------ #
    def _scales(self):
        try:
            return float(self.vars["box_x_scale"].get()), float(self.vars["box_y_scale"].get())
        except (tk.TclError, ValueError):
            return 1.0, 1.0

    def _step_for(self, step_type):
        xs, ys = self._scales()
        return {"x": xs, "y": ys, "breadth": max(xs, ys),
                "count": 1, "scale": 0.1}.get(step_type, 1.0)

    @staticmethod
    def _lo(step_type):
        return 0.1 if step_type == "scale" else 0.0

    @staticmethod
    def _hi(step_type):
        return 1.0e6

    def _hint(self, step_type):
        """Hint text shown beside each spinbox, with the live step size."""
        if step_type in ("x", "y", "breadth"):
            return "step = {:g} \u00b5m".format(self._step_for(step_type))
        if step_type == "count":
            return "integer"
        if step_type == "scale":
            return "cell size (step = {:g})".format(self._step_for(step_type))
        return ""

    def _update_steps(self):
        """Refresh every spinbox increment (and its hint) from the current scales."""
        for key, label, group, default, step_type, is_int in SPEC:
            sb = self.spinboxes.get(key)
            if sb is not None:
                sb.config(increment=self._step_for(step_type))
            hint = self.hints.get(key)
            if hint is not None:
                hint.config(text=self._hint(step_type))

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #
    def _on_change(self, *_event):
        self._update_steps()
        self._redraw()

    def _reset(self):
        for key, label, group, default, step_type, is_int in SPEC:
            self.vars[key].set(default)
        self._on_change()

    def _current_values(self):
        return {key: var.get() for key, var in self.vars.items()}

    def _plot_polys(self, polys, cmap_name):
        n = len(polys)
        if n == 0:
            return
        colors = _cmap(cmap_name)(np.linspace(0.2, 1, n))
        for i in range(n):
            x, y = polys[i].get_points()
            self.ax.fill(x, y, color=colors[i])

    def _redraw(self):
        try:
            mkid, circuit, capacitor, inductor, ground_plane = build_mkid(self._current_values())
        except Exception as exc:
            self._set_status("Build error: {}".format(exc), error=True)
            return

        self._mkid = mkid
        self.ax.clear()

        # same layering as the commented example: whole circuit in Reds, then
        # the capacitor (Blues) and inductor (Greens) painted on top, so the
        # ground plane reads red, the capacitor blue and the inductor green.
        self._plot_polys(ground_plane.get_polygons(), "Blues")
        self._plot_polys(capacitor.get_polygons(), "Greens")
        self._plot_polys(inductor.get_polygons(), "Reds")

        xs, ys = ground_plane.get_port_coords()
        self.ax.plot(xs, ys, "s", color="goldenrod", markersize=6)

        self.ax.set_aspect("equal", adjustable="box")
        self.ax.invert_yaxis()  # Sonnet y runs downward; show the layout top-down
        self.ax.set_xlabel("x (\u00b5m)")
        self.ax.set_ylabel("y (\u00b5m)")
        self.ax.set_title("MKID layout")
        self.fig.tight_layout()
        self.canvas.draw()

        self._set_status("Updated \u2014 {} polygons, {} ports".format(
            len(circuit.get_polygons()), len(xs)))

    def _save_son(self):
        try:
            mkid = build_mkid(self._current_values())[0]
            text = mkid.gen_sonnet_mkid()
        except Exception as exc:
            messagebox.showerror("Build error", str(exc))
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".son",
            filetypes=[("Sonnet project", "*.son"), ("All files", "*.*")],
            title="Save .son file")
        if not path:
            return
        try:
            with open(path, "w") as handle:
                handle.write(text)
        except OSError as exc:
            messagebox.showerror("Save error", str(exc))
            return
        self._set_status("Saved: {}".format(path))

    def _set_status(self, message, error=False):
        self.status.config(text=message, foreground="#b00020" if error else "#333333")


def main():
    root = tk.Tk()
    root.title("MKID Designer")
    root.geometry("1150x740")
    MkidGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
