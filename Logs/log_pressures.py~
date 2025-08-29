import os
import math
import time
from datetime import datetime
from typing import Tuple

from vacuum_gauges import RGM401AndThermisters, MKS275
from helper_functions import ecc

# -------------------- Paths & file naming --------------------
default_path = r"Z:\Logs"
fallback_path = r"C:\Users\Undergrad\Desktop\Logs_Server_Broadcast-master\Logs"

# Subdirectory suffixes under the chosen base path
suffixes = {
    "path_rough": "1041_Dewar_Foreline",
    "path_room":  "1041_Chamber_Pressure",
    "path_cryo":  "1041_Dewar_Pressure",
    "path_temp":  "1041_Chilled_Water",   # stores both ICR/ICH temperatures in one CSV
}

def ensure_dir(path: str) -> None:
    """Create directory if it does not exist."""
    os.makedirs(path, exist_ok=True)

def base_dir_exists(path: str) -> bool:
    """Return True if base path exists and is a directory."""

    try:
        return os.path.isdir(path)

    except Exception:
        return False

def compose_paths(base: str, date_str: str) -> dict:
    """
    Compose full directory paths and filenames for a given date.
    Returns a dict with:
      - dirs: dict of dir paths
      - files: dict of file paths
    """

    dirs = {
        name: os.path.join(base, sub)
        for name, sub in suffixes.items()
    }

    files = {
        "rough": os.path.join(dirs["path_rough"], f"{date_str}_foreline.log"),
        "room":  os.path.join(dirs["path_room"],  f"{date_str}_chamber.log"),
        "cryo":  os.path.join(dirs["path_cryo"],  f"{date_str}_dewar.log"),
        "temp":  os.path.join(dirs["path_temp"],  f"{date_str}_chilled_water.log"),
    }

    return {"dirs": dirs, "files": files}

def header_if_new(filepath: str, header: str) -> None:
    """Append header line if file is new or empty."""

    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        ensure_dir(os.path.dirname(filepath))
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(header)

def align_to_next_minute() -> None:
    """Sleep so that the next iteration lands on a wall-clock minute boundary."""

    now = time.time()
    sleep_s = 60.0 - (now % 60.0)

    if sleep_s < 0.01:
        sleep_s += 60.0
    time.sleep(sleep_s)

# -------------------- Instruments --------------------
# Auto-connect on construction for convenience
IG = RGM401AndThermisters(autoconnect=True)
CG = MKS275(autoconnect=True)

# -------------------- Read data with error correction --------------------
def read_ig_with_ecc(repeat: int = 5) -> Tuple[float, float, float, float]:
    """
    Read from the Arduino-backed gauge with minimal error correction.
    Returns:
        (p_room, p_cryo, T_ICR_C, T_ICH_C)
    """

    p_room_list, p_cryo_list, t_icr_list, t_ich_list = [], [], [], []

    repeat = max(1, int(repeat))
    for _ in range(repeat):
        p_room, p_cryo, t_icr, t_ich = IG.get_all()
        p_room_list.append(p_room)
        p_cryo_list.append(p_cryo)
        t_icr_list.append(t_icr)
        t_ich_list.append(t_ich)

    return (
        ecc(p_room_list),
        ecc(p_cryo_list),
        ecc(t_icr_list),
        ecc(t_ich_list),
    )

def read_cg_once() -> float:
    """Read foreline pressure (Convectron)."""
    return CG.get_pressure()

# -------------------- Logging --------------------
def main():
    """
    Minute-by-minute logging with daily file rotation.
    Strategy:
      - Try writing under `default_path`; if any write fails, retry once under `fallback_path`
      - Each day gets its own set of files, with CSV headers auto-inserted
      - On read failure, write NaN to keep the time series contiguous
    """

    # Choose a starting base directory
    base = default_path if base_dir_exists(default_path) else fallback_path
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    paths = compose_paths(base, current_date)

    # Ensure headers
    header_if_new(paths["files"]["room"],  "timestamp,pressure_Pa\n")
    header_if_new(paths["files"]["cryo"],  "timestamp,pressure_Pa\n")
    header_if_new(paths["files"]["rough"], "timestamp,pressure_Pa\n")
    header_if_new(paths["files"]["temp"],  "timestamp,T_ICR_C,T_ICH_C\n")

    try:
        while True:
            # Day roll-over handling
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")

            if date_str != current_date:
                current_date = date_str
                paths = compose_paths(base, current_date)
                header_if_new(paths["files"]["room"],  "timestamp,pressure_Pa\n")
                header_if_new(paths["files"]["cryo"],  "timestamp,pressure_Pa\n")
                header_if_new(paths["files"]["rough"], "timestamp,pressure_Pa\n")
                header_if_new(paths["files"]["temp"],  "timestamp,T_ICR_C,T_ICH_C\n")
            ts = now.strftime("%Y/%m/%d-%H:%M:%S")

            # Acquire data (gracefully degrade to NaN)
            try:
                p_room, p_cryo, t_icr, t_ich = read_ig_with_ecc(repeat=5)
            except Exception:
                p_room, p_cryo, t_icr, t_ich = math.nan, math.nan, math.nan, math.nan

            try:
                p_rough = read_cg_once()
            except Exception:
                p_rough = math.nan

            # Prepare CSV lines
            line_room  = f"{ts},{p_room}\n"
            line_cryo  = f"{ts},{p_cryo}\n"
            line_rough = f"{ts},{p_rough}\n"
            line_temp  = f"{ts},{t_icr},{t_ich}\n"
            # Try write under the current base; on failure, retry once under fallback

            def _write_with_fallback(filepath: str, line: str, header: str):

                try:
                    ensure_dir(os.path.dirname(filepath))
                    with open(filepath, "a", encoding="utf-8") as f:
                        f.write(line)

                except Exception:
                    # Switch to fallback for this write
                    fb_paths = compose_paths(fallback_path, current_date)
                    fb_file = None
                    # Map current file key to its fallback counterpart by filename
                    filename = os.path.basename(filepath)
                    # Identify which file is this and map to fallback
                    for key, path in paths["files"].items():
                        if os.path.basename(path) == filename:
                            fb_file = fb_paths["files"][key]
                            break
                    if fb_file is None:
                        # Default: same filename under fallback root
                        fb_file = os.path.join(fallback_path, filename)
                    # Ensure header on fallback file
                    header_if_new(fb_file, header)
                    ensure_dir(os.path.dirname(fb_file))
                    with open(fb_file, "a", encoding="utf-8") as f:
                        f.write(line)

            _write_with_fallback(paths["files"]["room"],  line_room,  "timestamp,pressure_Pa\n")
            _write_with_fallback(paths["files"]["cryo"],  line_cryo,  "timestamp,pressure_Pa\n")
            _write_with_fallback(paths["files"]["rough"], line_rough, "timestamp,pressure_Pa\n")
            _write_with_fallback(paths["files"]["temp"],  line_temp,  "timestamp,T_ICR_C,T_ICH_C\n")

            # Sleep to next minute boundary
            align_to_next_minute()

    except KeyboardInterrupt:
        print("Stopped by user.")

    finally:
        # Clean shutdown
        try:
            IG.close()
        except Exception:
            pass

        try:
            CG.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
