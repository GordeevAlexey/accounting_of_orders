CREATE TABLE IF NOT EXISTS ORDERS (
    id UID UNIQUE PRIMARY KEY NOT NULL,
    deleted boolean NOT NULL,
    create_date date NOT NULL,
    update_date date,
    issue_type TEXT NOT NULL,
    issue_idx INTEGER NOT NULL,
    approving_date date,
    title TEXT NOT NULL,
    initiator TEXT NOT NULL,
    approving_employee TEXT NOT NULL,
    employee TEXT NOT NULL,
    deadline TEXT,
    status_code TEXT NOT NULL,
    close_date date,
    comment TEXT NOT NULL,
    reference TEXT
);
