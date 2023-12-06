DROP TABLE bus_schedules;

CREATE TABLE transport_network (
    id SERIAL PRIMARY KEY,
    start_stop VARCHAR(50),
    end_stop VARCHAR(50),
    travel_time INTEGER
);

CREATE TABLE additional_times (
    id SERIAL PRIMARY KEY,
    stop1 VARCHAR(50),
    stop2 VARCHAR(50),
    stop3 VARCHAR(50),
    additional_time INTEGER
);

CREATE TABLE bus_schedules (
    id SERIAL PRIMARY KEY,
    stop_name VARCHAR(50) NOT NULL,
    destination_stop VARCHAR(50) NOT NULL,
    leading_minutes INTEGER[]
);
