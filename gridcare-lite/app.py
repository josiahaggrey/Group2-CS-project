"""
GridCare-Lite: a Tkinter/SQLite outage and maintenance management system.

The GUI never writes raw SQL - every screen calls a method on a domain
class from models.py (User, Substation, Outage, WorkOrder, Complaint).
Screens are responsible for layout and input handling only; all business
rules (validation, status transitions, what counts as "resolved") live in
the model classes so they're the same regardless of which screen calls them.

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

# Computed from this file's own location, not the current working directory -
# `python app.py` and `python gridcare-lite/app.py` must both find it.
DEFAULT_SUBSTATIONS_CSV = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "grid-analysis", "data", "cleaned", "substations_clean.csv",
)


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


class LoginWindow(tk.Frame):
    def __init__(self, master, conn, on_success):
        super().__init__(master)
        self.conn = conn
        self.on_success = on_success
        master.title("GridCare-Lite - Login")

        ttk.Label(self, text="Username:").grid(row=0, column=0, padx=8, pady=8, sticky="e")
        self.username_entry = ttk.Entry(self)
        self.username_entry.grid(row=0, column=1, padx=8, pady=8)

        ttk.Label(self, text="Password:").grid(row=1, column=0, padx=8, pady=8, sticky="e")
        self.password_entry = ttk.Entry(self, show="*")
        self.password_entry.grid(row=1, column=1, padx=8, pady=8)

        ttk.Button(self, text="Log In", command=self.attempt_login).grid(
            row=2, column=0, columnspan=2, pady=10)
        self.pack(padx=20, pady=20)
        self.username_entry.focus_set()
        master.bind("<Return>", lambda event: self.attempt_login())

    def attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showerror("Login Failed", "Please enter both a username and password.")
            return

        user = User.authenticate(self.conn, username, password)
        if user is None:
            messagebox.showerror("Login Failed", "Invalid username or password.")
            return

        self.on_success(user)


class OutageDashboard(tk.Frame):
    """Role-aware main screen: outage list plus role-appropriate action buttons."""

    def __init__(self, master, conn, user):
        super().__init__(master)
        self.conn = conn
        self.user = user
        master.title(f"GridCare-Lite - {user.username} ({user.role})")

        columns = ("outage_id", "substation", "description", "status", "reported_at")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=12)
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        button_bar = ttk.Frame(self)
        button_bar.pack(pady=5)
        ttk.Button(button_bar, text="Refresh", command=self.load_outages).pack(side="left", padx=4)

        if user.role in ("engineer", "admin"):
            ttk.Button(button_bar, text="Log New Outage",
                       command=self.open_new_outage_form).pack(side="left", padx=4)
        if user.role == "admin":
            ttk.Button(button_bar, text="Assign Work Order",
                       command=self.open_work_order_form).pack(side="left", padx=4)
        if user.role == "technician":
            ttk.Button(button_bar, text="My Work Orders",
                       command=self.open_technician_view).pack(side="left", padx=4)
        if user.role == "customer_service":
            ttk.Button(button_bar, text="Log Complaint",
                       command=self.open_complaint_form).pack(side="left", padx=4)

        self.pack(fill="both", expand=True)
        self.load_outages()

    def load_outages(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for outage in Outage.all(self.conn):
            self.tree.insert("", "end", values=(
                outage.outage_id, outage.substation_name, outage.description,
                outage.status, outage.reported_at,
            ))

    def open_new_outage_form(self):
        NewOutageForm(tk.Toplevel(self.master), self.conn, self.user, on_saved=self.load_outages)

    def open_work_order_form(self):
        WorkOrderForm(tk.Toplevel(self.master), self.conn, on_saved=self.load_outages)

    def open_technician_view(self):
        TechnicianView(tk.Toplevel(self.master), self.conn, self.user)

    def open_complaint_form(self):
        ComplaintForm(tk.Toplevel(self.master), self.conn, self.user)


class NewOutageForm(tk.Frame):
    def __init__(self, master, conn, user, on_saved):
        super().__init__(master)
        self.conn = conn
        self.user = user
        self.on_saved = on_saved
        master.title("Log New Outage")

        ttk.Label(self, text="Substation:").grid(row=0, column=0, padx=8, pady=8, sticky="e")
        self.substation_var = tk.StringVar()
        self.substation_combo = ttk.Combobox(self, textvariable=self.substation_var, state="readonly")
        self._load_substations()
        self.substation_combo.grid(row=0, column=1, padx=8, pady=8)

        ttk.Label(self, text="Description:").grid(row=1, column=0, padx=8, pady=8, sticky="ne")
        self.description_text = tk.Text(self, width=30, height=4)
        self.description_text.grid(row=1, column=1, padx=8, pady=8)

        ttk.Button(self, text="Submit", command=self.submit).grid(row=2, column=0, columnspan=2, pady=10)
        self.pack(padx=20, pady=20)

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


class WorkOrderForm(tk.Frame):
    def __init__(self, master, conn, on_saved):
        super().__init__(master)
        self.conn = conn
        self.on_saved = on_saved
        master.title("Assign Work Order")

        ttk.Label(self, text="Open Outage:").grid(row=0, column=0, padx=8, pady=8, sticky="e")
        self.outage_var = tk.StringVar()
        self.outage_combo = ttk.Combobox(self, textvariable=self.outage_var, state="readonly", width=40)
        self._load_open_outages()
        self.outage_combo.grid(row=0, column=1, padx=8, pady=8)

        ttk.Label(self, text="Technician:").grid(row=1, column=0, padx=8, pady=8, sticky="e")
        self.tech_var = tk.StringVar()
        self.tech_combo = ttk.Combobox(self, textvariable=self.tech_var, state="readonly")
        self._load_technicians()
        self.tech_combo.grid(row=1, column=1, padx=8, pady=8)

        ttk.Label(self, text="Scheduled Date (YYYY-MM-DD):").grid(row=2, column=0, padx=8, pady=8, sticky="e")
        self.date_entry = ttk.Entry(self)
        self.date_entry.grid(row=2, column=1, padx=8, pady=8)

        ttk.Button(self, text="Assign", command=self.submit).grid(row=3, column=0, columnspan=2, pady=10)
        self.pack(padx=20, pady=20)

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
        super().__init__(master)
        self.conn = conn
        self.user = user
        master.title("My Work Orders")

        columns = ("work_order_id", "outage_description", "scheduled_date", "status")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Button(self, text="Mark Selected Complete", command=self.mark_complete).pack(pady=5)
        self.pack(fill="both", expand=True)
        self.load_work_orders()

    def load_work_orders(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.work_orders = WorkOrder.for_technician(self.conn, self.user.user_id)
        for wo in self.work_orders:
            self.tree.insert("", "end", iid=wo.work_order_id, values=(
                wo.work_order_id, wo.outage_description, wo.scheduled_date, wo.status,
            ))

    def mark_complete(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("No Selection", "Select a work order first.")
            return
        work_order_id = int(selected[0])
        work_order = next(wo for wo in self.work_orders if wo.work_order_id == work_order_id)
        work_order.mark_complete(self.conn)
        self.load_work_orders()


class ComplaintForm(tk.Frame):
    def __init__(self, master, conn, user):
        super().__init__(master)
        self.conn = conn
        self.user = user
        master.title("Log Customer Complaint")

        ttk.Label(self, text="Customer Name:").grid(row=0, column=0, padx=8, pady=8, sticky="e")
        self.name_entry = ttk.Entry(self)
        self.name_entry.grid(row=0, column=1, padx=8, pady=8)

        ttk.Label(self, text="Related Outage ID (optional):").grid(row=1, column=0, padx=8, pady=8, sticky="e")
        self.outage_id_entry = ttk.Entry(self)
        self.outage_id_entry.grid(row=1, column=1, padx=8, pady=8)

        ttk.Label(self, text="Description:").grid(row=2, column=0, padx=8, pady=8, sticky="ne")
        self.description_text = tk.Text(self, width=30, height=4)
        self.description_text.grid(row=2, column=1, padx=8, pady=8)

        ttk.Button(self, text="Submit", command=self.submit).grid(row=3, column=0, columnspan=2, pady=10)
        self.pack(padx=20, pady=20)

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

    def show_dashboard(user):
        for widget in root.winfo_children():
            widget.destroy()
        OutageDashboard(root, conn, user)

    LoginWindow(root, conn, on_success=show_dashboard)
    root.mainloop()
    conn.close()


if __name__ == "__main__":
    main()
