import pandas as pd
import argparse
import json
from datetime import datetime
import os
from tqdm import tqdm

def load_zones(zones_path):
    with open(zones_path, 'r') as f:
        return json.load(f)

def stitch_events(events_df, zones_data):
    events_df['timestamp'] = pd.to_datetime(events_df['timestamp'])
    events_df = events_df.sort_values('timestamp')

    zones = zones_data['zones']
    active_people = {}
    next_person_id = 1
    completed_visits = []
    attribute_map = {}

    def get_person_id():
        nonlocal next_person_id
        pid = f"P_{next_person_id:04d}"
        next_person_id += 1
        return pid

    for _, event in tqdm(events_df.iterrows(), total=len(events_df), desc="Stitching"):
        ts = event['timestamp']
        z_id = event['zone_id']
        e_type = event['event_type']
        gender = event['gender']
        age = event['age_range']
        duration = event['duration_s']

        if e_type == 'entry':
            potential_pids = attribute_map.get((gender, age), [])
            best_match = None
            min_time_diff = float('inf')

            for pid in potential_pids:
                p = active_people[pid]
                if p['current_zone'] is None and p['last_exit_time'] is not None:
                    time_diff = (ts - p['last_exit_time']).total_seconds()
                    
                    if 0 <= time_diff <= 300:
                        if p['last_zone'] in zones and z_id in zones[p['last_zone']]['walk_seconds']:
                            if time_diff < zones[p['last_zone']]['walk_seconds'][z_id]:
                                continue
                        
                        if time_diff < min_time_diff:
                            min_time_diff = time_diff
                            best_match = pid
            
            if best_match:
                active_people[best_match]['current_zone'] = z_id
                active_people[best_match]['current_entry_time'] = ts
            elif z_id in ['Z_E1', 'Z_E2']:
                new_pid = get_person_id()
                active_people[new_pid] = {
                    'last_zone': None,
                    'last_exit_time': None,
                    'current_zone': z_id,
                    'current_entry_time': ts,
                    'gender': gender,
                    'age_range': age,
                    'visits': []
                }
                if (gender, age) not in attribute_map:
                    attribute_map[(gender, age)] = []
                attribute_map[(gender, age)].append(new_pid)
            else:
                continue

        elif e_type == 'linger':
            for pid in attribute_map.get((gender, age), []):
                if active_people[pid]['current_zone'] == z_id:
                    active_people[pid]['current_dwell'] = duration
                    break
        
        elif e_type == 'exit':
            for pid in attribute_map.get((gender, age), []):
                p = active_people[pid]
                if p['current_zone'] == z_id:
                    completed_visits.append({
                        'person_id': pid,
                        'zone_id': z_id,
                        'entry_time': p['current_entry_time'],
                        'exit_time': ts,
                        'dwell_s': p.get('current_dwell', 0),
                        'gender': gender,
                        'age_range': age,
                        'visit_date': ts.date(),
                        'hour_of_day': p['current_entry_time'].hour
                    })
                    p['last_zone'] = z_id
                    p['last_exit_time'] = ts
                    p['current_zone'] = None
                    p.pop('current_dwell', None)
                    break

    return pd.DataFrame(completed_visits)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    zones_path = 'data/zones.json'
    if not os.path.exists(zones_path):
        return

    zones_data = load_zones(zones_path)
    events_df = pd.read_csv(args.input)
    journeys_df = stitch_events(events_df, zones_data)
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    journeys_df.to_csv(args.output, index=False)

if __name__ == "__main__":
    main()
