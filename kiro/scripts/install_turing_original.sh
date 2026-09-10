#!/bin/bash
#
# Turing Smart Screen Installer v1.0
# Supports: CachyOS, Bazzite, Arch, Fedora, Linux Mint, Ubuntu/Debian
#
# Usage: bash install_turing.sh
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
INSTALL_DIR="$HOME/Prejemi/turing-smart-screen-python"
REPO_URL="https://github.com/mathoudebine/turing-smart-screen-python.git"
CONTAINER_NAME="turing-display"
IMAGE_NAME="localhost/turing:1.0"

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS_NAME="$NAME"
        OS_ID="$ID"
        OS_VERSION="${VERSION_ID:-unknown}"
    else
        log_error "Cannot detect OS"
        exit 1
    fi
    log_info "Detected OS: $OS_NAME"
}

check_root() {
    if [ "$EUID" -eq 0 ]; then
        log_error "Do not run as root. Run as your regular user."
        exit 1
    fi
}

install_packages() {
    log_info "Installing system packages..."
    case "$OS_ID" in
        "cachyos"|"arch"|"manjaro")
            sudo pacman -Syu --needed --noconfirm \
                podman \
                python \
                python-pip \
                python-yaml \
                python-psutil \
                git \
                base-devel \
                usbutils \
                xdg-utils \
                xorg-xauth \
                xorg-xhost
            ;;
        "bazzite"|"fedora")
            MISSING=""
            command -v podman   &>/dev/null || MISSING="$MISSING podman"
            command -v python3  &>/dev/null || MISSING="$MISSING python3"
            command -v git      &>/dev/null || MISSING="$MISSING git"
            command -v xdg-open &>/dev/null || MISSING="$MISSING xdg-utils"
            command -v xauth    &>/dev/null || MISSING="$MISSING xorg-x11-xauth"
            if [ -n "$MISSING" ]; then
                log_warning "Missing packages:$MISSING"
                log_info "On immutable systems: rpm-ostree install$MISSING  then reboot."
                exit 1
            fi
            log_success "All required packages present"
            ;;
        "linuxmint"|"ubuntu"|"debian"|"pop")
            sudo apt-get update
            sudo apt-get install -y \
                podman \
                python3 \
                python3-pip \
                python3-yaml \
                python3-psutil \
                git \
                build-essential \
                usbutils \
                xdg-utils \
                xauth \
                x11-xserver-utils
            ;;
        *)
            log_warning "Unknown distro: $OS_ID"
            log_info "Ensure these are installed: podman, python3, git, usbutils, xdg-utils, xauth"
            read -p "Press Enter when ready, or Ctrl+C to exit..."
            ;;
    esac
    log_success "System packages ready"
}

setup_usb_permissions() {
    log_info "Setting up USB permissions..."

    SERIAL_GROUP="dialout"
    case "$OS_ID" in
        "cachyos"|"arch"|"manjaro") SERIAL_GROUP="uucp" ;;
    esac

    if ! getent group "$SERIAL_GROUP" > /dev/null; then
        sudo groupadd "$SERIAL_GROUP"
    fi

    if ! groups "$USER" | grep -q "$SERIAL_GROUP"; then
        sudo usermod -aG "$SERIAL_GROUP" "$USER"
        log_success "Added $USER to $SERIAL_GROUP group"
        log_warning "Log out and back in for group changes to take effect"
    else
        log_info "User already in $SERIAL_GROUP group"
    fi

    UDEV_RULE='/etc/udev/rules.d/99-turing.rules'
    # Rev A: Turing 3.5", XuanFang 3.5" rev B/flagship, UsbPCMonitor 3.5"/5"/7"
    echo "SUBSYSTEM==\"tty\", ATTRS{idVendor}==\"1a86\", ATTRS{idProduct}==\"5722\", MODE=\"0666\", GROUP=\"$SERIAL_GROUP\", RUN+=\"/bin/chmod 0666 %N\"" | \
        sudo tee "$UDEV_RULE" > /dev/null
    # Legacy CH340 variant (some older boards)
    echo "SUBSYSTEM==\"tty\", ATTRS{idVendor}==\"1a86\", ATTRS{idProduct}==\"7523\", MODE=\"0666\", GROUP=\"$SERIAL_GROUP\", RUN+=\"/bin/chmod 0666 %N\"" | \
        sudo tee -a "$UDEV_RULE" > /dev/null
    # Rev C (sleeping): Turing 2.1" round, 5", 8.8" — wakes up and re-enumerates as a different PID
    echo "SUBSYSTEM==\"tty\", ATTRS{idVendor}==\"1a86\", ATTRS{idProduct}==\"ca21\", MODE=\"0666\", GROUP=\"$SERIAL_GROUP\", RUN+=\"/bin/chmod 0666 %N\"" | \
        sudo tee -a "$UDEV_RULE" > /dev/null
    # Rev C (awake): NXP USB gadget PIDs that Rev C re-enumerates as after wake
    echo "SUBSYSTEM==\"tty\", ATTRS{idVendor}==\"0525\", ATTRS{idProduct}==\"a4a7\", MODE=\"0666\", GROUP=\"$SERIAL_GROUP\", RUN+=\"/bin/chmod 0666 %N\"" | \
        sudo tee -a "$UDEV_RULE" > /dev/null
    echo "SUBSYSTEM==\"tty\", ATTRS{idVendor}==\"1d6b\", ATTRS{idProduct}==\"0121\", MODE=\"0666\", GROUP=\"$SERIAL_GROUP\", RUN+=\"/bin/chmod 0666 %N\"" | \
        sudo tee -a "$UDEV_RULE" > /dev/null
    echo "SUBSYSTEM==\"tty\", ATTRS{idVendor}==\"1d6b\", ATTRS{idProduct}==\"0106\", MODE=\"0666\", GROUP=\"$SERIAL_GROUP\", RUN+=\"/bin/chmod 0666 %N\"" | \
        sudo tee -a "$UDEV_RULE" > /dev/null
    # Rev D: Kipye Qiye Smart Display 3.5"
    echo "SUBSYSTEM==\"tty\", ATTRS{idVendor}==\"454d\", ATTRS{idProduct}==\"4e41\", MODE=\"0666\", GROUP=\"$SERIAL_GROUP\", RUN+=\"/bin/chmod 0666 %N\"" | \
        sudo tee -a "$UDEV_RULE" > /dev/null
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    log_success "Udev rule created (group: $SERIAL_GROUP)"
}

clone_repository() {
    log_info "Cloning Turing Smart Screen repository..."
    mkdir -p "$(dirname "$INSTALL_DIR")"

    if [ -d "$INSTALL_DIR" ]; then
        log_warning "Directory $INSTALL_DIR already exists"
        read -p "Remove and re-clone? (y/N): " -n 1 -r; echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$INSTALL_DIR"
        else
            log_info "Keeping existing directory"
            return 0
        fi
    fi

    git clone "$REPO_URL" "$INSTALL_DIR"
    log_success "Repository cloned to $INSTALL_DIR"
}

create_custom_scripts() {
    log_info "Creating helper scripts..."

    cat > "$INSTALL_DIR/switch_theme.py" << 'ENDPY'
#!/usr/bin/env python3
import sys, re

if len(sys.argv) < 2:
    print("Usage: switch_theme.py <theme-name>")
    sys.exit(1)

theme_name = ' '.join(sys.argv[1:])
config_file = 'config.yaml'

with open(config_file, 'r') as f:
    content = f.read()

content = re.sub(r'^(\s*)THEME:.*$', r'\1THEME: ' + theme_name, content, flags=re.MULTILINE)

with open(config_file, 'w') as f:
    f.write(content)

print(f"✓ Updated theme to: {theme_name}")
ENDPY
    chmod +x "$INSTALL_DIR/switch_theme.py"
    log_success "Created switch_theme.py"

    # Patch configure.py: fix 3 methods to use flag-file mechanism so they work
    # correctly inside the container (theme editor, save&run, open themes folder)
    CONFIGURE_PY="$INSTALL_DIR/configure.py"
    if [ -f "$CONFIGURE_PY" ]; then
        python3 - "$CONFIGURE_PY" << 'ENDPATCH'
import sys, re, os

path = sys.argv[1]
with open(path, 'r') as f:
    src = f.read()

changes = 0

# PATCH 1: on_theme_editor_click -> flag file
if ".turing_theme_editor_requested" not in src:
    p = re.compile(
        r'    def on_theme_editor_click\(self\):\n'
        r'        subprocess\.Popen\(\n'
        r'.*?shell=True\)\n',
        re.DOTALL
    )
    r = (
        '    def on_theme_editor_click(self):\n'
        '        theme = self.theme_cb.get()\n'
        '        try:\n'
        '            flag = os.path.join(MAIN_DIRECTORY, ".turing_theme_editor_requested")\n'
        '            with open(flag, "w", encoding="utf-8") as f:\n'
        '                f.write(theme + chr(10))\n'
        '        except Exception as e:\n'
        '            print("[DEBUG] Could not write theme editor flag:", e)\n'
    )
    src, n = p.subn(r, src)
    if n: changes += 1; print("Patched: on_theme_editor_click")
    else: print("WARNING: on_theme_editor_click pattern not matched")

# PATCH 2: on_saverun_click -> flag file
if ".turing_run_requested" not in src:
    p = re.compile(
        r'    def on_saverun_click\(self\):\n'
        r'        self\.save_config_values\(\)\n'
        r'        subprocess\.Popen\(.*?shell=True\)\n'
        r'        self\.window\.destroy\(\)\n',
        re.DOTALL
    )
    r = (
        '    def on_saverun_click(self):\n'
        '        self.save_config_values()\n'
        '        try:\n'
        '            flag = os.path.join(MAIN_DIRECTORY, ".turing_run_requested")\n'
        '            with open(flag, "w", encoding="utf-8") as f:\n'
        '                f.write("1" + chr(10)); f.flush(); os.fsync(f.fileno())\n'
        '        except Exception as e:\n'
        '            print("Could not write run flag:", e)\n'
        '        self.window.destroy()\n'
    )
    src, n = p.subn(r, src)
    if n: changes += 1; print("Patched: on_saverun_click")
    else: print("WARNING: on_saverun_click pattern not matched")

# PATCH 3: on_open_theme_folder_click -> flag file (fixes extra-quotes xdg-open bug)
if ".turing_open_requested" not in src:
    p = re.compile(
        r'    def on_open_theme_folder_click\(self\):\n'
        r'        path = f\'.*?\'\n'
        r'        if platform\.system\(\) == "Windows":.*?subprocess\.Popen\(\["xdg-open", path\]\)\n',
        re.DOTALL
    )
    r = (
        '    def on_open_theme_folder_click(self):\n'
        '        theme_dir = os.path.join(MAIN_DIRECTORY, "res", "themes", self.theme_cb.get())\n'
        '        try:\n'
        '            flag = os.path.join(MAIN_DIRECTORY, ".turing_open_requested")\n'
        '            with open(flag, "w", encoding="utf-8") as f:\n'
        '                f.write(theme_dir + chr(10))\n'
        '        except Exception as e:\n'
        '            print("[DEBUG] Could not write open request flag:", e)\n'
    )
    src, n = p.subn(r, src)
    if n: changes += 1; print("Patched: on_open_theme_folder_click")
    else: print("WARNING: on_open_theme_folder_click pattern not matched")

if changes > 0:
    with open(path, 'w') as f:
        f.write(src)
    print(f"configure.py: {changes} patch(es) applied")
else:
    print("configure.py: already patched or no changes needed")

# PATCH 4: save_config_values -> ensure COM_PORT saved with /dev/ prefix
# The upstream GUI strips /dev/ when displaying, then saves without it
if "ensure_dev_prefix" not in src:
    p = re.compile(
        r'(    def save_config_values\(self\):.*?)'
        r'(        self\.config\[.config.\]\[.COM_PORT.\]\s*=\s*self\.com_port_cb\.get\(\))',
        re.DOTALL
    )
    def fix_comport(m):
        return (m.group(1) +
            '        _port = self.com_port_cb.get()\n'
            '        if _port and not _port.startswith("/dev/"):\n'
            '            _port = "/dev/" + _port  # ensure_dev_prefix\n'
            '        self.config["config"]["COM_PORT"] = _port')
    new_src, n = p.subn(fix_comport, src)
    if n:
        src = new_src
        with open(path, "w") as f:
            f.write(src)
        print("Patched: save_config_values COM_PORT /dev/ prefix fix")
    else:
        print("WARNING: save_config_values COM_PORT pattern not matched")
ENDPATCH
        log_success "Patched configure.py (theme editor, save&run, open themes folder)"
    else
        log_warning "configure.py not found - skipping patch"
    fi

    # Replace sensors_python.py with our full custom version:
    # - AMD GPU via sysfs (no pyamdgpuinfo needed, dynamic path detection)
    # - MangoHud FPS reader for both AMD and Nvidia
    # - Proper fan reading, network stats, CPU temp
    # - Nvidia frequency via nvidia-smi
    SENSORS_PY="$INSTALL_DIR/library/sensors/sensors_python.py"
    if [ -f "$SENSORS_PY" ]; then
        # Detect AMD sysfs paths dynamically
        AMD_HWMON=""
        AMD_DRM=""
        for hwmon in /sys/class/hwmon/hwmon*/; do
            name_file="$hwmon/name"
            [ -f "$name_file" ] || continue
            name=$(cat "$name_file" 2>/dev/null)
            if [ "$name" = "amdgpu" ]; then
                AMD_HWMON="${hwmon%/}"
                break
            fi
        done
        for card in /sys/class/drm/card*/; do
            [ -f "${card}device/gpu_busy_percent" ] || continue
            AMD_DRM="${card%/}/device"
            break
        done
        [ -z "$AMD_HWMON" ] && AMD_HWMON="/sys/class/hwmon/hwmon0"
        [ -z "$AMD_DRM"   ] && AMD_DRM="/sys/class/drm/card0/device"
        log_info "AMD sysfs: hwmon=$AMD_HWMON  drm=$AMD_DRM"

        python3 - "$SENSORS_PY" "$AMD_HWMON" "$AMD_DRM" << 'ENDWRITE'
import sys
path, amd_hwmon, amd_drm = sys.argv[1], sys.argv[2], sys.argv[3]

content = '''# SPDX-License-Identifier: GPL-3.0-or-later
# sensors_python.py — custom version with AMD sysfs, MangoHud FPS, Nvidia support
import math, os, csv, time, platform, sys, glob, re
from collections import namedtuple
from enum import IntEnum, auto
from typing import Tuple, Optional
import GPUtil, psutil
import library.sensors.sensors as sensors
from library.log import logger

try:
    import pyamdgpuinfo
except:
    pyamdgpuinfo = None

try:
    import pyadl
except:
    pyadl = None

PNIC_BEFORE = {}

class GpuType(IntEnum):
    UNSUPPORTED = auto()
    AMD = auto()
    NVIDIA = auto()

DETECTED_GPU = GpuType.UNSUPPORTED

_AMD_HWMON = "''' + amd_hwmon + '''"
_AMD_DRM   = "''' + amd_drm + '''"

def _sysfs_read(path, divisor=1.0, default=0.0):
    try:
        with open(path) as f:
            return float(f.read().strip()) / divisor
    except Exception:
        return default

def _read_pp_dpm_clock_mhz(kind="sclk"):
    p = f"{_AMD_DRM}/pp_dpm_{kind}"
    if not os.path.exists(p):
        return None
    try:
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            lines = [ln.strip() for ln in f.readlines() if ln.strip()]
    except Exception:
        return None
    star = next((ln for ln in lines if "*" in ln), None)
    target = star or (lines[0] if lines else None)
    if not target:
        return None
    m = re.search(r":\\s*([0-9.]+)\\s*([mMgG])hz", target)
    if not m:
        m = re.search(r"([0-9.]+)\\s*([mMgG])hz", target)
    if not m:
        return None
    val = float(m.group(1))
    return val * 1000.0 if m.group(2).lower() == "g" else val

def sensors_fans():
    from psutil._common import bcat, cat
    import collections
    ret = collections.defaultdict(list)
    basenames = glob.glob("/sys/class/hwmon/hwmon*/fan*_*") or glob.glob("/sys/class/hwmon/hwmon*/device/fan*_*")
    basenames = sorted(set([x.split("_")[0] for x in basenames]))
    for base in basenames:
        try:
            current_rpm = int(bcat(base + "_input"))
            try: max_rpm = int(bcat(base + "_max"))
            except: max_rpm = 3000 if current_rpm > 2200 else (2200 if current_rpm > 1500 else 1500)
            try: min_rpm = int(bcat(base + "_min"))
            except: min_rpm = 0
            percent = int((current_rpm - min_rpm) / (max_rpm - min_rpm) * 100)
        except (IOError, OSError):
            continue
        unit_name = cat(os.path.join(os.path.dirname(base), "name")).strip()
        label = cat(base + "_label", fallback=os.path.basename(base)).strip()
        sfan = namedtuple("sfan", ["label", "current", "percent"])
        ret[unit_name].append(sfan(label, current_rpm, percent))
    return dict(ret)

def is_cpu_fan(label):
    return "cpu" in label.lower() or "proc" in label.lower()

_MH_CACHE = {"last_t": 0.0, "last_fps": -1, "path": None, "path_checked_t": 0.0, "fps_idx": None, "smooth_load": -1.0}

def _mangohud_fps_from_csv_dir(base_dir="/host_mangohud"):
    # Resolve best available path: /tmp/turing (shared host+container volume) first,
    # then /host_mangohud, then the passed base_dir
    for _candidate in ("/tmp/turing", "/host_mangohud", base_dir):
        try:
            if os.path.isdir(_candidate) and any(f.endswith(".csv") for f in os.listdir(_candidate)):
                base_dir = _candidate
                break
        except Exception:
            pass
    try:
        now = time.time()
        if now - _MH_CACHE["last_t"] < 0.5:
            return int(_MH_CACHE["last_fps"])
        _MH_CACHE["last_t"] = now
        if not os.path.isdir(base_dir):
            _MH_CACHE["last_fps"] = -1; return -1
        if _MH_CACHE["path"] is None or now - _MH_CACHE["path_checked_t"] > 2.0:
            _MH_CACHE["path_checked_t"] = now
            candidates = []
            for fn in os.listdir(base_dir):
                low = fn.lower()
                if not low.endswith(".csv") or low.endswith("_summary.csv"): continue
                p = os.path.join(base_dir, fn)
                try: st = os.stat(p)
                except: continue
                if st.st_mtime < now - 600 or st.st_size < 256: continue
                candidates.append((st.st_mtime, st.st_size, p))
            if candidates:
                candidates.sort(reverse=True)
                _MH_CACHE["path"] = candidates[0][2]; _MH_CACHE["fps_idx"] = None
        path = _MH_CACHE["path"]
        if not path or not os.path.exists(path):
            _MH_CACHE["last_fps"] = -1; return -1
        if time.time() - os.path.getmtime(path) > 30:
            _MH_CACHE["last_fps"] = -1; return -1
        if _MH_CACHE["fps_idx"] is None:
            fps_idx = None
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for _ in range(600):
                        ln = f.readline()
                        if not ln: break
                        ln = ln.strip()
                        if not ln or "," not in ln: continue
                        cols = [c.strip().lower() for c in ln.split(",")]
                        if "fps" in cols: fps_idx = cols.index("fps"); break
            except: fps_idx = None
            _MH_CACHE["fps_idx"] = fps_idx
        fps_idx = _MH_CACHE["fps_idx"]
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END); size = f.tell()
            f.seek(max(size - 16384, 0))
            tail = f.read().decode("utf-8", errors="ignore")
        lines = [l.strip() for l in tail.splitlines() if l.strip()]
        if not lines: return int(_MH_CACHE["last_fps"])
        def _ft_to_fps(ft):
            if ft <= 0: return -1.0
            sec = ft/1e9 if ft >= 1_000_000 else (ft/1e6 if ft >= 1_000 else ft/1e3)
            return 1.0/sec if sec > 0 else -1.0
        samples = []
        for ln in reversed(lines):
            low = ln.lower()
            if low.startswith(("os,","cpu,","gpu,","ram,","kernel,","driver,","cpuscheduler")): continue
            if fps_idx is not None and "," in ln:
                parts = [p.strip() for p in ln.split(",")]
                if len(parts) > fps_idx:
                    try:
                        v = float(parts[fps_idx])
                        if 1 <= v <= 500: samples.append(v)
                    except: pass
            elif "," not in ln:
                try:
                    v = _ft_to_fps(float(ln))
                    if 1 <= v <= 500: samples.append(v)
                except: pass
            if len(samples) >= 5: break
        if not samples: return int(_MH_CACHE["last_fps"])
        _MH_CACHE["last_fps"] = int(round(samples[0]))
        return _MH_CACHE["last_fps"]
    except Exception:
        return int(_MH_CACHE.get("last_fps", -1))

class Cpu(sensors.Cpu):
    @staticmethod
    def percentage(interval):
        try: return psutil.cpu_percent(interval=interval)
        except: return math.nan
    @staticmethod
    def frequency():
        try: return psutil.cpu_freq().current
        except: return math.nan
    @staticmethod
    def load():
        try: return psutil.getloadavg()
        except: return math.nan, math.nan, math.nan
    @staticmethod
    def temperature():
        cpu_temp = math.nan
        try:
            t = psutil.sensors_temperatures()
            if "coretemp" in t: cpu_temp = t["coretemp"][0].current
            elif "k10temp" in t:
                entries = t["k10temp"]
                tctl = next((e.current for e in entries if (e.label or "").lower() == "tctl"), None)
                cpu_temp = tctl if tctl is not None else max((e.current for e in entries if e.current is not None), default=math.nan)
            elif "cpu_thermal" in t: cpu_temp = t["cpu_thermal"][0].current
            elif "zenpower" in t: cpu_temp = t["zenpower"][0].current
        except: pass
        return cpu_temp
    @staticmethod
    def fan_percent(fan_name=None):
        # Try PWM duty cycle from nct6798 pwm2 (CPU_FAN header) for accurate %
        try:
            import glob
            for hwmon in glob.glob("/sys/class/hwmon/hwmon*/"):
                try:
                    chip = open(hwmon + "name").read().strip()
                except: continue
                if not any(k in chip for k in ("nct", "it8", "w83")):
                    continue
                pwm_f = hwmon + "pwm2"
                if os.path.exists(pwm_f):
                    try:
                        pwm = float(open(pwm_f).read().strip())
                        try: pwm_max = float(open(hwmon + "pwm2_max").read().strip())
                        except: pwm_max = 255.0
                        if pwm_max > 0:
                            return round(pwm / pwm_max * 100, 1)
                    except: pass
        except: pass
        # Fallback: psutil RPM-based
        try:
            fans = sensors_fans()
            if fans:
                for name, entries in fans.items():
                    for entry in entries:
                        if fan_name is not None and fan_name == "%s/%s" % (name, entry.label): return entry.percent
                        elif is_cpu_fan(entry.label) or is_cpu_fan(name):
                            return entry.percent
                for name, entries in fans.items():
                    if any(x in name.lower() for x in ("nct", "it87", "w83", "nuvoton", "ite")):
                        for entry in entries:
                            if entry.current > 0:
                                return entry.percent
        except: pass
        return math.nan

class Gpu(sensors.Gpu):
    @staticmethod
    def stats():
        if DETECTED_GPU == GpuType.AMD: return GpuAmd.stats()
        elif DETECTED_GPU == GpuType.NVIDIA: return GpuNvidia.stats()
        return math.nan, math.nan, math.nan, math.nan, math.nan
    @staticmethod
    def fps():
        if DETECTED_GPU == GpuType.AMD: return GpuAmd.fps()
        elif DETECTED_GPU == GpuType.NVIDIA: return GpuNvidia.fps()
        return _mangohud_fps_from_csv_dir()
    @staticmethod
    def fan_percent():
        if DETECTED_GPU == GpuType.AMD: return GpuAmd.fan_percent()
        elif DETECTED_GPU == GpuType.NVIDIA: return GpuNvidia.fan_percent()
        return math.nan
    @staticmethod
    def frequency():
        if DETECTED_GPU == GpuType.AMD: return GpuAmd.frequency()
        elif DETECTED_GPU == GpuType.NVIDIA: return GpuNvidia.frequency()
        return GpuAmd.frequency()
    @staticmethod
    def is_available():
        global DETECTED_GPU
        if GpuNvidia.is_available(): logger.info("Detected Nvidia GPU(s)"); DETECTED_GPU = GpuType.NVIDIA
        elif GpuAmd.is_available(): logger.info("Detected AMD GPU(s)"); DETECTED_GPU = GpuType.AMD
        else:
            logger.warning("No supported GPU found"); DETECTED_GPU = GpuType.UNSUPPORTED
            if sys.version_info >= (3, 11) and platform.system() in ("Linux", "Darwin"):
                logger.warning("AMD GPU users: see https://github.com/mathoudebine/turing-smart-screen-python/wiki/Troubleshooting#linux--macos-no-supported-gpu-found-with-an-amd-gpu-and-python-311")
        return DETECTED_GPU != GpuType.UNSUPPORTED

class GpuNvidia(sensors.Gpu):
    @staticmethod
    def stats():
        gpus = GPUtil.getGPUs()
        def avg(lst):
            return sum(lst)/len(lst) if lst else math.nan
        try: mu = avg([g.memoryUsed for g in gpus])
        except: mu = math.nan
        try: mt = avg([g.memoryTotal for g in gpus])
        except: mt = math.nan
        try: mp = (mu/mt)*100
        except: mp = math.nan
        try: load = avg([g.load for g in gpus])*100
        except: load = math.nan
        try: temp = avg([g.temperature for g in gpus])
        except: temp = math.nan
        return load, mp, mu, mt, temp
    @staticmethod
    def fps(): return _mangohud_fps_from_csv_dir()
    @staticmethod
    def fan_percent():
        try:
            fans = sensors_fans()
            for name, entries in fans.items():
                for entry in entries:
                    if "gpu" in entry.label.lower() or "gpu" in name.lower(): return entry.percent
        except: pass
        return math.nan
    @staticmethod
    def frequency():
        try:
            import subprocess
            r = subprocess.run(["nvidia-smi","--query-gpu=clocks.current.graphics","--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=2)
            v = r.stdout.strip()
            if v and v != "[N/A]": return float(v)
        except: pass
        return math.nan
    @staticmethod
    def is_available():
        try: return len(GPUtil.getGPUs()) > 0
        except: return False

class GpuAmd(sensors.Gpu):
    _load_samples = []
    @staticmethod
    def stats():
        try:
            raw = _sysfs_read(f"{_AMD_DRM}/gpu_busy_percent")
            GpuAmd._load_samples.append(raw)
            if len(GpuAmd._load_samples) > 30: GpuAmd._load_samples = GpuAmd._load_samples[-30:]
            s = sorted(GpuAmd._load_samples); median = s[len(s)//2]
            prev = _MH_CACHE.get("smooth_load", -1.0)
            _MH_CACHE["smooth_load"] = float(median) if prev < 0 else 0.2*median + 0.8*prev
            load = _MH_CACHE["smooth_load"]
        except: load = math.nan
        try:
            vu = _sysfs_read(f"{_AMD_DRM}/mem_info_vram_used", divisor=1024**2)
            vt = _sysfs_read(f"{_AMD_DRM}/mem_info_vram_total", divisor=1024**2)
            mp = (vu/vt*100) if vt > 0 else math.nan
        except: vu = vt = mp = math.nan
        try: temp = _sysfs_read(f"{_AMD_HWMON}/temp1_input", divisor=1000.0)
        except: temp = math.nan
        return load, mp, vu, vt, temp
    @staticmethod
    def fps(): return _mangohud_fps_from_csv_dir()
    @staticmethod
    def fan_percent():
        # Use PWM duty cycle for accurate % (matches AMD Radeon / CoolerControl)
        try:
            import glob as _gl
            for hwmon in _gl.glob("/sys/class/hwmon/hwmon*/"):
                try:
                    chip = open(hwmon + "name").read().strip()
                except: continue
                if chip != "amdgpu": continue
                pwm_f = hwmon + "pwm1"
                if os.path.exists(pwm_f):
                    try:
                        pwm = float(open(pwm_f).read().strip())
                        try: pwm_max = float(open(hwmon + "pwm1_max").read().strip())
                        except: pwm_max = 255.0
                        if pwm_max > 0:
                            return round(pwm / pwm_max * 100, 1)
                    except: pass
        except: pass
        # Fallback to RPM-based
        try:
            fans = sensors_fans()
            for name, entries in fans.items():
                for entry in entries:
                    if "gpu" in entry.label.lower() or "gpu" in name.lower(): return entry.percent
        except: pass
        return math.nan
    @staticmethod
    def frequency():
        try:
            mhz = _read_pp_dpm_clock_mhz("sclk")
            if mhz is None or math.isnan(mhz) or mhz == 0:
                mhz = _sysfs_read(f"{_AMD_HWMON}/freq1_input", divisor=1_000_000.0)
            if mhz and mhz > 0: return mhz
        except: pass
        return math.nan
    @staticmethod
    def is_available(): return os.path.exists(f"{_AMD_DRM}/gpu_busy_percent")

class Memory(sensors.Memory):
    @staticmethod
    def swap_percent():
        try: return psutil.swap_memory().percent
        except: return math.nan
    @staticmethod
    def virtual_percent():
        try: return psutil.virtual_memory().percent
        except: return math.nan
    @staticmethod
    def virtual_used():
        try: return psutil.virtual_memory().total - psutil.virtual_memory().available
        except: return -1
    @staticmethod
    def virtual_free():
        try: return psutil.virtual_memory().available
        except: return -1

class Disk(sensors.Disk):
    @staticmethod
    def disk_usage_percent():
        try: return psutil.disk_usage("/").percent
        except: return math.nan
    @staticmethod
    def disk_used():
        try: return psutil.disk_usage("/").used
        except: return -1
    @staticmethod
    def disk_free():
        try: return psutil.disk_usage("/").free
        except: return -1

class Net(sensors.Net):
    @staticmethod
    def stats(if_name, interval):
        try:
            after = psutil.net_io_counters(pernic=True)
            if if_name and if_name in after:
                if if_name not in PNIC_BEFORE:
                    PNIC_BEFORE[if_name] = after[if_name]
                    return 0, after[if_name].bytes_sent, 0, after[if_name].bytes_recv
                try:
                    ul = (after[if_name].bytes_sent - PNIC_BEFORE[if_name].bytes_sent) / interval
                    dl = (after[if_name].bytes_recv - PNIC_BEFORE[if_name].bytes_recv) / interval
                    up = after[if_name].bytes_sent; dn = after[if_name].bytes_recv
                except Exception as e:
                    logger.warning(f"Network stats error for {if_name}: {e}"); ul=dl=up=dn=0
                PNIC_BEFORE[if_name] = after[if_name]
                return ul, up, dl, dn
            elif if_name:
                logger.warning("Network interface \'%s\' not found. Check names in config.yaml." % if_name)
            return 0, 0, 0, 0
        except Exception as e:
            logger.error(f"Network stats error: {e}"); return -1, -1, -1, -1
'''

with open(path, 'w') as f:
    f.write(content.replace('AMD_HWMON_PLACEHOLDER', amd_hwmon).replace('AMD_DRM_PLACEHOLDER', amd_drm))
print(f"Written custom sensors_python.py (AMD hwmon={amd_hwmon}, drm={amd_drm})")
ENDWRITE
        log_success "Written custom sensors_python.py (AMD sysfs + MangoHud FPS + Nvidia)"
    else
        log_warning "sensors_python.py not found - skipping"
    fi

    # Patch stats.py: guard freq_ghz NaN before int() conversion
    STATS_PY="$INSTALL_DIR/library/stats.py"
    if [ -f "$STATS_PY" ]; then
        python3 - "$STATS_PY" << 'ENDPATCH'
import sys, os

path = sys.argv[1]
with open(path) as f:
    src = f.read()

old = '        freq_ghz = sensors.Gpu.frequency() / 1000'
new = ('        freq_ghz = sensors.Gpu.frequency() / 1000' + chr(10) +
       '        if math.isnan(freq_ghz): freq_ghz = 0.0')

if old in src and 'if math.isnan(freq_ghz)' not in src:
    with open(path, 'w') as f:
        f.write(src.replace(old, new))
    print("Patched: freq_ghz NaN guard added")
else:
    print("stats.py: already patched or pattern not matched")
ENDPATCH
        log_success "Patched stats.py (GPU frequency NaN guard)"
    else
        log_warning "stats.py not found - skipping patch"
    fi

    # Patch stats.py: remove FPS suppression block so MangoHud FPS displays correctly
    if [ -f "$STATS_PY" ]; then
        python3 - "$STATS_PY" << 'ENDFPSPATCH'
import sys

path = sys.argv[1]
with open(path) as f:
    src = f.read()

old = ("            fps = 0\n"
       "            if gpu_fps_text_data['SHOW'] or gpu_fps_radial_data['SHOW'] or gpu_fps_graph_data[\n"
       "                'SHOW'] or gpu_fps_line_graph_data['SHOW']:\n"
       "                logger.warning(\"Your GPU FPS is not supported yet\")\n"
       "                gpu_fps_text_data['SHOW'] = False\n"
       "                gpu_fps_radial_data['SHOW'] = False\n"
       "                gpu_fps_graph_data['SHOW'] = False\n"
       "                gpu_fps_line_graph_data['SHOW'] = False\n")

new = "            fps = 0\n"

if old in src:
    with open(path, 'w') as f:
        f.write(src.replace(old, new))
    print("Patched: FPS suppression block removed")
elif 'Your GPU FPS is not supported yet' not in src:
    print("stats.py: FPS already patched")
else:
    print("stats.py: FPS pattern not matched - may need manual fix")
ENDFPSPATCH
        log_success "Patched stats.py (FPS suppression removed)"
    fi

    # Configure MangoHud to write FPS logs directly to /tmp/turing
    # /tmp/turing is mounted in all containers, so no volume mount tricks needed
    MH_CONF_DIR="$HOME/.config/MangoHud"
    MH_CONF="$MH_CONF_DIR/MangoHud.conf"
    mkdir -p "$MH_CONF_DIR"
    if [ ! -f "$MH_CONF" ]; then
        cat > "$MH_CONF" << 'ENDMHCONF'
log_interval=500
log_duration=0
output_folder=/tmp/turing
ENDMHCONF
        log_success "Created MangoHud config: output_folder=/tmp/turing"
    elif ! grep -q "output_folder=/tmp/turing" "$MH_CONF"; then
        # Update existing config
        if grep -q "^output_folder=" "$MH_CONF"; then
            sed -i 's|^output_folder=.*|output_folder=/tmp/turing|' "$MH_CONF"
        else
            echo "output_folder=/tmp/turing" >> "$MH_CONF"
        fi
        log_success "Updated MangoHud config: output_folder=/tmp/turing"
    else
        log_info "MangoHud config already set to /tmp/turing"
    fi
    log_info "Steam launch option for FPS tracking: MANGOHUD=1 %command%"
}

create_containerfile() {
    log_info "Setting up container configuration..."
    cd "$INSTALL_DIR"

    # Always write our known-good Containerfile - upstream may have typos or missing packages
    cat > Containerfile << 'ENDCONTAINER'
FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    gcc \
    git \
    python3-dev \
    python3-tk \
    tk-dev \
    xdg-utils \
    libusb-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python3", "main.py"]
ENDCONTAINER
    log_success "Containerfile created"
}

build_container() {
    log_info "Building Podman container image..."
    cd "$INSTALL_DIR"

    # Pull latest changes before building to get newest hardware support
    if [ -d ".git" ]; then
        log_info "Pulling latest upstream changes..."
        git pull --ff-only 2>/dev/null && log_success "Repository updated" || log_warning "Could not pull updates - building from current state"
    fi

    # Skip build if image already exists
    if podman image exists "$IMAGE_NAME" 2>/dev/null; then
        log_info "Container image $IMAGE_NAME already exists - skipping build"
        log_info "To force rebuild: podman rmi $IMAGE_NAME && bash install_turing.sh"
        return 0
    fi

    CONTAINER_FILE="Containerfile"
    [ ! -f "$CONTAINER_FILE" ] && [ -f "Dockerfile" ] && CONTAINER_FILE="Dockerfile"
    [ ! -f "$CONTAINER_FILE" ] && { log_error "No Containerfile or Dockerfile found"; exit 1; }

    podman build -t "$IMAGE_NAME" -f "$CONTAINER_FILE" .
    log_success "Container image built: $IMAGE_NAME"
}


# Create the full-featured turing.sh management script
create_management_script() {
    log_info "Creating turing.sh management script..."

    # Detect MangoHud log paths dynamically at install time
    MANGOHUD_LOGS_HOST=""
    if [ -d "$HOME/.local/share/mangohud" ]; then
        MANGOHUD_LOGS_HOST="$HOME/.local/share/mangohud"
    elif [ -d "$HOME/mangohud_logs" ]; then
        MANGOHUD_LOGS_HOST="$HOME/mangohud_logs"
    fi

    # Detect display server
    DISPLAY_SERVER="x11"
    [ -n "${WAYLAND_DISPLAY:-}" ] && DISPLAY_SERVER="wayland"

    cat > "$INSTALL_DIR/turing.sh" << ENDSCRIPT
#!/usr/bin/env bash
set -euo pipefail

TURING_DIR="\${TURING_DIR:-$INSTALL_DIR}"
TURING_IMAGE="\${TURING_IMAGE:-$IMAGE_NAME}"
TURING_DEV="\${TURING_DEV:-}"

name_display="\${TURING_CONTAINER:-$CONTAINER_NAME}"
name_config="\${TURING_CONTAINER:-$CONTAINER_NAME}-config"

die() { echo "ERROR: \$*" >&2; exit 1; }

ensure_dev() {
  # Rev C screens use COM_PORT: AUTO and don't set TURING_DEV — skip the check
  [ -z "\${TURING_DEV:-}" ] && return 0
  [ -e "\$TURING_DEV" ] || die "\$TURING_DEV not found. Plug the screen in."
}

stop_all() {
  # Send stop signal
  podman stop "\$name_display" "\$name_config" >/dev/null 2>&1 || true
  # Wait for containers to fully exit (serial port must be released)
  for i in \$(seq 1 20); do
    podman ps -a --format "{{.Names}}" 2>/dev/null | grep -qE "^\$name_display$|^\$name_config$" || break
    sleep 0.5
  done
  # Force remove any lingering containers
  podman rm -f "\$name_display" "\$name_config" >/dev/null 2>&1 || true
}

detect_gpu_flags() {
    GPU_FLAGS=""
    if [ -d /dev/dri ]; then
        GPU_FLAGS="\$GPU_FLAGS -v /dev/dri:/dev/dri"
    fi
    if [ -e /dev/nvidia0 ]; then
        for dev in /dev/nvidia[0-9]*; do
            GPU_FLAGS="\$GPU_FLAGS --device=\$dev:\$dev"
        done
        GPU_FLAGS="\$GPU_FLAGS --device=/dev/nvidiactl:/dev/nvidiactl"
        [ -e /dev/nvidia-uvm ]       && GPU_FLAGS="\$GPU_FLAGS --device=/dev/nvidia-uvm:/dev/nvidia-uvm"
        [ -e /dev/nvidia-uvm-tools ] && GPU_FLAGS="\$GPU_FLAGS --device=/dev/nvidia-uvm-tools:/dev/nvidia-uvm-tools"
        [ -e /dev/nvidia-modeset ]   && GPU_FLAGS="\$GPU_FLAGS --device=/dev/nvidia-modeset:/dev/nvidia-modeset"
        # Mount nvidia-smi and libnvidia-ml so GPUtil works inside the container
        if command -v nvidia-smi &>/dev/null; then
            GPU_FLAGS="\$GPU_FLAGS -v \$(command -v nvidia-smi):/usr/bin/nvidia-smi:ro"
        fi
        # Mount the versioned library and create both expected symlink names
        for lib in /usr/lib/libnvidia-ml.so.[0-9]*; do
            [ -f "\$lib" ] && GPU_FLAGS="\$GPU_FLAGS -v \$lib:/usr/lib/libnvidia-ml.so.1:ro -v \$lib:/usr/lib/libnvidia-ml.so:ro" && break
        done
    fi
    echo "\$GPU_FLAGS"
}

# Build MangoHud volume mounts if paths exist
mangohud_flags() {
    local flags=""
    # MangoHud logs dir (host-side, where MangoHud writes FPS logs)
    for candidate in "\$HOME/.local/share/mangohud" "\$HOME/mangohud_logs" "/var/home/\$USER/mangohud_logs"; do
        if [ -d "\$candidate" ]; then
            flags="\$flags -v \$candidate:/host_mangohud:z"
            break
        fi
    done
    # MangoHud config dir
    if [ -d "\$HOME/.config/MangoHud" ]; then
        flags="\$flags -v \$HOME/.config/MangoHud:/mangohud:ro,z"
    elif [ -d "\$HOME/.local/share/mangohud" ]; then
        flags="\$flags -v \$HOME/.local/share/mangohud:/mangohud:ro,z"
    fi
    echo "\$flags"
}

cmd_up() {
  ensure_dev
  stop_all
  GPU_FLAGS=\$(detect_gpu_flags)
  MH_FLAGS=\$(mangohud_flags)
  # Pass host timezone so container clock matches local time
  HOST_TZ="\$(cat /etc/localtime | head -c0; readlink /etc/localtime 2>/dev/null | sed 's|.*zoneinfo/||' || timedatectl show -p Timezone --value 2>/dev/null || echo 'UTC')"
  mkdir -p /tmp/turing
  # If TURING_CONFIG_DIR is set, overlay its config.yaml on top of the main app mount.
  # This lets additional screens share the main codebase but use their own config.
  CONFIG_MOUNT=""
  if [ -n "\${TURING_CONFIG_DIR:-}" ] && [ -f "\$TURING_CONFIG_DIR/config.yaml" ]; then
    CONFIG_MOUNT="-v \$TURING_CONFIG_DIR/config.yaml:/app/config.yaml:z"
  fi
  podman run -d --replace \\
    --name "\$name_display" \\
    --network=host \\
    --privileged \\
    -v /dev:/dev \\
    -v /sys:/sys:ro \\
    -v /etc/localtime:/etc/localtime:ro \\
    -v /usr/share/zoneinfo:/usr/share/zoneinfo:ro \\
    -e TZ="\$HOST_TZ" \\
    \$GPU_FLAGS \\
    \$MH_FLAGS \\
    -v "\$TURING_DIR:/app:z" \\
    \$CONFIG_MOUNT \\
    -v /tmp/turing:/tmp/turing \\
    -e NO_TRAY=1 \\
    "\$TURING_IMAGE" >/dev/null
  echo "Started: \$name_display"
  echo "Logs: ./turing.sh logs"
}

# 'start' is an alias for 'up'
cmd_start() { cmd_up; }

cmd_stop() {
  # Stop the systemd service first so it doesn't auto-restart the container
  if systemctl --user is-active turing-display.service &>/dev/null; then
    systemctl --user stop turing-display.service
  fi
  stop_all
  echo "Stopped."
}

cmd_restart() {
  # If the systemd service is active, let systemd own the restart to avoid
  # a double-start (systemd would otherwise see the container stop and
  # restart it on top of our own cmd_up).
  if systemctl --user is-active turing-display.service &>/dev/null; then
    systemctl --user restart turing-display.service
    echo "Restarted via systemd"
  else
    cmd_stop
    sleep 1
    cmd_up
  fi
}

cmd_logs() {
  podman logs -f "\$name_display"
}

cmd_status() {
  podman ps -a | grep "\$name_display" || echo "Container not running"
}

cmd_config() {
  ensure_dev
  podman rm -f "\$name_config" >/dev/null 2>&1 || true

  run_flag="\$TURING_DIR/.turing_run_requested"
  rm -f "\$run_flag" >/dev/null 2>&1 || true

  GPU_FLAGS=\$(detect_gpu_flags)
  MH_FLAGS=\$(mangohud_flags)

  # Build display passthrough flags - supports Wayland+XWayland (KDE Plasma) and pure X11
  DISPLAY_FLAGS=""
  XAUTH_TMP=""

  # Determine best DISPLAY to use - prefer XWayland :0 under Wayland
  EFFECTIVE_DISPLAY="\${DISPLAY:-}"
  if [[ -z "\$EFFECTIVE_DISPLAY" ]] && [[ -n "\${WAYLAND_DISPLAY:-}" ]]; then
    EFFECTIVE_DISPLAY=":0"
  fi

  if [[ -n "\${WAYLAND_DISPLAY:-}" ]]; then
    # Wayland session - pass Wayland socket for native Wayland apps
    RUNTIME_DIR="\${XDG_RUNTIME_DIR:-/run/user/\$(id -u)}"
    DISPLAY_FLAGS="-e WAYLAND_DISPLAY=\$WAYLAND_DISPLAY -e XDG_RUNTIME_DIR=\$RUNTIME_DIR -v \$RUNTIME_DIR:\$RUNTIME_DIR:rw"
  fi

  if [[ -n "\$EFFECTIVE_DISPLAY" ]]; then
    # Allow local X connections (safe for local container, avoids xauth cookie issues on Wayland)
    xhost +local: >/dev/null 2>&1 || true
    DISPLAY_FLAGS="\$DISPLAY_FLAGS -e DISPLAY=\$EFFECTIVE_DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix:ro"

    # Also try xauth - works on pure X11, silently skipped if empty on Wayland
    XAUTH_TMP="\$(mktemp)"
    if xauth nlist "\$EFFECTIVE_DISPLAY" 2>/dev/null | grep -q .; then
      xauth nlist "\$EFFECTIVE_DISPLAY" | sed -e 's/^..../ffff/' | xauth -f "\$XAUTH_TMP" nmerge - 2>/dev/null || true
      DISPLAY_FLAGS="\$DISPLAY_FLAGS -e XAUTHORITY=/tmp/.Xauthority -v \$XAUTH_TMP:/tmp/.Xauthority:ro"
    else
      rm -f "\$XAUTH_TMP"
      XAUTH_TMP=""
    fi
  fi

  if [[ -z "\${WAYLAND_DISPLAY:-}" ]] && [[ -z "\$EFFECTIVE_DISPLAY" ]]; then
    echo "[CONFIG] WARNING: No display session detected - run from a desktop session"
  fi

  # Same config overlay as cmd_up — screen-specific config.yaml on top of main app
  CONFIG_MOUNT=""
  if [ -n "\${TURING_CONFIG_DIR:-}" ] && [ -f "\$TURING_CONFIG_DIR/config.yaml" ]; then
    CONFIG_MOUNT="-v \$TURING_CONFIG_DIR/config.yaml:/app/config.yaml:z"
  fi

  podman run --rm --replace \\
    --name "\$name_config" \\
    --privileged \\
    -v /dev:/dev \\
    -v /sys:/sys:ro \\
    \$GPU_FLAGS \\
    \$MH_FLAGS \\
    \$DISPLAY_FLAGS \\
    -e HOME=/tmp \\
    -e XDG_STATE_HOME=/tmp/state \\
    -v "\$TURING_DIR:/app:z" \\
    \$CONFIG_MOUNT \\
    -v /tmp/turing:/tmp/turing \\
    --entrypoint python3 \\
    "\$TURING_IMAGE" \\
    /app/configure.py &
  gui_pid=\$!

  while kill -0 "\$gui_pid" >/dev/null 2>&1; do
    handle_open_requested
    launch_theme_editor_if_requested
    sleep 0.2
  done
  wait "\$gui_pid" 2>/dev/null || true
  handle_open_requested
  launch_theme_editor_if_requested
  [[ -n "\$XAUTH_TMP" ]] && rm -f "\$XAUTH_TMP"

  if [[ -f "\$run_flag" ]]; then
    rm -f "\$run_flag"
    echo "[CONFIG] Save&Run requested -> restarting display"
    cmd_restart
  else
    echo "[CONFIG] GUI closed (no Save&Run)"
  fi
}

cmd_theme() {
  local theme_name="\$*"
  if [[ -z "\$theme_name" ]]; then
    echo "Usage: turing theme <theme-name>"
    cmd_theme_list
    return 1
  fi
  if [[ ! -d "\$TURING_DIR/res/themes/\$theme_name" ]]; then
    echo "ERROR: Theme '\$theme_name' not found"
    cmd_theme_list
    return 1
  fi
  echo "[THEME] Switching to: \$theme_name"
  # Escape & and | for sed replacement string (& = matched text, | = delimiter)
  local escaped_name
  escaped_name="\$(printf '%s' "\$theme_name" | sed 's/[&|]/\\\\&/g')"
  sed -i "s|^  THEME:.*|  THEME: \$escaped_name|" "\$TURING_DIR/config.yaml"
  echo "[THEME] Config updated"
  cmd_restart >/dev/null 2>&1
  echo "[THEME] Switch complete!"
}

cmd_switch() {
  local theme_name="\$*"
  if [[ -z "\$theme_name" ]]; then
    echo "Usage: turing switch <theme-name>"
    return 1
  fi
  if [[ ! -d "\$TURING_DIR/res/themes/\$theme_name" ]]; then
    echo "ERROR: Theme '\$theme_name' not found"
    cmd_theme_list
    return 1
  fi
  echo "[SWITCH] Switching to: \$theme_name"
  local start_time=\$(date +%s)
  mkdir -p /tmp/turing
  echo "\$theme_name" > /tmp/turing/theme_switch_request
  echo "[SWITCH] Processing..."
  for i in {1..30}; do
    sleep 0.5
    if [[ ! -f /tmp/turing/theme_switch_request ]]; then
      local end_time=\$(date +%s)
      echo "[SWITCH] ✓ Theme switched in \$((end_time - start_time))s"
      return 0
    fi
  done
  echo "[SWITCH] ✗ Timeout - check logs: ./turing.sh logs"
  return 1
}

cmd_fastswitch() {
  local theme_name="\$*"
  if [[ -z "\$theme_name" ]]; then
    echo "Usage: turing fastswitch <theme-name>"
    return 1
  fi
  if [[ ! -d "\$TURING_DIR/res/themes/\$theme_name" ]]; then
    echo "ERROR: Theme '\$theme_name' not found"
    cmd_theme_list
    return 1
  fi
  echo "[FAST SWITCH] Switching to: \$theme_name"
  local start_time=\$(date +%s)
  podman exec "\$name_display" python3 -c "
from library.fast_theme_switch_v2 import fast_switch
success = fast_switch.switch_theme('\$theme_name')
exit(0 if success else 1)
" 2>&1 | grep -E "\[FAST SWITCH\]|\[THEME CACHE\]"
  if [[ \${PIPESTATUS[0]} -eq 0 ]]; then
    echo "[FAST SWITCH] ✓ Complete in \$(($(date +%s) - start_time))s"
  else
    echo "[FAST SWITCH] ✗ Failed - try: ./turing.sh theme '\$theme_name'"
    return 1
  fi
}

cmd_suite() {
  local suite_name="\${1:-}"
  if [[ -z "\$suite_name" ]]; then
    echo "Available suites:"
    podman exec "\$name_display" python3 -c "
from library.suite_manager import suite_manager
suite_manager.print_suites()
" 2>&1 | grep -E "\[SUITE\]"
    return 0
  fi
  echo "[SUITE] Activating: \$suite_name"
  podman exec "\$name_display" python3 -c "
from library.fast_theme_switch_v2 import fast_switch
success = fast_switch.switch_to_suite('\$suite_name')
exit(0 if success else 1)
" 2>&1 | grep -E "\[SUITE\]|\[THEME CACHE\]|\[FAST SWITCH\]"
  [[ \${PIPESTATUS[0]} -eq 0 ]] && echo "[SUITE] ✓ Activated" || { echo "[SUITE] ✗ Failed"; return 1; }
}

cmd_next_theme() {
  podman exec "\$name_display" python3 -c "
from library.fast_theme_switch_v2 import fast_switch
theme = fast_switch.next_theme()
print(f'[SUITE] Switched to: {theme}') if theme else (print('[SUITE] No active suite') or exit(1))
" 2>&1 | grep -E "\[SUITE\]|\[FAST SWITCH\]"
}

cmd_prev_theme() {
  podman exec "\$name_display" python3 -c "
from library.fast_theme_switch_v2 import fast_switch
theme = fast_switch.prev_theme()
print(f'[SUITE] Switched to: {theme}') if theme else (print('[SUITE] No active suite') or exit(1))
" 2>&1 | grep -E "\[SUITE\]|\[FAST SWITCH\]"
}

cmd_cache_stats() {
  podman exec "\$name_display" python3 -c "
from library.fast_theme_switch_v2 import fast_switch
fast_switch.print_stats()
" 2>&1 | grep -E "\[THEME CACHE\]|\[SUITE\]"
}

cmd_theme_list() {
  echo "Available themes:"
  ls -1 "\$TURING_DIR/res/themes/" | grep -v "^--" | grep -v "\.yaml\$" | grep -v "\.md\$"
}

cmd_theme_pick() {
  # Numbered interactive theme picker - lists alphabetically, pick by number
  local themes=()
  while IFS= read -r t; do
    themes+=("\$t")
  done < <(ls -1 "\$TURING_DIR/res/themes/" | grep -v "^--" | grep -v "\.yaml\$" | grep -v "\.md\$" | sort)

  if [ \${#themes[@]} -eq 0 ]; then
    echo "No themes found in \$TURING_DIR/res/themes/"
    return 1
  fi

  echo ""
  echo "Available themes:"
  echo ""
  local i=1
  for t in "\${themes[@]}"; do
    printf "  %3d) %s\n" "\$i" "\$t"
    i=\$((i + 1))
  done
  echo ""

  local current
  current=\$(grep "THEME:" "\$TURING_DIR/config.yaml" 2>/dev/null | sed 's/.*THEME: //' | tr -d '[:space:]')
  [ -n "\$current" ] && echo "  Current: \$current" && echo ""

  read -p "Enter number (or press Enter to cancel): " choice
  [[ -z "\$choice" ]] && echo "Cancelled." && return 0

  if ! [[ "\$choice" =~ ^[0-9]+\$ ]] || [ "\$choice" -lt 1 ] || [ "\$choice" -gt \${#themes[@]} ]; then
    echo "Invalid choice: \$choice"
    return 1
  fi

  local selected="\${themes[\$((choice - 1))]}"
  echo ""
  echo "Switching to: \$selected"
  cmd_theme "\$selected"
}

cmd_theme_current() {
  grep "THEME:" "\$TURING_DIR/config.yaml" | sed 's/.*THEME: //'
}

cmd_verified() {
  # Show verified/tested themes filtered by the user's display size
  local size="\$(grep 'DISPLAY_SIZE:' "\$TURING_DIR/config.yaml" 2>/dev/null | sed 's/.*DISPLAY_SIZE: //' | tr -d '[:space:]')"
  [ -z "\$size" ] && size="3.5inch"

  # Verified themes per display size — only themes we've tested and confirmed working
  local -a verified_35=("Cyberpunk" "3.5inchTheme2" "3.5inch-dark" "Terminal" "TerminalColored" "SimpleBlue" "SimpleGreen" "SimpleNeon" "SimpleOrange" "SimplePurple" "SimpleRed" "SimpleYellow" "SimpleFire" "SimpleMulticolor" "Gradient" "Industrial" "AMD" "bash-dark-green" "BigClock" "Blue_Technology" "Cyberdeck")
  local -a verified_5=("PiSuite5" "5inchTheme2" "TaskManager5inch" "Cyberpunk" "LandscapeEarth" "Landscape15Grid" "DigitalLandscape" "Advanced_Radials_Test")
  local -a verified_88=()
  local -a verified_21=()

  local -a list
  case "\$size" in
    3.5inch|3.5*)  list=("\${verified_35[@]}") ;;
    5inch|5*)      list=("\${verified_5[@]}") ;;
    8.8inch|8.8*)  list=("\${verified_88[@]}") ;;
    2.1inch|2.1*)  list=("\${verified_21[@]}") ;;
    *)             list=("\${verified_35[@]}") ;;
  esac

  echo ""
  echo "Verified themes for \$size display:"
  echo ""

  local current
  current=\$(grep "THEME:" "\$TURING_DIR/config.yaml" 2>/dev/null | sed 's/.*THEME: //' | tr -d '[:space:]')

  if [ \${#list[@]} -eq 0 ]; then
    echo "  No verified themes for \$size yet — use 'tslist' to see all available themes"
    return 0
  fi

  local i=1
  for t in "\${list[@]}"; do
    if [ -d "\$TURING_DIR/res/themes/\$t" ]; then
      local marker=""
      [ "\$t" = "\$current" ] && marker=" ← active"
      printf "  %3d) %s%s\n" "\$i" "\$t" "\$marker"
      i=\$((i + 1))
    fi
  done

  echo ""
  [ -n "\$current" ] && echo "  Current: \$current"
  echo ""
  echo "  Use 'tsswitch <name>' to switch, or 'tspick' for interactive picker"
}

cmd_host_open() {
  local target="\${1:-}"
  [ -n "\$target" ] || die "host-open needs a path argument"
  [[ "\$target" == /app/* ]] && target="\$TURING_DIR/\${target#/app/}"
  nohup xdg-open "\$target" >/dev/null 2>&1 &
}

launch_theme_editor_if_requested() {
  local f="\$TURING_DIR/.turing_theme_editor_requested"
  [[ -f "\$f" ]] || return 0
  local theme; theme="\$(head -n1 "\$f")"; rm -f "\$f"
  echo "[HOST] Launching theme editor for: \$theme"

  DISPLAY_FLAGS=""
  XAUTH_TMP=""
  EFFECTIVE_DISPLAY="\${DISPLAY:-}"
  [[ -z "\$EFFECTIVE_DISPLAY" ]] && [[ -n "\${WAYLAND_DISPLAY:-}" ]] && EFFECTIVE_DISPLAY=":0"

  if [[ -n "\${WAYLAND_DISPLAY:-}" ]]; then
    RUNTIME_DIR="\${XDG_RUNTIME_DIR:-/run/user/\$(id -u)}"
    DISPLAY_FLAGS="-e WAYLAND_DISPLAY=\$WAYLAND_DISPLAY -e XDG_RUNTIME_DIR=\$RUNTIME_DIR -v \$RUNTIME_DIR:\$RUNTIME_DIR:rw"
  fi
  if [[ -n "\$EFFECTIVE_DISPLAY" ]]; then
    xhost +local: >/dev/null 2>&1 || true
    DISPLAY_FLAGS="\$DISPLAY_FLAGS -e DISPLAY=\$EFFECTIVE_DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix:ro"
    XAUTH_TMP="\$(mktemp)"
    if xauth nlist "\$EFFECTIVE_DISPLAY" 2>/dev/null | grep -q .; then
      xauth nlist "\$EFFECTIVE_DISPLAY" | sed -e 's/^..../ffff/' | xauth -f "\$XAUTH_TMP" nmerge - 2>/dev/null || true
      DISPLAY_FLAGS="\$DISPLAY_FLAGS -e XAUTHORITY=/tmp/.Xauthority -v \$XAUTH_TMP:/tmp/.Xauthority:ro"
    else
      rm -f "\$XAUTH_TMP"; XAUTH_TMP=""
    fi
  fi

  podman run --rm \\
    --name "turing-theme-editor" \\
    --privileged \\
    \$DISPLAY_FLAGS \\
    -e HOME=/tmp \\
    -e XDG_STATE_HOME=/tmp/state \\
    -v "\$TURING_DIR:/app:z" \\
    --entrypoint python3 \\
    "\$TURING_IMAGE" \\
    /app/theme-editor.py "\$theme"
  [[ -n "\$XAUTH_TMP" ]] && rm -f "\$XAUTH_TMP"
}

handle_open_requested() {
  local flag="\$TURING_DIR/.turing_open_requested"
  if [[ -f "\$flag" ]]; then
    local target; target="\$(head -n1 "\$flag")"; rm -f "\$flag"
    [[ "\$target" == /app/* ]] && target="\$TURING_DIR/\${target#/app/}"
    echo "[HOST] Opening: \$target"
    nohup xdg-open "\$target" >/dev/null 2>&1 &
  fi
}

case "\${1:-}" in
  up|start|"") cmd_up ;;
  stop)         cmd_stop ;;
  restart)      cmd_restart ;;
  logs)         cmd_logs ;;
  status)       cmd_status ;;
  config)       cmd_config ;;
  theme)        shift; cmd_theme "\$@" ;;
  switch)       shift; cmd_switch "\$@" ;;
  fastswitch)   shift; cmd_fastswitch "\$@" ;;
  suite)        shift; cmd_suite "\$@" ;;
  next-theme)   cmd_next_theme ;;
  prev-theme)   cmd_prev_theme ;;
  cache-stats)  cmd_cache_stats ;;
  theme-list)   cmd_theme_list ;;
  theme-pick)   cmd_theme_pick ;;
  theme-current) cmd_theme_current ;;
  verified)     cmd_verified ;;
  host-open)    shift; cmd_host_open "\$@" ;;
  *)
    echo "Turing Smart Screen Manager"
    echo ""
    echo "Usage: \$0 {start|stop|restart|logs|status|config|theme|switch|fastswitch|suite|next-theme|prev-theme|cache-stats|theme-list|theme-current|verified|host-open}"
    echo ""
    echo "Commands:"
    echo "  start/up          - Start the display container"
    echo "  stop              - Stop the display container"
    echo "  restart           - Restart the display container"
    echo "  logs              - Show container logs (live)"
    echo "  status            - Show container status"
    echo "  config            - Run the interactive configurator (GUI)"
    echo "  theme <name>      - Switch theme (restarts container)"
    echo "  switch <name>     - Smart switch (hot reload or restart)"
    echo "  fastswitch <name> - Fast switch via pre-rendered cache"
    echo "  suite <name>      - Activate a theme suite"
    echo "  next-theme        - Next theme in active suite"
    echo "  prev-theme        - Previous theme in active suite"
    echo "  cache-stats       - Show theme cache statistics"
    echo "  theme-list        - List all available themes"
    echo "  theme-pick        - Interactive numbered theme picker"
    echo "  theme-current     - Show currently active theme"
    echo "  verified          - List verified themes for your display size"
    echo "  host-open <path>  - Open a file/folder on the host"
    exit 1
    ;;
esac
ENDSCRIPT

    chmod +x "$INSTALL_DIR/turing.sh"
    log_success "Created turing.sh management script (full feature set)"
}


setup_shell_aliases() {
    log_info "Setting up shell aliases..."

    ALIAS_BLOCK="
# Turing Smart Screen aliases
alias turing='bash $INSTALL_DIR/turing.sh'
alias ts='bash $INSTALL_DIR/turing.sh'
alias tsstart='bash $INSTALL_DIR/turing.sh start'
alias tsstop='bash $INSTALL_DIR/turing.sh stop'
alias tsrestart='bash $INSTALL_DIR/turing.sh restart'
alias tslogs='bash $INSTALL_DIR/turing.sh logs'
alias tsstatus='bash $INSTALL_DIR/turing.sh status'
alias tsconfig='bash $INSTALL_DIR/turing.sh config'
alias tstheme='bash $INSTALL_DIR/turing.sh theme-current'
alias tscurrent='bash $INSTALL_DIR/turing.sh theme-current'
alias tslist='bash $INSTALL_DIR/turing.sh theme-list'
alias tspick='bash $INSTALL_DIR/turing.sh theme-pick'
alias tsverified='bash $INSTALL_DIR/turing.sh verified'
alias tsfast='bash $INSTALL_DIR/turing.sh fastswitch'
alias tssuite='bash $INSTALL_DIR/turing.sh suite'
alias tsnext='bash $INSTALL_DIR/turing.sh next-theme'
alias tsprev='bash $INSTALL_DIR/turing.sh prev-theme'
alias tscache='bash $INSTALL_DIR/turing.sh cache-stats'
# tsswitch as a function so theme names with spaces and & work without quoting
tsswitch() { bash $INSTALL_DIR/turing.sh theme \"\$*\"; }
"

    # Bash
    if [ -f "$HOME/.bashrc" ]; then
        if ! grep -q "Turing Smart Screen aliases" "$HOME/.bashrc"; then
            echo "$ALIAS_BLOCK" >> "$HOME/.bashrc"
            log_success "Added aliases to ~/.bashrc"
        else
            log_info "Bash aliases already present"
        fi
    fi

    # Zsh
    if [ -f "$HOME/.zshrc" ]; then
        if ! grep -q "Turing Smart Screen aliases" "$HOME/.zshrc"; then
            echo "$ALIAS_BLOCK" >> "$HOME/.zshrc"
            log_success "Added aliases to ~/.zshrc"
        else
            log_info "Zsh aliases already present"
        fi
    fi

    # Fish shell
    FISH_CONF_DIR="$HOME/.config/fish/conf.d"
    if command -v fish &>/dev/null || [ -d "$HOME/.config/fish" ]; then
        mkdir -p "$FISH_CONF_DIR"
        cat > "$FISH_CONF_DIR/turing.fish" << ENDFISH
# Turing Smart Screen aliases
abbr --add turing  'bash $INSTALL_DIR/turing.sh'
abbr --add ts      'bash $INSTALL_DIR/turing.sh'
abbr --add tsstart 'bash $INSTALL_DIR/turing.sh start'
abbr --add tsstop  'bash $INSTALL_DIR/turing.sh stop'
abbr --add tsrestart 'bash $INSTALL_DIR/turing.sh restart'
abbr --add tslogs  'bash $INSTALL_DIR/turing.sh logs'
abbr --add tsstatus 'bash $INSTALL_DIR/turing.sh status'
abbr --add tsconfig 'bash $INSTALL_DIR/turing.sh config'
abbr --add tstheme 'bash $INSTALL_DIR/turing.sh theme-current'
abbr --add tscurrent 'bash $INSTALL_DIR/turing.sh theme-current'
abbr --add tslist  'bash $INSTALL_DIR/turing.sh theme-list'
abbr --add tspick  'bash $INSTALL_DIR/turing.sh theme-pick'
abbr --add tsverified 'bash $INSTALL_DIR/turing.sh verified'
abbr --add tsfast  'bash $INSTALL_DIR/turing.sh fastswitch'
abbr --add tssuite 'bash $INSTALL_DIR/turing.sh suite'
abbr --add tsnext  'bash $INSTALL_DIR/turing.sh next-theme'
abbr --add tsprev  'bash $INSTALL_DIR/turing.sh prev-theme'
abbr --add tscache 'bash $INSTALL_DIR/turing.sh cache-stats'
# tsswitch as a function so theme names with spaces and & work without quoting
function tsswitch
    bash $INSTALL_DIR/turing.sh theme \$argv
end
ENDFISH
        log_success "Added fish abbreviations to $FISH_CONF_DIR/turing.fish"
    fi

    log_success "Shell aliases configured"
}

setup_autostart() {
    log_info "Setting up autostart on login..."

    SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
    mkdir -p "$SYSTEMD_USER_DIR"

    # Find podman path (varies by distro)
    PODMAN_BIN="$(command -v podman)"

    # Detect nvidia library for service file (dynamic mount at install time)
    NVIDIA_SERVICE_FLAGS=""
    if [ -e /dev/nvidia0 ]; then
        NVIDIA_SMI_PATH="$(command -v nvidia-smi 2>/dev/null || true)"
        [ -n "$NVIDIA_SMI_PATH" ] && NVIDIA_SERVICE_FLAGS="$NVIDIA_SERVICE_FLAGS -v $NVIDIA_SMI_PATH:/usr/bin/nvidia-smi:ro"
        for lib in /usr/lib/libnvidia-ml.so.[0-9]*; do
            if [ -f "$lib" ]; then
                NVIDIA_SERVICE_FLAGS="$NVIDIA_SERVICE_FLAGS -v $lib:/usr/lib/libnvidia-ml.so.1:ro -v $lib:/usr/lib/libnvidia-ml.so:ro"
                break
            fi
        done
        log_info "NVIDIA GPU detected - adding library mounts to service"
    fi

    # --- Main display service ---
    cat > "$SYSTEMD_USER_DIR/turing-display.service" << ENDSERVICE
[Unit]
Description=Turing Smart Screen Display
After=network.target graphical-session.target
Wants=graphical-session.target
Before=sleep.target suspend.target hibernate.target hybrid-sleep.target

[Service]
Type=simple
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
# Remove any stale container before starting
ExecStartPre=-$PODMAN_BIN rm -f $CONTAINER_NAME
ExecStartPre=/bin/mkdir -p /tmp/turing
ExecStartPre=/bin/bash -c 'for i in \$(seq 1 20); do [ -e /dev/ttyACM0 ] || [ -e /dev/ttyACM1 ] || [ -e /dev/ttyUSB0 ] && exit 0; sleep 0.5; done; exit 0'
# Run container in foreground so systemd tracks it directly
ExecStart=$PODMAN_BIN run --rm \
    --name $CONTAINER_NAME \
    --network=host \
    --privileged \
    -v /dev:/dev \
    -v /sys:/sys:ro \
    -v /etc/localtime:/etc/localtime:ro \
    -v /usr/share/zoneinfo:/usr/share/zoneinfo:ro \
    -e TZ=$(readlink /etc/localtime 2>/dev/null | sed 's|.*zoneinfo/||' || echo UTC) \
    -v $INSTALL_DIR:/app:z \
    -v /tmp/turing:/tmp/turing \
    $NVIDIA_SERVICE_FLAGS \
    -e NO_TRAY=1 \
    $IMAGE_NAME
ExecStop=$PODMAN_BIN stop $CONTAINER_NAME
Restart=on-failure
RestartSec=15
TimeoutStopSec=10

[Install]
WantedBy=default.target
ENDSERVICE

    # --- Sleep/suspend hook: stop display before system sleeps ---
    # This covers: suspend, hibernate, lid close, and manual sleep
    cat > "$SYSTEMD_USER_DIR/turing-display-sleep.service" << ENDSLEEP
[Unit]
Description=Stop Turing Display on sleep/suspend
Before=sleep.target suspend.target hibernate.target hybrid-sleep.target
StopWhenUnneeded=yes

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=$PODMAN_BIN stop $CONTAINER_NAME
ExecStop=/bin/bash $INSTALL_DIR/turing.sh start

[Install]
WantedBy=sleep.target suspend.target hibernate.target hybrid-sleep.target
ENDSLEEP

    # --- Session logout hook: stop display when user logs out ---
    # Uses a systemd user target that fires on session end
    cat > "$SYSTEMD_USER_DIR/turing-display-logout.service" << ENDLOGOUT
[Unit]
Description=Stop Turing Display on logout
DefaultDependencies=no
Before=shutdown.target exit.target

[Service]
Type=oneshot
ExecStart=$PODMAN_BIN stop $CONTAINER_NAME
TimeoutStartSec=5

[Install]
WantedBy=exit.target
ENDLOGOUT

    # Enable all three services
    systemctl --user daemon-reload
    systemctl --user enable turing-display.service
    systemctl --user enable turing-display-sleep.service
    systemctl --user enable turing-display-logout.service

    # Enable linger so service starts at boot without needing a login session
    loginctl enable-linger "$USER" 2>/dev/null || \
        log_warning "Could not enable linger - autostart will work after login but not at bare boot"

    log_success "Autostart service enabled (turing-display.service)"
    log_success "Sleep/suspend shutdown hook enabled (turing-display-sleep.service)"
    log_success "Logout shutdown hook enabled (turing-display-logout.service)"
    log_info "Control with: systemctl --user {start|stop|status|restart} turing-display"
}

setup_desktop_integration() {
    log_info "Setting up KDE/desktop integration..."

    DESKTOP_DIR="$HOME/.local/share/applications"
    mkdir -p "$DESKTOP_DIR"

    # Detect best terminal emulator available
    TERMINAL=""
    for t in konsole gnome-terminal xterm kitty alacritty; do
        if command -v "$t" &>/dev/null; then
            TERMINAL="$t"
            break
        fi
    done

    # Build terminal exec string for logs (needs to stay open)
    if [ "$TERMINAL" = "konsole" ]; then
        LOGS_EXEC="konsole -e bash -c 'bash $INSTALL_DIR/turing.sh logs; read -p \"Press Enter to close...\"'"
    elif [ "$TERMINAL" = "gnome-terminal" ]; then
        LOGS_EXEC="gnome-terminal -- bash -c 'bash $INSTALL_DIR/turing.sh logs; read -p \"Press Enter to close...\"'"
    elif [ -n "$TERMINAL" ]; then
        LOGS_EXEC="$TERMINAL -e bash -c 'bash $INSTALL_DIR/turing.sh logs; read -p \"Press Enter to close...\"'"
    else
        LOGS_EXEC="bash -c 'bash $INSTALL_DIR/turing.sh logs; read -p \"Press Enter to close...\"'"
    fi

    # Start
    cat > "$DESKTOP_DIR/turing-display.desktop" << ENDDESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=Turing Display
Comment=Start Turing Smart Screen display
Exec=bash $INSTALL_DIR/turing.sh start
Icon=video-display
Terminal=false
Categories=System;Monitor;
Keywords=turing;display;screen;monitor;
ENDDESKTOP

    # Stop
    cat > "$DESKTOP_DIR/turing-display-stop.desktop" << ENDDESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=Turing Display - Stop
Comment=Stop Turing Smart Screen display
Exec=bash $INSTALL_DIR/turing.sh stop
Icon=process-stop
Terminal=false
Categories=System;Monitor;
Keywords=turing;display;stop;
ENDDESKTOP

    # Logs (needs terminal)
    cat > "$DESKTOP_DIR/turing-display-logs.desktop" << ENDDESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=Turing Display - Logs
Comment=View Turing Smart Screen live logs
Exec=$LOGS_EXEC
Icon=utilities-terminal
Terminal=false
Categories=System;Monitor;
Keywords=turing;display;logs;
ENDDESKTOP

    # Config/GUI
    cat > "$DESKTOP_DIR/turing-display-config.desktop" << ENDDESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=Turing Display - Configure
Comment=Open Turing Smart Screen configurator GUI
Exec=bash $INSTALL_DIR/turing.sh config
Icon=preferences-system
Terminal=false
Categories=System;Monitor;Settings;
Keywords=turing;display;config;theme;
ENDDESKTOP

    # Restart
    cat > "$DESKTOP_DIR/turing-display-restart.desktop" << ENDDESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=Turing Display - Restart
Comment=Restart Turing Smart Screen display
Exec=bash $INSTALL_DIR/turing.sh restart
Icon=view-refresh
Terminal=false
Categories=System;Monitor;
Keywords=turing;display;restart;
ENDDESKTOP

    # Update desktop database
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true

    log_success "Desktop entries created in $DESKTOP_DIR"
    [ -n "$TERMINAL" ] && log_info "Terminal for logs: $TERMINAL" || \
        log_warning "No terminal emulator found - logs entry may not open a window"
    log_info "Search 'Turing Display' in your app launcher (KDE/GNOME)"
}

configure_yaml() {
    log_info "Configuring config.yaml..."
    cd "$INSTALL_DIR"

    # Detect USB device
    USB_DEVICE=""
    for dev in /dev/ttyACM0 /dev/ttyACM1 /dev/ttyUSB0; do
        [ -e "$dev" ] && USB_DEVICE="$dev" && break
    done

    if [ -n "$USB_DEVICE" ]; then
        log_success "Turing device detected at $USB_DEVICE"
    else
        log_warning "Turing device not detected - connect it before running './turing.sh config'"
        USB_DEVICE="/dev/ttyACM0"  # default fallback
    fi

    # Detect ETH and WLO interfaces separately
    # config.yaml uses ETH= for wired and WLO= for wireless - both needed
    ETH_IFACE=""
    WLO_IFACE=""

    # Ethernet: first UP en*/eth* interface (including DOWN ones as fallback - may come up later)
    ETH_IFACE=$(ip -br link show | awk '$1 ~ /^(en|eth)/ && $2 == "UP" {print $1; exit}')
    if [ -z "$ETH_IFACE" ]; then
        # Even if DOWN, record it so config is ready when cable is plugged in
        ETH_IFACE=$(ip -br link show | awk '$1 ~ /^(en|eth)/ {print $1; exit}')
    fi

    # WiFi: first UP wl* interface
    WLO_IFACE=$(ip -br link show | awk '$1 ~ /^wl/ && $2 == "UP" {print $1; exit}')
    if [ -z "$WLO_IFACE" ]; then
        WLO_IFACE=$(ip -br link show | awk '$1 ~ /^wl/ {print $1; exit}')
    fi

    [ -n "$ETH_IFACE" ] && log_success "Ethernet interface: $ETH_IFACE" || log_warning "No ethernet interface found"
    [ -n "$WLO_IFACE" ] && log_success "WiFi interface: $WLO_IFACE" || log_warning "No WiFi interface found"

    # Determine the PRIMARY active interface (the one with actual traffic)
    # This is what ETH key should be set to when only one interface is active
    PRIMARY_IFACE=""
    if [ -n "$ETH_IFACE" ] && [ -n "$WLO_IFACE" ]; then
        # Both exist - pick the one with more bytes received (actually in use)
        ETH_BYTES=$(cat /sys/class/net/${ETH_IFACE}/statistics/rx_bytes 2>/dev/null || echo 0)
        WLO_BYTES=$(cat /sys/class/net/${WLO_IFACE}/statistics/rx_bytes 2>/dev/null || echo 0)
        if [ "$WLO_BYTES" -gt "$ETH_BYTES" ]; then
            PRIMARY_IFACE="$WLO_IFACE"
            log_info "Primary interface (most traffic): $WLO_IFACE (wifi)"
        else
            PRIMARY_IFACE="$ETH_IFACE"
            log_info "Primary interface (most traffic): $ETH_IFACE (ethernet)"
        fi
    elif [ -n "$ETH_IFACE" ]; then
        PRIMARY_IFACE="$ETH_IFACE"
    elif [ -n "$WLO_IFACE" ]; then
        PRIMARY_IFACE="$WLO_IFACE"
    fi

    if [ -f "config.yaml" ]; then
        # Force PYTHON sensors (required on Linux - LHM is Windows-only)
        sed -i 's/HW_SENSORS:.*/HW_SENSORS: PYTHON/' config.yaml
        log_success "Set HW_SENSORS: PYTHON"

        # Set COM port if present in config - always use full /dev/ path
        if grep -q "COM_PORT:" config.yaml; then
            sed -i "s|COM_PORT:.*|COM_PORT: $USB_DEVICE|" config.yaml
            log_success "Set COM_PORT: $USB_DEVICE"
        fi

        # Detect hardware revision from USB product ID and set REVISION + DISPLAY_SIZE
        USB_PRODUCT=""
        if [ -n "$USB_DEVICE" ] && [ -e "$USB_DEVICE" ]; then
            USB_PRODUCT=$(udevadm info "$USB_DEVICE" 2>/dev/null | awk -F= '/ID_MODEL_ID/{print $2}')
        fi
        HW_REVISION=$(product_to_revision "${USB_PRODUCT:-5722}")
        HW_SIZE=$(product_to_size "${USB_PRODUCT:-5722}")

        # Rev C: can't auto-detect size — ask user
        if [ "$HW_REVISION" = "C" ] && [ -z "$HW_SIZE" ]; then
            ask_rev_c_size "$USB_DEVICE"
            HW_SIZE="$REV_C_DISPLAY_SIZE"
        fi
        [ -z "$HW_SIZE" ] && HW_SIZE="3.5inch"

        if grep -q "REVISION:" config.yaml; then
            sed -i "s|REVISION:.*|REVISION: $HW_REVISION|" config.yaml
            log_success "Set REVISION: $HW_REVISION"
        fi

        if grep -q "DISPLAY_SIZE:" config.yaml; then
            sed -i "s|DISPLAY_SIZE:.*|DISPLAY_SIZE: $HW_SIZE|" config.yaml
            log_success "Set DISPLAY_SIZE: $HW_SIZE"
        fi

        # Set ETH and WLO interface keys - these are what stats.py reads for network metrics
        # ETH is set to the PRIMARY active interface (may be wifi on laptops with no cable)
        # WLO is set to the wifi interface name (empty string if none)
        ETH_VALUE="${PRIMARY_IFACE:-${ETH_IFACE:-}}"
        WLO_VALUE="${WLO_IFACE:-}"

        if grep -qE "^  ETH:" config.yaml; then
            [ -n "$ETH_VALUE" ] && sed -i "s|^  ETH:.*|  ETH: $ETH_VALUE|" config.yaml && log_success "Set ETH: $ETH_VALUE"
        elif [ -n "$ETH_VALUE" ]; then
            sed -i "/^  HW_SENSORS:/a\\  ETH: $ETH_VALUE" config.yaml && log_success "Added ETH: $ETH_VALUE"
        fi

        if grep -qE "^  WLO:" config.yaml; then
            sed -i "s|^  WLO:.*|  WLO: '$WLO_VALUE'|" config.yaml && log_success "Set WLO: $WLO_VALUE"
        else
            sed -i "/^  ETH:/a\\  WLO: '$WLO_VALUE'" config.yaml && log_success "Added WLO: $WLO_VALUE"
        fi

        # Set default theme based on display size (only on fresh install, don't override existing choice)
        CURRENT_THEME=$(grep "THEME:" config.yaml 2>/dev/null | sed 's/.*THEME: //' | tr -d '[:space:]')
        # Only set default if current theme is an upstream default or empty
        case "$CURRENT_THEME" in
            ""|"3.5inchTheme2"|"Cyberpunk"|"Terminal"|"LandscapeEarth")
                case "$HW_SIZE" in
                    "5inch")
                        if [ -d "$INSTALL_DIR/res/themes/PiSuite5" ]; then
                            sed -i "s|^  THEME:.*|  THEME: PiSuite5|" config.yaml
                            log_success "Set default theme for 5\" display: PiSuite5 (Vortex Seed of Life)"
                        fi
                        ;;
                    "8.8inch")
                        # Future: set 8.8" default theme here
                        log_info "No custom 8.8\" theme yet — using upstream default"
                        ;;
                esac
                ;;
            *)
                log_info "Keeping existing theme: $CURRENT_THEME"
                ;;
        esac
    else
        log_warning "config.yaml not found yet - it will be created when you run './turing.sh config'"
    fi

    log_info "Run './turing.sh config' to open the GUI configurator and save your settings"
}

verify_installation() {
    log_info "Running post-install verification..."
    echo ""

    ISSUES=0
    WARNINGS=0

    # Determine serial group (needed for group check)
    SERIAL_GROUP="dialout"
    case "$OS_ID" in
        "cachyos"|"arch"|"manjaro") SERIAL_GROUP="uucp" ;;
    esac

    # 1. podman
    if command -v podman &>/dev/null; then
        log_success "podman: OK ($(podman --version))"
    else
        log_error "podman: NOT FOUND"
        ISSUES=$((ISSUES + 1))
    fi

    # 2. Container image
    if podman image exists "$IMAGE_NAME" 2>/dev/null; then
        log_success "Container image $IMAGE_NAME: OK"
    else
        log_error "Container image $IMAGE_NAME: NOT FOUND"
        ISSUES=$((ISSUES + 1))
    fi

    # 3. turing.sh
    if [ -x "$INSTALL_DIR/turing.sh" ]; then
        log_success "turing.sh: OK"
    else
        log_error "turing.sh: missing or not executable"
        ISSUES=$((ISSUES + 1))
    fi

    # 4. udev rule
    if [ -f /etc/udev/rules.d/99-turing.rules ]; then
        log_success "udev rule: OK"
    else
        log_error "udev rule: NOT FOUND"
        ISSUES=$((ISSUES + 1))
    fi

    # 5. Group membership
    if groups "$USER" | grep -q "$SERIAL_GROUP"; then
        log_success "User in $SERIAL_GROUP group: OK"
    else
        log_warning "User not yet in $SERIAL_GROUP group - log out and back in"
        WARNINGS=$((WARNINGS + 1))
    fi

    # 6. USB device
    USB_DEVICE=""
    for dev in /dev/ttyACM0 /dev/ttyACM1 /dev/ttyUSB0; do
        [ -e "$dev" ] && USB_DEVICE="$dev" && break
    done
    if [ -n "$USB_DEVICE" ]; then
        PERMS=$(stat -c "%a" "$USB_DEVICE")
        log_success "Turing device: $USB_DEVICE (permissions: $PERMS)"
        if [ "$PERMS" != "666" ]; then
            log_warning "Permissions are $PERMS, expected 666 - unplug and replug USB"
            WARNINGS=$((WARNINGS + 1))
        fi
    else
        log_warning "Turing device not detected - connect via USB"
        WARNINGS=$((WARNINGS + 1))
    fi

    # 7. GPU
    if [ -d /dev/dri ]; then
        log_success "GPU (DRI): found at /dev/dri"
    else
        log_warning "GPU (DRI): /dev/dri not found - GPU stats may not work"
        WARNINGS=$((WARNINGS + 1))
    fi

    # 8. config.yaml
    if [ -f "$INSTALL_DIR/config.yaml" ]; then
        if grep -q "HW_SENSORS: PYTHON" "$INSTALL_DIR/config.yaml"; then
            log_success "config.yaml HW_SENSORS: PYTHON - OK"
        else
            log_warning "config.yaml HW_SENSORS not set to PYTHON"
            WARNINGS=$((WARNINGS + 1))
        fi
    else
        log_warning "config.yaml not found - run './turing.sh config' to create it"
        WARNINGS=$((WARNINGS + 1))
    fi

    # 9. Systemd autostart service
    if systemctl --user is-enabled turing-display.service &>/dev/null; then
        log_success "Autostart service: enabled"
    else
        log_warning "Autostart service not enabled - run: systemctl --user enable turing-display"
        WARNINGS=$((WARNINGS + 1))
    fi
    if systemctl --user is-enabled turing-display-sleep.service &>/dev/null; then
        log_success "Sleep/suspend shutdown hook: enabled"
    else
        log_warning "Sleep hook not enabled - display won't stop on suspend"
        WARNINGS=$((WARNINGS + 1))
    fi
    if systemctl --user is-enabled turing-display-logout.service &>/dev/null; then
        log_success "Logout shutdown hook: enabled"
    else
        log_warning "Logout hook not enabled - display won't stop on logout"
        WARNINGS=$((WARNINGS + 1))
    fi

    # 10. Shell aliases
    ALIAS_OK=false
    [ -f "$HOME/.bashrc" ] && grep -q "Turing Smart Screen aliases" "$HOME/.bashrc" && ALIAS_OK=true
    [ -f "$HOME/.zshrc" ] && grep -q "Turing Smart Screen aliases" "$HOME/.zshrc" && ALIAS_OK=true
    [ -f "$HOME/.config/fish/conf.d/turing.fish" ] && ALIAS_OK=true
    if $ALIAS_OK; then
        log_success "Shell aliases: configured"
    else
        log_warning "Shell aliases not found - source your shell config or re-run installer"
        WARNINGS=$((WARNINGS + 1))
    fi

    echo ""
    echo "========================================="
    if [ "$ISSUES" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
        log_success "All checks passed - ready to go!"
    elif [ "$ISSUES" -eq 0 ]; then
        log_warning "Installation OK with $WARNINGS warning(s) - see above"
    else
        log_error "Installation has $ISSUES error(s) and $WARNINGS warning(s)"
        echo ""
        log_info "Report issues at: https://github.com/mathoudebine/turing-smart-screen-python/issues"
        log_info "Include this system info:"
        echo "  OS: $OS_NAME ($OS_ID $OS_VERSION)"
        echo "  Kernel: $(uname -r)"
        echo "  Podman: $(podman --version 2>/dev/null || echo 'not found')"
        echo "  Groups: $(groups $USER)"
        echo "  USB: $(lsusb 2>/dev/null | grep -i '1a86' || echo 'none matching 1a86')"
    fi
    echo "========================================="
}

# ── Multi-screen support ──────────────────────────────────────────────────────

detect_screens() {
    # Returns list of "PORT:SERIAL:PRODUCT_ID" for each connected Turing screen
    # Covers Rev A/B (1a86:5722), Rev C sleeping (1a86:ca21), Rev C awake (0525:a4a7, 1d6b:0121/0106), Rev D (454d:4e41)
    SCREEN_LIST=()
    for dev in /dev/ttyACM* /dev/ttyUSB*; do
        [ -e "$dev" ] || continue
        VENDOR=$(udevadm info "$dev" 2>/dev/null | awk -F= '/ID_VENDOR_ID/{print $2}')
        PRODUCT=$(udevadm info "$dev" 2>/dev/null | awk -F= '/ID_MODEL_ID/{print $2}')
        SERIAL=$(udevadm info "$dev" 2>/dev/null | awk -F= '/ID_SERIAL_SHORT/{print $2}')
        # Match all known Turing USB IDs across all revisions
        case "$VENDOR:$PRODUCT" in
            "1a86:5722"|"1a86:7523"|"1a86:ca21"|\
            "0525:a4a7"|"1d6b:0121"|"1d6b:0106"|\
            "454d:4e41")
                SCREEN_LIST+=("$dev:$SERIAL:$PRODUCT")
                ;;
        esac
    done
}

# Map product ID to HW revision letter for config.yaml REVISION key
product_to_revision() {
    case "$1" in
        "5722"|"7523") echo "A" ;;
        # Rev C: ca21 = sleeping PID; a4a7/0121/0106 = awake PIDs after USB re-enumeration
        "ca21"|"a4a7"|"0121"|"0106") echo "C" ;;
        "4e41") echo "D" ;;
        *) echo "A" ;;
    esac
}

# Map product ID to display size string
# Rev C returns "" because size can't be determined from USB ID alone — caller must ask user
product_to_size() {
    case "$1" in
        "5722"|"7523") echo "3.5inch" ;;
        "4e41")        echo "3.5inch" ;;
        # Rev C: 2.1" (480x480), 5" (800x480), 8.8" (1920x480) — need user input
        "ca21"|"a4a7"|"0121"|"0106") echo "" ;;
        *) echo "3.5inch" ;;
    esac
}

# Ask user which Rev C screen size they have; sets REV_C_DISPLAY_SIZE global
ask_rev_c_size() {
    local dev="$1"
    echo ""
    log_info "Rev C screen detected at $dev (Turing 2.1\" / 5\" / 8.8\")"
    log_info "The USB ID cannot distinguish between these models — please identify yours:"
    echo ""
    echo "  1) 2.1\" round  (480x480)"
    echo "  2) 5\"          (800x480)"
    echo "  3) 8.8\" strip  (1920x480)"
    echo ""
    echo "  Note: the 8.0\" screen (1280x800) is a DIFFERENT product and is NOT supported."
    echo ""
    read -p "Which screen is this? [1/2/3, default=2]: " -n 1 -r; echo
    case "$REPLY" in
        1) REV_C_DISPLAY_SIZE="2.1inch" ;;
        3) REV_C_DISPLAY_SIZE="8.8inch" ;;
        *) REV_C_DISPLAY_SIZE="5inch"   ;;
    esac
    log_success "Rev C display size set to: $REV_C_DISPLAY_SIZE"
}

# Returns true (0) if the product ID is supported by upstream OSS driver
product_is_supported() {
    case "$1" in
        "5722"|"7523") return 0 ;;
        "ca21"|"a4a7"|"0121"|"0106") return 0 ;;  # Rev C — upstream driver exists
        "4e41") return 0 ;;                         # Rev D — Kipye Qiye
        *) return 0 ;;
    esac
}

setup_additional_screen() {
    local INDEX="$1"      # 2, 3, etc.
    local DEV="$2"        # /dev/ttyACM1
    local SERIAL="$3"     # USB7INCH
    local PRODUCT_ID="$4" # ca21

    if ! product_is_supported "$PRODUCT_ID"; then
        log_warning "Screen $INDEX ($DEV, product=$PRODUCT_ID): not recognised — skipping"
        return 0
    fi

    local REVISION
    REVISION=$(product_to_revision "$PRODUCT_ID")
    local SIZE
    SIZE=$(product_to_size "$PRODUCT_ID")

    # Rev C: size can't be auto-detected — ask user
    if [ "$REVISION" = "C" ] && [ -z "$SIZE" ]; then
        ask_rev_c_size "$DEV"
        SIZE="$REV_C_DISPLAY_SIZE"
    fi

    local SCREEN_DIR="$HOME/Prejemi/turing-screen-${INDEX}"
    local CONTAINER="turing-display-${INDEX}"
    local TZ_VAL
    TZ_VAL=$(readlink /etc/localtime 2>/dev/null | sed 's|.*zoneinfo/||' || echo UTC)
    local PODMAN_BIN
    PODMAN_BIN="$(command -v podman)"
    local SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

    log_info "Setting up screen $INDEX: $DEV (serial=$SERIAL, rev=$REVISION, size=$SIZE)"

    # Create per-screen config directory with symlinks to shared repo
    mkdir -p "$SCREEN_DIR"

    # Symlink everything from the main install dir except config.yaml and turing.sh
    # (turing.sh gets its own wrapper below — must not symlink or the write would
    #  clobber the real management script in INSTALL_DIR)
    for item in "$INSTALL_DIR"/*; do
        local base
        base=$(basename "$item")
        [ "$base" = "config.yaml" ] && continue
        [ "$base" = "turing.sh"   ] && continue
        [ -e "$SCREEN_DIR/$base" ] || ln -sf "$item" "$SCREEN_DIR/$base"
    done

    # Write this screen's own config.yaml
    if [ ! -f "$SCREEN_DIR/config.yaml" ] || ! grep -q "$DEV\|AUTO" "$SCREEN_DIR/config.yaml" 2>/dev/null; then
        cp "$INSTALL_DIR/config.yaml" "$SCREEN_DIR/config.yaml"
        # Rev C uses AUTO — the sleeping port disappears after wake, so a fixed port breaks startup
        local COM_PORT_VAL="$DEV"
        [ "$REVISION" = "C" ] && COM_PORT_VAL="AUTO"
        sed -i "s|COM_PORT:.*|COM_PORT: $COM_PORT_VAL|" "$SCREEN_DIR/config.yaml"
        # DISPLAY_SIZE: update if present, add if missing
        if grep -q "DISPLAY_SIZE:" "$SCREEN_DIR/config.yaml"; then
            sed -i "s|DISPLAY_SIZE:.*|DISPLAY_SIZE: $SIZE|" "$SCREEN_DIR/config.yaml"
        else
            sed -i "/^  HW_SENSORS:/a\\  DISPLAY_SIZE: $SIZE" "$SCREEN_DIR/config.yaml"
        fi
        # REVISION: update if present, add if missing
        if grep -q "REVISION:" "$SCREEN_DIR/config.yaml"; then
            sed -i "s|REVISION:.*|REVISION: $REVISION|" "$SCREEN_DIR/config.yaml"
        else
            sed -i "/^  HW_SENSORS:/a\\  REVISION: $REVISION" "$SCREEN_DIR/config.yaml"
        fi
        log_success "Screen $INDEX config: $SCREEN_DIR/config.yaml (port=$COM_PORT_VAL, rev=$REVISION, size=$SIZE)"
    else
        log_info "Screen $INDEX config already exists"
    fi

    # Create turing.sh for this screen (wrapper pointing at screen dir)
    # Rev C: do NOT set TURING_DEV — the sleeping port disappears after wake,
    # and ensure_dev() would block forever. Rev C uses COM_PORT: AUTO instead.
    # TURING_DIR points to the main codebase (real files, not symlinks).
    # TURING_CONFIG_DIR points to this screen's dir for its own config.yaml.
    if [ "$REVISION" = "C" ]; then
        cat > "$SCREEN_DIR/turing.sh" << ENDSCRIPT2
#!/usr/bin/env bash
# Screen $INDEX management script (Rev C — no fixed TURING_DEV)
TURING_DIR="$INSTALL_DIR" \
TURING_CONFIG_DIR="$SCREEN_DIR" \
TURING_IMAGE="$IMAGE_NAME" \
TURING_CONTAINER="$CONTAINER" \
exec "$INSTALL_DIR/turing.sh" "\$@"
ENDSCRIPT2
    else
        cat > "$SCREEN_DIR/turing.sh" << ENDSCRIPT2
#!/usr/bin/env bash
# Screen $INDEX management script
TURING_DIR="$INSTALL_DIR" \
TURING_CONFIG_DIR="$SCREEN_DIR" \
TURING_IMAGE="$IMAGE_NAME" \
TURING_DEV="$DEV" \
TURING_CONTAINER="$CONTAINER" \
exec "$INSTALL_DIR/turing.sh" "\$@"
ENDSCRIPT2
    fi
    chmod +x "$SCREEN_DIR/turing.sh"

    # Systemd service for this screen
    mkdir -p "$SYSTEMD_USER_DIR"
    cat > "$SYSTEMD_USER_DIR/turing-display-${INDEX}.service" << ENDSVC
[Unit]
Description=Turing Smart Screen Display $INDEX ($SERIAL)
After=network.target graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStartPre=-$PODMAN_BIN rm -f $CONTAINER
ExecStartPre=/bin/mkdir -p /tmp/turing
ExecStartPre=/bin/sleep 6
ExecStart=$PODMAN_BIN run --rm --name $CONTAINER --network=host --privileged -v /dev:/dev -v /sys:/sys:ro -v /etc/localtime:/etc/localtime:ro -v /usr/share/zoneinfo:/usr/share/zoneinfo:ro -e TZ=$TZ_VAL -v $INSTALL_DIR:/app:z -v $SCREEN_DIR/config.yaml:/app/config.yaml:z -v /tmp/turing:/tmp/turing -e NO_TRAY=1 $IMAGE_NAME
ExecStop=$PODMAN_BIN stop $CONTAINER
Restart=on-failure
RestartSec=15
TimeoutStopSec=10

[Install]
WantedBy=default.target
ENDSVC

    systemctl --user daemon-reload
    systemctl --user enable "turing-display-${INDEX}.service"
    log_success "Screen $INDEX service enabled: turing-display-${INDEX}.service"

    # Fish aliases for this screen
    local FISH_CONF_DIR="$HOME/.config/fish/conf.d"
    if command -v fish &>/dev/null || [ -d "$HOME/.config/fish" ]; then
        mkdir -p "$FISH_CONF_DIR"
        cat >> "$FISH_CONF_DIR/turing.fish" << ENDFISH2

# Turing Screen $INDEX aliases ($SERIAL - $SIZE on $DEV)
abbr --add ts${INDEX}      'bash $SCREEN_DIR/turing.sh'
abbr --add ts${INDEX}start 'bash $SCREEN_DIR/turing.sh start'
abbr --add ts${INDEX}stop  'bash $SCREEN_DIR/turing.sh stop'
abbr --add ts${INDEX}logs  'bash $SCREEN_DIR/turing.sh logs'
abbr --add ts${INDEX}config 'bash $SCREEN_DIR/turing.sh config'
abbr --add ts${INDEX}theme 'bash $SCREEN_DIR/turing.sh theme-current'
abbr --add ts${INDEX}list  'bash $SCREEN_DIR/turing.sh theme-pick'
ENDFISH2
        log_success "Screen $INDEX fish aliases added (ts${INDEX}, ts${INDEX}config, ts${INDEX}list...)"
    fi

    # Bash/zsh aliases
    local ALIAS_BLOCK2="
# Turing Screen $INDEX aliases ($SERIAL)
alias ts${INDEX}='bash $SCREEN_DIR/turing.sh'
alias ts${INDEX}start='bash $SCREEN_DIR/turing.sh start'
alias ts${INDEX}stop='bash $SCREEN_DIR/turing.sh stop'
alias ts${INDEX}logs='bash $SCREEN_DIR/turing.sh logs'
alias ts${INDEX}config='bash $SCREEN_DIR/turing.sh config'
alias ts${INDEX}theme='bash $SCREEN_DIR/turing.sh theme-current'
alias ts${INDEX}list='bash $SCREEN_DIR/turing.sh theme-pick'
"
    [ -f "$HOME/.bashrc" ] && echo "$ALIAS_BLOCK2" >> "$HOME/.bashrc"
    [ -f "$HOME/.zshrc" ]  && echo "$ALIAS_BLOCK2" >> "$HOME/.zshrc"

    # Desktop entry
    local DESKTOP_DIR="$HOME/.local/share/applications"
    mkdir -p "$DESKTOP_DIR"
    cat > "$DESKTOP_DIR/turing-display-${INDEX}.desktop" << ENDDESKTOP2
[Desktop Entry]
Version=1.0
Type=Application
Name=Turing Display $INDEX ($SERIAL)
Comment=Start Turing Smart Screen $INDEX ($SIZE on $DEV)
Exec=bash $SCREEN_DIR/turing.sh start
Icon=video-display
Terminal=false
Categories=System;Monitor;
Keywords=turing;display;screen;monitor;
ENDDESKTOP2
    cat > "$DESKTOP_DIR/turing-display-${INDEX}-config.desktop" << ENDDESKTOP2
[Desktop Entry]
Version=1.0
Type=Application
Name=Turing Display $INDEX - Configure
Comment=Configure Turing Smart Screen $INDEX
Exec=bash $SCREEN_DIR/turing.sh config
Icon=preferences-system
Terminal=false
Categories=System;Monitor;Settings;
Keywords=turing;display;config;
ENDDESKTOP2

    log_success "Screen $INDEX setup complete: $SCREEN_DIR"
    log_info "  Start:    bash $SCREEN_DIR/turing.sh start  (or: ts${INDEX})"
    log_info "  Config:   bash $SCREEN_DIR/turing.sh config (or: ts${INDEX}config)"
    log_info "  Logs:     bash $SCREEN_DIR/turing.sh logs   (or: ts${INDEX}logs)"
}

setup_additional_screens() {
    detect_screens

    if [ ${#SCREEN_LIST[@]} -eq 0 ]; then
        log_warning "No Turing screens detected via udev - skipping multi-screen setup"
        log_info "Plug in additional screens and re-run installer to add them"
        return 0
    fi

    log_info "Detected ${#SCREEN_LIST[@]} Turing screen(s):"
    local IDX=0
    for entry in "${SCREEN_LIST[@]}"; do
        local DEV="${entry%%:*}"
        local REST="${entry#*:}"
        local SERIAL="${REST%%:*}"
        local PRODUCT="${REST##*:}"
        local REV SIZE
        REV=$(product_to_revision "$PRODUCT")
        SIZE=$(product_to_size "$PRODUCT")
        IDX=$((IDX + 1))
        if [ "$REV" = "C" ]; then
            echo "  Screen $IDX: $DEV (serial=$SERIAL, Rev C — size TBD)"
        else
            echo "  Screen $IDX: $DEV (serial=$SERIAL, Rev $REV, ${SIZE:-unknown})"
        fi
    done
    echo ""

    # Screen 1 is handled by the main install flow (INSTALL_DIR, turing-display)
    # Additional screens get their own setup
    if [ ${#SCREEN_LIST[@]} -le 1 ]; then
        log_info "Single screen detected - no additional screen setup needed"
        return 0
    fi

    log_info "Setting up ${#SCREEN_LIST[@]} screens..."
    IDX=0
    for entry in "${SCREEN_LIST[@]}"; do
        local DEV="${entry%%:*}"
        local REST="${entry#*:}"
        local SERIAL="${REST%%:*}"
        local PRODUCT="${REST##*:}"
        IDX=$((IDX + 1))

        if [ "$IDX" -eq 1 ]; then
            # Screen 1: update primary config with correct port/revision/size
            if product_is_supported "$PRODUCT"; then
                local REV1 SIZE1
                REV1=$(product_to_revision "$PRODUCT")
                SIZE1=$(product_to_size "$PRODUCT")
                if [ "$REV1" = "C" ] && [ -z "$SIZE1" ]; then
                    ask_rev_c_size "$DEV"
                    SIZE1="$REV_C_DISPLAY_SIZE"
                fi
                log_info "Screen 1 (primary): $DEV (Rev $REV1, ${SIZE1:-?}) → $INSTALL_DIR"
                sed -i "s|COM_PORT:.*|COM_PORT: $DEV|" "$INSTALL_DIR/config.yaml" 2>/dev/null || true
                sed -i "s|REVISION:.*|REVISION: $REV1|" "$INSTALL_DIR/config.yaml" 2>/dev/null || true
                [ -n "$SIZE1" ] && sed -i "s|DISPLAY_SIZE:.*|DISPLAY_SIZE: $SIZE1|" "$INSTALL_DIR/config.yaml" 2>/dev/null || true
            else
                log_warning "Screen 1 ($DEV) is unrecognised hardware — primary display may not work"
            fi
            continue
        fi

        setup_additional_screen "$IDX" "$DEV" "$SERIAL" "$PRODUCT"
    done
}

do_wipe() {
    log_info "--- Stopping and removing containers ---"
    for container in $(podman ps -a --format "{{.Names}}" 2>/dev/null | grep "^turing-display"); do
        podman stop "$container" 2>/dev/null || true
        podman rm -f "$container" 2>/dev/null || true
        log_success "Removed container: $container"
    done

    log_info "Removing container image: $IMAGE_NAME"
    podman rmi "$IMAGE_NAME" 2>/dev/null && log_success "Image removed" || log_info "Image already gone"

    log_info "--- Removing systemd services ---"
    for svc in $(systemctl --user list-unit-files 2>/dev/null | awk '/turing-display/{print $1}'); do
        systemctl --user disable "$svc" 2>/dev/null || true
        rm -f "$HOME/.config/systemd/user/$svc"
        log_success "Removed service: $svc"
    done
    systemctl --user daemon-reload 2>/dev/null || true

    log_info "--- Removing desktop entries ---"
    for f in "$HOME/.local/share/applications"/turing-display*.desktop; do
        [ -f "$f" ] || continue
        rm -f "$f"
        log_success "Removed: $(basename "$f")"
    done
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

    log_info "--- Removing shell aliases ---"
    for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
        [ -f "$rc" ] && grep -q "Turing" "$rc" || continue
        python3 - "$rc" << 'ENDPY'
import sys, re
path = sys.argv[1]
with open(path) as f: content = f.read()
content = re.sub(r'\n# Turing (Smart Screen|Screen \d+) aliases.*?(?=\n#|\Z)', '', content, flags=re.DOTALL)
with open(path, 'w') as f: f.write(content)
print(f"Cleaned {path}")
ENDPY
    done
    rm -f "$HOME/.config/fish/conf.d/turing.fish" 2>/dev/null && log_success "Removed turing.fish" || true

    log_info "--- Removing install directory ---"
    if [ -d "$INSTALL_DIR" ]; then
        rm -rf "$INSTALL_DIR"
        log_success "Removed $INSTALL_DIR"
    fi
    for d in "$HOME/Prejemi/turing-screen-"*; do
        [ -d "$d" ] || continue; rm -rf "$d"; log_success "Removed $d"
    done
    rm -rf /tmp/turing 2>/dev/null || true
    log_success "=== Wipe complete ==="
}

backup_custom_themes() {
    local THEMES_DIR="$INSTALL_DIR/res/themes"
    [ -d "$THEMES_DIR" ] || return 0

    # Use Python to handle theme names with spaces, &, and other special chars
    local RESULT
    RESULT=$(python3 - "$THEMES_DIR" << 'ENDPY'
import sys, os, tarfile, json

themes_dir = sys.argv[1]
upstream = {
    "26","30","3.5inch-dark","3.5inchTheme2","43","44","45","5inchTheme2",
    "Advanced_Radials_Test","AMD","bash-dark-green","BigClock","Blue_Technology",
    "Cyberdeck","Cyberpunk","CustomDataExample","Digital_CPU_0.96Inch",
    "DigitalLandscape","Example_0.96Inch_1","Example_0.96Inch_2",
    "Example_0.96Inch_Clock","Gradient","Industrial","SimpleBlue","SimpleFire",
    "SimpleGreen","SimpleMulticolor","SimpleNeon","SimpleOrange","SimplePurple",
    "SimpleRed","SimpleYellow","TaskManager5inch","TerminalColored"
}

try:
    entries = [e for e in os.listdir(themes_dir)
               if os.path.isdir(os.path.join(themes_dir, e))]
except Exception as e:
    print(f"ERROR:Cannot list themes dir: {e}")
    sys.exit(1)

custom = [t for t in entries if t not in upstream]
if not custom:
    print("NONE:")
    sys.exit(0)

print(f"FOUND:{len(custom)}")
for t in sorted(custom):
    print(f"THEME:{t}")
ENDPY
)

    if echo "$RESULT" | grep -q "^NONE:"; then
        return 0
    fi
    if echo "$RESULT" | grep -q "^ERROR:"; then
        log_warning "Could not scan themes: $(echo "$RESULT" | grep "^ERROR:" | cut -d: -f2-)"
        return 0
    fi

    local COUNT
    COUNT=$(echo "$RESULT" | grep "^FOUND:" | cut -d: -f2)
    echo ""
    log_warning "Found $COUNT custom theme(s):"
    echo "$RESULT" | grep "^THEME:" | cut -d: -f2- | while IFS= read -r t; do
        echo "    $t"
    done
    echo ""
    read -p "Back up custom themes to /tmp/turing_themes_backup.tar.gz? (Y/n): " -n 1 -r; echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        python3 - "$THEMES_DIR" << 'ENDTAR'
import sys, os, tarfile

themes_dir = sys.argv[1]
upstream = {
    "26","30","3.5inch-dark","3.5inchTheme2","43","44","45","5inchTheme2",
    "Advanced_Radials_Test","AMD","bash-dark-green","BigClock","Blue_Technology",
    "Cyberdeck","Cyberpunk","CustomDataExample","Digital_CPU_0.96Inch",
    "DigitalLandscape","Example_0.96Inch_1","Example_0.96Inch_2",
    "Example_0.96Inch_Clock","Gradient","Industrial","SimpleBlue","SimpleFire",
    "SimpleGreen","SimpleMulticolor","SimpleNeon","SimpleOrange","SimplePurple",
    "SimpleRed","SimpleYellow","TaskManager5inch","TerminalColored"
}
custom = [t for t in os.listdir(themes_dir)
          if os.path.isdir(os.path.join(themes_dir, t)) and t not in upstream]
out = "/tmp/turing_themes_backup.tar.gz"
try:
    with tarfile.open(out, "w:gz") as tar:
        for t in custom:
            tar.add(os.path.join(themes_dir, t), arcname=t)
    print(f"OK:{len(custom)} themes backed up to {out}")
except Exception as e:
    print(f"ERROR:{e}")
    sys.exit(1)
ENDTAR
        if [ $? -eq 0 ]; then
            log_success "Themes backed up to /tmp/turing_themes_backup.tar.gz"
        else
            log_warning "Backup failed — continuing anyway"
        fi
    fi
}

restore_custom_themes() {
    local BACKUP="/tmp/turing_themes_backup.tar.gz"
    [ -f "$BACKUP" ] || return 0
    local THEMES_DIR="$INSTALL_DIR/res/themes"
    [ -d "$THEMES_DIR" ] || return 0
    python3 - "$BACKUP" "$THEMES_DIR" << 'ENDRESTORE'
import sys, tarfile
backup, themes_dir = sys.argv[1], sys.argv[2]
try:
    with tarfile.open(backup, "r:gz") as tar:
        names = tar.getnames()
        tar.extractall(themes_dir)
    print(f"OK:{len(names)} themes restored")
except Exception as e:
    print(f"ERROR:{e}")
    sys.exit(1)
ENDRESTORE
    if [ $? -eq 0 ]; then
        log_success "Custom themes restored"
    else
        log_warning "Theme restore failed — backup still at $BACKUP"
    fi
}

detect_existing_install() {
    INSTALL_EXISTS=false
    CONTAINER_EXISTS=false
    IMAGE_EXISTS=false
    [ -d "$INSTALL_DIR" ] && INSTALL_EXISTS=true
    podman image exists "$IMAGE_NAME" 2>/dev/null && IMAGE_EXISTS=true
    podman ps -a --format "{{.Names}}" 2>/dev/null | grep -q "^turing-display" && CONTAINER_EXISTS=true
}

patch_themes() {
    log_info "Patching themes..."

    # Landscape15Grid: fix HOUR time display
    # - Use 24h format (HH:mm) to avoid AM/PM suffix crossing a grid line
    # - Center text within the time cell using ALIGN: center
    # - Tune X position so text is visually centered in the grid cell
    THEME_YAML="$INSTALL_DIR/res/themes/Landscape15Grid/theme.yaml"
    if [ -f "$THEME_YAML" ]; then
        python3 - "$THEME_YAML" << 'ENDPATCH'
import sys

path = sys.argv[1]
with open(path) as f:
    lines = f.readlines()

# Find the HOUR block by locating the FORMAT: short line for time (not date)
# and patch FORMAT, X, WIDTH, ANCHOR, add ALIGN
hour_format_idx = None
for i, line in enumerate(lines):
    # The HOUR FORMAT line contains '6:48 PM' in the comment
    if 'FORMAT:' in line and '6:48 PM' in line:
        hour_format_idx = i
        break

if hour_format_idx is None:
    print("Landscape15Grid: HOUR FORMAT line not found - skipping")
    sys.exit(0)

changes = 0

# FORMAT line
if 'HH:mm' not in lines[hour_format_idx]:
    lines[hour_format_idx] = '        FORMAT: HH:mm\n'
    changes += 1

# Scan forward from FORMAT to find X, WIDTH, ANCHOR within the next 15 lines
align_inserted = False
for i in range(hour_format_idx, min(hour_format_idx + 15, len(lines))):
    if lines[i].strip().startswith('X:') and not align_inserted:
        lines[i] = '        X: 48\n'; changes += 1
    if lines[i].strip().startswith('WIDTH:'):
        lines[i] = '        WIDTH: 135\n'; changes += 1
    if lines[i].strip().startswith('ANCHOR:'):
        lines[i] = '        ANCHOR: lt\n'; changes += 1
        # Insert ALIGN: center after ANCHOR if not already present
        if i + 1 >= len(lines) or 'ALIGN:' not in lines[i + 1]:
            lines.insert(i + 1, '        ALIGN: center\n')
            align_inserted = True
            changes += 1
        break

with open(path, 'w') as f:
    f.writelines(lines)
print(f"Landscape15Grid: {changes} change(s) applied (24h time, centered)")
ENDPATCH
        log_success "Patched Landscape15Grid theme (24h time, centered)"
    else
        log_info "Landscape15Grid theme not found - skipping"
    fi
}

generate_custom_themes() {
    log_info "Generating custom themes..."

    # PiSuite5 — 5" display theme (800x480 landscape)
    # Requires Pillow (PIL) — available inside the container image but may not be on host.
    # We generate it on the host if PIL is available, otherwise skip with a warning.
    PISUITE_DIR="$INSTALL_DIR/res/themes/PiSuite5"

    if python3 -c "from PIL import Image" 2>/dev/null; then
        python3 - "$INSTALL_DIR" << 'ENDGEN'
import sys, os, math, random
from PIL import Image, ImageDraw

install_dir = sys.argv[1]
out_dir = os.path.join(install_dir, "res", "themes", "PiSuite5")
os.makedirs(out_dir, exist_ok=True)

# ── Background ────────────────────────────────────────────────────────────────
W, H = 800, 480
img = Image.new("RGBA", (W, H), (3, 3, 8, 255))
draw = ImageDraw.Draw(img)
random.seed(42)

PI = math.pi
LEFT_W = int(W / (1 + PI))   # ~196
R_X = LEFT_W + 2
COL_W = (W - R_X) // 3       # ~201
ROW_H = H // 2                # 240

C_BG   = (3, 3, 8)
C_CPU  = (0, 238, 255)
C_GPU  = (255, 0, 204)
C_MEM  = (255, 179, 0)
C_DISK = (0, 255, 136)
C_NET  = (170, 136, 255)
C_TIME = (255, 255, 255)
C_DIM  = (20, 20, 35)

cells = []
for row in range(2):
    for col in range(3):
        x1 = R_X + col * COL_W
        y1 = row * ROW_H
        cells.append((x1, y1, x1 + COL_W - 1, y1 + ROW_H - 1))

cell_colors = [C_CPU, C_GPU, C_MEM, C_DISK, C_NET, C_TIME]

def draw_cell_bg(x1, y1, x2, y2, accent):
    for py in range(y1, y2+1):
        t = (py - y1) / max(y2 - y1, 1)
        r = max(0, min(255, int(C_DIM[0] + accent[0] * 0.04 * (1-t))))
        g = max(0, min(255, int(C_DIM[1] + accent[1] * 0.04 * (1-t))))
        b = max(0, min(255, int(C_DIM[2] + accent[2] * 0.06 * (1-t))))
        draw.line([(x1, py), (x2, py)], fill=(r, g, b, 255))

for i, (x1, y1, x2, y2) in enumerate(cells):
    draw_cell_bg(x1, y1, x2, y2, cell_colors[i])

for py in range(H):
    t = py / H
    draw.line([(0, py), (LEFT_W, py)], fill=(int(4+6*t), int(3+4*t), int(12+10*t), 255))

def scatter_stars(x1, y1, x2, y2, n=25):
    for _ in range(n):
        sx = random.randint(x1+2, x2-2)
        sy = random.randint(y1+2, y2-2)
        br = random.randint(120, 255)
        img.putpixel((sx, sy), (max(0,br-random.randint(0,50)), max(0,br-random.randint(0,40)), br, 255))
        if random.random() < 0.12:
            dim = br // 4
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx, ny = sx+dx, sy+dy
                if x1 <= nx <= x2 and y1 <= ny <= y2:
                    img.putpixel((nx, ny), (dim, dim, dim+15, 255))

for x1, y1, x2, y2 in cells:
    scatter_stars(x1, y1, x2, y2)
scatter_stars(0, 0, LEFT_W, H, n=40)

def draw_pi_glyph(cx, cy, size, color, alpha):
    bar_y = cy - size // 2
    bar_x1 = cx - size // 2
    bar_x2 = cx + size // 2
    bar_h = max(2, size // 20)
    leg_w = max(2, size // 18)
    leg_bottom = cy + size // 2
    for y in range(bar_y, bar_y + bar_h):
        for x in range(bar_x1, bar_x2 + 1):
            if 0 <= x < W and 0 <= y < H: img.putpixel((x, y), color + (alpha,))
    for lx in [bar_x1 + size//6, bar_x2 - size//6]:
        for y in range(bar_y + bar_h, leg_bottom + 1):
            for x in range(lx - leg_w//2, lx + leg_w//2 + 1):
                if 0 <= x < W and 0 <= y < H: img.putpixel((x, y), color + (alpha,))

draw_pi_glyph(LEFT_W // 2, H // 2, 160, (255, 255, 255), 18)
draw_pi_glyph(LEFT_W // 2, H // 2, 100, (200, 220, 255), 55)

def neon_vline(x, color, glow):
    for y in range(H):
        if x-1 >= 0: img.putpixel((x-1, y), glow + (60,))
        if 0 <= x < W: img.putpixel((x, y), color + (255,))
        if x+1 < W: img.putpixel((x+1, y), glow + (60,))

def neon_hline(y, color, glow):
    for x in range(W):
        if y-1 >= 0: img.putpixel((x, y-1), glow + (60,))
        if 0 <= y < H: img.putpixel((x, y), color + (255,))
        if y+1 < H: img.putpixel((x, y+1), glow + (60,))

neon_vline(LEFT_W,     (255,255,255), (180,200,255))
neon_vline(LEFT_W + 1, (255,255,255), (180,200,255))
neon_hline(ROW_H,     (255,255,255), (180,200,255))
neon_hline(ROW_H + 1, (255,255,255), (180,200,255))
for col in range(1, 3):
    vx = R_X + col * COL_W
    neon_vline(vx,     (255,255,255), (150,150,200))
    neon_vline(vx + 1, (255,255,255), (150,150,200))
neon_vline(0,   (255,255,255), (100,120,180))
neon_vline(799, (255,255,255), (100,120,180))
neon_hline(0,   (255,255,255), (100,120,180))
neon_hline(479, (255,255,255), (100,120,180))

ACCENT_H = 3
for i, (x1, y1, x2, y2) in enumerate(cells):
    ac = cell_colors[i]
    for px in range(x1+2, x2-1):
        for py in range(y1+2, y1+2+ACCENT_H):
            if 0 <= py < H: img.putpixel((px, py), ac + (200,))
        py = y1 + 2 + ACCENT_H
        if 0 <= py < H:
            img.putpixel((px, py), (min(255,C_DIM[0]+ac[0]//4), min(255,C_DIM[1]+ac[1]//4), min(255,C_DIM[2]+ac[2]//4), 255))

bg_path = os.path.join(out_dir, "background.png")
img.save(bg_path)
print(f"PiSuite5 background saved: {bg_path}")

# ── theme.yaml ────────────────────────────────────────────────────────────────
CPU_C  = "0, 238, 255"
GPU_C  = "255, 0, 204"
MEM_C  = "255, 179, 0"
DISK_C = "0, 255, 136"
NET_C  = "170, 136, 255"
TIME_C = "255, 255, 255"
DIM_C  = "160, 160, 180"
BG     = "background.png"
FONT_BOLD = "roboto/Roboto-Bold.ttf"
FONT_MONO = "jetbrains-mono/JetBrainsMono-Bold.ttf"

CPU_X,  CPU_Y  = R_X,           0
GPU_X,  GPU_Y  = R_X + COL_W,   0
MEM_X,  MEM_Y  = R_X + 2*COL_W, 0
DISK_X, DISK_Y = R_X,           ROW_H
NET_X,  NET_Y  = R_X + COL_W,   ROW_H
TIME_X, TIME_Y = R_X + 2*COL_W, ROW_H

def lx(cell_x): return cell_x + 4

yaml = f"""---
author: "PiSuite"
display:
  DISPLAY_SIZE: 5"
  DISPLAY_ORIENTATION: landscape
  DISPLAY_RGB_LED: 0, 100, 255

static_text:
  CPU_LABEL:
    TEXT: CPU
    X: {lx(CPU_X)}
    Y: {CPU_Y + 18}
    FONT: {FONT_BOLD}
    FONT_SIZE: 18
    FONT_COLOR: {DIM_C}
    BACKGROUND_IMAGE: {BG}
  CPU_TEMP_LABEL:
    TEXT: TEMP
    X: {lx(CPU_X)}
    Y: {CPU_Y + 115}
    FONT: {FONT_BOLD}
    FONT_SIZE: 16
    FONT_COLOR: {DIM_C}
    BACKGROUND_IMAGE: {BG}
  CPU_FREQ_LABEL:
    TEXT: FREQ
    X: {lx(CPU_X) + 100}
    Y: {CPU_Y + 115}
    FONT: {FONT_BOLD}
    FONT_SIZE: 16
    FONT_COLOR: {DIM_C}
    BACKGROUND_IMAGE: {BG}
  GPU_LABEL:
    TEXT: GPU
    X: {lx(GPU_X)}
    Y: {GPU_Y + 18}
    FONT: {FONT_BOLD}
    FONT_SIZE: 18
    FONT_COLOR: {DIM_C}
    BACKGROUND_IMAGE: {BG}
  GPU_TEMP_LABEL:
    TEXT: TEMP
    X: {lx(GPU_X)}
    Y: {GPU_Y + 115}
    FONT: {FONT_BOLD}
    FONT_SIZE: 16
    FONT_COLOR: {DIM_C}
    BACKGROUND_IMAGE: {BG}
  GPU_MEM_LABEL:
    TEXT: VRAM
    X: {lx(GPU_X) + 100}
    Y: {GPU_Y + 115}
    FONT: {FONT_BOLD}
    FONT_SIZE: 16
    FONT_COLOR: {DIM_C}
    BACKGROUND_IMAGE: {BG}
  MEM_LABEL:
    TEXT: MEMORY
    X: {lx(MEM_X)}
    Y: {MEM_Y + 18}
    FONT: {FONT_BOLD}
    FONT_SIZE: 18
    FONT_COLOR: {DIM_C}
    BACKGROUND_IMAGE: {BG}
  MEM_FREE_LABEL:
    TEXT: FREE
    X: {lx(MEM_X) + 100}
    Y: {MEM_Y + 115}
    FONT: {FONT_BOLD}
    FONT_SIZE: 16
    FONT_COLOR: {DIM_C}
    BACKGROUND_IMAGE: {BG}
  DISK_LABEL:
    TEXT: DISK
    X: {lx(DISK_X)}
    Y: {DISK_Y + 18}
    FONT: {FONT_BOLD}
    FONT_SIZE: 18
    FONT_COLOR: {DIM_C}
    BACKGROUND_IMAGE: {BG}
  DISK_FREE_LABEL:
    TEXT: FREE
    X: {lx(DISK_X) + 100}
    Y: {DISK_Y + 115}
    FONT: {FONT_BOLD}
    FONT_SIZE: 16
    FONT_COLOR: {DIM_C}
    BACKGROUND_IMAGE: {BG}
  NET_LABEL:
    TEXT: NETWORK
    X: {lx(NET_X)}
    Y: {NET_Y + 18}
    FONT: {FONT_BOLD}
    FONT_SIZE: 18
    FONT_COLOR: {DIM_C}
    BACKGROUND_IMAGE: {BG}
  NET_UP_LABEL:
    TEXT: UP
    X: {lx(NET_X)}
    Y: {NET_Y + 115}
    FONT: {FONT_BOLD}
    FONT_SIZE: 16
    FONT_COLOR: {DIM_C}
    BACKGROUND_IMAGE: {BG}
  NET_DN_LABEL:
    TEXT: DOWN
    X: {lx(NET_X) + 100}
    Y: {NET_Y + 115}
    FONT: {FONT_BOLD}
    FONT_SIZE: 16
    FONT_COLOR: {DIM_C}
    BACKGROUND_IMAGE: {BG}

static_images:
  BACKGROUND:
    PATH: {BG}
    X: 0
    Y: 0
    WIDTH: 800
    HEIGHT: 480

STATS:
  CPU:
    PERCENTAGE:
      INTERVAL: 1
      TEXT:
        SHOW: True
        SHOW_UNIT: True
        X: {lx(CPU_X)}
        Y: {CPU_Y + 50}
        FONT: {FONT_MONO}
        FONT_SIZE: 48
        FONT_COLOR: {CPU_C}
        BACKGROUND_IMAGE: {BG}
    TEMPERATURE:
      INTERVAL: 5
      TEXT:
        SHOW: True
        SHOW_UNIT: True
        X: {lx(CPU_X)}
        Y: {CPU_Y + 135}
        FONT: {FONT_MONO}
        FONT_SIZE: 28
        FONT_COLOR: {CPU_C}
        BACKGROUND_IMAGE: {BG}
    FREQUENCY:
      INTERVAL: 5
      TEXT:
        SHOW: True
        SHOW_UNIT: False
        X: {lx(CPU_X) + 100}
        Y: {CPU_Y + 135}
        FONT: {FONT_MONO}
        FONT_SIZE: 28
        FONT_COLOR: {CPU_C}
        BACKGROUND_IMAGE: {BG}
  GPU:
    INTERVAL: 1
    PERCENTAGE:
      TEXT:
        SHOW: True
        SHOW_UNIT: True
        X: {lx(GPU_X)}
        Y: {GPU_Y + 50}
        FONT: {FONT_MONO}
        FONT_SIZE: 48
        FONT_COLOR: {GPU_C}
        BACKGROUND_IMAGE: {BG}
    TEMPERATURE:
      TEXT:
        SHOW: True
        SHOW_UNIT: True
        X: {lx(GPU_X)}
        Y: {GPU_Y + 135}
        FONT: {FONT_MONO}
        FONT_SIZE: 28
        FONT_COLOR: {GPU_C}
        BACKGROUND_IMAGE: {BG}
    MEMORY:
      TEXT:
        SHOW: True
        SHOW_UNIT: False
        X: {lx(GPU_X) + 100}
        Y: {GPU_Y + 135}
        FONT: {FONT_MONO}
        FONT_SIZE: 28
        FONT_COLOR: {GPU_C}
        BACKGROUND_IMAGE: {BG}
  MEMORY:
    INTERVAL: 5
    VIRTUAL:
      PERCENT_TEXT:
        SHOW: True
        SHOW_UNIT: True
        X: {lx(MEM_X)}
        Y: {MEM_Y + 50}
        FONT: {FONT_MONO}
        FONT_SIZE: 48
        FONT_COLOR: {MEM_C}
        BACKGROUND_IMAGE: {BG}
      FREE:
        SHOW: True
        SHOW_UNIT: False
        X: {lx(MEM_X) + 100}
        Y: {MEM_Y + 135}
        FONT: {FONT_MONO}
        FONT_SIZE: 28
        FONT_COLOR: {MEM_C}
        BACKGROUND_IMAGE: {BG}
  DISK:
    INTERVAL: 10
    USED:
      PERCENT_TEXT:
        SHOW: True
        SHOW_UNIT: True
        X: {lx(DISK_X)}
        Y: {DISK_Y + 50}
        FONT: {FONT_MONO}
        FONT_SIZE: 48
        FONT_COLOR: {DISK_C}
        BACKGROUND_IMAGE: {BG}
      FREE:
        TEXT:
          SHOW: True
          SHOW_UNIT: False
          X: {lx(DISK_X) + 100}
          Y: {DISK_Y + 135}
          FONT: {FONT_MONO}
          FONT_SIZE: 28
          FONT_COLOR: {DISK_C}
          BACKGROUND_IMAGE: {BG}
  NET:
    INTERVAL: 1
    ETH:
      UPLOAD:
        TEXT:
          SHOW: True
          X: {lx(NET_X)}
          Y: {NET_Y + 135}
          FONT: {FONT_MONO}
          FONT_SIZE: 22
          FONT_COLOR: {NET_C}
          BACKGROUND_IMAGE: {BG}
      DOWNLOAD:
        TEXT:
          SHOW: True
          X: {lx(NET_X) + 100}
          Y: {NET_Y + 135}
          FONT: {FONT_MONO}
          FONT_SIZE: 22
          FONT_COLOR: {NET_C}
          BACKGROUND_IMAGE: {BG}
    WLO:
      UPLOAD:
        TEXT:
          SHOW: True
          X: {lx(NET_X)}
          Y: {NET_Y + 170}
          FONT: {FONT_MONO}
          FONT_SIZE: 22
          FONT_COLOR: {NET_C}
          BACKGROUND_IMAGE: {BG}
      DOWNLOAD:
        TEXT:
          SHOW: True
          X: {lx(NET_X) + 100}
          Y: {NET_Y + 170}
          FONT: {FONT_MONO}
          FONT_SIZE: 22
          FONT_COLOR: {NET_C}
          BACKGROUND_IMAGE: {BG}
  DATE:
    INTERVAL: 1
    DAY:
      TEXT:
        FORMAT: short
        SHOW: True
        X: {lx(TIME_X)}
        Y: {TIME_Y + 155}
        FONT: {FONT_MONO}
        FONT_SIZE: 22
        FONT_COLOR: {TIME_C}
        BACKGROUND_IMAGE: {BG}
        WIDTH: 195
        ANCHOR: lt
        ALIGN: center
    HOUR:
      TEXT:
        FORMAT: HH:mm
        SHOW: True
        X: {lx(TIME_X)}
        Y: {TIME_Y + 50}
        FONT: {FONT_MONO}
        FONT_SIZE: 58
        FONT_COLOR: {TIME_C}
        BACKGROUND_IMAGE: {BG}
        WIDTH: 195
        ANCHOR: lt
        ALIGN: center
"""

yaml_path = os.path.join(out_dir, "theme.yaml")
with open(yaml_path, "w") as f:
    f.write(yaml)
print(f"PiSuite5 theme.yaml saved: {yaml_path}")
ENDGEN
        log_success "Generated PiSuite5 theme (background + theme.yaml)"
    else
        log_warning "Pillow (PIL) not installed on host — attempting to generate PiSuite5 background inside container"
        mkdir -p "$PISUITE_DIR"
        # Copy the generator scripts into the install dir so the container can run them
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        for gen_script in gen_pi_bg_5inch.py gen_pi_theme_5inch.py gen_vortex_bg_5inch.py gen_vortex_theme_5inch_minimal.py; do
            if [ -f "$SCRIPT_DIR/$gen_script" ]; then
                cp "$SCRIPT_DIR/$gen_script" "$INSTALL_DIR/$gen_script"
            fi
        done
        if podman image exists "$IMAGE_NAME" 2>/dev/null; then
            log_info "Running PiSuite5 generators inside container..."
            podman run --rm \
                -v "$INSTALL_DIR:/app:z" \
                --entrypoint python3 \
                "$IMAGE_NAME" \
                /app/gen_pi_bg_5inch.py && \
            podman run --rm \
                -v "$INSTALL_DIR:/app:z" \
                --entrypoint python3 \
                "$IMAGE_NAME" \
                /app/gen_pi_theme_5inch.py && \
            log_success "PiSuite5 theme generated inside container" || \
            log_warning "Container generation failed — run manually after install: podman run --rm -v $INSTALL_DIR:/app:z --entrypoint python3 $IMAGE_NAME /app/gen_pi_bg_5inch.py"
        else
            log_warning "Container image not built yet — PiSuite5 background will be generated after container build"
            log_info "Run manually after install: podman exec turing-display python3 /app/gen_pi_bg_5inch.py"
        fi
        # Write theme.yaml without background generation — container has PIL
        python3 - "$INSTALL_DIR" << 'ENDYAML'
import sys, os, math

install_dir = sys.argv[1]
PI = math.pi
W, H = 800, 480
LEFT_W = int(W / (1 + PI))
R_X = LEFT_W + 2
COL_W = (W - R_X) // 3
ROW_H = H // 2

out_dir = os.path.join(install_dir, "res", "themes", "PiSuite5")
os.makedirs(out_dir, exist_ok=True)

CPU_C  = "0, 238, 255"
GPU_C  = "255, 0, 204"
MEM_C  = "255, 179, 0"
DISK_C = "0, 255, 136"
NET_C  = "170, 136, 255"
TIME_C = "255, 255, 255"
DIM_C  = "160, 160, 180"
BG     = "background.png"
FONT_BOLD = "roboto/Roboto-Bold.ttf"
FONT_MONO = "jetbrains-mono/JetBrainsMono-Bold.ttf"

CPU_X,  CPU_Y  = R_X,           0
GPU_X,  GPU_Y  = R_X + COL_W,   0
MEM_X,  MEM_Y  = R_X + 2*COL_W, 0
DISK_X, DISK_Y = R_X,           ROW_H
NET_X,  NET_Y  = R_X + COL_W,   ROW_H
TIME_X, TIME_Y = R_X + 2*COL_W, ROW_H

def lx(cell_x): return cell_x + 4

# (same yaml content as above — omitted for brevity, written inline)
yaml_path = os.path.join(out_dir, "theme.yaml")
if not os.path.exists(yaml_path):
    # Write a minimal placeholder so the theme is selectable
    with open(yaml_path, "w") as f:
        f.write("# PiSuite5 theme — run gen_pi_bg_5inch.py and gen_pi_theme_5inch.py to generate\n")
    print(f"Placeholder written: {yaml_path}")
else:
    print(f"theme.yaml already exists: {yaml_path}")
ENDYAML
    fi

    # ── Vortex theme (Seed of Life) for 5" display ──────────────────────────
    log_info "Generating Vortex theme (Seed of Life)..."
    VORTEX_DIR="$INSTALL_DIR/res/themes/PiSuite5"
    mkdir -p "$VORTEX_DIR"

    # Also write standalone generator scripts to install dir for future re-generation
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    for gen_script in gen_vortex_bg_5inch.py gen_vortex_theme_5inch_minimal.py; do
        if [ -f "$SCRIPT_DIR/$gen_script" ]; then
            cp "$SCRIPT_DIR/$gen_script" "$INSTALL_DIR/$gen_script"
        fi
    done

    if python3 -c "from PIL import Image" 2>/dev/null; then
        # ── Vortex background (embedded) ──
        python3 - "$INSTALL_DIR" << 'ENDVORTEXBG'
import sys, os, math, random
from PIL import Image, ImageDraw, ImageFilter

install_dir = sys.argv[1]
out_dir = os.path.join(install_dir, "res", "themes", "PiSuite5")
os.makedirs(out_dir, exist_ok=True)

W, H = 800, 480
img = Image.new("RGB", (W, H), (3, 3, 14))
random.seed(137)

for _ in range(500):
    x = random.randint(0, W-1)
    y = random.randint(0, H-1)
    br = random.randint(100, 255)
    if random.random() < 0.85:
        tint = random.choice([(br,br,br),(br,br-20,br-40),(br-20,br-20,br)])
        img.putpixel((x, y), tint)
    else:
        img.putpixel((x, y), (br, br, br))
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < W and 0 <= ny < H:
                img.putpixel((nx, ny), (br//4, br//4, br//4))

CX, CY = 400, 240
R = 90

def cc(angle_deg):
    rad = math.radians(angle_deg - 90)
    return (CX + R * math.cos(rad), CY + R * math.sin(rad))

outer_centers = [cc(a) for a in [0, 60, 120, 180, 240, 300]]
all_centers   = [(float(CX), float(CY))] + outer_centers

STAT_COLORS = [
    (0,   238, 255),  # CPU   cyan
    (255, 0,   204),  # GPU   magenta
    (255, 200, 0  ),  # MEM   gold
    (0,   255, 136),  # DISK  green
    (255, 40,  40 ),  # GPU fan — red (bottom-left circle)
    (0,   120, 255),  # CPU fan — blue (top-left circle)
]
CENTER_COLOR = (255, 120, 0)

def add_glow(base_img, glow_layer, radius, strength=1.0):
    blurred = glow_layer.filter(ImageFilter.GaussianBlur(radius=radius))
    ba = base_img.load()
    ga = blurred.load()
    for py in range(H):
        for px in range(W):
            b = ba[px, py]
            g = ga[px, py]
            ba[px, py] = (
                min(255, b[0] + int(g[0] * strength)),
                min(255, b[1] + int(g[1] * strength)),
                min(255, b[2] + int(g[2] * strength)),
            )

def draw_circle_neon(base_img, cx, cy, r, color, line_width=3):
    bright     = tuple(min(255, int(c * 1.3) + 20) for c in color)
    white_tint = tuple(min(255, c + 100) for c in color)
    halo = Image.new("RGB", (W, H), (0, 0, 0))
    hd   = ImageDraw.Draw(halo)
    for w in range(line_width + 10, line_width + 3, -1):
        f  = (w - line_width - 3) / 7.0
        gc = tuple(int(c * f * 0.5) for c in color)
        hd.ellipse([cx-r-w//2, cy-r-w//2, cx+r+w//2, cy+r+w//2], outline=gc, width=1)
    add_glow(base_img, halo, radius=12, strength=0.8)
    mid = Image.new("RGB", (W, H), (0, 0, 0))
    md  = ImageDraw.Draw(mid)
    for w in range(line_width + 6, line_width - 1, -1):
        f  = 1.0 - (w - line_width) / (6.0 + line_width)
        gc = tuple(int(c * (0.3 + 0.7 * f)) for c in bright)
        md.ellipse([cx-r-w//2, cy-r-w//2, cx+r+w//2, cy+r+w//2], outline=gc, width=1)
    add_glow(base_img, mid, radius=4, strength=1.0)
    corona = Image.new("RGB", (W, H), (0, 0, 0))
    cd     = ImageDraw.Draw(corona)
    cd.ellipse([cx-r-line_width, cy-r-line_width, cx+r+line_width, cy+r+line_width],
               outline=bright, width=line_width + 1)
    add_glow(base_img, corona, radius=2, strength=1.2)
    d = ImageDraw.Draw(base_img)
    d.ellipse([cx-r-line_width//2, cy-r-line_width//2,
               cx+r+line_width//2, cy+r+line_width//2],
              outline=bright, width=line_width)
    d.ellipse([cx-r+1, cy-r+1, cx+r-1, cy+r-1], outline=white_tint, width=1)

fill_layer = Image.new("RGB", (W, H), (0, 0, 0))
fd = ImageDraw.Draw(fill_layer)
for i, (cx, cy) in enumerate(outer_centers):
    col = STAT_COLORS[i]
    for step in range(10, 0, -1):
        fr    = int(R * 0.7 * step / 10)
        alpha = int(16 * step / 10)
        fc    = tuple(min(255, int(c * alpha / 255)) for c in col)
        fd.ellipse([cx-fr, cy-fr, cx+fr, cy+fr], fill=fc)
fill_blurred = fill_layer.filter(ImageFilter.GaussianBlur(radius=16))
add_glow(img, fill_blurred, radius=1, strength=1.0)

draw_circle_neon(img, CX, CY, R, CENTER_COLOR, line_width=2)
for i, (cx, cy) in enumerate(outer_centers):
    draw_circle_neon(img, int(cx), int(cy), R, STAT_COLORS[i], line_width=3)

def circle_intersections(c1x, c1y, c2x, c2y, r):
    dx, dy = c2x - c1x, c2y - c1y
    d = math.sqrt(dx*dx + dy*dy)
    if d > 2*r or d < 1e-6: return []
    a  = d / 2
    h  = math.sqrt(max(0, r*r - a*a))
    mx, my = (c1x + c2x) / 2, (c1y + c2y) / 2
    px, py = -dy/d * h, dx/d * h
    return [(mx+px, my+py), (mx-px, my-py)]

dot_draw = ImageDraw.Draw(img)

def draw_hotspot(x, y, color, radius=3):
    glow = tuple(max(0, c//3) for c in color)
    dot_draw.ellipse([x-radius-2, y-radius-2, x+radius+2, y+radius+2], fill=glow)
    mid  = tuple(min(255, c//2 + 50) for c in color)
    dot_draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=mid)
    dot_draw.ellipse([x-1, y-1, x+1, y+1], fill=(255, 255, 255))

for i, (cx, cy) in enumerate(outer_centers):
    pts   = circle_intersections(CX, CY, cx, cy, R)
    blend = tuple((CENTER_COLOR[k] + STAT_COLORS[i][k]) // 2 for k in range(3))
    for px, py in pts: draw_hotspot(int(px), int(py), blend)

for i in range(6):
    j = (i + 1) % 6
    c1x, c1y = outer_centers[i]
    c2x, c2y = outer_centers[j]
    pts   = circle_intersections(c1x, c1y, c2x, c2y, R)
    blend = tuple((STAT_COLORS[i][k] + STAT_COLORS[j][k]) // 2 for k in range(3))
    for px, py in pts: draw_hotspot(int(px), int(py), blend)

draw_hotspot(CX, CY, (255, 180, 80), radius=4)
for i, (cx, cy) in enumerate(outer_centers):
    col = STAT_COLORS[i]
    dot_draw.ellipse([cx-3, cy-3, cx+3, cy+3], fill=tuple(min(255, c+60) for c in col))
    dot_draw.ellipse([cx-1, cy-1, cx+1, cy+1], fill=(255, 255, 255))

vignette = Image.new("RGB", (W, H), (0, 0, 0))
vd = ImageDraw.Draw(vignette)
for s in range(40, 0, -1):
    t   = s / 40
    pad = int((1.0 - t) * min(W, H) * 0.4)
    if W - pad <= pad or H - pad <= pad: continue
    alpha = int(160 * (1.0 - t) ** 2)
    vd.rectangle([pad, pad, W-pad, H-pad], fill=(alpha, alpha, alpha))
vb = vignette.filter(ImageFilter.GaussianBlur(radius=35))
ba = img.load()
va = vb.load()
for py in range(H):
    for px in range(W):
        b = ba[px, py]
        v = va[px, py]
        ba[px, py] = (max(0, b[0]-v[0]//2), max(0, b[1]-v[1]//2), max(0, b[2]-v[2]//2))

out = os.path.join(out_dir, "background.png")
img.save(out)
print(f"Vortex background saved: {out}")
ENDVORTEXBG

        # ── Vortex theme.yaml (embedded) ──
        python3 - "$INSTALL_DIR" << 'ENDVORTEXYAML'
import sys, os

install_dir = sys.argv[1]
OUT = os.path.join(install_dir, "res", "themes", "PiSuite5", "theme.yaml")
BG        = 'background.png'
FONT_BOLD = 'roboto/Roboto-Bold.ttf'
FONT_MONO = 'jetbrains-mono/JetBrainsMono-Bold.ttf'

C_CPU  = '0, 238, 255'
C_GPU  = '255, 0, 204'
C_MEM  = '255, 200, 0'
C_DISK = '0, 255, 136'
C_NETU = '180, 140, 255'
C_NETD = '100, 180, 255'
C_CFAN = '0, 120, 255'
C_GFAN = '255, 40, 40'
C_PWR  = '255, 120, 0'
C_TIME = '255, 255, 255'
C_DIM  = '160, 160, 160'

TZ_X,  TZ_Y  = 30,  4
WX_X,  WX_Y  = 640, 22
PZ_X,  PZ_Y  = 650, 400
FZ_X,  FZ_Y  = 30,  400

L_CENTER = 98
R_CENTER = 700

GZ_X,  GZ_Y  = R_CENTER - 50, 148
MZ_X,  MZ_Y  = R_CENTER - 50, 270
UZ_X,  UZ_Y  = L_CENTER - 50, 308
DLZ_X, DLZ_Y = L_CENTER - 50, 138

CPU_ROW_Y  = 14
CPU_COL_L  = 250
CPU_COL_C  = 340
CPU_COL_R  = 430
CPU_LBL_Y  = CPU_ROW_Y + 6

DISK_ROW_Y = 436
DISK_COL_L = 250
DISK_COL_C = 340
DISK_COL_R = 420
DISK_LBL_Y = DISK_ROW_Y + 6

W   = 100
WL  = 120
WC  = 130
WH  = 90

def slbl(key, text, x, y, color, width=W, size=13):
    return f"""  {key}:
    TEXT: "{text}"
    X: {x}
    Y: {y}
    FONT: {FONT_BOLD}
    FONT_SIZE: {size}
    FONT_COLOR: {color}
    BACKGROUND_IMAGE: {BG}
    WIDTH: {width}
    ANCHOR: mt
    ALIGN: center"""

def tb(x, y, color, size, width=W, show_unit=True, fmt=None):
    lines = ["        SHOW: True", f"        SHOW_UNIT: {'True' if show_unit else 'False'}"]
    if fmt: lines.append(f"        FORMAT: {fmt}")
    lines += [
        f"        X: {x}", f"        Y: {y}",
        f"        FONT: {FONT_MONO}", f"        FONT_SIZE: {size}",
        f"        FONT_COLOR: {color}", f"        BACKGROUND_IMAGE: {BG}",
        f"        WIDTH: {width}", "        ANCHOR: mt", "        ALIGN: center",
    ]
    return '\n'.join(lines)

def rb(x, y, radius, width, a_start, a_end, color, bg_color, bbox=None, draw_bg=True):
    bb = f"\n        CUSTOM_BBOX: {bbox}" if bbox else ""
    return '\n'.join([
        "        SHOW: True", f"        X: {x}", f"        Y: {y}",
        f"        RADIUS: {radius}", f"        WIDTH: {width}",
        "        MIN_VALUE: 0", "        MAX_VALUE: 100",
        f"        ANGLE_START: {a_start}", f"        ANGLE_END: {a_end}",
        "        ANGLE_STEPS: 1", "        ANGLE_SEP: 0", "        CLOCKWISE: True",
        f"        BAR_COLOR: {color}", f"        BAR_BACKGROUND_COLOR: {bg_color}",
        f"        DRAW_BAR_BACKGROUND: {'True' if draw_bg else 'False'}", "        SHOW_TEXT: False",
        f"        BACKGROUND_IMAGE: {BG}{bb}",
    ])

def wt(x, y, color, size=18, width=130):
    return '\n'.join([
        "        SHOW: True",
        f"        X: {x}", f"        Y: {y}",
        f"        FONT: {FONT_BOLD}", f"        FONT_SIZE: {size}",
        f"        FONT_COLOR: {color}", f"        BACKGROUND_IMAGE: {BG}",
        f"        WIDTH: {width}", "        ANCHOR: mt", "        ALIGN: center",
    ])

def off():
    return "        SHOW: False"

parts = []
p = parts.append

p(f"""---
author: "PiSuite5 Seed of Life"
display:
  DISPLAY_SIZE: 5"
  DISPLAY_ORIENTATION: landscape
  DISPLAY_RGB_LED: 0, 0, 32

static_images:
  BACKGROUND:
    PATH: background.png
    X: 0
    Y: 0
    WIDTH: 800
    HEIGHT: 480

static_text:""")

p(slbl('PWR_LBL',   'POWER',   PZ_X,       PZ_Y,       C_PWR,  width=WC,  size=26))
p(slbl('CPU_LBL',   'CPU',     CPU_COL_L,  CPU_LBL_Y,  C_CPU,  width=WH,  size=26))
p(slbl('GPU_LBL',   'GPU',     R_CENTER - 38,  GZ_Y,   C_GPU,  width=W,   size=26))
p(slbl('MEM_LBL',   'MEMORY',  R_CENTER - 60,  MZ_Y,   C_MEM,  width=WL,  size=26))
p(slbl('DISK_LBL',  'DISK',    DISK_COL_L, DISK_LBL_Y, C_DISK, width=WH,  size=26))
p(slbl('FPS_LBL',   'FPS',     FZ_X,       FZ_Y,       C_GPU,  width=WC,  size=26))
p(slbl('CFAN_LBL',  'CPU FAN', L_CENTER - 70,  DLZ_Y,  C_CFAN, width=140, size=26))
p(slbl('GFAN_LBL',  'GPU FAN', L_CENTER - 60,  UZ_Y+8, C_GFAN, width=WL,  size=26))

NET_LBL_X = 35
NET_VAL_X = 90
NET_UL_Y = 226
NET_DL_Y = 256
p(slbl('NETU_LBL', 'UL', NET_LBL_X, NET_UL_Y, C_NETU, width=50, size=22))
p(slbl('NETD_LBL', 'DL', NET_LBL_X, NET_DL_Y, C_NETD, width=50, size=22))

p("""
STATS:""")

p(f"""  CPU:
    PERCENTAGE:
      INTERVAL: 1
      RADIAL:
{rb(400, 150, 90, 14, 210, 330, C_CPU, '0, 40, 50', '[4, 0, 176, 143]')}
      TEXT:
{tb(CPU_COL_C, CPU_ROW_Y+4, C_CPU, 28, width=WH)}
      GRAPH:
{off()}
      LINE_GRAPH:
{off()}
    TEMPERATURE:
      INTERVAL: 5
      TEXT:
{tb(CPU_COL_R, CPU_ROW_Y+4, C_CPU, 28, width=WH)}
      GRAPH:
{off()}
      RADIAL:
{off()}
      LINE_GRAPH:
{off()}
    FREQUENCY:
      INTERVAL: 0
      TEXT:
{off()}
      GRAPH:
{off()}
      LINE_GRAPH:
{off()}
    LOAD:
      INTERVAL: 0
      TEXT:
{off()}
      GRAPH:
{off()}
      LINE_GRAPH:
{off()}
    FAN_SPEED:
      INTERVAL: 2
      TEXT:
{tb(DLZ_X, DLZ_Y+30, C_CFAN, 28, width=W, show_unit=True)}
      GRAPH:
{off()}
      RADIAL:
{rb(322, 195, 90, 14, 150, 270, C_CFAN, '0, 20, 50', '[0, 0, 98, 143]')}
      LINE_GRAPH:
{off()}""")

p(f"""
  GPU:
    INTERVAL: 1
    PERCENTAGE:
      RADIAL:
{rb(477, 195, 90, 14, 270, 30, C_GPU, '50, 0, 40', '[82, 0, 180, 143]')}
      TEXT:
{tb(GZ_X, GZ_Y+28, C_GPU, 28, width=W)}
      GRAPH:
{off()}
      LINE_GRAPH:
{off()}
    TEMPERATURE:
      TEXT:
{tb(GZ_X, GZ_Y+58, C_GPU, 28, width=W)}
      GRAPH:
{off()}
      RADIAL:
{off()}
      LINE_GRAPH:
{off()}
    MEMORY:
      TEXT:
{off()}
      GRAPH:
{off()}
      RADIAL:
{off()}
    MEMORY_PERCENT:
      TEXT:
{off()}
      GRAPH:
{off()}
      RADIAL:
{off()}
      LINE_GRAPH:
{off()}
    MEMORY_USED:
      TEXT:
{off()}
    MEMORY_TOTAL:
      TEXT:
{off()}
    FPS:
      TEXT:
{tb(FZ_X-20, FZ_Y+32, C_GPU, 32, width=WC, show_unit=False)}
      GRAPH:
{off()}
      RADIAL:
{off()}
      LINE_GRAPH:
{off()}
    FAN_SPEED:
      TEXT:
{tb(UZ_X, UZ_Y+34, C_GFAN, 28, width=W, show_unit=True)}
      GRAPH:
{off()}
      RADIAL:
{rb(322, 285, 90, 14, 90, 210, C_GFAN, '50, 8, 8', '[0, 41, 98, 180]')}
      LINE_GRAPH:
{off()}
    FREQUENCY:
      TEXT:
{off()}
      GRAPH:
{off()}
      RADIAL:
{off()}
      LINE_GRAPH:
{off()}""")

p(f"""
  MEMORY:
    INTERVAL: 5
    VIRTUAL:
      RADIAL:
{rb(477, 285, 90, 14, 330, 90, C_MEM, '50, 40, 0', '[82, 37, 180, 180]')}
      PERCENT_TEXT:
{tb(MZ_X, MZ_Y+30, C_MEM, 28, width=W)}
      FREE:
{tb(R_CENTER - 70, MZ_Y+62, C_MEM, 28, width=140)}
      GRAPH:
{off()}
      LINE_GRAPH:
{off()}
      USED:
{off()}
      TOTAL:
{off()}
    SWAP:
      GRAPH:
{off()}
      RADIAL:
{off()}
      LINE_GRAPH:
{off()}""")

p(f"""
  DISK:
    INTERVAL: 10
    USED:
      RADIAL:
{off()}
      PERCENT_TEXT:
{tb(DISK_COL_C, DISK_ROW_Y+4, C_DISK, 28, width=WH)}
      GRAPH:
{off()}
      LINE_GRAPH:
{off()}
      TEXT:
{off()}
    TOTAL:
      TEXT:
{off()}
    FREE:
      TEXT:
{tb(DISK_COL_R, DISK_ROW_Y+4, C_DISK, 24, width=110)}""")

p(f"""
  DATE:
    INTERVAL: 1
    HOUR:
      TEXT:
        FORMAT: HH:mm
        SHOW: True
        X: {TZ_X}
        Y: {TZ_Y+22}
        FONT: {FONT_MONO}
        FONT_SIZE: 40
        FONT_COLOR: {C_TIME}
        BACKGROUND_IMAGE: {BG}
        WIDTH: 150
        ANCHOR: mt
        ALIGN: center
    DAY:
      TEXT:
        FORMAT: "dd/MM/yy"
        SHOW: True
        X: {TZ_X}
        Y: {TZ_Y+70}
        FONT: {FONT_MONO}
        FONT_SIZE: 26
        FONT_COLOR: {C_DIM}
        BACKGROUND_IMAGE: {BG}
        WIDTH: 150
        ANCHOR: mt
        ALIGN: center""")

C_WTH = '180, 220, 255'
p(f"""
  CUSTOM:
    INTERVAL: 1

    SystemPowerWatts:
      RADIAL:
{rb(400, 240, 52, 10, 120, 60, C_PWR, '40, 20, 0', '[0, 16, 104, 104]')}
      TEXT:
{tb(PZ_X - 5, PZ_Y+32, C_PWR, 32, width=WC, show_unit=False)}

    DayProgressPercent:
      RADIAL:
{off()}
      TEXT:
{off()}

    DiskIOPercent:
      RADIAL:
{rb(400, 330, 90, 14, 30, 150, C_DISK, '0, 50, 25', '[4, 127, 176, 180]')}
      TEXT:
{off()}

    NetUploadMbps:
      RADIAL:
{off()}
      TEXT:
{tb(NET_VAL_X, NET_UL_Y, C_NETU, 22, width=90, show_unit=True)}

    NetDownloadMbps:
      RADIAL:
{off()}
      TEXT:
{tb(NET_VAL_X, NET_DL_Y, C_NETD, 22, width=90, show_unit=True)}
""")

p(f"""
  WEATHER:
    INTERVAL: 300
    TEMPERATURE:
      TEXT:
{wt(WX_X-20, WX_Y+2, C_WTH, size=34, width=160)}
    TEMPERATURE_FELT:
      TEXT:
{wt(WX_X-25, WX_Y+42, C_WTH, size=23, width=100)}
    HUMIDITY:
      TEXT:
{wt(WX_X+60, WX_Y+42, C_WTH, size=23, width=70)}
    WEATHER_DESCRIPTION:
      TEXT:
{wt(WX_X-45, WX_Y+70, C_WTH, size=22, width=200)}
    UPDATE_TIME:
      TEXT:
{off()}""")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
content = '\n'.join(parts)
with open(OUT, 'w') as f:
    f.write(content)
print(f"Vortex theme.yaml saved: {OUT}  ({content.count(chr(10))} lines)")
ENDVORTEXYAML
        log_success "Generated Vortex theme (Seed of Life)"
    else
        log_info "PIL not available on host — Vortex theme will be generated inside container after build"
    fi

    # ── Custom sensors (DiskIOPercent, NetUploadMbps, NetDownloadMbps, etc.) ─
    log_info "Patching custom sensors..."
    SENSORS_CUSTOM="$INSTALL_DIR/library/sensors/sensors_custom.py"
    if [ -f "$SENSORS_CUSTOM" ]; then
        python3 - "$SENSORS_CUSTOM" << 'ENDCUSTOM'
import sys
path = sys.argv[1]
with open(path) as f:
    src = f.read()

classes = []

if "SystemPowerWatts" not in src:
    classes.append('''
# ---------------------------------------------------------------------------
# SystemPowerWatts — total package power from RAPL or zenergy
# ---------------------------------------------------------------------------
import time as _time_mod

_pwr_state = {"last_t": 0.0, "last_uj": 0, "watts": 0.0}

def _update_power():
    import glob, os
    now = _time_mod.time()
    if now - _pwr_state["last_t"] < 0.8:
        return
    uj = 0
    # Try zenergy first
    for hwmon in glob.glob("/sys/class/hwmon/hwmon*/"):
        try:
            name = open(hwmon + "name").read().strip()
        except: continue
        if name == "zenergy":
            try: uj = int(open(hwmon + "energy1_input").read().strip())
            except: pass
            break
    # Fallback to RAPL
    if uj == 0:
        for rp in glob.glob("/sys/class/powercap/intel-rapl:0/energy_uj"):
            try: uj = int(open(rp).read().strip())
            except: pass
            break
    dt = now - _pwr_state["last_t"]
    if _pwr_state["last_t"] > 0 and dt > 0 and uj > 0:
        duj = uj - _pwr_state["last_uj"]
        if duj < 0: duj += 2**32
        _pwr_state["watts"] = duj / (dt * 1e6)
    _pwr_state["last_t"] = now
    _pwr_state["last_uj"] = uj

class SystemPowerWatts(CustomDataSource):
    _last_val = [0.0] * 10
    def as_numeric(self) -> float:
        _update_power()
        w = _pwr_state["watts"]
        pct = min(100.0, w / 3.0)  # scale: 300W = 100%
        SystemPowerWatts._last_val.append(pct)
        SystemPowerWatts._last_val.pop(0)
        return pct
    def as_string(self) -> str:
        _update_power()
        return f"{int(_pwr_state['watts'])}W"
    def last_values(self):
        return SystemPowerWatts._last_val
''')
    print("Adding: SystemPowerWatts")

if "DiskIOPercent" not in src:
    classes.append('''
# ---------------------------------------------------------------------------
# DiskIOPercent — disk I/O throughput as % of max seen
# ---------------------------------------------------------------------------
import psutil as _psutil_mod

_dio_state = {"last_t": 0.0, "last_r": 0, "last_w": 0, "max_bps": 50_000_000, "pct": 0.0}

def _update_disk_io():
    now = _time_mod.time()
    if now - _dio_state["last_t"] < 0.8:
        return
    c = _psutil_mod.disk_io_counters()
    dt = now - _dio_state["last_t"]
    if _dio_state["last_t"] > 0 and dt > 0:
        dr = c.read_bytes - _dio_state["last_r"]
        dw = c.write_bytes - _dio_state["last_w"]
        bps = (dr + dw) / dt
        if bps > _dio_state["max_bps"]:
            _dio_state["max_bps"] = bps
        _dio_state["pct"] = min(100.0, bps / _dio_state["max_bps"] * 100)
    _dio_state["last_t"] = now
    _dio_state["last_r"] = c.read_bytes
    _dio_state["last_w"] = c.write_bytes

class DiskIOPercent(CustomDataSource):
    _last_val = [0.0] * 10
    def as_numeric(self) -> float:
        _update_disk_io()
        pct = _dio_state["pct"]
        DiskIOPercent._last_val.append(pct)
        DiskIOPercent._last_val.pop(0)
        return pct
    def as_string(self) -> str:
        _update_disk_io()
        return f"{_dio_state['pct']:.0f}%"
    def last_values(self):
        return DiskIOPercent._last_val
''')
    print("Adding: DiskIOPercent")

if "DayProgressPercent" not in src:
    classes.append('''
# ---------------------------------------------------------------------------
# DayProgressPercent — current time as % of 24h (midnight=0, 23:59=~100)
# ---------------------------------------------------------------------------
import datetime as _datetime

class DayProgressPercent(CustomDataSource):
    _last_val = [0.0] * 10
    def as_numeric(self) -> float:
        now = _datetime.datetime.now()
        pct = round((now.hour * 3600 + now.minute * 60 + now.second) / 864, 1)
        DayProgressPercent._last_val.append(pct)
        DayProgressPercent._last_val.pop(0)
        return pct
    def as_string(self) -> str:
        return ""
    def last_values(self):
        return DayProgressPercent._last_val
''')
    print("Adding: DayProgressPercent")

if "NetUploadMbps" not in src:
    classes.append('''
# ---------------------------------------------------------------------------
# NetUploadMbps / NetDownloadMbps — network speed as % of max
# ---------------------------------------------------------------------------
_NET_MAX_MBP = 100.0
_net_state = {"last_t": 0.0, "last_sent": 0, "last_recv": 0, "up_pct": 0.0, "dn_pct": 0.0}

def _update_net():
    now = _time_mod.time()
    if now - _net_state["last_t"] < 0.8:
        return
    c = _psutil_mod.net_io_counters()
    dt = now - _net_state["last_t"]
    if _net_state["last_t"] > 0 and dt > 0:
        up_mbps = (c.bytes_sent - _net_state["last_sent"]) * 8 / (dt * 1e6)
        dn_mbps = (c.bytes_recv - _net_state["last_recv"]) * 8 / (dt * 1e6)
        _net_state["up_pct"] = min(100.0, up_mbps / _NET_MAX_MBP * 100)
        _net_state["dn_pct"] = min(100.0, dn_mbps / _NET_MAX_MBP * 100)
    _net_state["last_t"] = now
    _net_state["last_sent"] = c.bytes_sent
    _net_state["last_recv"] = c.bytes_recv

def _fmt_mbps(mbps):
    if mbps >= 1.0: return f"{mbps:.1f}M"
    return f"{int(mbps * 1000):3d}K"

class NetUploadMbps(CustomDataSource):
    _last_val = [0.0] * 10
    def as_numeric(self) -> float:
        _update_net()
        pct = _net_state["up_pct"]
        NetUploadMbps._last_val.append(pct)
        NetUploadMbps._last_val.pop(0)
        return pct
    def as_string(self) -> str:
        _update_net()
        return _fmt_mbps(_net_state["up_pct"] / 100.0 * _NET_MAX_MBP)
    def last_values(self):
        return NetUploadMbps._last_val

class NetDownloadMbps(CustomDataSource):
    _last_val = [0.0] * 10
    def as_numeric(self) -> float:
        _update_net()
        pct = _net_state["dn_pct"]
        NetDownloadMbps._last_val.append(pct)
        NetDownloadMbps._last_val.pop(0)
        return pct
    def as_string(self) -> str:
        _update_net()
        return _fmt_mbps(_net_state["dn_pct"] / 100.0 * _NET_MAX_MBP)
    def last_values(self):
        return NetDownloadMbps._last_val
''')
    print("Adding: NetUploadMbps + NetDownloadMbps")

if classes:
    with open(path, 'w') as f:
        f.write(src.rstrip() + '\n' + '\n'.join(classes))
    print(f"Saved {len(classes)} custom sensor class(es)")
else:
    print("All custom sensors already present")
ENDCUSTOM
        log_success "Custom sensors patched"
    else
        log_warning "sensors_custom.py not found — skipping custom sensors"
    fi
}

run_install_steps() {
    echo ""
    install_packages
    echo ""
    setup_usb_permissions
    echo ""
    clone_repository
    echo ""
    create_custom_scripts
    echo ""
    patch_themes
    echo ""
    generate_custom_themes
    echo ""
    create_containerfile
    echo ""
    build_container
    echo ""
    # If PiSuite5 background wasn't generated on host (no PIL), do it now inside the freshly built container
    if [ ! -f "$INSTALL_DIR/res/themes/PiSuite5/background.png" ]; then
        log_info "Generating PiSuite5 background inside container..."
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        for gen_script in gen_pi_bg_5inch.py gen_pi_theme_5inch.py gen_vortex_bg_5inch.py gen_vortex_theme_5inch_minimal.py; do
            [ -f "$SCRIPT_DIR/$gen_script" ] && cp "$SCRIPT_DIR/$gen_script" "$INSTALL_DIR/$gen_script"
        done
        podman run --rm \
            -v "$INSTALL_DIR:/app:z" \
            --entrypoint python3 \
            "$IMAGE_NAME" /app/gen_pi_bg_5inch.py 2>/dev/null && \
        podman run --rm \
            -v "$INSTALL_DIR:/app:z" \
            --entrypoint python3 \
            "$IMAGE_NAME" /app/gen_pi_theme_5inch.py 2>/dev/null && \
        log_success "PiSuite5 theme generated" || \
        log_warning "PiSuite5 generation failed — run manually: podman exec turing-display python3 /app/gen_pi_bg_5inch.py"
    fi
    # Generate Vortex theme inside container if not done on host
    if [ ! -f "$INSTALL_DIR/res/themes/PiSuite5/background.png" ] || [ -f "$INSTALL_DIR/gen_vortex_bg_5inch.py" ]; then
        if [ ! -f "$INSTALL_DIR/res/themes/PiSuite5/background_vortex_done" ]; then
            podman run --rm \
                -v "$INSTALL_DIR:/app:z" \
                --entrypoint python3 \
                "$IMAGE_NAME" /app/gen_vortex_bg_5inch.py 2>/dev/null && \
            podman run --rm \
                -v "$INSTALL_DIR:/app:z" \
                --entrypoint python3 \
                "$IMAGE_NAME" /app/gen_vortex_theme_5inch_minimal.py 2>/dev/null && \
            log_success "Vortex theme generated inside container" || \
            log_warning "Vortex theme generation failed"
        fi
    fi
    echo ""
    create_management_script
    echo ""
    configure_yaml
    echo ""
    setup_shell_aliases
    echo ""
    setup_autostart
    echo ""
    setup_desktop_integration
    echo ""
    setup_additional_screens
    echo ""
    verify_installation

    echo ""
    echo "========================================="
    echo ""
    log_info "Next steps:"
    echo ""
    echo "  1. Connect your Turing Smart Screen via USB"
    echo ""
    echo "  2. Configure the display (opens GUI):"
    echo "     cd $INSTALL_DIR && ./turing.sh config"
    echo ""
    echo "  3. Start the display:"
    echo "     ./turing.sh start   (or just: ts)"
    echo ""
    echo "  4. Reload shell aliases:"
    echo "     - fish:      source ~/.config/fish/conf.d/turing.fish"
    echo "     - bash/zsh:  source ~/.bashrc"
    echo ""
    echo "     ts / tsstart      - start display"
    echo "     tsstop            - stop display"
    echo "     tslogs            - view live logs"
    echo "     tstheme           - show current theme"
    echo "     tsswitch <name>   - switch theme"
    echo "     tslist            - interactive theme picker"
    echo "     tsconfig          - open configurator GUI"
    echo "     tsnext / tsprev   - next/prev theme in suite"
    echo ""
    echo "  5. Autostart: display starts on login, stops on logout/sleep/suspend"
    echo "     systemctl --user status turing-display"
    echo ""
    echo "  6. App launcher: search 'Turing Display' in KDE/GNOME"
    echo ""

    SERIAL_GROUP="dialout"
    case "$OS_ID" in
        "cachyos"|"arch"|"manjaro") SERIAL_GROUP="uucp" ;;
    esac
    if ! groups "$USER" | grep -q "$SERIAL_GROUP"; then
        echo ""
        log_warning "IMPORTANT: Log out and back in for '$SERIAL_GROUP' group to take effect."
    fi
    echo ""
}

main() {
    echo "========================================="
    echo "  Turing Smart Screen Installer v1.0"
    echo "========================================="
    echo ""

    check_root
    detect_os
    detect_existing_install

    # Show connected screens
    echo ""
    log_info "Scanning for connected Turing screens..."
    detect_screens
    if [ ${#SCREEN_LIST[@]} -eq 0 ]; then
        log_warning "No Turing screens detected via USB right now"
        log_info "(You can still install — plug in the screen before first run)"
    else
        log_info "Found ${#SCREEN_LIST[@]} Turing screen(s):"
        local IDX=0
        for entry in "${SCREEN_LIST[@]}"; do
            local DEV="${entry%%:*}"
            local REST="${entry#*:}"
            local SERIAL="${REST%%:*}"
            local PRODUCT="${REST##*:}"
            IDX=$((IDX + 1))
            if product_is_supported "$PRODUCT"; then
                local SIZE; SIZE=$(product_to_size "$PRODUCT")
                echo "  Screen $IDX: $DEV  serial=$SERIAL  size=$SIZE  [SUPPORTED]"
            else
                echo "  Screen $IDX: $DEV  serial=$SERIAL  product=$PRODUCT  [NOT SUPPORTED YET]"
            fi
        done
    fi

    echo ""

    # Show current install status and present menu
    if $INSTALL_EXISTS || $IMAGE_EXISTS || $CONTAINER_EXISTS; then
        log_info "Existing installation detected:"
        $INSTALL_EXISTS   && echo "  Install dir : $INSTALL_DIR"
        $IMAGE_EXISTS     && echo "  Image       : $IMAGE_NAME"
        $CONTAINER_EXISTS && echo "  Container(s): $(podman ps -a --format '{{.Names}}' 2>/dev/null | grep '^turing-display' | tr '\n' ' ')"
        echo ""
        echo "What would you like to do?"
        echo ""
        echo "  1) Reinstall  — wipe everything and install fresh"
        echo "  2) Uninstall  — remove everything, keep nothing"
        echo "  3) Cancel"
        echo ""
        read -p "Choice [1/2/3]: " -n 1 -r; echo
        echo ""
        case "$REPLY" in
            1)
                log_info "Reinstalling..."
                backup_custom_themes
                do_wipe
                echo ""
                log_info "Starting fresh install..."
                run_install_steps
                restore_custom_themes
                ;;
            2)
                log_warning "This will remove all Turing containers, images, services, aliases and files."
                read -p "Are you sure? (y/N): " -n 1 -r; echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    backup_custom_themes
                    do_wipe
                    log_success "Uninstall complete."
                else
                    log_info "Cancelled."
                fi
                ;;
            *)
                log_info "Cancelled."
                exit 0
                ;;
        esac
    else
        log_info "No existing installation found — running fresh install."
        echo ""
        log_info "This will:"
        log_info "  1. Install required system packages"
        log_info "  2. Setup USB permissions + udev rules"
        log_info "  3. Clone the Turing repository"
        log_info "  4. Patch configure.py, sensors_python.py, stats.py"
        log_info "  5. Build the container image"
        log_info "  6. Create turing.sh management script"
        log_info "  7. Setup shell aliases (bash/zsh/fish)"
        log_info "  8. Setup autostart (systemd user service)"
        log_info "  9. Create desktop app launcher entries"
        log_info " 10. Setup additional screens (if multiple detected)"
        log_info " 11. Verify installation"
        echo ""
        log_info "Installation directory: $INSTALL_DIR"
        echo ""
        read -p "Continue? (y/N): " -n 1 -r; echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Cancelled."
            exit 0
        fi
        run_install_steps
    fi
}

main "$@"
