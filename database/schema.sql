CREATE TABLE IF NOT EXISTS ORDERS (
    id UID UNIQUE PRIMARY KEY NOT NULL,
    title TEXT NOT NULL,
    creator TEXT NOT NULL,
    initiator TEXT NOT NULL,
    employee TEXT NOT NULL,
    department TEXT NOT NULL,
    create_date date NOT NULL,
    deadline date,
    close_date date,
    status_code TEXT NOT NULL,
    text_close TEXT NOT NULL
);
