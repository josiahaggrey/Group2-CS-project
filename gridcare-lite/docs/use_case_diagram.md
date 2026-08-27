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
    ViewDash(("View outage\ndashboard"))
    LogOutage(("Log new outage"))
    AssignWO(("Assign work order\nto a technician"))
    ViewMyWO(("View my\nwork orders"))
    CompleteWO(("Mark work order\ncomplete"))
    LogComplaint(("Log customer\ncomplaint"))
    LinkComplaint(("Link complaint\nto an outage"))

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
```

## Actor -> permitted action matrix

| Action | Admin | Engineer | Technician | Customer Service |
|---|:---:|:---:|:---:|:---:|
| View outage dashboard | Yes | Yes | Yes | Yes |
| Log new outage | Yes | Yes | No | No |
| Assign work order | Yes | No | No | No |
| View own work orders | No | No | Yes | No |
| Mark work order complete | No | No | Yes | No |
| Log complaint | No | No | No | Yes |
| Link complaint to an outage | No | No | No | Yes (optional field) |

Enforced in two places, per the course spec's requirement that role
separation not be "merely hiding buttons":

1. **GUI** — `OutageDashboard` only adds the buttons relevant to
   `user.role`.
2. **Application logic** — e.g. `WorkOrder.for_technician(conn,
   technician_id)` only ever returns that technician's own rows; a
   technician can't fetch another technician's work orders even by calling
   the model method directly.
