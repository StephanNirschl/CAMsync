import tkinter as tk
from tkinter import ttk


class ToolingDBTab(ttk.Frame):
    """Placeholder tab for Tooling DB features."""

    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config

        ttk.Label(self, text="Tooling DB placeholder").pack(padx=10, pady=10)
