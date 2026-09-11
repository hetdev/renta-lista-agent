#!/usr/bin/env bash
# Smoke Bedrock + AgentCore control plane from the rentalista profile.
set -euo pipefail
export AWS_PROFILE="${AWS_PROFILE:-rentalista}"
export AWS_REGION="${AWS_REGION:-us-east-1}"
echo "== identity =="
aws sts get-caller-identity
echo "== bedrock nova micro =="
aws bedrock-runtime converse \
  --region "$AWS_REGION" \
  --model-id amazon.nova-micro-v1:0 \
  --messages '[{"role":"user","content":[{"text":"Responde solo: hola"}]}]' \
  --inference-config '{"maxTokens":20}' >/tmp/bedrock-smoke.json
python3 -c "import json;print(json.load(open('/tmp/bedrock-smoke.json'))['output']['message']['content'][0]['text'])"
echo "== agentcore lists =="
aws bedrock-agentcore-control list-agent-runtimes --region "$AWS_REGION" || true
aws bedrock-agentcore-control list-gateways --region "$AWS_REGION" || true
aws bedrock-agentcore-control list-browsers --region "$AWS_REGION" || true
echo "smoke ok"
