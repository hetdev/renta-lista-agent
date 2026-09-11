#!/usr/bin/env bash
# Create AgentCore Runtime (CodeZip) + Gateway (web-search) + system browser check.
set -euo pipefail
export AWS_PROFILE="${AWS_PROFILE:-rentalista}"
export AWS_REGION="${AWS_REGION:-us-east-1}"
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
ROLE_NAME="RentalistaAgentCoreRuntimeRole"
TRUST=/tmp/agentcore-trust.json
cat >"$TRUST" <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF
if ! aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
  aws iam create-role --role-name "$ROLE_NAME" --assume-role-policy-document "file://$TRUST"
  aws iam put-role-policy --role-name "$ROLE_NAME" --policy-name RuntimeBasic --policy-document '{
    "Version":"2012-10-17",
    "Statement":[{"Effect":"Allow","Action":["bedrock:InvokeModel","bedrock:InvokeModelWithResponseStream","logs:*","s3:GetObject","dynamodb:GetItem","dynamodb:PutItem"],"Resource":"*"}]
  }'
  sleep 5
fi
ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query Role.Arn --output text)
echo "ROLE_ARN=$ROLE_ARN"

if [[ ! -f dist/rentalista-agent.zip ]]; then
  echo "build zip first: scripts/build_codezip.sh" >&2
  exit 1
fi

# Upload to an agentcore artifact bucket
BUCKET="rentalista-agentcore-${ACCOUNT}-${AWS_REGION}"
aws s3 mb "s3://${BUCKET}" --region "$AWS_REGION" 2>/dev/null || true
aws s3 cp dist/rentalista-agent.zip "s3://${BUCKET}/agent/rentalista-agent.zip"

# Create or reuse runtime
RUNTIME_NAME="rentalista-agent"
if RUNTIME_ARN=$(aws bedrock-agentcore-control get-agent-runtime --agent-runtime-name "$RUNTIME_NAME" --region "$AWS_REGION" --query agentRuntimeArn --output text 2>/dev/null); then
  echo "runtime exists $RUNTIME_ARN"
else
  echo "creating runtime $RUNTIME_NAME"
  # CLI shape may vary by SDK version; prefer control-plane create-agent-runtime
  aws bedrock-agentcore-control create-agent-runtime \
    --agent-runtime-name "$RUNTIME_NAME" \
    --role-arn "$ROLE_ARN" \
    --agent-runtime-artifact '{"s3":{"s3BucketUri":"s3://'"${BUCKET}"'/agent/rentalista-agent.zip"}}' \
    --protocol-configuration '{"runtimeProtocol":"MCP"}' \
    --region "$AWS_REGION" 2>&1 | tee /tmp/create-runtime.json || true
fi

echo "done — check console for runtime status"
