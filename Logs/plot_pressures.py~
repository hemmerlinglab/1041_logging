#!/usr/bin/env python3

"""
Live monitor for RGM401 (pressures) + thermistors (temperatures) + MKS275 foreline.
- One figure with two y-axes:
    * Left  (axP): pressures in Pa (log scale)
    * Right (axT): temperatures in degree Celcius (linear)
- Reads once per second (configurable), keeps a scrolling window (default 300 s)
- CheckButtons to toggle which series are visible
- Minimal error handling: on read failure, append NaN for that channel and continue

To run this script, use:
    `python plot_pressures.py --window 600 --refresh 1.0 --channels room,cryo,icr,ich,foreline`

Disable MKS275 is possible, just use --no-foreline
"""

import argparse
import math
import time
from collections import deque
from typing import Dict, Deque, List, Tuple
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import CheckButtons

from vacuum_gauges import RGM401AndThermisters, MKS275
from helper_functions import ecc
# ---------------------- Helpers ----------------------
def now_s() -> float:
    """Monotonic seconds since an arbitrary point (good for plotting elapsed time)."""
    return time.monotonic()

def safe_log_data(xs: List[float], ys: List[float]) -> Tuple[List[float], List[float]]:
    """
    For log-axis plotting: replace non-positive y with NaN so Matplotlib won't error.
    Returns filtered lists (same length) where invalid y -> nan.
    """

    out_x, out_y = [], []

    for x, y in zip(xs, ys):
        out_x.append(x)
        if y is None or not isinstance(y, (int, float)) or y <= 0 or math.isnan(y):
            out_y.append(float("nan"))
        else:
            out_y.append(float(y))

    return out_x, out_y

# ---------------------- Main Live Monitor ----------------------
class LiveMonitor:
    """
    Live plot of selected channels from:
      - RGM401AndThermisters: p_room, p_cryo, T_ICR, T_ICH
      - MKS275 foreline: p_foreline
    """

    PRESSURE_KEYS = ("room", "cryo", "foreline")  # plotted on log-left axis
    TEMP_KEYS = ("icr", "ich")                    # plotted on linear-right axis
    ALL_KEYS = PRESSURE_KEYS + TEMP_KEYS

    def __init__(
        self,
        window_s: int = 300,
        refresh_s: float = 1.0,
        channels: Tuple[str, ...] = ALL_KEYS,
        use_foreline: bool = True,
        ig_kwargs: Dict = None,
        cg_kwargs: Dict = None,
    ):
        """
        Args:
            window_s: Length of the scrolling time window in seconds.
            refresh_s: Sampling/refresh period in seconds.
            channels: Tuple of channel names to show initially.
                      Allowed: "room","cryo","foreline","icr","ich".
            use_foreline: If False, skip creating the MKS275 instance.
            ig_kwargs: Optional kwargs to pass to RGM401AndThermisters(...).
            cg_kwargs: Optional kwargs to pass to MKS275(...).
        """

        self.window_s = int(window_s)
        self.refresh_s = float(refresh_s)
        self.use_foreline = bool(use_foreline)

        # Selected channels set
        invalid = set(channels) - set(self.ALL_KEYS)
        if invalid:
            raise ValueError(f"Unknown channels: {invalid}. Allowed: {self.ALL_KEYS}")
        self.selected = {k: (k in channels) for k in self.ALL_KEYS}

        # Instruments
        ig_kwargs = ig_kwargs or {}
        cg_kwargs = cg_kwargs or {}
        self.ig = RGM401AndThermisters(autoconnect=True, **ig_kwargs)
        self.cg = MKS275(autoconnect=True, **cg_kwargs) if self.use_foreline else None

        # Data buffers (deques with fixed maxlen)
        self.t0 = now_s()
        self.ts: Deque[float] = deque(maxlen=self.window_s + 5)  # extra headroom
        self.buf: Dict[str, Deque[float]] = {
            "room": deque(maxlen=self.window_s + 5),
            "cryo": deque(maxlen=self.window_s + 5),
            "foreline": deque(maxlen=self.window_s + 5),
            "icr": deque(maxlen=self.window_s + 5),
            "ich": deque(maxlen=self.window_s + 5),
        }

        # Matplotlib state
        self.fig, self.axP = plt.subplots(figsize=(10, 5))
        self.axT = self.axP.twinx()
        self.lines: Dict[str, any] = {}  # channel -> Line2D
        self._build_plot()

        # Animation timer
        interval_ms = int(self.refresh_s * 1000)
        self.ani = animation.FuncAnimation(
            self.fig, self._on_timer, interval=interval_ms, blit=False
        )

        # Key bindings
        self.fig.canvas.mpl_connect("key_press_event", self._on_key)

    # -------- Plot construction --------
    def _build_plot(self):
        """Initial axis/lines/legend and add CheckButtons to toggle visibility."""

        self.axP.set_title("Live RGM401 & Thermistors (pressures on left, temperatures on right)")
        self.axP.set_xlabel("Time (s)")
        self.axP.set_ylabel("Pressure (Pa)")
        self.axP.set_yscale("log")
        self.axP.grid(True, which="both", alpha=0.3)
        self.axT.set_ylabel("Temperature (C)")

        # Lines
        self.lines["room"], = self.axP.plot([], [], label="chamber (Pa)", visible=self.selected["room"])
        self.lines["cryo"], = self.axP.plot([], [], label="dewar (Pa)",   visible=self.selected["cryo"])
        if self.use_foreline:
            self.lines["foreline"], = self.axP.plot([], [], label="foreline (raw)", visible=self.selected["foreline"])
        else:
            self.lines["foreline"], = self.axP.plot([], [], label="foreline (raw)", visible=False)
        self.lines["icr"], = self.axT.plot([], [], label="ICR (C)", visible=self.selected["icr"])
        self.lines["ich"], = self.axT.plot([], [], label="ICH (C)", visible=self.selected["ich"])

        # ---- Legend moved outside (figure-level legend) ----
        # Reserve right margin for legend + checkboxes
        # (left, bottom, right, top) figure fraction
        self.fig.tight_layout(rect=[0.03, 0.03, 0.80, 0.97])
        # Order the legend entries explicitly so we can sync visibility later
        self.legend_order = ["room", "cryo"] + (["foreline"] if self.use_foreline else []) + ["icr", "ich"]
        handles = [self.lines[k] for k in self.legend_order]
        labels = [h.get_label() for h in handles]

        # Put the legend in the right margin, top-left corner of that margin
        self.legend = self.fig.legend(
            handles, labels,
            loc="upper left",
            bbox_to_anchor=(0.82, 0.97),   # x,y in figure fraction
            borderaxespad=0.0,
            framealpha=0.9,
        )

        # ---- CheckButtons ----
        # [left, bottom, width, height] in figure fraction
        rax = plt.axes([0.82, 0.40, 0.16, 0.22])
        labels_cb = ["room", "cryo", "foreline", "icr", "ich"] if self.use_foreline else ["room", "cryo", "icr", "ich"]
        actives = [self.selected[k] for k in labels_cb]
        self.chk = CheckButtons(rax, labels_cb, actives)

        def _on_check(label):
            self.selected[label] = not self.selected[label]
            self.lines[label].set_visible(self.selected[label])
            self._sync_legend_alpha()
            self.fig.canvas.draw_idle()
    
        self.chk.on_clicked(_on_check)

    # -------- Data acquisition --------
    def _read_data(self, repeat: int = 5) -> Dict[str, float]:
        """
        Read one sample from devices.
        Returns a dict with keys in ALL_KEYS; missing/failed readings are NaN.
        """

        vals = {k: float("nan") for k in self.ALL_KEYS}

        try:
            p_room_list, p_cryo_list, t_icr_list, t_ich_list = [], [], [], []

            for _ in range(repeat):
                p_room, p_cryo, t_icr, t_ich = self.ig.get_all()
                p_room_list.append(p_room)
                p_cryo_list.append(p_cryo)
                t_icr_list.append(t_icr)
                t_ich_list.append(t_ich)

            vals["room"] = ecc(p_room_list)
            vals["cryo"] = ecc(p_cryo_list)
            vals["icr"] = ecc(t_icr_list)
            vals["ich"] = ecc(t_ich_list)

        except Exception:
            # Leave NaNs; continue
            pass

        if self.use_foreline:
            try:
                vals["foreline"] = self.cg.get_pressure()
            except Exception:
                pass

        return vals

    # -------- Animation callback --------
    def _on_timer(self, _frame):
        """Matplotlib animation callback: fetch data, update buffers, redraw lines."""

        t = now_s() - self.t0
        vals = self._read_data(repeat=5)

        # Append to buffers
        self.ts.append(t)
        for k in self.ALL_KEYS:
            self.buf[k].append(vals[k])

        # Compute window range
        tmin = max(0.0, t - self.window_s)

        # Slice data inside window
        xs = list(self.ts)
        xs = [x for x in xs if x >= tmin]

        # For each series, set line data
        # Pressures on left (log-safe prep)
        for k in self.PRESSURE_KEYS:
            ys = list(self.buf[k])[-len(self.ts):]  # align length; deques stay in step
            ys = ys[-len(xs):]
            xx, yy = safe_log_data(xs[-len(ys):], ys)  # ensure same length
            self.lines[k].set_data(xx, yy)

        # Temperatures on right
        for k in self.TEMP_KEYS:
            ys = list(self.buf[k])[-len(self.ts):]
            ys = ys[-len(xs):]
            self.lines[k].set_data(xs[-len(ys):], ys)

        # Update axes limits
        self.axP.set_xlim(tmin, tmin + self.window_s)

        # Y-lims: auto for temps; for pressures, let autoscale handle but with try/except
        try:
            self.axP.relim()
            self.axP.autoscale_view(scalex=False, scaley=True)
        except Exception:
            pass

        try:
            self.axT.relim()
            self.axT.autoscale_view(scalex=False, scaley=True)
        except Exception:
            pass

        # Redraw legend to reflect visibility (optional)
        # (Matplotlib legends do not auto-hide lines, here we rebuild labels visibility)
        for legline, orig in zip(self.legend.get_lines(), [self.lines[k] for k in self.ALL_KEYS]):
            legline.set_visible(orig.get_visible())
            
        # Return artists if blitting; here we return nothing (blit=False)
        return []

    # -------- Key handlers --------
    def _on_key(self, event):
        """
        Keyboard shortcuts:
          q : quit
          p : pause/resume (toggle animation event source)
          1..5 : toggle channels in order [room,cryo,foreline,icr,ich]
        """

        if event.key == "q":
            plt.close(self.fig)
            return

        if event.key == "p":
            src = self.ani.event_source
            if src.is_running():
                src.stop()
            else:
                src.start()
            return

        keymap = ["1", "2", "3", "4", "5"]
        labels = ["room", "cryo", "foreline", "icr", "ich"]

        if not self.use_foreline:
            labels = ["room", "cryo", "icr", "ich"]
            keymap = ["1", "2", "3", "4"]

        if event.key in keymap:
            idx = keymap.index(event.key)
            label = labels[idx]
            self.selected[label] = not self.selected[label]
            self.lines[label].set_visible(self.selected[label])
            self.fig.canvas.draw_idle()

# ---------------------- CLI ----------------------
def parse_args():

    p = argparse.ArgumentParser(description="Live 1 Hz monitor for RGM401 + thermistors (+ optional foreline)")
    p.add_argument("--window", type=int, default=300, help="Time window in seconds (default: 300)")
    p.add_argument("--refresh", type=float, default=1.0, help="Refresh period in seconds (default: 1.0)")
    p.add_argument(
        "--channels",
        type=str,
        default="room,cryo,foreline,icr,ich",
        help="Comma-separated channels to show initially. Choices: room,cryo,foreline,icr,ich",
    )
    p.add_argument("--no-foreline", action="store_true", help="Disable MKS275 (foreline) reader")
    p.add_argument("--ig-port", type=str, default="COM7", help="Serial port for RGM401 Arduino")
    p.add_argument("--ig-baud", type=int, default=115200, help="Baudrate for RGM401 Arduino")
    p.add_argument("--cg-port", type=str, default="COM6", help="Serial port for MKS275")
    p.add_argument("--cg-baud", type=int, default=19200, help="Baudrate for MKS275")

    return p.parse_args()

def main():

    args = parse_args()
    channels = tuple([s.strip().lower() for s in args.channels.split(",") if s.strip()])
    monitor = LiveMonitor(
        window_s=args.window,
        refresh_s=args.refresh,
        channels=channels,
        use_foreline=not args.no_foreline,
        ig_kwargs={"port": args.ig_port, "baudrate": args.ig_baud, "timeout": 1.0},
        cg_kwargs={"port": args.cg_port, "baudrate": args.cg_baud, "timeout": 0.5},
    )
    plt.show()
    
    # Clean shutdown after window closed
    try:
        monitor.ig.close()
    except Exception:
        pass

    try:
        if monitor.cg:
            monitor.cg.close()
    except Exception:
        pass

if __name__ == "__main__":
    main()
