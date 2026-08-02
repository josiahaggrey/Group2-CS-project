"""
GridCare-Lite: a Tkinter/SQLite outage and maintenance management system starter.

Run `python db.py` (or just run this file, which calls init_db() itself) then
`python seed_users.py` to create demo accounts, then `python app.py`.

Demo accounts (see seed_users.py):
    admin1 / Admin123!          (admin)
    engineer1 / Engineer123!    (engineer)
    tech1 / Tech123!            (technician)
    cs1 / CustService123!       (customer_service)

Role separation is enforced both in the GUI (which screens/buttons are shown) and
in application logic (queries are scoped by role, e.g. a technician only sees their
own work orders).
"""
import tkinter as tk
from tkinter import messagebox, ttk

import bcrypt

from db import init_db


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

        cur = self.conn.cursor()
        cur.execute("SELECT user_id, password_hash, role FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        if row is None:
            messagebox.showerror("Login Failed", "Invalid username or password.")
            return

        user_id, password_hash, role = row
        if not bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8")):
            messagebox.showerror("Login Failed", "Invalid username or password.")
            return

        self.on_success(user_id, username, role)


class OutageDashboard(tk.Frame):
    """Role-aware main screen: outage list plus role-appropriate action buttons."""

    def __init__(self, master, conn, user_id, username, role):
        super().__init__(master)
        self.conn = conn
        self.user_id = user_id
        self.username = username
        self.role = role
        master.title(f"GridCare-Lite - {username} ({role})")

        columns = ("outage_id", "substation", "description", "status", "reported_at")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=12)
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        button_bar = ttk.Frame(self)
        button_bar.pack(pady=5)
        ttk.Button(button_bar, text="Refresh", command=self.load_outages).pack(side="left", padx=4)

        if role in ("engineer", "admin"):
            ttk.Button(button_bar, text="Log New Outage",
                       command=self.open_new_outage_form).pack(side="left", padx=4)
        if role == "admin":
            ttk.Button(button_bar, text="Assign Work Order",
                       command=self.open_work_order_form).pack(side="left", padx=4)
        if role == "technician":
            ttk.Button(button_bar, text="My Work Orders",
                       command=self.open_technician_view).pack(side="left", padx=4)
        if role == "customer_service":
            ttk.Button(button_bar, text="Log Complaint",
                       command=self.open_complaint_form).pack(side="left", padx=4)

        self.pack(fill="both", expand=True)
        self.load_outages()

    def load_outages(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        cur = self.conn.cursor()
        cur.execute("""
            SELECT o.outage_id, s.name, o.description, o.status, o.reported_at
            FROM outages o
            LEFT JOIN substations s ON o.substation_id = s.substation_id
            ORDER BY o.reported_at DESC
        """)
        for row in cur.fetchall():
            self.tree.insert("", "end", values=row)

    def open_new_outage_form(self):
        NewOutageForm(tk.Toplevel(self.master), self.conn, self.user_id, on_saved=self.load_outages)

    def open_work_order_form(self):
        WorkOrderForm(tk.Toplevel(self.master), self.conn, on_saved=self.load_outages)

    def open_technician_view(self):
        TechnicianView(tk.Toplevel(self.master), self.conn, self.user_id)

    def open_complaint_form(self):
        ComplaintForm(tk.Toplevel(self.master), self.conn, self.user_id)


class NewOutageForm(tk.Frame):
    def __init__(self, master, conn, user_id, on_saved):
        super().__init__(master)
        self.conn = conn
        self.user_id = user_id
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
        cur = self.conn.cursor()
        cur.execute("SELECT substation_id, name FROM substations ORDER BY name")
        self.substations = cur.fetchall()
        self.substation_combo["values"] = [f"{sid}: {name}" for sid, name in self.substations]
        if self.substations:
            self.substation_combo.current(0)

    def submit(self):
        if not self.substations:
            messagebox.showerror(
                "No Substations", "No substations found. Import substations.csv via "
                "db.import_substations_from_csv() first.")
            return
        selection = self.substation_combo.current()
        substation_id = self.substations[selection][0]
        description = self.description_text.get("1.0", "end").strip()
        if not description:
            messagebox.showerror("Validation Error", "Description is required.")
            return

        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO outages (substation_id, reported_by, description) VALUES (?, ?, ?)",
            (substation_id, self.user_id, description),
        )
        self.conn.commit()
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
        cur = self.conn.cursor()
        cur.execute("SELECT outage_id, description FROM outages WHERE status = 'Open'")
        self.outages = cur.fetchall()
        self.outage_combo["values"] = [f"#{oid}: {desc[:40]}" for oid, desc in self.outages]
        if self.outages:
            self.outage_combo.current(0)

    def _load_technicians(self):
        cur = self.conn.cursor()
        cur.execute("SELECT user_id, username FROM users WHERE role = 'technician'")
        self.technicians = cur.fetchall()
        self.tech_combo["values"] = [f"{uid}: {name}" for uid, name in self.technicians]
        if self.technicians:
            self.tech_combo.current(0)

    def submit(self):
        if not self.outages:
            messagebox.showerror("No Open Outages", "There are no open outages to assign.")
            return
        if not self.technicians:
            messagebox.showerror("No Technicians", "No technician accounts exist yet.")
            return

        outage_id = self.outages[self.outage_combo.current()][0]
        technician_id = self.technicians[self.tech_combo.current()][0]
        scheduled_date = self.date_entry.get().strip()
        if not scheduled_date:
            messagebox.showerror("Validation Error", "Scheduled date is required.")
            return

        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO work_orders (outage_id, assigned_technician, scheduled_date, status) "
            "VALUES (?, ?, ?, 'Scheduled')",
            (outage_id, technician_id, scheduled_date),
        )
        cur.execute("UPDATE outages SET status = 'In Progress' WHERE outage_id = ?", (outage_id,))
        self.conn.commit()
        messagebox.showinfo("Success", "Work order assigned.")
        self.on_saved()
        self.master.destroy()


class TechnicianView(tk.Frame):
    def __init__(self, master, conn, technician_id):
        super().__init__(master)
        self.conn = conn
        self.technician_id = technician_id
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
        cur = self.conn.cursor()
        cur.execute("""
            SELECT w.work_order_id, o.description, w.scheduled_date, w.status
            FROM work_orders w
            JOIN outages o ON w.outage_id = o.outage_id
            WHERE w.assigned_technician = ?
            ORDER BY w.scheduled_date
        """, (self.technician_id,))
        for row in cur.fetchall():
            self.tree.insert("", "end", values=row)

    def mark_complete(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("No Selection", "Select a work order first.")
            return
        work_order_id = self.tree.item(selected[0])["values"][0]
        cur = self.conn.cursor()
        cur.execute("UPDATE work_orders SET status = 'Completed' WHERE work_order_id = ?", (work_order_id,))
        cur.execute("""
            UPDATE outages SET status = 'Resolved', resolved_at = CURRENT_TIMESTAMP
            WHERE outage_id = (SELECT outage_id FROM work_orders WHERE work_order_id = ?)
        """, (work_order_id,))
        self.conn.commit()
        self.load_work_orders()


class ComplaintForm(tk.Frame):
    def __init__(self, master, conn, user_id):
        super().__init__(master)
        self.conn = conn
        self.user_id = user_id
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

        if not name or not description:
            messagebox.showerror("Validation Error", "Customer name and description are required.")
            return

        outage_id = None
        if outage_id_raw:
            if not outage_id_raw.isdigit():
                messagebox.showerror("Validation Error", "Outage ID must be numeric.")
                return
            cur = self.conn.cursor()
            cur.execute("SELECT 1 FROM outages WHERE outage_id = ?", (outage_id_raw,))
            if cur.fetchone() is None:
                messagebox.showerror("Validation Error", "That outage ID does not exist.")
                return
            outage_id = int(outage_id_raw)

        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO complaints (outage_id, logged_by, customer_name, description) VALUES (?, ?, ?, ?)",
            (outage_id, self.user_id, name, description),
        )
        self.conn.commit()
        messagebox.showinfo("Success", "Complaint logged.")
        self.master.destroy()


def main():
    conn = init_db()
    root = tk.Tk()

    def show_dashboard(user_id, username, role):
        for widget in root.winfo_children():
            widget.destroy()
        OutageDashboard(root, conn, user_id, username, role)

    LoginWindow(root, conn, on_success=show_dashboard)
    root.mainloop()
    conn.close()


if __name__ == "__main__":
    main()
