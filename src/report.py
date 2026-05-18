import argparse
import json
import os

def generate_markdown_report(insights_data):
    report = "# Relatório Semanal de Inteligência de Retalho\n\n"
    report += "## 1. Resumo Executivo\n"
    resumo = insights_data.get('resumo_executivo', 'N/A')
    if isinstance(resumo, list):
        for item in resumo: report += f"- {item}\n"
        report += "\n"
    else:
        report += str(resumo) + "\n\n"
    
    insights = insights_data.get('insights', [])
    def check_cat(ins, cat):
        c = ins.get('categoria', '')
        return cat in c.split('|') or cat == c

    sections = [
        ("2. Performance de Tráfego", "trafego"),
        ("3. Análise de Zonas", "zona"),
        ("4. Funil de Clientes", "funil"),
        ("5. Anomalias da Semana", "anomalia")
    ]

    for title, cat in sections:
        report += f"## {title}\n"
        found = False
        for ins in insights:
            if check_cat(ins, cat):
                report += f"### {ins.get('titulo')}\n"
                report += f"**Observação:** {ins.get('observacao')}\n\n"
                report += f"**Implicação:** {ins.get('implicacao')}\n\n"
                found = True
        if not found: report += "Sem insights relevantes esta semana.\n\n"

    report += "## 6. Recomendações para a Próxima Semana\n"
    urg_m = {'imediata': 0, 'esta_semana': 1, 'proximo_mes': 2}
    sorted_recs = sorted(insights, key=lambda x: urg_m.get(x.get('urgencia'), 3))
    
    for i, ins in enumerate(sorted_recs[:5]):
        report += f"{i+1}. **[{ins.get('urgencia').upper()}] {ins.get('titulo')}**: {ins.get('recomendacao')}\n"
    
    if not sorted_recs: report += "Sem recomendações específicas.\n"
    return report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    if not os.path.exists(args.input): return
    with open(args.input, 'r') as f: insights_data = json.load(f)
    report_md = generate_markdown_report(insights_data)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f: f.write(report_md)

if __name__ == '__main__':
    main()
