import argparse
import json
import os
import requests
import sys

def get_llm_response(prompt, model="qwen2.5:7b"):
    url = "http://localhost:11434/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False, "format": "json"}
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json().get('response', '{}')
    except Exception as e:
        print(f"LLM Error: {e}", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--prompt', default='prompts/few_shot.txt')
    parser.add_argument('--model', default='qwen2.5:7b')
    args = parser.parse_args()

    if not os.path.exists(args.input) or not os.path.exists(args.prompt): return

    with open(args.input, 'r') as f: metrics = json.load(f)
    with open(args.prompt, 'r') as f: template = f.read()

    prompt = template.replace('{{METRICS}}', json.dumps(metrics, indent=2))
    response_text = get_llm_response(prompt, model=args.model)
    
    if response_text:
        try:
            insights = json.loads(response_text)
            os.makedirs(os.path.dirname(args.output), exist_ok=True)
            with open(args.output, 'w') as f: json.dump(insights, f, indent=2, ensure_ascii=False)
            print(f"Saved: {args.output}")
        except Exception as e:
            print(f"JSON Error: {e}", file=sys.stderr)
    else:
        print("Empty LLM response", file=sys.stderr)

if __name__ == "__main__":
    main()
