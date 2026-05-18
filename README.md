# From Raw Detections to Real Intelligence

Este projeto implementa um pipeline completo de análise de comportamento de clientes em ambientes de retalho físico. Através da combinação de algoritmos clássicos de processamento de dados e IA Generativa local, o sistema transforma deteções anónimas em relatórios estratégicos acionáveis.

## 🚀 Estrutura do Projeto

O pipeline é composto por quatro módulos independentes que devem ser executados sequencialmente:

1.  **Stitcher** (`src/stitcher.py`): Reconstrói trajetórias individuais a partir de eventos anónimos usando heurísticas demográficas e espaciais.
2.  **Analytics** (`src/analytics.py`): Processa as trajetórias para calcular KPIs (Dwell Time, Stop Rate, Funil de Conversão) e detetar anomalias estatísticas ($2\sigma$).
3.  **Insights** (`src/insights.py`): Utiliza um LLM para interpretar as métricas e gerar observações estratégicas estruturadas.
4.  **Report** (`src/report.py`): Consolida os resultados num briefing semanal em Markdown formatado para gestores de loja.

## 📋 Pré-requisitos

*   **Python**: 3.10 ou superior.
*   **Ollama**: Instalado e configurado para inferência local.
*   **Modelo LLM**: `llama3.1:8b`.

## 🛠️ Instalação e Configuração

1.  Instalar dependências de Python:
    ```bash
    pip install -r requirements.txt
    ```

2.  Descarregar o modelo necessário no Ollama:
    ```bash
    ollama pull llama3.1:8b
    ```

## 💻 Execução do Pipeline

Para processar o ciclo completo de dados, execute os seguintes comandos por ordem:

```bash
# 1. Reconstrução de trajetórias
python src/stitcher.py --input data/events.csv --output output/journeys.csv

# 2. Cálculo de métricas e deteção de anomalias
python src/analytics.py --input output/journeys.csv --output output/metrics.json

# 3. Geração de insights via LLM
python src/insights.py --input output/metrics.json --output output/insights.json

# 4. Geração do relatório final
python src/report.py --input output/insights.json --output output/weekly_report.md
```

## 🧪 Avaliação e Qualidade

O sistema inclui um harness de avaliação para medir a precisão técnica e a integridade das respostas do LLM:

```bash
python evaluate.py --data data/events_validation.csv --output evaluation_report.json
```

### Resultados Obtidos (Baseline)
| Indicador | Performance |
| :--- | :--- |
| **Consistência de Trajetórias** | 100.0% |
| **Cobertura de Eventos** | 100.0% |
| **Completude do Percurso** | 63.1% |
| **Precisão Numérica (LLM)** | 100.0% |
| **Ausência de Alucinação** | 100.0% |

## 🏗️ Decisões de Arquitetura

*   **Privacidade por Design**: O sistema opera localmente e de forma anónima, em total conformidade com o RGPD.
*   **Princípio de Separação**: O LLM nunca acede aos dados brutos (CSV). Recebe apenas métricas pré-calculadas em JSON, garantindo 100% de rigor numérico.
*   **Engenharia de Prompts**: Utilização de estratégia *Few-Shot* para garantir que o modelo evita generalidades e se foca em IDs de zonas e números concretos.

---
**Autor**: Marco Alves [53589]
**Unidade Curricular**: IMLE - Interação com Modelos de Larga Escala
