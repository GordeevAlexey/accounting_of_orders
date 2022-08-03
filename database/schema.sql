CREATE TABLE IF NOT EXISTS HEAD (
    id UID UNIQUE PRIMARY KEY NOT NULL,
    creator UID NOT NULL,
    initiator UID NOT NULL,
    employee UID NOT NULL,
    department UID NOT NULL,
    create_date date NOT NULL,
    deadline date,
    close_date date,
    status_code UID NOT NULL,
    text_close TEXT NOT NULL,
    foreign key (department) references department(id),
    foreign key (creator) references users(id),
    foreign key (employee) references users(id),
    foreign key (initiator) references users(id)
);

CREATE TABLE IF NOT EXISTS USERS (
    id UID UNIQUE PRIMARY KEY NOT NULL,
    fio TEXT NOT NULL,
    usr_login TEXT NOT NULL,
    department UID NOT NULL,
    email TEXT UNIQUE,
    phone TEXT,
    foreign key (department) references department(id)
);

CREATE TABLE IF NOT EXISTS DEPARTMENT (
    id UID UNIQUE PRIMARY KEY NOT NULL,
    department_name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS STATUS (
    id UID UNIQUE PRIMARY KEY NOT NULL,
    status_code TEXT NOT NULL
);