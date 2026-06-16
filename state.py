import json
import os

STATE_FILE = os.path.join(os.path.dirname(__file__), "state.json")

DEFAULT_STATE = {
    "tier": 1,
    "city_index": 0,
    "exhausted_tier1": False,
    "exhausted_tier2": False,
    "keyword_cursors": {},
    "buyer_cursors": {},
    "last_transition": "",
    "last_run_date": "",
    "last_run_city": "",
    "last_run_cities": [],
    "last_run_city_count": 0,
    "rotation_cycle": 1,
}


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            s = json.load(f)
        for k, v in DEFAULT_STATE.items():
            s.setdefault(k, v)
        return s
    return dict(DEFAULT_STATE)


def save_state(state):
    temp_file = f"{STATE_FILE}.tmp"
    with open(temp_file, "w") as f:
        json.dump(state, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp_file, STATE_FILE)


def get_scheduled_city(state, cities, run_date):
    """Keep manual/retry runs on one city, but change city on a new date."""
    run_date = str(run_date)
    if state.get("last_run_date") == run_date and state.get("last_run_city"):
        return state["last_run_city"]
    return cities[int(state.get("city_index", 0)) % len(cities)]


def get_batch_start_index(state, cities, run_date):
    """Resume today's incomplete batch without changing tomorrow's rotation."""
    current_index = int(state.get("city_index", 0)) % len(cities)
    if state.get("last_run_date") != str(run_date):
        return current_index
    consumed = max(1, int(state.get("last_run_city_count", 1)))
    return (current_index - consumed) % len(cities)


def record_city_batch_progress(state, cities, run_date, used_cities):
    """Reserve towns as soon as they are worked so tomorrow does not repeat."""
    run_date = str(run_date)
    used_cities = list(used_cities)
    if not used_cities:
        return state
    if state.get("last_run_date") == run_date:
        previous_consumed = max(1, int(state.get("last_run_city_count", 1)))
        consumed = max(previous_consumed, len(used_cities))
        additional = consumed - previous_consumed
        if additional:
            state["city_index"] = (
                int(state.get("city_index", 0)) + additional
            ) % len(cities)
        state["last_run_cities"] = used_cities
        state["last_run_city"] = used_cities[0]
        state["last_run_city_count"] = consumed
        save_state(state)
        return state
    consumed = max(1, len(used_cities))
    next_index = int(state.get("city_index", 0)) + consumed
    cycles, next_index = divmod(next_index, len(cities))
    if cycles:
        state["rotation_cycle"] = int(state.get("rotation_cycle", 1)) + cycles
        state["last_transition"] = "national_rotation_restarted"
    else:
        state["last_transition"] = ""
    state["last_run_date"] = run_date
    state["last_run_city"] = used_cities[0]
    state["last_run_cities"] = list(used_cities)
    state["last_run_city_count"] = consumed
    state["city_index"] = next_index
    save_state(state)
    return state


def complete_city_batch(state, cities, run_date, used_cities):
    """Finalize the towns included in today's combined lead batch."""
    return record_city_batch_progress(state, cities, run_date, used_cities)
