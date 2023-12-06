from flask import Flask, request, render_template
import networkx as nx
import datetime
from database import get_additional_times, get_bus_schedules, get_transport_network

app = Flask(__name__)
graph = get_transport_network()
additional_times = get_additional_times()
bus_schedules = get_bus_schedules()
transfer_stops = ['Dworzec', 'Teatr', 'Most']

G = nx.Graph()

for node, edges in graph.items():
    for edge, weight in edges.items():
        G.add_edge(node, edge, weight=weight)

def get_paths(G, start, stop, direct_only, transfer_stops):
    all_paths = list(nx.all_simple_paths(G, start, stop))
    direct_paths = [path for path in all_paths if not any(stop in path[1:-1] for stop in transfer_stops)]
    if direct_only:
        if direct_paths:
            return direct_paths
        else:
            raise ValueError("Brak bezpośrednich połączeń między przystankami.")
    else:
        return all_paths

def get_departure_time(departure_time, bus_schedules, start, path):
    departure_hour = departure_time.hour
    departure_minute = departure_time.minute
    while True:
        try:
            possible_departures = [minute for minute in bus_schedules[start][path[1]] if minute >= departure_minute]
            if not possible_departures:
                # Brak późniejszych odjazdów w danej godzinie, przejdź do następnej godziny
                departure_hour += 1
                departure_minute = 0
                continue
            next_departure = min(possible_departures)
            
            if next_departure <= departure_minute:
                # Wybrany czas odjazdu jest wcześniejszy lub równy niż wybrany w formularzu, przejdź do kolejnego dostępnego odjazdu
                departure_hour += 1
                departure_minute = 0
                continue

            departure_minute = next_departure
            break
        except KeyError:
            raise ValueError(f"Brak danych w rozkładzie jazdy dla przystanku {path[1]}.")

    real_departure_hour = departure_hour % 24
    real_departure_time = datetime.datetime(departure_time.year, departure_time.month, departure_time.day, real_departure_hour, departure_minute)

    if real_departure_time <= departure_time:
        real_departure_time += datetime.timedelta(hours=24)

    return real_departure_time.hour, real_departure_time.minute

@app.route('/', methods=['GET', 'POST'])
def find_route():
    if request.method == 'POST':
        start = request.form.get('start')
        stop = request.form.get('stop')
        via_stop = request.form.get('via')
        departure_time_str = request.form.get('departureTime')
        departure_date_str = request.form.get('departureDate')
        direct_only = request.form.get('directOnly')
        sort_order = request.form.get('sortOrder')

        if not start or not stop or not departure_time_str or departure_time_str == '--:--' or departure_date_str == '':
            return '''<h2>Proszę wypełnić wszystkie pola.</h2>
                      <p>Musisz podać przystanek początkowy, końcowy oraz godzinę.</p>'''

        if start == stop:
            return '''<h2>Przystanek początkowy i końcowy nie mogą być takie same.</h2>
                      <p>Proszę wybrać różne przystanki.</p>'''

        if via_stop and (via_stop == start or via_stop == stop):
            return '''<h2>Przystanek pośredni nie może być taki sam jak początkowy lub końcowy.</h2>
                      <p>Proszę wybrać inny przystanek pośredni.</p>'''


        departure_date = datetime.datetime.strptime(departure_date_str, '%Y-%m-%d')
        departure_time = datetime.datetime.strptime(departure_time_str, '%H:%M').time()
        departure_datetime = datetime.datetime.combine(departure_date, departure_time)

        not_found_stops = [stop for stop in [start, stop] if stop not in graph]
        if not_found_stops:
            return f'''<h2>Nie znaleziono przystanku(-ów): "{', '.join(not_found_stops)}".</h2>
                       <p>Spróbuj poprawić nazwę(-y) przystanku(-ów).</p>'''

        try:
            paths = get_paths(G, start, stop, direct_only, transfer_stops)
        except ValueError:
            return '''<h2>Brak połączeń między przystankami.</h2>
                      <p>Spróbuj wybrać inne przystanki lub odznacz opcję "Tylko połączenia bezpośrednie".</p>'''

        results = []
        for path in paths:
            if not via_stop or (via_stop and via_stop != start and via_stop != stop and via_stop in path[1:-1]):
                time = sum(G[path[i]][path[i + 1]]['weight'] for i in range(len(path) - 1))
                for i in range(len(path) - 2):
                    time += additional_times.get((path[i], path[i + 1], path[i + 2]), 0)

                results.append((path, time))

        if not results:
            return '''<h2>Brak połączeń.</h2>
                      <p>Spróbuj wybrać inne przystanki lub odznacz opcję "Tylko połączenia bezpośrednie".</p>'''

        results.sort(key=lambda x: x[1])

        if sort_order == 'desc':
            results.reverse()

        rendered_results = []
        for path, time in results:
            transfers = sum(1 for stop in path if stop in transfer_stops) - int(start in transfer_stops) - int(stop in transfer_stops)
            departure_hour, departure_minute = get_departure_time(departure_datetime, bus_schedules, start, path)
            min_departure_datetime = departure_datetime.replace(hour=departure_hour % 24, minute=departure_minute)
            arrival_datetime = min_departure_datetime + datetime.timedelta(minutes=time)

            if min_departure_datetime.time() > arrival_datetime.time():
                arrival_datetime += datetime.timedelta(days=1)

            if arrival_datetime.date() > departure_date.date():
                arrival_datetime = arrival_datetime.replace(day=arrival_datetime.day - 1)
            
            if min_departure_datetime.day == departure_date.day and min_departure_datetime.time() < departure_time:
                min_departure_datetime += datetime.timedelta(days=1)
                arrival_datetime += datetime.timedelta(days=1)

            rendered_results.append({
                'start': start,
                'stop': stop,
                'via': via_stop,
                'path': ' -> '.join(path),
                'time': time,
                'transfers': transfers,
                'departureDate': min_departure_datetime.strftime('%d.%m.%Y'),
                'departureHour': min_departure_datetime.strftime('%H:%M'),
                'arrivalDate': arrival_datetime.strftime('%d.%m.%Y'),
                'arrivalHour': arrival_datetime.strftime('%H:%M')
            })
        return render_template('results.html', results=rendered_results)

    else:
        return render_template('index.html')
    
@app.route('/list', methods=['GET', 'POST'])
def list_stops():
    stops = graph.keys()
    return render_template('list.html', stops=stops)

@app.route('/schedule/<stop>', methods=['GET'])
def schedule(stop):
    # Pobierz rozkład jazdy dla danego przystanku
    schedules = bus_schedules[stop]

    # Przygotuj dane do wyświetlenia
    data = {}
    for destination, times in schedules.items():
        if destination in transfer_stops:
            data[destination] = [(hour * 60) % (24 * 60) for hour in range(24)]
            for i in range (24):
                data[destination][i]+=times.start

    return render_template('schedule.html', stop=stop, schedules=data)


if __name__ == '__main__':
    app.run(debug=True)