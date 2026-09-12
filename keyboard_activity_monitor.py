#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
 PRODIGY_CS_04 - Keyboard Activity Monitor
===============================================================================
 An educational, ethical keyboard activity monitoring application built with
 Python's standard library and Tkinter.

 DISCLAIMER / ETHICAL NOTICE
 ---------------------------
 This tool is intended STRICTLY for educational purposes and self-monitoring.
 It captures key presses ONLY while the application's own Tkinter window has
 keyboard focus. It does NOT:
     - Monitor the system globally or in the background
     - Capture keystrokes in other applications
     - Send any data anywhere
     - Use pynput, keyboard, or any third-party monitoring library

 Please use responsibly and only on your own machine for learning purposes.

 Task    : PRODIGY_CS_04
 Platform: Windows / Linux / macOS (cross-platform via Tkinter)
 Dependencies: standard library only
===============================================================================
"""

# ---------------------------------------------------------------------------
# Standard library imports (cross-platform, no third-party dependencies)
# ---------------------------------------------------------------------------
import os                 # Working with file paths and the current directory
import datetime           # Generating timestamps for key-press events
import tkinter as tk      # Base Tkinter toolkit (GUI framework)
from tkinter import ttk   # Themed Tkinter widgets (modern look)
from tkinter import messagebox  # User-friendly message dialogs
from tkinter import filedialog  # Native save/open file dialogs
from tkinter import scrolledtext  # Auto-scrolling multi-line text widget

# ---------------------------------------------------------------------------
# Constants and configuration
# ---------------------------------------------------------------------------
APP_TITLE = "PRODIGY_CS_04 - Keyboard Activity Monitor"
LOG_FILENAME = "activity_log.txt"      # Default log file written by the app
AUTO_FLUSH_THRESHOLD = 200             # In-memory events before auto-save


class ActivityLog:
    """
    Handles the persistence of keyboard activity events.

    Responsibilities:
        - Accumulate key-press events in memory
        - Flush them to a plain-text log file (activity_log.txt)
        - Build formatted snapshots used by the Export Log feature
    """

    def __init__(self):
        """Initialise an empty in-memory list of events."""
        # Each event is a dictionary:
        #   {"sequence": 1, "timestamp": "...", "key": "a"}
        self._events = []

    # -- Public API ----------------------------------------------------------

    def add_event(self, key_label, timestamp):
        """Append a new key event to the in-memory store.

        Args:
            key_label (str): Human-readable name of the pressed key.
            timestamp (datetime.datetime): Exact moment the key was pressed.
        """
        sequence = len(self._events) + 1
        self._events.append(
            {
                "sequence": sequence,
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                "key": key_label,
            }
        )

    def clear(self):
        """Remove all recorded events from memory."""
        self._events.clear()

    @property
    def count(self):
        """Return the total number of captured key events."""
        return len(self._events)

    @property
    def events(self):
        """Return a read-only, ordered view of the captured events."""
        return tuple(self._events)

    # -- File helpers --------------------------------------------------------

    def save(self, filename):
        """Append buffered events to the given log file, then reset memory.

        The newest events are written first so a fresh session always shows
        the latest activity at the top of the live view on re-launch.
        """
        with open(filename, "a", encoding="utf-8") as handle:
            for event in reversed(self._events):
                handle.write(self._format_event(event) + "\n")
        self._events.clear()

    def snapshot_text(self):
        """Return a complete, formatted snapshot of ALL events.

        Used by the Export Log feature to produce a self-contained report.
        """
        text = self.header_text()
        for event in self._events:
            text += self._format_event(event) + "\n"
        return text

    # -- Formatting helpers --------------------------------------------------

    @staticmethod
    def _format_event(event):
        """Format a single event dictionary as a plain-text log line."""
        return f"[{event['timestamp']}]  #{event['sequence']:>5}  {event['key']}"

    def header_text(self):
        """Return a descriptive header block for the exported log file."""
        generated_on = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            "=" * 62,
            " PRODIGY_CS_04 - Keyboard Activity Monitor - Export",
            f" Generated on: {generated_on}",
            f" Total events : {self.count}",
            "=" * 62,
            "",
            " #       Timestamp                      Key",
            " ----    ----------------------------   -------------------",
        ]
        return "\n".join(lines) + "\n"


class ActivityMonitor:
    """
    Core application class (Tkinter window + logic).

    Manages the GUI, binds key events, updates the live display and
    coordinates the ActivityLog object.
    """

    def __init__(self, root):
        """Set up the window, widgets, theme, and key bindings.

        Args:
            root (tk.Tk): The root Tkinter window.
        """
        self.root = root
        self.log = ActivityLog()

        # Application state flags -------------------------------------------
        self.logging_active = False   # Whether key logging is currently on
        self._held_chars = set()      # Chars currently held (auto-repeat guard)

        self._configure_window()
        self._build_style()
        self._build_banner()
        self._build_status_bar()
        self._build_log_view()
        self._build_controls()

        # Capture key events ONLY while THIS window has focus ----------------
        self.root.bind("<KeyPress>", self._on_key_press)
        self.root.bind("<KeyRelease>", self._on_key_release)
        self.root.bind("<FocusOut>", self._on_focus_out)

        # Graceful shutdown: flush buffered events before closing ------------
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ======================================================================
    #  GUI construction
    # ======================================================================

    def _configure_window(self):
        """Set the window title/size, centre it, and configure the grid."""
        self.root.title(APP_TITLE)
        self.root.geometry("760x560")
        self.root.minsize(640, 480)
        self.root.configure(bg="#1e1e2e")          # Dracula-style dark bg
        self.root.grid_rowconfigure(2, weight=1)   # Log area expands
        self.root.grid_columnconfigure(0, weight=1)

        # Centre the window on the user's screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _build_style(self):
        """Configure a modern themed style for all standard widgets."""
        style = ttk.Style()

        # Pick the closest modern theme available on this platform.
        # 'clam' is bundled with Tk and looks clean on all OSes.
        for theme in ("clam", "alt", "default", "classic"):
            if theme in style.theme_names():
                style.theme_use(theme)
                break

        style.configure("TFrame", background="#1e1e2e", foreground="#cdd6f4")
        style.configure(
            "Banner.TLabel",
            background="#1e1e2e",
            foreground="#89b4fa",
            font=("Segoe UI", 16, "bold"),
        )
        style.configure(
            "Sub.TLabel",
            background="#1e1e2e",
            foreground="#a6adc8",
            font=("Segoe UI", 10),
        )
        style.configure(
            "TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 6),
            background="#313244",
            foreground="#cdd6f4",
        )
        style.map(
            "TButton",
            background=[("active", "#45475a")],
            foreground=[("disabled", "#585b70")],
        )
        style.configure(
            "Status.TLabel",
            background="#1e1e2e",
            foreground="#f38ba8",
            font=("Consolas", 10, "bold"),
        )

    def _build_banner(self):
        """Render the professional banner + subtitle at the top of the GUI."""
        banner_frame = ttk.Frame(self.root, padding=(20, 16, 20, 8))
        banner_frame.grid(row=0, column=0, sticky="ew")
        banner_frame.grid_columnconfigure(0, weight=1)

        ttk.Label(
            banner_frame, text=APP_TITLE, style="Banner.TLabel", anchor="center"
        ).grid(row=0, column=0, sticky="ew")

        ttk.Label(
            banner_frame,
            text="Educational key monitoring — restrained to this window only. "
                 "Logs are saved locally to activity_log.txt.",
            style="Sub.TLabel",
            anchor="center",
            wraplength=700,
        ).grid(row=1, column=0, sticky="ew", pady=(2, 0))

    def _build_status_bar(self):
        """Build a status row showing logging state and total key count."""
        status = ttk.Frame(self.root, padding=(20, 4, 20, 4))
        status.grid(row=1, column=0, sticky="ew")

        self.status_label = ttk.Label(
            status, text="●  Logging: OFF", style="Status.TLabel"
        )
        self.status_label.grid(row=0, column=0, sticky="w")

        self.counter_label = ttk.Label(
            status, text="Keys pressed: 0", style="Status.TLabel",
            foreground="#f9e2af",
        )
        self.counter_label.grid(row=0, column=1, sticky="e")

        ttk.Separator(self.root, orient="horizontal").grid(  # divider line
            row=2, column=0, sticky="ew"
        )

    def _build_log_view(self):
        """Build the scrolling, read-only log display."""
        log_frame = ttk.Frame(self.root, padding=(20, 10, 20, 6))
        log_frame.grid(row=3, column=0, sticky="nsew")
        self.root.grid_rowconfigure(3, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        # Read-only, automatically scrolling text area for live events
        self.log_view = scrolledtext.ScrolledText(
            log_frame,
            state="disabled",
            wrap="none",
            bg="#11111b",
            fg="#cdd6f4",
            insertbackground="#89b4fa",
            font=("Consolas", 10),
            relief="flat",
            bd=0,
            padx=10,
            pady=10,
        )
        self.log_view.grid(row=0, column=0, sticky="nsew")

        # Horizontal scrollbar for very wide lines
        hbar = ttk.Scrollbar(
            log_frame, orient="horizontal", command=self.log_view.xview
        )
        self.log_view.configure(xscrollcommand=hbar.set)
        hbar.grid(row=1, column=0, sticky="ew")

    def _build_controls(self):
        """Build the control buttons row (Start/Stop/Clear/Export)."""
        controls = ttk.Frame(self.root, padding=(20, 8, 20, 16))
        controls.grid(row=4, column=0, sticky="ew")

        self.btn_start = ttk.Button(
            controls, text="▶  Start Logging", command=self.start_logging
        )
        self.btn_start.pack(side="left", padx=(0, 8))

        self.btn_stop = ttk.Button(
            controls, text="⏹  Stop Logging", command=self.stop_logging,
            state="disabled",
        )
        self.btn_stop.pack(side="left", padx=(0, 8))

        self.btn_clear = ttk.Button(
            controls, text="🗑  Clear Log", command=self.clear_log
        )
        self.btn_clear.pack(side="left", padx=(0, 8))

        self.btn_export = ttk.Button(
            controls, text="📤  Export Log", command=self.export_log
        )
        self.btn_export.pack(side="right")

    # ======================================================================
    #  Key event handling (application-local only)
    # ======================================================================

    def _on_key_press(self, event):
        """Handle a single key press INSIDE the application window.

        Printable characters are logged by their literal value (spaces are
        shown as <space> for readability). Special and modifier keys are
        logged by their symbolic name, e.g. <Return>, <Shift_L>, <Tab>.

        A set of currently-held characters (`_held_chars`) prevents the same
        key from being logged again when auto-repeat fires while held.
        """
        if not self.logging_active:
            return

        now = datetime.datetime.now()

        # --- Printable characters --------------------------------------------
        if event.char and event.char != "" and event.char.isprintable():
            if event.char in self._held_chars:
                return          # auto-repeat of an already-held key: skip it
            self._held_chars.add(event.char)
            label = "<space>" if event.char == " " else event.char
            self.record_key(label, now)
            return

        # --- Special / modifier keys -----------------------------------------
        self.record_key(f"<{event.keysym}>", now)

    def _on_key_release(self, event):
        """Remove released characters from the held-key set.

        Removing a character on release means the next physical press of that
        key is treated as a brand-new event (no auto-repeat flood).
        """
        if event.char and event.char != "" and event.char.isprintable():
            self._held_chars.discard(event.char)
        # Special keys emit a single event per press and need no release logic.

    def _on_focus_out(self, _event):
        """Reset held-key state when the window loses focus.

        This guarantees no activity is ever attributed to a key that is still
        physically held down after the window loses focus.
        """
        self._held_chars.clear()

    def record_key(self, key_label, timestamp):
        """Store one key event in the log and refresh the GUI.

        Args:
            key_label (str): Human-readable key name.
            timestamp (datetime.datetime): When the event occurred.
        """
        self.log.add_event(key_label, timestamp)
        line = ActivityLog._format_event(self.log.events[-1])
        self._append_line(line)
        self._update_counters()
        self._auto_save_if_needed()

    def _append_line(self, line):
        """Append a single line of text to the live, read-only log view."""
        self.log_view.configure(state="normal")
        self.log_view.insert("end", line + "\n")
        self.log_view.configure(state="disabled")
        self.log_view.see("end")   # Always keep the newest entry in view

    def _update_counters(self):
        """Refresh the status labels to reflect current state."""
        self.counter_label.configure(text=f"Keys pressed: {self.log.count}")

    # ======================================================================
    #  Logging lifecycle: start / stop / clear / export
    # ======================================================================

    def start_logging(self):
        """Enable keystroke capture within the application window."""
        self.logging_active = True
        self._held_chars.clear()
        self._set_status("●  Logging: ON", "#a6e3a1")
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.btn_clear.configure(state="disabled")
        self.btn_export.configure(state="disabled")
        self.root.focus_force()   # Ensure keys arrive at this window

    def stop_logging(self):
        """Disable keystroke capture and flush events to the log file."""
        self.logging_active = False
        self._held_chars.clear()
        self._set_status("●  Logging: OFF", "#f38ba8")
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.btn_clear.configure(state="normal")
        self.btn_export.configure(state="normal")
        self._flush_log()

    def clear_log(self):
        """Clear the in-memory log and the visible log view."""
        self.log.clear()
        self.log_view.configure(state="normal")
        self.log_view.delete("1.0", "end")
        self.log_view.configure(state="disabled")
        self._update_counters()

    def export_log(self):
        """
        Export a complete snapshot of the current log to a user-chosen file.

        Uses the native save dialog so the file lands where the user wants.
        """
        target = filedialog.asksaveasfilename(
            title="Export Activity Log",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not target:
            return                  # user cancelled the dialog

        try:
            with open(target, "w", encoding="utf-8") as handle:
                handle.write(self.log.snapshot_text())
        except OSError as exc:
            self._show_error(f"Could not write export file:\n{exc}")
            return

        messagebox.showinfo(
            "Export Complete",
            f"Log exported successfully.\n\n{self.log.count} event(s) "
            f"written to:\n{target}",
        )

    # ======================================================================
    #  File helpers & utilities
    # ======================================================================

    def _flush_log(self):
        """Write buffered events to activity_log.txt (if any)."""
        if self.log.count == 0:
            return
        try:
            count = self.log.count
            self.log.save(LOG_FILENAME)
            self._set_status(
                f"●  Saved {count} event(s) → {LOG_FILENAME}", "#89b4fa"
            )
        except OSError as exc:
            self._show_error(f"Could not write log file:\n{exc}")

    def _auto_save_if_needed(self):
        """Safety net: periodically flush large buffers to disk.

        Prevents losing data if the application crashes or is closed while
        many events are still only in memory.
        """
        if self.log.count >= AUTO_FLUSH_THRESHOLD:
            self._flush_log()

    def on_close(self):
        """Window close handler — flush any buffered events, then quit."""
        try:
            self._flush_log()
        finally:
            self.root.destroy()

    # -- Small helpers ------------------------------------------------------

    def _set_status(self, text, color):
        """Update the status bar with a message and colour."""
        self.status_label.configure(text=text, foreground=color)

    def _show_error(self, message):
        """Display a friendly, non-blocking error dialog."""
        messagebox.showerror("Keyboard Activity Monitor - Error", message)


# ---------------------------------------------------------------------------
# Application entry point
# ---------------------------------------------------------------------------
def main():
    """
    Launch the Keyboard Activity Monitor application.

    Creates the root window, instantiates the monitor class, and hands
    control over to Tkinter's main event loop.
    """
    try:
        root = tk.Tk()
        app = ActivityMonitor(root)
        root.mainloop()
    except tk.TclError as exc:
        # No display available (e.g. headless server): report cleanly.
        print("Error: Unable to initialise the graphical window.")
        print(f"Tkinter error: {exc}")
        print(
            "Run this from a desktop session with a working graphical "
            "environment (and Tkinter installed for your Python)."
        )
        raise SystemExit(1)
    except Exception as exc:  # noqa: BLE001 - top-level safety net
        print("An unexpected error occurred:", exc)
        raise


if __name__ == "__main__":
    main()