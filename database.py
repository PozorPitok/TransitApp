import psycopg2

# Funkcja pobierająca dane z tabeli transport_network
def get_transport_network():
    conn = psycopg2.connect(
        dbname="transit",
        user="postgres",
        password="admin",
        host="localhost"
    )
    cur = conn.cursor()
    
    cur.execute("SELECT start_stop, end_stop, travel_time FROM transport_network")
    data = cur.fetchall()
    
    cur.close()
    conn.close()
    
    # Przekształcenie danych z postaci krotek do postaci słownika
    network_dict = {}
    for row in data:
        start_stop, end_stop, travel_time = row
        if start_stop not in network_dict:
            network_dict[start_stop] = {}
        network_dict[start_stop][end_stop] = travel_time
    
    return network_dict

# Funkcja pobierająca dane z tabeli additional_times
def get_additional_times():
    conn = psycopg2.connect(
        dbname="transit",
        user="postgres",
        password="admin",
        host="localhost"
    )
    cur = conn.cursor()
    
    cur.execute("SELECT stop1, stop2, stop3, additional_time FROM additional_times")
    data = cur.fetchall()
    
    cur.close()
    conn.close()
    
    # Przekształcenie danych z postaci krotek do postaci słownika
    additional_times_dict = {}
    for row in data:
        stop1, stop2, stop3, additional_time = row
        additional_times_dict[(stop1, stop2, stop3)] = additional_time
    
    return additional_times_dict

def get_bus_schedules():
    conn = psycopg2.connect(
        dbname="transit",
        user="postgres",
        password="admin",
        host="localhost"
    )
    cur = conn.cursor()
    
    cur.execute("SELECT stop_name, destination_stop, leading_minutes FROM bus_schedules")
    data = cur.fetchall()
    
    cur.close()
    conn.close()
    
    # Przekształcenie danych z postaci krotek do postaci słownika
    bus_schedules_dict = {}
    for row in data:
        stop_name, destination_stop, leading_minutes = row
        if stop_name not in bus_schedules_dict:
            bus_schedules_dict[stop_name] = {destination_stop: leading_minutes}
        else:
            bus_schedules_dict[stop_name][destination_stop] = leading_minutes
    
    return bus_schedules_dict