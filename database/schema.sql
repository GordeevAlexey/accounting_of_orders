CREATE TABLE IF NOT EXISTS ORDERS (
    id UID UNIQUE PRIMARY KEY NOT NULL,
    deleted boolean NOT NULL,
    create_date date NOT NULL,
    update_date date,
    issue_type TEXT NOT NULL,
    initiator TEXT NOT NULL,
    title TEXT NOT NULL,
    issue_date date,
    employee TEXT NOT NULL,
    status_code TEXT NOT NULL,
    close_date date,
    comment TEXT NOT NULL,
    reference TEXT
);
