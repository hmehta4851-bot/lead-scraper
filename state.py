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
    """Keep retries on the active town until a day is formally completed."""
    run_date = str(run_date)
    if state.get("last_run_date") == run_date and state.get("last_run_city"):
        return state["last_run_city"]
    return cities[int(state.get("city_index", 0)) % len(cities)]


def get_batch_start_index(state, cities, run_date):
    """Resume the active batch from its original town index."""
    return int(state.get("city_index", 0)) % len(cities)


def record_city_batch_progress(state, cities, run_date, used_cities):
    """Persist the current day's worked towns without advancing rotation."""
    run_date = str(run_date)
    used_cities = list(used_cities)
    if not used_cities:
        return state
    state["last_run_date"] = run_date
    state["last_run_city"] = used_cities[0]
    state["last_run_cities"] = list(used_cities)
    state["last_run_city_count"] = max(1, len(used_cities))
    save_state(state)
    return state


def complete_city_batch(
    state,
    cities,
    run_date,
    used_cities,
    completed=True,
):
    """Finalize the active batch and advance rotation only after a good day."""
    used_cities = list(used_cities)
    already_completed = (
        completed
        and state.get("last_run_date") == str(run_date)
        and state.get("last_run_cities") == used_cities
        and state.get("last_transition") != "carryover_batch_pending"
    )
    if already_completed:
        return state

    state = record_city_batch_progress(state, cities, run_date, used_cities)
    if not completed or not used_cities:
        state["last_transition"] = "carryover_batch_pending"
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
    state["city_index"] = next_index
    save_state(state)
    return state
