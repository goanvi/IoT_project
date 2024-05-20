create table if not exists "tickets" (
    machine_id UUID PRIMARY KEY,
    ticket_id UUID,
    drink_id INT,
    created_at TIMESTAMP,
    milk INT,
    coffee INT
);
