"""Visual theme for GridCare-Lite: color/font tokens plus one function that
configures every ttk style the screens in app.py use.

Kept separate from app.py so the two concerns - "what a screen does" and
"what it looks like" - don't get tangled, matching the domain/presentation
split already used for models.py vs app.py (see docs/architecture.md).
"""
from tkinter import ttk

FONT_FAMILY = "Segoe UI"

# Slate header + amber accent: legible on a light working surface, and the
# amber reads as "utility/alert" without relying on red (reserved for
# destructive actions nowhere in this app).
COLOR_BG = "#f2f3f6"
COLOR_SURFACE = "#ffffff"
COLOR_SURFACE_ALT = "#f7f8fa"
COLOR_BORDER = "#dcdfe6"
COLOR_TEXT = "#1f2430"
COLOR_TEXT_DIM = "#5b6072"
COLOR_TEXT_FAINT = "#8b90a0"

COLOR_HEADER_BG = "#1f2937"
COLOR_HEADER_BG_HOVER = "#2c3648"
COLOR_HEADER_TEXT = "#ffffff"
COLOR_HEADER_TEXT_DIM = "#aab2c5"

COLOR_ACCENT = "#f2a71b"
COLOR_ACCENT_HOVER = "#d99110"
COLOR_ACCENT_TEXT = "#241a00"

COLOR_SELECTED_BG = "#fde8bf"
COLOR_SELECTED_TEXT = "#241a00"

FONT_BODY = (FONT_FAMILY, 10)
FONT_BODY_BOLD = (FONT_FAMILY, 10, "bold")
FONT_SMALL = (FONT_FAMILY, 9)
FONT_TITLE = (FONT_FAMILY, 20, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 10)
FONT_HEADER_TITLE = (FONT_FAMILY, 14, "bold")
FONT_HEADER_META = (FONT_FAMILY, 9)


def configure_style(root):
    """Configure every ttk style used across app.py's screens. Call once,
    right after creating the root window."""
    root.configure(bg=COLOR_BG)

    style = ttk.Style(root)
    style.theme_use("clam")

    # --- frames -----------------------------------------------------
    style.configure("TFrame", background=COLOR_BG)
    style.configure("Surface.TFrame", background=COLOR_SURFACE)
    style.configure("Header.TFrame", background=COLOR_HEADER_BG)
    style.configure("HeaderRight.TFrame", background=COLOR_HEADER_BG)

    # --- labels -------------------------------------------------------
    style.configure("TLabel", background=COLOR_BG, foreground=COLOR_TEXT, font=FONT_BODY)
    style.configure("Dim.TLabel", background=COLOR_BG, foreground=COLOR_TEXT_DIM, font=FONT_BODY)
    style.configure("SectionTitle.TLabel", background=COLOR_BG, foreground=COLOR_TEXT,
                     font=(FONT_FAMILY, 12, "bold"))

    style.configure("Card.TLabel", background=COLOR_SURFACE, foreground=COLOR_TEXT, font=FONT_BODY)
    style.configure("CardTitle.TLabel", background=COLOR_SURFACE, foreground=COLOR_TEXT, font=FONT_TITLE)
    style.configure("CardSubtitle.TLabel", background=COLOR_SURFACE, foreground=COLOR_TEXT_DIM,
                     font=FONT_SUBTITLE)
    style.configure("CardError.TLabel", background=COLOR_SURFACE, foreground="#b3261e", font=FONT_SMALL)
    style.configure("StatNumber.TLabel", background=COLOR_SURFACE, foreground=COLOR_TEXT,
                     font=(FONT_FAMILY, 22, "bold"))
    style.configure("StatLabel.TLabel", background=COLOR_SURFACE, foreground=COLOR_TEXT_FAINT,
                     font=(FONT_FAMILY, 9))
    style.configure("CardHeading.TLabel", background=COLOR_SURFACE, foreground=COLOR_TEXT,
                     font=(FONT_FAMILY, 11, "bold"))

    style.configure("Header.TLabel", background=COLOR_HEADER_BG, foreground=COLOR_HEADER_TEXT,
                     font=FONT_HEADER_META)
    style.configure("HeaderTitle.TLabel", background=COLOR_HEADER_BG, foreground=COLOR_HEADER_TEXT,
                     font=FONT_HEADER_TITLE)
    style.configure("HeaderMeta.TLabel", background=COLOR_HEADER_BG, foreground=COLOR_HEADER_TEXT_DIM,
                     font=FONT_HEADER_META)

    # --- entries / combobox --------------------------------------------
    style.configure("TEntry", fieldbackground=COLOR_SURFACE, foreground=COLOR_TEXT,
                     bordercolor=COLOR_BORDER, lightcolor=COLOR_BORDER, darkcolor=COLOR_BORDER,
                     insertcolor=COLOR_TEXT, padding=7, relief="flat")
    style.map("TEntry", bordercolor=[("focus", COLOR_ACCENT)])

    style.configure("TCombobox", fieldbackground=COLOR_SURFACE, background=COLOR_SURFACE,
                     foreground=COLOR_TEXT, arrowcolor=COLOR_TEXT_DIM,
                     bordercolor=COLOR_BORDER, lightcolor=COLOR_BORDER, darkcolor=COLOR_BORDER,
                     padding=6, relief="flat")
    style.map("TCombobox",
              fieldbackground=[("readonly", COLOR_SURFACE)],
              bordercolor=[("focus", COLOR_ACCENT)])

    # --- buttons --------------------------------------------------------
    style.configure("TButton", font=FONT_BODY, padding=(14, 8), background=COLOR_SURFACE,
                     foreground=COLOR_TEXT, bordercolor=COLOR_BORDER, borderwidth=1, relief="flat",
                     focusthickness=0)
    style.map("TButton",
              background=[("active", COLOR_SURFACE_ALT), ("disabled", COLOR_SURFACE_ALT)],
              foreground=[("disabled", COLOR_TEXT_FAINT)])

    style.configure("Primary.TButton", font=FONT_BODY_BOLD, padding=(16, 9),
                     background=COLOR_ACCENT, foreground=COLOR_ACCENT_TEXT, borderwidth=0,
                     focusthickness=0)
    style.map("Primary.TButton",
              background=[("active", COLOR_ACCENT_HOVER), ("disabled", COLOR_BORDER)],
              foreground=[("disabled", COLOR_TEXT_FAINT)])

    style.configure("Logout.TButton", font=FONT_SMALL, padding=(12, 6),
                     background=COLOR_HEADER_BG, foreground=COLOR_HEADER_TEXT,
                     bordercolor=COLOR_HEADER_TEXT_DIM, borderwidth=1, relief="flat",
                     focusthickness=0)
    style.map("Logout.TButton", background=[("active", COLOR_HEADER_BG_HOVER)])

    # --- treeview ---------------------------------------------------------
    style.configure("Treeview", background=COLOR_SURFACE, fieldbackground=COLOR_SURFACE,
                     foreground=COLOR_TEXT, rowheight=28, font=FONT_BODY, borderwidth=0, relief="flat")
    style.configure("Treeview.Heading", background=COLOR_HEADER_BG, foreground=COLOR_HEADER_TEXT,
                     font=FONT_BODY_BOLD, padding=(10, 8), relief="flat")
    style.map("Treeview.Heading", background=[("active", COLOR_HEADER_BG)])
    style.map("Treeview",
              background=[("selected", COLOR_SELECTED_BG)],
              foreground=[("selected", COLOR_SELECTED_TEXT)])
    style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

    return style


def draw_horizontal_bars(canvas, data, width, color=COLOR_ACCENT):
    """Draw a simple horizontal bar chart onto an empty tk.Canvas - no
    matplotlib dependency needed for the Reports screen's "simple charts".

    `data` is a list of (label, count) tuples, already sorted by the
    caller; `width` is the canvas's configured width in pixels (read once
    by the caller rather than via winfo_width(), which is unreliable
    before the widget has been laid out).
    """
    canvas.delete("all")
    if not data:
        canvas.create_text(6, 14, anchor="w", text="No data yet.",
                            fill=COLOR_TEXT_FAINT, font=FONT_SMALL)
        canvas.configure(height=28)
        return

    row_h = 26
    label_w = 128
    gap = 8
    bar_max_w = max(width - label_w - 46, 40)
    max_count = max(count for _, count in data) or 1

    for index, (label, count) in enumerate(data):
        y = index * row_h + gap
        canvas.create_text(2, y + 8, anchor="w", text=str(label),
                            fill=COLOR_TEXT, font=FONT_SMALL, width=label_w - 6)
        track_x0 = label_w
        canvas.create_rectangle(track_x0, y, track_x0 + bar_max_w, y + 16,
                                 fill=COLOR_SURFACE_ALT, outline=COLOR_BORDER)
        bar_w = max(int((count / max_count) * bar_max_w), 2) if count else 0
        if bar_w:
            canvas.create_rectangle(track_x0, y, track_x0 + bar_w, y + 16,
                                     fill=color, outline="")
        canvas.create_text(track_x0 + bar_max_w + 8, y + 8, anchor="w", text=str(count),
                            fill=COLOR_TEXT_DIM, font=FONT_SMALL)

    canvas.configure(height=len(data) * row_h + gap)


def style_text_widget(widget):
    """Apply the theme to a plain tk.Text widget (not ttk - Text has no ttk
    equivalent, so it needs its colours set directly)."""
    widget.configure(
        background=COLOR_SURFACE, foreground=COLOR_TEXT, insertbackground=COLOR_TEXT,
        relief="flat", highlightthickness=1, highlightbackground=COLOR_BORDER,
        highlightcolor=COLOR_ACCENT, font=FONT_BODY, padx=8, pady=6, wrap="word",
    )
