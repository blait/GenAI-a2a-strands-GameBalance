#!/bin/bash
# Show agent interaction trace for a query

QUERY="${1:-현재 게임 밸런스를 분석해줘}"

echo "📤 Sending query: $QUERY"
echo ""

curl -s -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"$QUERY\"}" | python3 << 'EOF'
import json, sys

data = json.load(sys.stdin)
traces = data['response']['metrics']['traces']

print("="*80)
print("🔄 AGENT INTERACTION LOG")
print("="*80)

cycle_count = 0
for trace in traces:
    if 'Cycle' not in trace['name']:
        continue
    
    cycle_count += 1
    print(f"\n{'─'*80}")
    print(f"📍 Cycle {cycle_count}")
    print(f"{'─'*80}")
    
    for child in trace.get('children', []):
        # Game Balance Agent thinking
        if child['name'] == 'stream_messages':
            msg = child.get('message', {})
            for content in msg.get('content', []):
                if 'text' in content and '<thinking>' in content['text']:
                    thinking = content['text'].split('<thinking>')[1].split('</thinking>')[0].strip()
                    print(f"\n🧠 [Game Balance Agent]")
                    print(f"   {thinking}")
                
                if 'toolUse' in content:
                    tool = content['toolUse']
                    agent_name = tool['name'].replace('call_', '').replace('_', ' ').title()
                    print(f"\n📞 [Game Balance Agent → {agent_name}]")
                    print(f"   Query: {tool['input']['query']}")
        
        # Other agents' responses
        if 'Tool:' in child['name']:
            agent = child['name'].replace('Tool: ', '').split(' - ')[0]
            agent_name = agent.replace('call_', '').replace('_', ' ').title()
            
            msg = child.get('message', {})
            for content in msg.get('content', []):
                if 'toolResult' in content:
                    result = content['toolResult']
                    text = result['content'][0]['text']
                    
                    # Agent thinking
                    if '<thinking>' in text:
                        thinking = text.split('<thinking>')[1].split('</thinking>')[0].strip()
                        print(f"\n💭 [{agent_name}]")
                        print(f"   {thinking}")
                    
                    # Agent response
                    response = text.split('</thinking>')[-1].strip()
                    print(f"\n✅ [{agent_name} → Game Balance Agent]")
                    # Truncate long responses
                    if len(response) > 300:
                        response = response[:300] + "..."
                    print(f"   {response}")

print(f"\n{'='*80}")
print("✅ FINAL ANSWER TO USER")
print("="*80)
final = data['response']['message']['content'][0]['text']
if '</thinking>' in final:
    final = final.split('</thinking>')[-1].strip()
print(final)

print(f"\n{'='*80}")
print("📊 SUMMARY")
print("="*80)
print(f"Total Cycles: {cycle_count}")
print(f"Total Time: {data['response']['metrics']['accumulated_metrics']['latencyMs']/1000:.2f}s")
print(f"Tokens: {data['response']['metrics']['accumulated_usage']['totalTokens']}")
print("="*80)
EOF
