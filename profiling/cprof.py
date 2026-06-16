#!/usr/bin/env python3
"""
cprof — like mprof, but tracks both Memory (RSS) and CPU % over time.
Tracks the full process tree (parent + all children).
Works on Linux, macOS, and Windows.

File format: one line per sample
    MEM <timestamp> <elapsed> <mem_mb>
    CPU <timestamp> <elapsed> <cpu_pct>
    CMD <command string>

Usage:
    cprof run <command> [args...]     # run and record
    cprof plot [<output.dat>]         # plot last (or given) recording
    cprof list                        # list recordings
    cprof clean                       # delete all recordings
"""

import sys
import os
import subprocess
import time
import glob
from datetime import datetime

WINDOWS = sys.platform == "win32"

if not WINDOWS:
    import signal

try:
    import psutil
except ImportError:
    print("psutil is required: pip install psutil")
    sys.exit(1)


SAMPLE_INTERVAL = 0.1   # seconds between samples
DAT_PREFIX      = "cprof_"


# ── CPU time delta tracking ───────────────────────────────────────────────────

def _cpu_times_total(p):
    """Return user+system CPU time for a process (seconds)."""
    t = p.cpu_times()
    return t.user + t.system


def _compute_cpu_pct(pid, now_cpu, now_wall, cpu_time_cache, wall_time_cache):
    """
    Returns CPU % for a PID given current and previous CPU/wall times.
    Returns 0.0 on the first call for a PID (no delta yet).
    """
    if pid not in cpu_time_cache:
        cpu_time_cache[pid]  = now_cpu
        wall_time_cache[pid] = now_wall
        return 0.0

    delta_cpu  = now_cpu  - cpu_time_cache[pid]
    delta_wall = now_wall - wall_time_cache[pid]
    cpu_time_cache[pid]  = now_cpu
    wall_time_cache[pid] = now_wall

    if delta_wall < 1e-6:
        return 0.0
    return round((delta_cpu / delta_wall) * 100.0, 2)


# ── helpers ───────────────────────────────────────────────────────────────────

_PROC_ERRORS = (psutil.NoSuchProcess, psutil.AccessDenied)
if not WINDOWS:
    _PROC_ERRORS = (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess)


def get_full_usage(parent, proc_cache, cpu_time_cache, wall_time_cache):
    """Sum RSS (MB) and CPU % across the full process tree."""
    try:
        children     = parent.children(recursive=True)
        current_tree = [parent] + children
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None, None

    total_mem    = 0.0
    total_cpu    = 0.0
    current_pids = set()
    now_wall     = time.perf_counter()

    for p in current_tree:
        try:
            with p.oneshot():
                pid     = p.pid
                mem     = p.memory_info().rss   # RSS — same metric as /usr/bin/time
                now_cpu = _cpu_times_total(p)

            current_pids.add(pid)
            proc_cache[pid] = p
            total_mem += mem
            total_cpu += _compute_cpu_pct(
                pid, now_cpu, now_wall, cpu_time_cache, wall_time_cache
            )

        except _PROC_ERRORS:
            continue

    dead = set(proc_cache.keys()) - current_pids
    for pid in dead:
        proc_cache.pop(pid, None)
        cpu_time_cache.pop(pid, None)
        wall_time_cache.pop(pid, None)

    return total_mem / (1000 * 1000), total_cpu


def _kill_tree(proc):
    """Terminate the entire process tree, cross-platform."""
    if WINDOWS:
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except Exception:
            proc.kill()
    else:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


def _popen(command):
    """Launch command with the right process-group flags for each OS."""
    if WINDOWS:
        return subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    else:
        return subprocess.Popen(command, start_new_session=True)


# ── file format ───────────────────────────────────────────────────────────────
#
# Plain text, one line per event — same philosophy as mprof:
#
#   CMD ./spinner 10 4
#   MEM 1700000000.123 0.100 45.2
#   CPU 1700000000.123 0.100 387.5
#   MEM 1700000000.223 0.200 45.3
#   CPU 1700000000.223 0.200 390.1
#   ...
#
# timestamp = Unix time (for wall-clock reference)
# elapsed   = seconds since process start (for plotting)
# Appending one MEM+CPU pair per sample means the file is always
# readable mid-run — just like mprof.

def _write_header(f, command):
    f.write(f"CMD {' '.join(command)}\n")
    f.flush()


def _write_sample(f, elapsed, mem_mb, cpu_pct):
    ts = time.time()
    f.write(f"MEM {ts:.3f} {elapsed:.3f} {mem_mb:.3f}\n")
    f.write(f"CPU {ts:.3f} {elapsed:.3f} {cpu_pct:.2f}\n")
    f.flush()   # ensure it's on disk immediately — same as mprof


def _read_dat(dat_file):
    """Parse a .dat file, return (command, samples) where
    samples = list of (elapsed, mem_mb, cpu_pct)."""
    command = []
    mem_map = {}   # elapsed -> mem_mb
    cpu_map = {}   # elapsed -> cpu_pct

    with open(dat_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if parts[0] == "CMD":
                command = parts[1:]
            elif parts[0] == "MEM" and len(parts) == 4:
                elapsed = float(parts[2])
                mem_map[elapsed] = float(parts[3])
            elif parts[0] == "CPU" and len(parts) == 4:
                elapsed = float(parts[2])
                cpu_map[elapsed] = float(parts[3])

    # Pair up MEM and CPU by elapsed time
    all_elapsed = sorted(set(mem_map) & set(cpu_map))
    samples = [(e, mem_map[e], cpu_map[e]) for e in all_elapsed]
    return command, samples


# ── run ───────────────────────────────────────────────────────────────────────

def cmd_run(command):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dat_file  = f"{DAT_PREFIX}{timestamp}.dat"

    print(f"[cprof] Recording to {dat_file}")
    print(f"[cprof] Running: {' '.join(command)}\n")

    try:
        proc = _popen(command)
    except FileNotFoundError:
        print(f"[cprof] Command not found: {command[0]}")
        sys.exit(1)
    except PermissionError:
        print(f"[cprof] Permission denied: {command[0]}")
        sys.exit(1)

    time.sleep(0.01)   # let the OS register the PID

    proc_cache      = {}
    cpu_time_cache  = {}
    wall_time_cache = {}
    sample_count    = 0

    try:
        ps = psutil.Process(proc.pid)
    except psutil.NoSuchProcess:
        proc.wait()
        print("[cprof] Process ended before profiling could start.")
        return

    with open(dat_file, "w", buffering=1) as f:   # line-buffered
        _write_header(f, command)

        t0          = time.perf_counter()
        next_sample = t0

        try:
            while proc.poll() is None:
                mem_mb, cpu = get_full_usage(ps, proc_cache, cpu_time_cache, wall_time_cache)
                if mem_mb is not None:
                    elapsed = round(time.perf_counter() - t0, 3)
                    _write_sample(f, elapsed, mem_mb, cpu)
                    sample_count += 1

                # Drift-corrected sleep
                next_sample += SAMPLE_INTERVAL
                sleep_for = next_sample - time.perf_counter()
                if sleep_for <= 0:
                    next_sample = time.perf_counter()
                    sleep_for   = 0.0
                time.sleep(sleep_for)

        except KeyboardInterrupt:
            print("\n[cprof] Interrupted — terminating process tree and saving data...")
            _kill_tree(proc)

        # Final sample
        mem_mb, cpu = get_full_usage(ps, proc_cache, cpu_time_cache, wall_time_cache)
        if mem_mb is not None:
            elapsed = round(time.perf_counter() - t0, 3)
            _write_sample(f, elapsed, mem_mb, cpu)
            sample_count += 1

    proc.wait()
    total = round(time.perf_counter() - t0, 2)
    print(f"\n[cprof] Finished in {total}s — {sample_count} samples in {dat_file}")
    print(f"[cprof] Plot with: python cprof.py plot {dat_file}")


# ── plot ──────────────────────────────────────────────────────────────────────

def cmd_plot(dat_file=None):
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec

    if dat_file is None:
        files = sorted(glob.glob(f"{DAT_PREFIX}*.dat"))
        if not files:
            print("No recordings found. Run something first.")
            sys.exit(1)
        dat_file = files[-1]
        print(f"[cprof] Plotting {dat_file}")

    try:
        command, samples = _read_dat(dat_file)
    except OSError as e:
        print(f"[cprof] Could not read {dat_file}: {e}")
        sys.exit(1)
    except (ValueError, IndexError) as e:
        print(f"[cprof] Corrupted data in {dat_file}: {e}")
        sys.exit(1)

    if not samples:
        print("[cprof] No samples in this recording — process may have ended too quickly.")
        return

    times   = [s[0] for s in samples]
    mem_mb  = [s[1] for s in samples]
    cpu_pct = [s[2] for s in samples]
    duration = round(times[-1], 2)

    xmax = max(times) if max(times) > 0 else 0.001

    fig = plt.figure(figsize=(12, 6), layout="constrained")
    fig.suptitle(
        f"cprof — {' '.join(command)}\n({len(samples)} samples over {duration}s)",
        fontsize=11
    )

    gs = gridspec.GridSpec(2, 1, figure=fig)

    # — Memory —
    ax1 = fig.add_subplot(gs[0])
    ax1.plot(times, mem_mb, color="#2196F3", linewidth=1.5, label="Memory RSS (full tree)")
    ax1.fill_between(times, mem_mb, alpha=0.15, color="#2196F3")
    ax1.set_ylabel("Memory (MB)", color="#2196F3")
    ax1.set_xlabel("Time (s)")
    ax1.set_xlim(0, xmax)
    ax1.set_ylim(bottom=0)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc="upper right")
    peak_mem = max(mem_mb)
    ax1.axhline(peak_mem, color="#2196F3", linestyle="--", linewidth=0.8, alpha=0.6)
    ax1.text(0.01, peak_mem, f" peak {peak_mem:.1f} MB",
             va="bottom", color="#2196F3", fontsize=8,
             transform=ax1.get_yaxis_transform())

    # — CPU —
    ax2 = fig.add_subplot(gs[1])
    ax2.plot(times, cpu_pct, color="#F44336", linewidth=1.5, label="CPU % (full tree)")
    ax2.fill_between(times, cpu_pct, alpha=0.15, color="#F44336")
    ax2.set_ylabel("CPU %", color="#F44336")
    ax2.set_xlabel("Time (s)")
    ax2.set_xlim(0, xmax)
    ax2.set_ylim(0, max(10, max(cpu_pct)) * 1.1)
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc="upper right")
    peak_cpu = max(cpu_pct)
    ax2.axhline(peak_cpu, color="#F44336", linestyle="--", linewidth=0.8, alpha=0.6)
    ax2.text(0.01, peak_cpu, f" peak {peak_cpu:.1f}%",
             va="bottom", color="#F44336", fontsize=8,
             transform=ax2.get_yaxis_transform())

    out_png = dat_file.replace(".dat", ".png")
    plt.savefig(out_png, dpi=150, bbox_inches="tight")
    print(f"[cprof] Plot saved to {out_png}")

    try:
        plt.show()
    except Exception:
        print("[cprof] Could not open interactive window — PNG saved above.")


# ── list / clean ──────────────────────────────────────────────────────────────

def cmd_list():
    files = sorted(glob.glob(f"{DAT_PREFIX}*.dat"))
    if not files:
        print("No recordings found.")
        return
    for f in files:
        try:
            command, samples = _read_dat(f)
            duration = round(samples[-1][0], 2) if samples else 0.0
            print(f"  {f}  —  {' '.join(command)}  ({duration}s, {len(samples)} samples)")
        except Exception:
            print(f"  {f}  —  [corrupted]")


def cmd_clean():
    files = glob.glob(f"{DAT_PREFIX}*.dat") + glob.glob(f"{DAT_PREFIX}*.png")
    removed = 0
    for f in files:
        try:
            os.remove(f)
            removed += 1
        except (FileNotFoundError, PermissionError):
            pass
    print(f"[cprof] Removed {removed} file(s).")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    sub = sys.argv[1]

    if sub == "run":
        if len(sys.argv) < 3:
            print("Usage: cprof run <command> [args...]")
            sys.exit(1)
        cmd_run(sys.argv[2:])
    elif sub == "plot":
        cmd_plot(sys.argv[2] if len(sys.argv) > 2 else None)
    elif sub == "list":
        cmd_list()
    elif sub == "clean":
        cmd_clean()
    else:
        print(f"Unknown subcommand: {sub}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()