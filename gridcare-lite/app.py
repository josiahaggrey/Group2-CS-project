"""
GridCare-Lite: a Tkinter/SQLite outage and maintenance management system.

The GUI never writes raw SQL - every screen calls a method on a domain
class from models.py (User, Substation, Outage, WorkOrder, Complaint).
Screens are responsible for layout and input handling only; all business
rules (validation, status transitions, what counts as "resolved") live in
the model classes so they're the same regardless of which screen calls them.
Visual styling lives in theme.py, applied once via configure_style().

Run `python db.py` (or just run this file, which calls init_db() itself) then
`python seed_users.py` to create demo accounts, then `python app.py`.

Demo accounts (see seed_users.py):
    admin1 / Admin123!          (admin)
    engineer1 / Engineer123!    (engineer)
    tech1 / Tech123!            (technician)
    cs1 / CustService123!       (customer_service)

Role separation is enforced both in the GUI (which screens/buttons are
shown) and in application logic (e.g. a technician only ever sees their
own work orders via WorkOrder.for_technician()).
"""
import os
import tkinter as tk
from tkinter import messagebox, ttk

from db import init_db
from models import Complaint, Outage, Substation, User, WorkOrder
from theme import (
    COLOR_BG,
    COLOR_BORDER,
    COLOR_HEADER_BG,
    COLOR_SURFACE,
    configure_style,
    style_text_widget,
)

# Computed from this file's own location, not the current working directory -
# `python app.py` and `python gridcare-lite/app.py` must both find it.
DEFAULT_SUBSTATIONS_CSV = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "grid-analysis", "data", "cleaned", "substations_clean.csv",
)

ROLE_LABELS = {
    "admin": "Administrator",
    "engineer": "Engineer",
    "technician": "Technician",
    "customer_service": "Customer Service",
}


def ensure_substations_loaded(conn, csv_path=DEFAULT_SUBSTATIONS_CSV):
    """Auto-import grid-analysis's cleaned substation list on first run.

    Previously a manual step (see git history for the snippet this replaces)
    - a fresh clone opened straight to an empty substation picker. Runs once:
    skips the import if the table already has rows, and skips it quietly
    (rather than crashing the GUI) if the grid-analysis component hasn't
    been cloned/generated alongside gridcare-lite.
    """
    if Substation.all(conn):
        return
    if not os.path.exists(csv_path):
        print(f"No substation reference data imported - {csv_path} not found. "
              f"Outages can still be logged, but the substation picker will be empty "
              f"until you run Substation.import_from_csv(conn, <path>).")
        return
    count = Substation.import_from_csv(conn, csv_path)
    print(f"Imported {count} substations from {csv_path}")


def _card(master):
    """A white panel with a 1px border - the shared container for the login
    box and every popup form. Plain tk.Frame because ttk's 'clam' theme has
    no simple per-widget border colour for TFrame."""
    return tk.Frame(master, bg=COLOR_SURFACE, highlightbackground=COLOR_BORDER,
                     highlightthickness=1, bd=0)


class LoginWindow(tk.Frame):
    def __init__(self, master, conn, on_success):
        super().__init__(master, bg=COLOR_BG)
        self.conn = conn
        self.on_success = on_success
        master.title("GridCare-Lite - Login")

        self.pack(fill="both", expand=True)

        card = _card(self)
        card.place(relx=0.5, rely=0.45, anchor="center")
        inner = ttk.Frame(card, style="Surface.TFrame", padding=(40, 36))
        inner.pack()

        ttk.Label(inner, text="GridCare-Lite", style="CardTitle.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(inner, text="Outage & Maintenance Management", style="CardSubtitle.TLabel").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(2, 24))

        ttk.Label(inner, text="Username", style="Card.TLabel").grid(
            row=2, column=0, columnspan=2, sticky="w")
        self.username_entry = ttk.Entry(inner, width=28, font=("Segoe UI", 10))
        self.username_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(4, 14))

        ttk.Label(inner, text="Password", style="Card.TLabel").grid(
            row=4, column=0, columnspan=2, sticky="w")
        self.password_entry = ttk.Entry(inner, show="*", width=28, font=("Segoe UI", 10))
        self.password_entry.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(4, 6))

        self.error_label = ttk.Label(inner, text="", style="CardError.TLabel")
        self.error_label.grid(row=6, column=0, columnspan=2, sticky="w", pady=(0, 4))

        ttk.Button(inner, text="Log In", style="Primary.TButton", command=self.attempt_login).grid(
            row=7, column=0, columnspan=2, sticky="ew", pady=(14, 0))

        self.username_entry.focus_set()
        master.bind("<Return>", lambda event: self.attempt_login())

    def attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            self.error_label.configure(text="Enter both a username and password.")
            return

        user = User.authenticate(self.conn, username, password)
        if user is None:
            self.error_label.configure(text="Invalid username or password.")
            return

        self.on_success(user)


class Header(tk.Frame):
    """The dark title bar shown on every dashboard: app name, current user,
    and (if a logout handler is given) a Log Out button."""

    def __init__(self, master, title, subtitle=None, user=None, on_logout=None):
        super().__init__(master, bg=COLOR_HEADER_BG)
        self.pack(fill="x")
        inner = ttk.Frame(self, style="Header.TFrame", padding=(24, 16))
        inner.pack(fill="x")

        left = ttk.Frame(inner, style="Header.TFrame")
        left.pack(side="left")
        ttk.Label(left, text=title, style="HeaderTitle.TLabel").pack(side="left")
        if subtitle:
            ttk.Label(left, text=f"   {subtitle}", style="HeaderMeta.TLabel").pack(
                side="left", pady=(3, 0))

        right = ttk.Frame(inner, style="Header.TFrame")
        right.pack(side="right")
        if on_logout is not None:
            ttk.Button(right, text="Log Out", style="Logout.TButton", command=on_logout).pack(
                side="right")
        if user is not None:
            role_frame = ttk.Frame(right, style="Header.TFrame")
            role_frame.pack(side="right", padx=(0, 16))
            ttk.Label(role_frame, text=user.username, style="HeaderTitle.TLabel",
                      font=("Segoe UI", 11, "bold")).pack(anchor="e")
            ttk.Label(role_frame, text=ROLE_LABELS.get(user.role, user.role),
                      style="HeaderMeta.TLabel").pack(anchor="e")


class OutageDashboard(tk.Frame):
    """Role-aware main screen: outage list plus role-appropriate action buttons."""

    def __init__(self, master, conn, user, on_logout):
        super().__init__(master, bg=COLOR_BG)
        self.conn = conn
        self.user = user
        self.on_logout = on_logout
        master.title(f"GridCare-Lite - {user.username} ({ROLE_LABELS.get(user.role, user.role)})")

        Header(self, "GridCare-Lite", "Outage Dashboard", user=user, on_logout=self._logout)

        body = ttk.Frame(self, padding=(24, 20))
        body.pack(fill="both", expand=True)

        ttk.Label(body, text="Reported Outages", style="SectionTitle.TLabel").pack(
            anchor="w", pady=(0, 10))

        tree_wrap = tk.Frame(body, bg=COLOR_SURFACE, highlightbackground=COLOR_BORDER,
                              highlightthickness=1, bd=0)
        tree_wrap.pack(fill="both", expand=True)

        columns = ("outage_id", "substation", "description", "status", "reported_at")
        headings = ("ID", "Substation", "Description", "Status", "Reported At")
        self.tree = ttk.Treeview(tree_wrap, columns=columns, show="headings", height=12)
        for col, heading in zip(columns, headings):
            self.tree.heading(col, text=heading)
        self.tree.column("outage_id", width=50, anchor="center")
        self.tree.column("substation", width=150)
        self.tree.column("description", width=260)
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("reported_at", width=140)
        self.tree.tag_configure("odd", background="#f7f8fa")
        self.tree.tag_configure("even", background=COLOR_SURFACE)
        self.tree.pack(fill="both", expand=True, padx=1, pady=1)

        button_bar = ttk.Frame(body)
        button_bar.pack(fill="x", pady=(14, 0))
        ttk.Button(button_bar, text="Refresh", command=self.load_outages).pack(side="left")

        if user.role in ("engineer", "admin"):
            ttk.Button(button_bar, text="Log New Outage", style="Primary.TButton",
                       command=self.open_new_outage_form).pack(side="left", padx=(10, 0))
        if user.role == "admin":
            ttk.Button(button_bar, text="Assign Work Order", style="Primary.TButton",
                       command=self.open_work_order_form).pack(side="left", padx=(10, 0))
        if user.role == "technician":
            ttk.Button(button_bar, text="My Work Orders", style="Primary.TButton",
                       command=self.open_technician_view).pack(side="left", padx=(10, 0))
        if user.role == "customer_service":
            ttk.Button(button_bar, text="Log Complaint", style="Primary.TButton",
                       command=self.open_complaint_form).pack(side="left", padx=(10, 0))

        self.pack(fill="both", expand=True)
        self.load_outages()

    def load_outages(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for index, outage in enumerate(Outage.all(self.conn)):
            tag = "odd" if index % 2 else "even"
            self.tree.insert("", "end", values=(
                outage.outage_id, outage.substation_name, outage.description,
                outage.status, outage.reported_at,
            ), tags=(tag,))

    def open_new_outage_form(self):
        NewOutageForm(tk.Toplevel(self.master), self.conn, self.user, on_saved=self.load_outages)

    def open_work_order_form(self):
        WorkOrderForm(tk.Toplevel(self.master), self.conn, on_saved=self.load_outages)

    def open_technician_view(self):
        TechnicianView(tk.Toplevel(self.master), self.conn, self.user)

    def open_complaint_form(self):
        ComplaintForm(tk.Toplevel(self.master), self.conn, self.user)

    def _logout(self):
        self.destroy()
        self.on_logout()


class FormWindow(tk.Frame):
    """Shared chrome for the popup forms below: a titled card on a plain
    background, sized to its content. Subclasses build `inner` (the form
    fields) and call `_finish(row)` to add the submit button."""

    def __init__(self, master, window_title, form_title):
        super().__init__(master, bg=COLOR_BG)
        master.title(window_title)
        master.configure(bg=COLOR_BG)
        master.resizable(False, False)
        self.pack(fill="both", expand=True, padx=18, pady=18)

        card = _card(self)
        card.pack(fill="both", expand=True)
        self.inner = ttk.Frame(card, style="Surface.TFrame", padding=(24, 20))
        self.inner.pack()
        self.inner.columnconfigure(1, weight=1)

        ttk.Label(self.inner, text=form_title, style="CardTitle.TLabel",
                  font=("Segoe UI", 15, "bold")).grid(row=0, column=0, columnspan=2, sticky="w",
                                                       pady=(0, 16))

    def _field_label(self, row, text):
        ttk.Label(self.inner, text=text, style="Card.TLabel").grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 4))

    def _submit_button(self, row, text, command):
        ttk.Button(self.inner, text=text, style="Primary.TButton", command=command).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(16, 0))


class NewOutageForm(FormWindow):
    def __init__(self, master, conn, user, on_saved):
        super().__init__(master, "Log New Outage", "Log New Outage")
        self.conn = conn
        self.user = user
        self.on_saved = on_saved

        self._field_label(1, "Substation")
        self.substation_var = tk.StringVar()
        self.substation_combo = ttk.Combobox(self.inner, textvariable=self.substation_var,
                                              state="readonly", width=34)
        self._load_substations()
        self.substation_combo.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 14))

        self._field_label(3, "Description")
        self.description_text = tk.Text(self.inner, width=34, height=5)
        style_text_widget(self.description_text)
        self.description_text.grid(row=4, column=0, columnspan=2, sticky="ew")

        self._submit_button(5, "Submit", self.submit)

    def _load_substations(self):
        self.substations = Substation.all(self.conn)
        self.substation_combo["values"] = [str(s) for s in self.substations]
        if self.substations:
            self.substation_combo.current(0)

    def submit(self):
        if not self.substations:
            messagebox.showerror(
                "No Substations", "No substations found. Import substations.csv via "
                "Substation.import_from_csv() first.")
            return
        substation = self.substations[self.substation_combo.current()]
        description = self.description_text.get("1.0", "end").strip()

        try:
            Outage.report(self.conn, substation.substation_id, self.user.user_id, description)
        except ValueError as error:
            messagebox.showerror("Validation Error", str(error))
            return

        messagebox.showinfo("Success", "Outage logged.")
        self.on_saved()
        self.master.destroy()


class WorkOrderForm(FormWindow):
    def __init__(self, master, conn, on_saved):
        super().__init__(master, "Assign Work Order", "Assign Work Order")
        self.conn = conn
        self.on_saved = on_saved

        self._field_label(1, "Open Outage")
        self.outage_var = tk.StringVar()
        self.outage_combo = ttk.Combobox(self.inner, textvariable=self.outage_var,
                                          state="readonly", width=40)
        self._load_open_outages()
        self.outage_combo.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 14))

        self._field_label(3, "Technician")
        self.tech_var = tk.StringVar()
        self.tech_combo = ttk.Combobox(self.inner, textvariable=self.tech_var,
                                        state="readonly", width=40)
        self._load_technicians()
        self.tech_combo.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 14))

        self._field_label(5, "Scheduled Date (YYYY-MM-DD)")
        self.date_entry = ttk.Entry(self.inner, width=40)
        self.date_entry.grid(row=6, column=0, columnspan=2, sticky="ew")

        self._submit_button(7, "Assign", self.submit)

    def _load_open_outages(self):
        self.outages = Outage.open_outages(self.conn)
        self.outage_combo["values"] = [
            f"#{o.outage_id}: {o.description[:40]}" for o in self.outages
        ]
        if self.outages:
            self.outage_combo.current(0)

    def _load_technicians(self):
        self.technicians = User.find_by_role(self.conn, "technician")
        self.tech_combo["values"] = [str(t) for t in self.technicians]
        if self.technicians:
            self.tech_combo.current(0)

    def submit(self):
        if not self.outages:
            messagebox.showerror("No Open Outages", "There are no open outages to assign.")
            return
        if not self.technicians:
            messagebox.showerror("No Technicians", "No technician accounts exist yet.")
            return

        outage = self.outages[self.outage_combo.current()]
        technician = self.technicians[self.tech_combo.current()]
        scheduled_date = self.date_entry.get().strip()

        try:
            WorkOrder.assign(self.conn, outage.outage_id, technician.user_id, scheduled_date)
        except ValueError as error:
            messagebox.showerror("Validation Error", str(error))
            return

        messagebox.showinfo("Success", "Work order assigned.")
        self.on_saved()
        self.master.destroy()


class TechnicianView(tk.Frame):
    def __init__(self, master, conn, user):
        super().__init__(master, bg=COLOR_BG)
        self.conn = conn
        self.user = user
        master.title("My Work Orders")
        master.configure(bg=COLOR_BG)

        Header(self, "My Work Orders", user=user)

        body = ttk.Frame(self, padding=(20, 18))
        body.pack(fill="both", expand=True)

        tree_wrap = tk.Frame(body, bg=COLOR_SURFACE, highlightbackground=COLOR_BORDER,
                              highlightthickness=1, bd=0)
        tree_wrap.pack(fill="both", expand=True)

        columns = ("work_order_id", "outage_description", "scheduled_date", "status")
        headings = ("ID", "Outage", "Scheduled", "Status")
        self.tree = ttk.Treeview(tree_wrap, columns=columns, show="headings")
        for col, heading in zip(columns, headings):
            self.tree.heading(col, text=heading)
        self.tree.column("work_order_id", width=50, anchor="center")
        self.tree.column("outage_description", width=260)
        self.tree.column("scheduled_date", width=110, anchor="center")
        self.tree.column("status", width=100, anchor="center")
        self.tree.tag_configure("odd", background="#f7f8fa")
        self.tree.tag_configure("even", background=COLOR_SURFACE)
        self.tree.pack(fill="both", expand=True, padx=1, pady=1)

        ttk.Button(body, text="Mark Selected Complete", style="Primary.TButton",
                   command=self.mark_complete).pack(anchor="w", pady=(14, 0))

        self.pack(fill="both", expand=True)
        self.load_work_orders()

    def load_work_orders(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.work_orders = WorkOrder.for_technician(self.conn, self.user.user_id)
        for index, wo in enumerate(self.work_orders):
            tag = "odd" if index % 2 else "even"
            self.tree.insert("", "end", iid=wo.work_order_id, values=(
                wo.work_order_id, wo.outage_description, wo.scheduled_date, wo.status,
            ), tags=(tag,))

    def mark_complete(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("No Selection", "Select a work order first.")
            return
        work_order_id = int(selected[0])
        work_order = next(wo for wo in self.work_orders if wo.work_order_id == work_order_id)
        work_order.mark_complete(self.conn)
        self.load_work_orders()


class ComplaintForm(FormWindow):
    def __init__(self, master, conn, user):
        super().__init__(master, "Log Customer Complaint", "Log Customer Complaint")
        self.conn = conn
        self.user = user

        self._field_label(1, "Customer Name")
        self.name_entry = ttk.Entry(self.inner, width=34)
        self.name_entry.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 14))

        self._field_label(3, "Related Outage ID (optional)")
        self.outage_id_entry = ttk.Entry(self.inner, width=34)
        self.outage_id_entry.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 14))

        self._field_label(5, "Description")
        self.description_text = tk.Text(self.inner, width=34, height=5)
        style_text_widget(self.description_text)
        self.description_text.grid(row=6, column=0, columnspan=2, sticky="ew")

        self._submit_button(7, "Submit", self.submit)

    def submit(self):
        name = self.name_entry.get().strip()
        description = self.description_text.get("1.0", "end").strip()
        outage_id_raw = self.outage_id_entry.get().strip()

        outage_id = None
        if outage_id_raw:
            if not outage_id_raw.isdigit():
                messagebox.showerror("Validation Error", "Outage ID must be numeric.")
                return
            outage_id = int(outage_id_raw)

        try:
            Complaint.log(self.conn, self.user.user_id, name, description, outage_id=outage_id)
        except ValueError as error:
            messagebox.showerror("Validation Error", str(error))
            return

        messagebox.showinfo("Success", "Complaint logged.")
        self.master.destroy()


def main():
    conn = init_db()
    ensure_substations_loaded(conn)

    root = tk.Tk()
    root.title("GridCare-Lite")
    root.geometry("900x600")
    root.minsize(760, 520)
    configure_style(root)

    def show_login():
        for widget in root.winfo_children():
            widget.destroy()
        LoginWindow(root, conn, on_success=show_dashboard)

    def show_dashboard(user):
        for widget in root.winfo_children():
            widget.destroy()
        OutageDashboard(root, conn, user, on_logout=show_login)

    show_login()
    root.mainloop()
    conn.close()


if __name__ == "__main__":
    main()
