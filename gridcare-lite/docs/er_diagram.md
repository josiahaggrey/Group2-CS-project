# Entity-Relationship Diagram — GridCare-Lite (`gridcare.db`)

Generated from the schema in `db.py`.

```mermaid
erDiagram
    USERS ||--o{ OUTAGES : reports
    USERS ||--o{ WORK_ORDERS : "is assigned"
    USERS ||--o{ COMPLAINTS : logs
    SUBSTATIONS ||--o{ OUTAGES : "location of"
    OUTAGES ||--o| WORK_ORDERS : "resolved via"
    OUTAGES ||--o{ COMPLAINTS : "optionally linked to"

    USERS {
        int user_id PK
        string username UK
        string password_hash "bcrypt"
        string role "admin / engineer / technician / customer_service"
    }

    SUBSTATIONS {
        int substation_id PK
        string name
        string region
    }

    OUTAGES {
        int outage_id PK
        int substation_id FK
        int reported_by FK "-> users.user_id"
        string description
        string status "Open / In Progress / Resolved"
        string reported_at
        string resolved_at
    }

    WORK_ORDERS {
        int work_order_id PK
        int outage_id FK
        int assigned_technician FK "-> users.user_id"
        string scheduled_date
        string status "Pending / Scheduled / Completed"
    }

    COMPLAINTS {
        int complaint_id PK
        int outage_id FK "nullable"
        int logged_by FK "-> users.user_id"
        string customer_name
        string description
        string logged_at
    }
```

## Notes

- SQLite's `CHECK` constraints on `role`/`status` columns enforce the
  enumerations shown above at the database layer, not just in Python
  (`db.py`) — a direct `INSERT`/`UPDATE` outside `models.py` would still be
  rejected for an invalid role or status.
- `work_orders.outage_id` is not declared `UNIQUE` in the schema, so the
  "one outage, at most one active work order" rule shown as `||--o|` above
  is an application-level convention (`WorkOrder.assign` is only ever called
  from `WorkOrderForm` against `Outage.open_outages()`), not a DB constraint.
  Worth revisiting if GridCare-Lite ever needs to support re-assigning a
  failed repair.
