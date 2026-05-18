import pandas as pd
import argparse
import json
import os
import numpy as np

def calculate_metrics(journeys_df):
    metrics = {}
    
    journeys_df['entry_time'] = pd.to_datetime(journeys_df['entry_time'])
    journeys_df['exit_time'] = pd.to_datetime(journeys_df['exit_time'])
    journeys_df['visit_date'] = pd.to_datetime(journeys_df['visit_date'])
    
    metrics['traffic'] = {}
    
    daily = journeys_df.groupby('visit_date')['person_id'].nunique()
    metrics['traffic']['daily_unique_visitors'] = daily.reset_index().rename(columns={'visit_date': 'date', 'person_id': 'count'}).to_dict(orient='records')
    for item in metrics['traffic']['daily_unique_visitors']:
        item['date'] = str(item['date'].date()) if hasattr(item['date'], 'date') else str(item['date'])

    hourly = journeys_df.groupby(['visit_date', 'hour_of_day'])['person_id'].nunique()
    metrics['traffic']['hourly_unique_visitors'] = []
    for (date, hour), count in hourly.items():
        metrics['traffic']['hourly_unique_visitors'].append({
            'date': str(date.date()) if hasattr(date, 'date') else str(date),
            'hour': int(hour),
            'count': int(count)
        })

    person_v = journeys_df.groupby('person_id').agg({'entry_time': 'min', 'exit_time': 'max'})
    person_v['duration'] = (person_v['exit_time'] - person_v['entry_time']).dt.total_seconds()
    metrics['traffic']['avg_visit_duration_seconds'] = float(person_v['duration'].mean())

    metrics['zones'] = {}
    z_traffic = journeys_df.groupby('zone_id')['person_id'].nunique()
    z_dwell = journeys_df[journeys_df['dwell_s'] > 0].groupby('zone_id')['dwell_s'].mean()
    z_linger = journeys_df[journeys_df['dwell_s'] > 0].groupby('zone_id')['person_id'].nunique()
    z_stop_rate = (z_linger / z_traffic).fillna(0)
    
    metrics['zones']['performance'] = []
    for zone in z_traffic.index:
        metrics['zones']['performance'].append({
            'zone_id': zone,
            'unique_visitors': int(z_traffic[zone]),
            'avg_dwell_seconds': float(z_dwell.get(zone, 0)),
            'stop_rate': float(z_stop_rate.get(zone, 0))
        })

    seqs = journeys_df.sort_values(['person_id', 'entry_time']).groupby('person_id')['zone_id'].apply(lambda x: " -> ".join(x))
    top_seqs = seqs.value_counts().head(10)
    metrics['zones']['top_sequences'] = [{'sequence': str(s), 'count': int(c)} for s, c in top_seqs.items()]

    metrics['funnel'] = {}
    total = journeys_df['person_id'].nunique()
    metrics['funnel']['total_visitors'] = int(total)
    
    def get_prefix(z_id):
        if z_id == 'Z_CK': return 'Z_CK'
        parts = z_id.split('_')
        return f"Z_{parts[1][0]}" if len(parts) >= 2 else z_id

    journeys_df['zone_prefix'] = journeys_df['zone_id'].apply(get_prefix)
    f_reach = journeys_df.groupby('zone_prefix')['person_id'].nunique()
    metrics['funnel']['reach_by_type'] = {str(k): int(v) for k, v in f_reach.items()}
    
    checkout_z = ['Z_C1', 'Z_C2', 'Z_C3', 'Z_CK']
    v_checkout = journeys_df[journeys_df['zone_id'].isin(checkout_z)]['person_id'].unique()
    metrics['funnel']['conversion_rate'] = float(len(v_checkout) / total) if total > 0 else 0
    metrics['funnel']['reached_checkout'] = int(len(v_checkout))

    non_conv_pids = set(journeys_df['person_id'].unique()) - set(v_checkout)
    non_conv_df = journeys_df[journeys_df['person_id'].isin(non_conv_pids)].drop_duplicates('person_id')
    metrics['funnel']['non_converted_profile'] = non_conv_df.groupby(['gender', 'age_range']).size().reset_index(name='count').to_dict(orient='records') if not non_conv_df.empty else []

    metrics['demographics'] = {}
    demo_h = journeys_df.groupby(['hour_of_day', 'gender', 'age_range'])['person_id'].nunique().unstack(level=[1, 2]).fillna(0)
    metrics['demographics']['hourly_distribution'] = []
    for h, row in demo_h.iterrows():
        entry = {'hour': int(h)}
        for (g, a), c in row.items(): entry[f"{g}_{a}"] = int(c)
        metrics['demographics']['hourly_distribution'].append(entry)

    seg_dwell = journeys_df[journeys_df['dwell_s'] > 0].groupby(['gender', 'age_range', 'zone_id'])['dwell_s'].mean().unstack(level=2).fillna(0)
    metrics['demographics']['segment_dwell_by_zone'] = []
    for (g, a), row in seg_dwell.iterrows():
        metrics['demographics']['segment_dwell_by_zone'].append({
            'gender': str(g), 'age_range': str(a), 'zones': {str(z): float(d) for z, d in row.items()}
        })

    metrics['anomalies'] = []
    dates = sorted(journeys_df['visit_date'].unique())
    if len(dates) >= 7:
        train = journeys_df[journeys_df['visit_date'].isin(dates[:6])]
        stats = train.groupby(['hour_of_day', 'zone_id'])['person_id'].nunique().reset_index().groupby(['hour_of_day', 'zone_id'])['person_id'].agg(['mean', 'std']).fillna(0)
        test = journeys_df[journeys_df['visit_date'] == dates[6]].groupby(['hour_of_day', 'zone_id'])['person_id'].nunique().reset_index()
        
        for _, row in test.iterrows():
            h, z, c = row['hour_of_day'], row['zone_id'], row['person_id']
            if (h, z) in stats.index:
                m, s = stats.loc[(h, z), 'mean'], stats.loc[(h, z), 'std']
                if s > 0 and abs(c - m) > 2 * s:
                    metrics['anomalies'].append({
                        'date': str(dates[6].date()) if hasattr(dates[6], 'date') else str(dates[6]),
                        'hour': int(h), 'zone_id': str(z), 'observed': int(c),
                        'expected_mean': float(m), 'expected_std': float(s), 'deviation_sigma': float((c - m) / s)
                    })
    return metrics

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    if not os.path.exists(args.input): return
    journeys_df = pd.read_csv(args.input)
    metrics = calculate_metrics(journeys_df)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f: json.dump(metrics, f, indent=2)

if __name__ == "__main__":
    main()
