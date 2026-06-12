import json
import os

STATE_FILE = os.path.join(os.path.dirname(__file__), "state.json")

DEFAULT_STATE = {
    "tier": 1,
    "city_index": 0,
    "exhausted_tier1": False,
    "exhausted_tier2": False,
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
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_today_city(state, tier1_cities, tier2_cities):
    if state["tier"] == 1:
        cities = tier1_cities
    else:
        cities = tier2_cities
    idx = state["city_index"] % len(cities)
    return cities[idx]


def advance_city(state, tier1_cities, tier2_cities):
    if state["tier"] == 1:
        cities = tier1_cities
    else:
        cities = tier2_cities

    state["city_index"] += 1

    if state["city_index"] >= len(cities):
        if state["tier"] == 1:
            state["exhausted_tier1"] = True
            state["tier"] = 2
            state["city_index"] = 0
        else:
            state["exhausted_tier2"] = True
            state["tier"] = 1
            state["city_index"] = 0

    save_state(state)
    return state
