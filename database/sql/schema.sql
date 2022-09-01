
CREATE TABLE IF NOT EXISTS ORDERS (
    id UID UNIQUE PRIMARY KEY NOT NULL,
    deleted boolean NOT NULL,
    create_date date NOT NULL,
    update_date date,
    issue_type TEXT NOT NULL,
    issue_idx TEXT NOT NULL,
    approving_date date not null,
    title TEXT NOT NULL,
    initiator TEXT NOT NULL,
    approving_employee TEXT NOT NULL,
    deadline TEXT NOT NULL,
    performance_note TEXT,
    status_code TEXT NOT NULL,
    close_date date,
    comment TEXT,
    reference TEXT
);

CREATE TABLE IF NOT EXISTS SUBORDERS(
    id UID UNIQUE PRIMARY KEY NOT NULL,
    id_orders UID NOT NULL,
    deleted boolean NOT NULL,
    create_date date NOT NULL,
    update_date date,
    employee TEXT NOT NULL,
    deadline TEXT NOT NULL,
    content TEXT NOT NULL,
    performance_note TEXT,
    status_code TEXT NOT NULL,
    close_date date,
    comment TEXT,

    FOREIGN KEY (id_orders)
       REFERENCES ORDERS (id)
);
