import io
import os
import queue
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, ttk

from eight_towers.errors import Crash
from eight_towers.machine import Machine
from eight_towers.syntax import Operation, Program

class InputBuffer:
    """Thread-safe interactive input stream."""

    def __init__(self):
        self.queue = queue.Queue()
        self.closed = False

    def add(self, data):
        if self.closed:
            return

        for byte in data:
            self.queue.put(byte)

    def read(self, size=1):
        if size != 1:
            raise ValueError("8 Towers input reads exactly one byte")

        value = self.queue.get()

        if value is None:
            return b""

        return bytes([value])

    def close(self):
        if not self.closed:
            self.closed = True
            self.queue.put(None)


class OutputBuffer(io.BytesIO):
    """Output stream used by the GUI."""


class TowerCanvas(tk.Canvas):
    """Displays the towers in the current realm."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            background="#111111",
            highlightthickness=0,
            **kwargs,
        )

        self.towers = []
        self.pointer = 0

        self.bind(
            "<Configure>",
            lambda event: self.redraw(),
        )

    def redraw(self):
        self.draw(self.towers, self.pointer)

    def draw(self, towers, pointer=0):
        self.towers = list(towers)
        self.pointer = pointer

        self.delete("all")

        width = max(self.winfo_width(), 500)
        height = max(self.winfo_height(), 250)

        if not towers:
            self.create_text(
                width / 2,
                height / 2,
                text="No machine running",
                fill="#888888",
                font=("TkDefaultFont", 12),
            )
            return

        spacing = width / len(towers)
        zero_y = height / 2

        for index, tower in enumerate(towers):
            value = tower.value
            x = spacing * index + spacing / 2

            if index == pointer:
                self.create_rectangle(
                    x - spacing / 2 + 5,
                    10,
                    x + spacing / 2 - 5,
                    height - 10,
                    outline="#f0c674",
                    width=2,
                )

            self.create_text(
                x,
                25,
                text=f"T{index}",
                fill="#ffffff",
                font=("TkDefaultFont", 11, "bold"),
            )

            self.create_line(
                x,
                50,
                x,
                height - 50,
                fill="#444444",
                width=2,
            )

            self.create_line(
                x - 20,
                zero_y,
                x + 20,
                zero_y,
                fill="#555555",
            )

            normalized = (value + 128) / 255

            y = (
                height - 60
                - normalized * (height - 110)
            )

            color = (
                "#61afef"
                if value >= 0
                else "#e06c75"
            )

            self.create_oval(
                x - 8,
                y - 8,
                x + 8,
                y + 8,
                fill=color,
                outline="",
            )

            self.create_text(
                x,
                height - 25,
                text=str(value),
                fill="#dddddd",
                font=("TkDefaultFont", 11),
            )


class FindReplaceDialog(tk.Toplevel):
    """Find/replace dialog attached to the main GUI."""

    def __init__(self, gui):
        super().__init__(gui.root)

        self.gui = gui

        self.title("Find / Replace")
        self.resizable(False, False)

        self.transient(gui.root)

        self.find_var = tk.StringVar()
        self.replace_var = tk.StringVar()
        self.ignore_case_var = tk.BooleanVar(value=False)

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="Find:",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=4,
        )

        self.find_entry = ttk.Entry(
            frame,
            textvariable=self.find_var,
            width=40,
        )

        self.find_entry.grid(
            row=0,
            column=1,
            columnspan=2,
            sticky="ew",
            pady=4,
        )

        ttk.Label(
            frame,
            text="Replace:",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=4,
        )

        self.replace_entry = ttk.Entry(
            frame,
            textvariable=self.replace_var,
            width=40,
        )

        self.replace_entry.grid(
            row=1,
            column=1,
            columnspan=2,
            sticky="ew",
            pady=4,
        )

        ttk.Checkbutton(
            frame,
            text="Ignore case",
            variable=self.ignore_case_var,
        ).grid(
            row=2,
            column=1,
            sticky="w",
            pady=(4, 10),
        )

        button_frame = ttk.Frame(frame)
        button_frame.grid(
            row=3,
            column=0,
            columnspan=3,
            sticky="e",
        )

        ttk.Button(
            button_frame,
            text="Find Next",
            command=self.find_next,
        ).pack(
            side="left",
            padx=3,
        )

        ttk.Button(
            button_frame,
            text="Replace",
            command=self.replace,
        ).pack(
            side="left",
            padx=3,
        )

        ttk.Button(
            button_frame,
            text="Replace All",
            command=self.replace_all,
        ).pack(
            side="left",
            padx=3,
        )

        ttk.Button(
            button_frame,
            text="Close",
            command=self.destroy,
        ).pack(
            side="left",
            padx=3,
        )

        frame.columnconfigure(
            1,
            weight=1,
        )

        self.search_index = "1.0"

        self.bind(
            "<Escape>",
            lambda event: self.destroy(),
        )

        self.bind(
            "<Return>",
            lambda event: self.find_next(),
        )

        self.protocol(
            "WM_DELETE_WINDOW",
            self.destroy,
        )

        self.find_entry.focus_set()

    def find_next(self):
        needle = self.find_var.get()

        if not needle:
            return

        source = self.gui.source

        start = self.search_index

        index = source.search(
            needle,
            start,
            stopindex="end",
            nocase=self.ignore_case_var.get(),
        )

        if not index:
            index = source.search(
                needle,
                "1.0",
                stopindex=start,
                nocase=self.ignore_case_var.get(),
            )

        if not index:
            messagebox.showinfo(
                "Find",
                f'Could not find "{needle}".',
                parent=self,
            )
            return

        end = f"{index}+{len(needle)}c"

        source.tag_remove(
            "find_match",
            "1.0",
            "end",
        )

        source.tag_add(
            "find_match",
            index,
            end,
        )

        source.tag_remove(
            "sel",
            "1.0",
            "end",
        )

        source.tag_add(
            "sel",
            index,
            end,
        )

        source.mark_set(
            "insert",
            end,
        )

        source.see(index)

        self.search_index = end

    def replace(self):
        needle = self.find_var.get()

        if not needle:
            return

        source = self.gui.source

        try:
            start = source.index("sel.first")
            end = source.index("sel.last")
            selected = source.get(start, end)

        except tk.TclError:
            self.find_next()
            return

        if (
            selected.lower() == needle.lower()
            if self.ignore_case_var.get()
            else selected == needle
        ):
            source.delete(start, end)
            source.insert(
                start,
                self.replace_var.get(),
            )

            replacement = self.replace_var.get()

            self.search_index = (
                f"{start}+"
                f"{len(replacement)}c"
            )

            self.gui._source_changed()

            source.tag_remove(
                "find_match",
                "1.0",
                "end",
            )

            self.find_next()

        else:
            self.find_next()

    def replace_all(self):
        needle = self.find_var.get()

        if not needle:
            return

        replacement = self.replace_var.get()
        source = self.gui.source

        count = 0
        start = "1.0"

        nocase = self.ignore_case_var.get()

        while True:
            index = source.search(
                needle,
                start,
                stopindex="end",
                nocase=nocase,
            )

            if not index:
                break

            end = f"{index}+{len(needle)}c"

            source.delete(index, end)
            source.insert(index, replacement)

            start = f"{index}+{len(replacement)}c"
            count += 1

        source.tag_remove(
            "find_match",
            "1.0",
            "end",
        )

        self.search_index = start

        if count:
            self.gui._source_changed()

        messagebox.showinfo(
            "Replace All",
            f"Replaced {count} occurrence(s).",
            parent=self,
        )


class EightTowersGUI:
    def __init__(self, root):
        self.root = root

        self.root.title("8 Towers")
        self.root.geometry("1000x750")
        self.root.minsize(750, 550)

        self.machine = None
        self.input_buffer = None
        self.output_buffer = None

        self.worker = None
        self.stop_event = threading.Event()

        self.running = False
        self.waiting_for_input = False
        self.step_mode = False

        self.filename = None
        self.modified = False

        self.find_dialog = None

        self.realms_var = tk.BooleanVar(
            value=False,
        )

        self.output_mode_var = tk.StringVar(
            value="hex",
        )

        self._build_menu()
        self._build_ui()

        self.source.edit_modified(False)

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.quit,
        )

        self._update_title()
        self._update_display()
        self._set_controls_running(False)

   
    # Menu
   

    def _build_menu(self):
        menubar = tk.Menu(self.root)

        # --------------------------------------------------------------
        # File
        # --------------------------------------------------------------

        file_menu = tk.Menu(
            menubar,
            tearoff=False,
        )

        file_menu.add_command(
            label="New",
            accelerator="Ctrl+N",
            command=self.new_program,
        )

        file_menu.add_command(
            label="Open...",
            accelerator="Ctrl+O",
            command=self.open_file,
        )

        file_menu.add_separator()

        file_menu.add_command(
            label="Save",
            accelerator="Ctrl+S",
            command=self.save_file,
        )

        file_menu.add_command(
            label="Save As...",
            accelerator="Ctrl+Shift+S",
            command=self.save_file_as,
        )

        file_menu.add_separator()

        file_menu.add_command(
            label="Exit",
            accelerator="Alt+F4",
            command=self.quit,
        )

        menubar.add_cascade(
            label="File",
            menu=file_menu,
        )

        # --------------------------------------------------------------
        # Edit
        # --------------------------------------------------------------

        edit_menu = tk.Menu(
            menubar,
            tearoff=False,
        )

        edit_menu.add_command(
            label="Undo",
            accelerator="Ctrl+Z",
            command=lambda: self.source.event_generate(
                "<<Undo>>"
            ),
        )

        edit_menu.add_command(
            label="Redo",
            accelerator="Ctrl+Y",
            command=lambda: self.source.event_generate(
                "<<Redo>>"
            ),
        )

        edit_menu.add_separator()

        edit_menu.add_command(
            label="Cut",
            accelerator="Ctrl+X",
            command=lambda: self.source.event_generate(
                "<<Cut>>"
            ),
        )

        edit_menu.add_command(
            label="Copy",
            accelerator="Ctrl+C",
            command=lambda: self.source.event_generate(
                "<<Copy>>"
            ),
        )

        edit_menu.add_command(
            label="Paste",
            accelerator="Ctrl+V",
            command=lambda: self.source.event_generate(
                "<<Paste>>"
            ),
        )

        edit_menu.add_separator()

        edit_menu.add_command(
            label="Select All",
            accelerator="Ctrl+A",
            command=self.select_all,
        )

        edit_menu.add_separator()


        edit_menu.add_command(
            label="Find / Replace...",
            accelerator="Ctrl+F",
            command=self.show_find,
        )

        menubar.add_cascade(
            label="Edit",
            menu=edit_menu,
        )

        # --------------------------------------------------------------
        # Machine
        # --------------------------------------------------------------

        machine_menu = tk.Menu(
            menubar,
            tearoff=False,
        )

        machine_menu.add_command(
            label="Run",
            command=self.run,
        )

        machine_menu.add_command(
            label="Step",
            command=self.step,
        )

        machine_menu.add_command(
            label="Stop",
            command=self.stop,
        )

        machine_menu.add_command(
            label="Restart",
            command=self.restart,
        )

        menubar.add_cascade(
            label="Machine",
            menu=machine_menu,
        )

        # --------------------------------------------------------------
        # Help
        # --------------------------------------------------------------

        help_menu = tk.Menu(
            menubar,
            tearoff=False,
        )

        help_menu.add_command(
            label="Language Specification",
            command=self.open_spec,
        )

        help_menu.add_separator()

        help_menu.add_command(
            label="About 8 Towers",
            command=self.show_about,
        )

        menubar.add_cascade(
            label="Help",
            menu=help_menu,
        )

        self.root.config(
            menu=menubar,
        )

        # --------------------------------------------------------------
        # Keyboard shortcuts
        # --------------------------------------------------------------

        self.root.bind(
            "<Control-n>",
            lambda event: self.new_program(),
        )

        self.root.bind(
            "<Control-o>",
            lambda event: self.open_file(),
        )

        self.root.bind(
            "<Control-s>",
            lambda event: self.save_file(),
        )

        self.root.bind(
            "<Control-Shift-S>",
            lambda event: self.save_file_as(),
        )

        self.root.bind(
            "<Control-f>",
            lambda event: self.show_find(),
        )

        self.root.bind(
            "<Control-h>",
            lambda event: self.show_find(),
        )

        self.root.bind(
            "<Control-a>",
            lambda event: self.select_all(),
        )

   
    # User interface
   

    def _build_ui(self):
        toolbar = ttk.Frame(
            self.root,
            padding=8,
        )

        toolbar.pack(
            fill="x",
        )

        self.run_button = ttk.Button(
            toolbar,
            text="Run",
            command=self.run,
        )

        self.run_button.pack(
            side="left",
            padx=3,
        )

        self.step_button = ttk.Button(
            toolbar,
            text="Step",
            command=self.step,
        )

        self.step_button.pack(
            side="left",
            padx=3,
        )

        self.stop_button = ttk.Button(
            toolbar,
            text="Stop",
            command=self.stop,
        )

        self.stop_button.pack(
            side="left",
            padx=3,
        )

        self.restart_button = ttk.Button(
            toolbar,
            text="Restart",
            command=self.restart,
        )

        self.restart_button.pack(
            side="left",
            padx=3,
        )

        ttk.Checkbutton(
            toolbar,
            text="Realm Extension (2.0)",
            variable=self.realms_var,
        ).pack(
            side="left",
            padx=15,
        )

        ttk.Label(
            toolbar,
            text="Output:",
        ).pack(
            side="left",
            padx=(10, 3),
        )

        self.output_mode_combo = ttk.Combobox(
            toolbar,
            textvariable=self.output_mode_var,
            values=("hex", "ASCII"),
            state="readonly",
            width=8,
        )

        self.output_mode_combo.pack(
            side="left",
        )

        self.output_mode_combo.bind(
            "<<ComboboxSelected>>",
            lambda event: self._refresh_output(),
        )

        self.status_var = tk.StringVar(
            value="Ready",
        )

        self.status_label = ttk.Label(
            toolbar,
            textvariable=self.status_var,
        )

        self.status_label.pack(
            side="right",
        )

        main = ttk.PanedWindow(
            self.root,
            orient=tk.VERTICAL,
        )

        main.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=(0, 8),
        )

        # --------------------------------------------------------------
        # Source
        # --------------------------------------------------------------

        source_frame = ttk.LabelFrame(
            main,
            text="Source",
            padding=5,
        )

        source_frame.rowconfigure(
            0,
            weight=1,
        )

        source_frame.columnconfigure(
            0,
            weight=1,
        )

        self.source = tk.Text(
            source_frame,
            wrap="none",
            undo=True,
            font=("Consolas", 12),
        )

        self.source.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        source_scroll = ttk.Scrollbar(
            source_frame,
            orient="vertical",
            command=self.source.yview,
        )

        source_scroll.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        self.source.configure(
            yscrollcommand=source_scroll.set,
        )

        self.source.tag_configure(
            "find_match",
            background="#f0c674",
            foreground="#111111",
        )

        self.source.bind(
            "<<Modified>>",
            self._source_modified,
        )

        main.add(
            source_frame,
            weight=2,
        )

        # --------------------------------------------------------------
        # Bottom
        # --------------------------------------------------------------

        bottom = ttk.Frame(main)

        bottom.columnconfigure(
            0,
            weight=1,
        )

        bottom.rowconfigure(
            0,
            weight=1,
        )

        # --------------------------------------------------------------
        # Towers
        # --------------------------------------------------------------

        tower_frame = ttk.LabelFrame(
            bottom,
            text="Towers",
            padding=5,
        )

        tower_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 5),
        )

        tower_frame.rowconfigure(
            0,
            weight=1,
        )

        tower_frame.columnconfigure(
            0,
            weight=1,
        )

        self.tower_canvas = TowerCanvas(
            tower_frame,
        )

        self.tower_canvas.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        # --------------------------------------------------------------
        # Side panel
        # --------------------------------------------------------------

        side = ttk.Frame(bottom)

        side.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        # --------------------------------------------------------------
        # Machine information
        # --------------------------------------------------------------

        info = ttk.LabelFrame(
            side,
            text="Machine",
            padding=10,
        )

        info.pack(
            fill="x",
        )

        self.pc_var = tk.StringVar(
            value="-",
        )

        self.realm_var = tk.StringVar(
            value="-",
        )

        self.pointer_var = tk.StringVar(
            value="-",
        )

        self._info_row(
            info,
            "PC",
            self.pc_var,
            0,
        )

        self._info_row(
            info,
            "Realm",
            self.realm_var,
            1,
        )

        self._info_row(
            info,
            "Pointer",
            self.pointer_var,
            2,
        )

        # --------------------------------------------------------------
        # Input
        # --------------------------------------------------------------

        input_frame = ttk.LabelFrame(
            side,
            text="Input",
            padding=10,
        )

        input_frame.pack(
            fill="x",
            pady=(10, 0),
        )

        self.input_entry = ttk.Entry(
            input_frame,
            width=18,
        )

        self.input_entry.pack(
            side="left",
        )

        self.input_entry.bind(
            "<Return>",
            self.send_input,
        )

        self.input_button = ttk.Button(
            input_frame,
            text="Send",
            command=self.send_input,
        )

        self.input_button.pack(
            side="left",
            padx=(5, 0),
        )

        ttk.Label(
            input_frame,
            text="decimal / 0x / 0b / 0o / 'c'",
        ).pack(
            anchor="w",
            pady=(5, 0),
        )

        # --------------------------------------------------------------
        # Output
        # --------------------------------------------------------------

        output_frame = ttk.LabelFrame(
            side,
            text="Output",
            padding=10,
        )

        output_frame.pack(
            fill="both",
            expand=True,
            pady=(10, 0),
        )

        self.output_text = tk.Text(
            output_frame,
            width=30,
            height=8,
            wrap="word",
            state="disabled",
            font=("Consolas", 10),
        )

        self.output_text.pack(
            fill="both",
            expand=True,
        )

        main.add(
            bottom,
            weight=3,
        )

    @staticmethod
    def _info_row(parent, label, variable, row):
        ttk.Label(
            parent,
            text=f"{label}:",
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=2,
        )

        ttk.Label(
            parent,
            textvariable=variable,
        ).grid(
            row=row,
            column=1,
            sticky="e",
            padx=(15, 0),
            pady=2,
        )

   
    # Editing
   

    def select_all(self):
        self.source.tag_add(
            "sel",
            "1.0",
            "end-1c",
        )

        self.source.mark_set(
            "insert",
            "1.0",
        )

        self.source.see("1.0")

    def show_find(self):
        """Open or focus the Find / Replace dialog."""

        if (
            self.find_dialog is not None
            and self.find_dialog.winfo_exists()
        ):
            self.find_dialog.lift()
            self.find_dialog.focus_force()

            try:
                start = self.source.index("sel.first")
                end = self.source.index("sel.last")

                selected = self.source.get(
                    start,
                    end,
                )

                if selected:
                    self.find_dialog.find_var.set(
                        selected
                    )

            except tk.TclError:
                pass

            return

        self.find_dialog = FindReplaceDialog(self)

        self.find_dialog.bind(
            "<Destroy>",
            self._find_dialog_destroyed,
            add="+",
        )

        try:
            start = self.source.index("sel.first")
            end = self.source.index("sel.last")

            selected = self.source.get(
                start,
                end,
            )

            if selected:
                self.find_dialog.find_var.set(
                    selected
                )

        except tk.TclError:
            pass

    def _find_dialog_destroyed(self, event=None):
        if (
            self.find_dialog is not None
            and not self.find_dialog.winfo_exists()
        ):
            self.find_dialog = None

    def _source_modified(self, event=None):
        if not self.source.edit_modified():
            return

        self.modified = True
        self._update_title()

        self.source.edit_modified(False)

    def _source_changed(self):
        self.modified = True
        self._update_title()

   
    # File handling
   

    def _update_title(self):
        name = (
            os.path.basename(self.filename)
            if self.filename
            else "Untitled"
        )

        if self.modified:
            name += " *"

        self.root.title(
            f"8 Towers - {name}"
        )

    def new_program(self):
        if not self._confirm_discard():
            return

        self.stop()
        self._reset_machine()

        self.source.delete(
            "1.0",
            "end",
        )

        self.source.edit_modified(False)

        self.filename = None
        self.modified = False

        self.status_var.set(
            "Ready"
        )

        self._update_title()
        self._update_display()

    def open_file(self):
        if not self._confirm_discard():
            return

        filename = filedialog.askopenfilename(
            title="Open 8 Towers program",
            filetypes=[
                ("8 Towers programs", "*.8t"),
                ("Text files", "*.txt"),
                ("All files", "*.*"),
            ],
        )

        if not filename:
            return

        try:
            with open(
                filename,
                "r",
                encoding="utf-8",
            ) as file:
                source = file.read()

        except OSError as exc:
            messagebox.showerror(
                "Open failed",
                str(exc),
            )
            return

        self.stop()
        self._reset_machine()

        self.source.delete(
            "1.0",
            "end",
        )

        self.source.insert(
            "1.0",
            source,
        )

        self.source.edit_modified(False)

        self.filename = filename
        self.modified = False

        self.status_var.set(
            "Ready"
        )

        self._update_title()
        self._update_display()

    def save_file(self):
        if self.filename is None:
            return self.save_file_as()

        return self._write_file(
            self.filename,
        )

    def save_file_as(self):
        filename = filedialog.asksaveasfilename(
            title="Save 8 Towers program",
            defaultextension=".8t",
            filetypes=[
                ("8 Towers programs", "*.8t"),
                ("Text files", "*.txt"),
                ("All files", "*.*"),
            ],
        )

        if not filename:
            return False

        return self._write_file(
            filename,
        )

    def _write_file(self, filename):
        source = self.source.get(
            "1.0",
            "end-1c",
        )

        try:
            with open(
                filename,
                "w",
                encoding="utf-8",
                newline="",
            ) as file:
                file.write(source)

        except OSError as exc:
            messagebox.showerror(
                "Save failed",
                str(exc),
            )
            return False

        self.filename = filename
        self.modified = False

        self.source.edit_modified(False)

        self._update_title()

        return True

    def _confirm_discard(self):
        if not self.modified:
            return True

        answer = messagebox.askyesnocancel(
            "Unsaved Changes",
            "Save changes before continuing?",
        )

        if answer is None:
            return False

        if answer:
            return self.save_file()

        return True

   
    # Help

    def open_spec(self):
        """Open the local 8 Towers language specification."""

        project_dir = os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )

        path = os.path.join(
            project_dir,
            "docs",
            "SPEC.HTML",
        )

        if not os.path.isfile(path):
            messagebox.showerror(
                "Language Specification",
                f"Could not find the language specification:\n\n{path}",
                parent=self.root,
            )
            return

        webbrowser.open(
            "file://"
            + os.path.abspath(path)
        )


    def show_about(self):
        messagebox.showinfo(
            "About 8 Towers",
            "8 Towers Interpreter\n\n"
            "Interactive interpreter and debugger "
            "for the 8 Towers programming language.\n\n"
            "Use Help → Language Specification "
            "for the authoritative language guide.",
            parent=self.root,
        )

   
    # Machine creation

    def _create_machine(self):
        source = self.source.get(
            "1.0",
            "end-1c",
        )

        try:
            program = Program.from_source(
                source,
            )

        except Exception as exc:
            messagebox.showerror(
                "Invalid program",
                str(exc),
                parent=self.root,
            )
            return None

        self.input_buffer = InputBuffer()
        self.output_buffer = OutputBuffer()

        return Machine(
            program,
            realms_expansion=self.realms_var.get(),
            input_stream=self.input_buffer,
            output_stream=self.output_buffer,
        )

    def _reset_machine(self):
        if self.input_buffer is not None:
            self.input_buffer.close()

        self.machine = None
        self.input_buffer = None
        self.output_buffer = None

        self.running = False
        self.waiting_for_input = False
        self.step_mode = False

        self.stop_event.set()
        self.stop_event.clear()

        self._clear_output()

    def restart(self):
        """
        Restart using exactly what is currently in the source editor.

        This intentionally reparses the editor contents rather than
        reusing the previously-created Program object.
        """

        if self.running:
            self.stop()

        self._reset_machine()

        self.machine = self._create_machine()

        if self.machine is None:
            self.status_var.set(
                "Ready"
            )
            self._update_display()
            return

        self.status_var.set(
            "Ready"
        )

        self._set_controls_running(False)
        self._update_display()

   
    # Execution

    def run(self):
        if self.running:
            return

        if self.machine is None:
            self.machine = self._create_machine()

            if self.machine is None:
                return

        if self.machine.pc >= len(
            self.machine.program
        ):
            if self.machine.loop_stack:
                self._machine_crashed(
                    Crash(
                        "EOF reached inside an active loop"
                    )
                )
            else:
                self.status_var.set(
                    "Finished"
                )

            self._update_display()
            return

        self.running = True
        self.step_mode = False
        self.stop_event.clear()

        self.waiting_for_input = (
            self._next_operation_is_receive()
        )

        if self.waiting_for_input:
            self.status_var.set(
                "Waiting for input"
            )
        else:
            self.status_var.set(
                "Running"
            )

        self._set_controls_running(True)

        self.worker = threading.Thread(
            target=self._run_machine,
            daemon=True,
        )

        self.worker.start()

    def _run_machine(self):
        try:
            while not self.stop_event.is_set():
                if self.machine.pc >= len(
                    self.machine.program
                ):
                    if self.machine.loop_stack:
                        raise Crash(
                            "EOF reached inside an active loop"
                        )

                    break

                waiting = (
                    self._next_operation_is_receive()
                )

                self.root.after(
                    0,
                    lambda waiting=waiting:
                    self._set_execution_status(
                        waiting,
                    ),
                )

                self.machine.step()

                self.root.after(
                    0,
                    self._update_display,
                )

        except Crash as exc:
            self.root.after(
                0,
                lambda exc=exc:
                self._machine_crashed(exc),
            )
            return

        except Exception as exc:
            self.root.after(
                0,
                lambda exc=exc:
                self._machine_error(exc),
            )
            return

        self.root.after(
            0,
            self._machine_finished,
        )

    def step(self):
        """
        Execute exactly one Machine.step().

        A RECEIVE operation runs on the worker thread so the GUI remains
        responsive while waiting for interactive input.
        """

        if self.running:
            return

        if self.machine is None:
            self.machine = self._create_machine()

            if self.machine is None:
                return

        if self.machine.pc >= len(
            self.machine.program
        ):
            if self.machine.loop_stack:
                self._machine_crashed(
                    Crash(
                        "EOF reached inside an active loop"
                    )
                )
            else:
                self.status_var.set(
                    "Finished"
                )

            self._update_display()
            return

        self.running = True
        self.step_mode = True
        self.stop_event.clear()

        self.waiting_for_input = (
            self._next_operation_is_receive()
        )

        if self.waiting_for_input:
            self.status_var.set(
                "Waiting for input"
            )
        else:
            self.status_var.set(
                "Stepping"
            )

        self._set_controls_running(True)

        self.worker = threading.Thread(
            target=self._step_machine,
            daemon=True,
        )

        self.worker.start()

    def _step_machine(self):
        try:
            self.machine.step()

        except Crash as exc:
            self.root.after(
                0,
                lambda exc=exc:
                self._machine_crashed(exc),
            )
            return

        except Exception as exc:
            self.root.after(
                0,
                lambda exc=exc:
                self._machine_error(exc),
            )
            return

        self.root.after(
            0,
            self._step_finished,
        )

    def _step_finished(self):
        self.running = False
        self.waiting_for_input = False
        self.step_mode = False

        if self.machine.pc >= len(
            self.machine.program
        ):
            if self.machine.loop_stack:
                self.status_var.set(
                    "Crashed"
                )
            else:
                self.status_var.set(
                    "Finished"
                )
        else:
            self.status_var.set(
                "Paused"
            )

        self._set_controls_running(False)
        self._update_display()

    def stop(self):
        if not self.running:
            return

        self.stop_event.set()

        self.running = False
        self.waiting_for_input = False
        self.step_mode = False

        self.status_var.set(
            "Stopped"
        )

        self._set_controls_running(False)

    def _set_execution_status(self, waiting):
        if not self.running:
            return

        self.waiting_for_input = waiting

        if waiting:
            self.status_var.set(
                "Waiting for input"
            )
        else:
            self.status_var.set(
                "Running"
            )

    def _machine_finished(self):
        self.running = False
        self.waiting_for_input = False
        self.step_mode = False

        self.status_var.set(
            "Finished"
        )

        self._set_controls_running(False)
        self._update_display()

    def _machine_crashed(self, exc):
        self.running = False
        self.waiting_for_input = False
        self.step_mode = False

        self.status_var.set(
            "Crashed"
        )

        self._set_controls_running(False)
        self._update_display()

        messagebox.showerror(
            "8 Towers crashed",
            str(exc),
            parent=self.root,
        )

    def _machine_error(self, exc):
        self.running = False
        self.waiting_for_input = False
        self.step_mode = False

        self.status_var.set(
            "Error"
        )

        self._set_controls_running(False)
        self._update_display()

        messagebox.showerror(
            "Interpreter error",
            str(exc),
            parent=self.root,
        )

    def _set_controls_running(self, running):
        self.run_button.configure(
            state=(
                "disabled"
                if running
                else "normal"
            ),
        )

        self.step_button.configure(
            state=(
                "disabled"
                if running
                else "normal"
            ),
        )

        self.stop_button.configure(
            state=(
                "normal"
                if running
                else "disabled"
            ),
        )

        self.restart_button.configure(
            state="normal",
        )

        self.input_button.configure(
            state="normal",
        )

   
    # Input
   
    def _next_operation_is_receive(self):
        if self.machine is None:
            return False

        if self.machine.pc >= len(
            self.machine.program
        ):
            return False

        return (
            self.machine.program[
                self.machine.pc
            ].operation
            is Operation.RECEIVE
        )

    def send_input(self, event=None):
        text = self.input_entry.get().strip()

        if not text:
            return

        try:
            value = self._parse_byte(
                text,
            )

        except ValueError as exc:
            messagebox.showerror(
                "Invalid byte",
                str(exc),
                parent=self.root,
            )
            return

        if self.input_buffer is None:
            self.input_buffer = InputBuffer()

        self.input_buffer.add(
            bytes([value]),
        )

        self.input_entry.delete(
            0,
            "end",
        )

        if self.running:
            self.status_var.set(
                "Running"
            )

    @staticmethod
    def _parse_byte(text):
        text = text.strip()

        if not text:
            raise ValueError(
                "empty byte"
            )

        if (
            len(text) >= 2
            and text[0] == "'"
            and text[-1] == "'"
        ):
            literal = text[1:-1]

            if len(literal) != 1:
                raise ValueError(
                    "character literal must contain "
                    "one character"
                )

            number = ord(literal)

        else:
            try:
                number = int(text, 0)

            except ValueError as exc:
                raise ValueError(
                    "invalid byte; use decimal, "
                    "hexadecimal (0x...), binary "
                    "(0b...), octal (0o...), or "
                    "a character literal"
                ) from exc

        if not -128 <= number <= 255:
            raise ValueError(
                "byte must be between -128 and 255"
            )

        return number & 0xFF

   
    # Output

    def _refresh_output(self):
        if self.output_buffer is None:
            return

        data = self.output_buffer.getvalue()

        self.output_text.configure(
            state="normal",
        )

        self.output_text.delete(
            "1.0",
            "end",
        )

        if data:
            mode = self.output_mode_var.get()

            if mode == "ASCII":
                text = data.decode(
                    "latin-1",
                )
            else:
                text = data.hex(
                    " ",
                ).upper()

            self.output_text.insert(
                "1.0",
                text,
            )

        self.output_text.configure(
            state="disabled",
        )

        self.output_text.see("end")

    def _clear_output(self):
        self.output_text.configure(
            state="normal",
        )

        self.output_text.delete(
            "1.0",
            "end",
        )

        self.output_text.configure(
            state="disabled",
        )

   
    # Display
   
    def _update_display(self):
        if self.machine is None:
            self.tower_canvas.draw(
                [],
                0,
            )

            self.pc_var.set("-")
            self.realm_var.set("-")
            self.pointer_var.set("-")

            return

        self.tower_canvas.draw(
            self.machine.current_towers,
            self.machine.tower,
        )

        self.pc_var.set(
            str(self.machine.pc)
        )

        self.realm_var.set(
            str(self.machine.realm)
        )

        self.pointer_var.set(
            f"T{self.machine.tower}"
        )

        self._refresh_output()

   
    # Shutdown

    def quit(self):
        if not self._confirm_discard():
            return

        self.stop()

        if self.input_buffer is not None:
            self.input_buffer.close()

        self.root.destroy()


def main():
    root = tk.Tk()
    EightTowersGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
