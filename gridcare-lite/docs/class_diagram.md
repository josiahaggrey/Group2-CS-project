# Class Diagram — GridCare-Lite

Matches `models.py`. Every class owns its own data access and behaviour;
`app.py` only calls these methods (see `docs/architecture.md` at the repo
root for why).

```mermaid
classDiagram
    class User {
        +int user_id
        +str username
        +str role
        +str password_hash
        +check_password(password) bool
        +hash_password(password)$ str
        +create(conn, username, password, role)$ User
        +find_by_username(conn, username)$ User
        +authenticate(conn, username, password)$ User
        +find_by_role(conn, role)$ list~User~
    }

    class Substation {
        +int substation_id
        +str name
        +str region
        +all(conn)$ list~Substation~
        +regions(conn)$ list~str~
        +exists(conn, substation_id)$ bool
        +import_from_csv(conn, csv_path)$ int
    }

    class Outage {
        +int outage_id
        +int substation_id
        +int reported_by
        +str description
        +str severity
        +str status
        +str reported_at
        +str resolved_at
        +report(conn, substation_id, reported_by, description, severity)$ Outage
        +all(conn)$ list~Outage~
        +search(conn, region, status)$ list~Outage~
        +open_outages(conn)$ list~Outage~
        +mark_in_progress(conn)
        +mark_resolved(conn)
    }

    class WorkOrder {
        +int work_order_id
        +int outage_id
        +int assigned_technician
        +str scheduled_date
        +str status
        +assign(conn, outage_id, technician_id, scheduled_date)$ WorkOrder
        +for_technician(conn, technician_id)$ list~WorkOrder~
        +mark_complete(conn)
    }

    class Complaint {
        +int complaint_id
        +int outage_id
        +int logged_by
        +str customer_name
        +str description
        +str logged_at
        +log(conn, logged_by, customer_name, description, outage_id)$ Complaint
        +all(conn)$ list~Complaint~
    }

    class Report {
        +status_counts(conn)$ dict
        +severity_counts(conn)$ dict
        +outages_by_region(conn)$ list~tuple~
        +average_resolution_hours(conn)$ float
        +summary(conn)$ dict
    }

    User "1" --> "0..*" Outage : reports (reported_by)
    User "1" --> "0..*" WorkOrder : assigned to (technician)
    User "1" --> "0..*" Complaint : logs (logged_by)
    Substation "1" --> "0..*" Outage : location of
    Outage "1" --> "0..1" WorkOrder : resolved via
    Outage "1" --> "0..*" Complaint : optionally linked to
    Report ..> Outage : reads
    Report ..> Complaint : reads
```

## Notes

- **State transitions live on the class that owns them, once.**
  `WorkOrder.assign()` also flips its outage to `"In Progress"`;
  `WorkOrder.mark_complete()` also flips its outage to `"Resolved"`. A screen
  never sets `outage.status` directly, so the two tables can't drift apart.
- **Validation raises `ValueError`, screens catch it.** E.g. an empty outage
  description, a missing scheduled date, or a `Complaint` linked to a
  nonexistent outage ID all raise from the model; `app.py` shows the message
  in a `messagebox.showerror`.
- **`Substation` is intentionally minimal** — it's a local reference copy of
  `grid-analysis`'s cleaned data, not the canonical source. See
  `import_from_csv()` and the root architecture doc.
- **`Outage.report()` validates two things the schema can't enforce alone:**
  the substation must exist (`Substation.exists()`), and there must not
  already be an open outage with the exact same description at that
  substation - both raise `ValueError` rather than silently succeeding.
- **`Report` is read-only** — it never appears on the left side of an
  association above; every method only issues `SELECT`s over data the
  other classes already wrote. Kept separate from `Outage`/`Complaint`
  rather than added as more classmethods on them, since aggregating across
  the whole table is a different responsibility from managing one row.
