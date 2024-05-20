create table if not exists "tickets" (
    ticket_id UUID PRIMARY KEY,
    machine_id UUID,
    drink_id INT,
    created_at TIMESTAMP,
    milk INT,
    coffee INT
);
