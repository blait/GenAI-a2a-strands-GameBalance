#!/bin/bash
QUERY="${1:-현재 게임 밸런스를 분석해줘}"

RESPONSE=$(curl -s -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"$QUERY\"}")

if [ -z "$RESPONSE" ]; then
    echo "Error: No response from server"
    exit 1
fi

echo "$RESPONSE" | python3 -c "
import json, sys

try:
    data = json.load(sys.stdin)
except json.JSONDecodeError as e:
    print(f'Error: Failed to parse JSON - {e}')
    sys.exit(1)

traces = data['response']['metrics']['traces']
request_timestamp = data.get('request_timestamp', 0)

# Find new request start using timestamp
new_request_start = None
cycle_num = 0

for trace in traces:
    if 'Cycle' not in trace['name']:
        continue
    cycle_num += 1
    
    # Check if this cycle started after the request
    trace_start_time = trace.get('start_time', 0)
    if trace_start_time >= request_timestamp:
        if new_request_start is None:
            new_request_start = cycle_num

# Fallback: if no timestamp match, use last 2 cycles
if new_request_start is None:
    new_request_start = max(1, cycle_num - 1)

print()
print('='*80)
print('🎯 Query:', data['query'])
print(f'📊 Total Cycles: {cycle_num}')
print(f'🆕 New Request: Cycle {new_request_start} ~ {cycle_num}')
if request_timestamp > 0:
    print(f'⏰ Request Time: {request_timestamp:.2f}')
print('='*80)

cycle_num = 0
for trace in traces:
    if 'Cycle' not in trace['name']:
        continue
    
    cycle_num += 1
    
    # Skip old cycles
    if cycle_num < new_request_start:
        continue
    
    print(f\"\\n{'─'*80}\")
    print(f'📍 Cycle {cycle_num} 🆕')
    print('─'*80)
    
    for child in trace.get('children', []):
        if 'stream_messages' in child['name']:
            msg = child.get('message')
            if not msg:
                continue
            for c in msg.get('content', []):
                if 'text' in c and '<thinking>' in c['text']:
                    thinking = c['text'].split('<thinking>')[1].split('</thinking>')[0].strip()
                    print(f'\\n🧠 [Thinking]')
                    print(f'{thinking}\\n')
                
                if 'toolUse' in c:
                    tool = c['toolUse']
                    agent = tool['name'].replace('call_', '').replace('_', ' ').title()
                    print(f'📞 → {agent}: {tool[\"input\"][\"query\"]}\\n')
        
        if 'Tool:' in child['name']:
            agent = child['name'].replace('Tool: ', '').split(' - ')[0].replace('call_', '').replace('_', ' ').title()
            msg = child.get('message')
            if not msg:
                continue
            for c in msg.get('content', []):
                if 'toolResult' in c:
                    text = c['toolResult']['content'][0]['text']
                    response = text.split('</thinking>')[-1].strip()
                    print(f'✅ ← {agent}:\\n{response}\\n')

print('='*80)
print('✅ FINAL ANSWER')
print('='*80)
final = data['response']['message']['content'][0]['text']
if '</thinking>' in final:
    final = final.split('</thinking>')[-1].strip()
print(final)
print('='*80 + '\\n')
"
