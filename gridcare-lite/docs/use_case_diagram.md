# Use-Case Diagram — GridCare-Lite

Four roles, each restricted to their own screens in `app.py`
(`OutageDashboard.__init__` builds the button bar conditionally on
`user.role`).

```mermaid
flowchart LR
    Admin(["Administrator"])
    Engineer(["Engineer"])
    Technician(["Technician"])
    CS(["Customer-Service Rep"])

    Login(("Log in"))
    ViewDash(("View outage dashboard,\nfiltered by region/status"))
    LogOutage(("Log new outage\n+ severity"))
    AssignWO(("Assign work order\nto a technician"))
    ViewMyWO(("View my\nwork orders"))
    CompleteWO(("Mark work order\ncomplete"))
    LogComplaint(("Log customer\ncomplaint"))
    LinkComplaint(("Link complaint\nto an outage"))
    ViewComplaints(("View complaint\nhistory"))
    ViewReports(("View operational\nreports"))
    Logout(("Log out"))

    Admin --> Login
    Engineer --> Login
    Technician --> Login
    CS --> Login

    Login --> ViewDash
    Admin --> ViewDash
    Engineer --> ViewDash
    Technician --> ViewDash
    CS --> ViewDash

    Admin --> LogOutage
    Engineer --> LogOutage
    Admin --> AssignWO
    Technician --> ViewMyWO --> CompleteWO
    CS --> LogComplaint --> LinkComplaint
    CS --> ViewComplaints
    Admin --> ViewComplaints
    Admin --> ViewReports

    Admin --> Logout
    Engineer --> Logout
    Technician --> Logout
    CS --> Logout
```

## Actor -> permitted action matrix

| Action | Admin | Engineer | Technician | Customer Service |
|---|:---:|:---:|:---:|:---:|
| View outage dashboard, filter by region/status | Yes | Yes | Yes | Yes |
| Log new outage (with severity) | Yes | Yes | No | No |
| Assign work order | Yes | No | No | No |
| View own work orders | No | No | Yes | No |
| Mark work order complete | No | No | Yes | No |
| Log complaint | No | No | No | Yes |
| Link complaint to an outage | No | No | No | Yes (optional field) |
| View complaint history | Yes | No | No | Yes |
| View operational reports | Yes | No | No | No |
| Log out | Yes | Yes | Yes | Yes |

Enforced in two places, per the course spec's requirement that role
separation not be "merely hiding buttons":

1. **GUI** — `OutageDashboard` only adds the buttons relevant to
   `user.role`.
2. **Application logic** — e.g. `WorkOrder.for_technician(conn,
   technician_id)` only ever returns that technician's own rows; a
   technician can't fetch another technician's work orders even by calling
   the model method directly.

Still a known gap (see `docs/test_plan.md`, case GC-03): the model layer
itself doesn't re-check role for `WorkOrder.assign()` or similar - a
non-standard client bypassing the GUI could still call them directly.
Role separation today is GUI-button-level plus per-user data scoping, not
a role check inside every mutating method.
