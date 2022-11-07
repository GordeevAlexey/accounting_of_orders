
CREATE TABLE IF NOT EXISTS ORDERS (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    deleted boolean NOT NULL DEFAULT FALSE,
    create_date date NOT NULL default CURRENT_DATE,
    update_date date default null,
    issue_type TEXT NOT NULL,
    issue_idx TEXT NOT NULL,
    approving_date date not null,
    title TEXT NOT NULL,
    initiator TEXT NOT NULL,
    approving_employee TEXT NOT NULL,
    deadline TEXT NOT NULL,
    status_code TEXT NOT NULL,
    close_date date default null,
    comment TEXT default null,
    reference TEXT default null
);

CREATE TABLE IF NOT EXISTS SUBORDERS(
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    id_orders UUID NOT NULL,
    deleted boolean NOT NULL DEFAULT FALSE,
    create_date date NOT NULL default CURRENT_DATE,
    update_date date default null,
    employee TEXT NOT NULL,
    deadline TEXT NOT NULL,
    content TEXT NOT NULL,
    status_code TEXT NOT NULL,
    close_date date default null,
    comment TEXT,

    FOREIGN KEY (id_orders)
       REFERENCES ORDERS (id)
);

CREATE TABLE IF NOT EXISTS HISTORY(
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    id_orders UUID NOT NULL,
    id_suborders UUID NOT NULL,
    change_date date NOT NULL default CURRENT_DATE,
    data jsonb not null
);