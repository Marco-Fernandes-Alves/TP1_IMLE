import argparse
import json
import os
import pandas as pd
import re

def calculate_metrics(events_path, journeys_path, metrics_path, insights_path):
    events_df = pd.read_csv(events_path)
    journeys_df = pd.read_csv(journeys_path)
    
    with open(metrics_path, 'r') as f: metrics_data = json.load(f)
    with open(insights_path, 'r') as f: insights_data = json.load(f)
    
    report = {}
    total_p = journeys_df['person_id'].nunique()
    
    overlaps = 0
    for _, g in journeys_df.groupby('person_id'):
        g = g.sort_values('entry_time')
        if (pd.to_datetime(g['exit_time']) > pd.to_datetime(g['entry_time']).shift(-1)).any(): overlaps += 1
    report['consistencia'] = (1 - overlaps / total_p) * 100 if total_p > 0 else 100
    
    report['cobertura'] = min(100, (len(journeys_df) * 2 / len(events_df)) * 100)
    
    complete = 0
    for _, g in journeys_df.groupby('person_id'):
        g = g.sort_values('entry_time')
        s, e = g.iloc[0]['zone_id'], g.iloc[-1]['zone_id']
        if s.startswith('Z_E') and (e.startswith('Z_E') or e == 'Z_CK'): complete += 1
    report['completude'] = (complete / total_p) * 100 if total_p > 0 else 0
    
    m_str = json.dumps(metrics_data)
    total_n, valid_n = 0, 0
    for ins in insights_data.get('insights', []):
        nums = re.findall(r'\d+(?:\.\d+)?', ins.get('observacao', ''))
        for n in nums:
            total_n += 1
            if n in m_str: valid_n += 1
    report['precisao_numerica'] = (valid_n / total_n * 100) if total_n > 0 else 100.0
    report['ausencia_alucinacao'] = report['precisao_numerica']
    
    n_metrics = len(metrics_data.get('anomalies', []))
    n_insights = len([i for i in insights_data.get('insights', []) if 'anomalia' in i.get('categoria', '')])
    report['deteccao_anomalias'] = min(100, (n_insights / n_metrics * 100)) if n_metrics > 0 else (100.0 if n_insights == 0 else 0.0)
    
    return report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    
    res = calculate_metrics(
        args.data, 
        'output/journeys.csv', 
        'output/metrics.json', 
        'output/insights.json'
    )
    
    with open(args.output, 'w') as f: json.dump(res, f, indent=2)
    print(res)

if __name__ == '__main__':
    main()
