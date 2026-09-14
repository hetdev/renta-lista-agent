#!/usr/bin/env bash
# Copy the current API package (master account Lambda, behind pi4y909mlf) to the member-account
# Lambda `rentalista-api` (behind lnfsntpv6j, CloudFront origin). Verifies GET /draft through
# CloudFront and rolls back to the previous package if it does not answer 200.
# Both Lambdas: python3.13, arm64, handler lambda_handler.handler (verified 14 Sep 2026).
set -euo pipefail
export AWS_REGION="${AWS_REGION:-us-east-1}"
MASTER_PROFILE="${MASTER_PROFILE:-rentalista-dev2}"   # account 690968743338
MEMBER_PROFILE="${MEMBER_PROFILE:-rentalista}"        # account 697020387519
FN=rentalista-api
BASE=https://deuhmh4dvlr6i.cloudfront.net
WORK="$(mktemp -d)"

echo "== download current packages =="
curl -sS -o "$WORK/master.zip" "$(AWS_PROFILE=$MASTER_PROFILE aws lambda get-function --function-name $FN --query Code.Location --output text)"
curl -sS -o "$WORK/member-backup.zip" "$(AWS_PROFILE=$MEMBER_PROFILE aws lambda get-function --function-name $FN --query Code.Location --output text)"
unzip -p "$WORK/master.zip" rentalista/api/main.py | grep -q 'def get_draft' || { echo "master package has no get_draft route; abort"; exit 1; }
echo "master: $(du -h "$WORK/master.zip" | cut -f1)  backup: $(du -h "$WORK/member-backup.zip" | cut -f1)  ($WORK)"

echo "== deploy to member =="
AWS_PROFILE=$MEMBER_PROFILE aws lambda update-function-code --function-name $FN --zip-file "fileb://$WORK/master.zip" --query '[CodeSha256,LastUpdateStatus]' --output text
AWS_PROFILE=$MEMBER_PROFILE aws lambda wait function-updated --function-name $FN

echo "== verify through CloudFront =="
C=$(curl -sS --max-time 30 -X POST "$BASE/api/v1/cases?locale=en")
ID=$(echo "$C" | python3 -c 'import sys,json; print(json.load(sys.stdin)["case_id"])')
TOK=$(echo "$C" | python3 -c 'import sys,json; print(json.load(sys.stdin)["case_token"])')
curl -sS -o /dev/null --max-time 30 -X PUT "$BASE/api/v1/cases/$ID/profile" -H 'Content-Type: application/json' -H "x-case-token: $TOK" \
  -d '{"resident_2025":true,"not_required_accounting":true,"initial_filing":true,"timely_filing":true,"iva_responsible_dec_31":false,"labor_income_only":true,"national_financial_income":true,"assets_only_colombia":true,"no_foreign_currency":true,"no_excluded_facts":true,"dependents_confirmed":1,"absence_attestations":{"pensiones":true,"dividendos":true,"ganancias_ocasionales":true}}'
curl -sS -o /dev/null --max-time 30 -X POST "$BASE/api/v1/cases/$ID/jobs" -H 'Content-Type: application/json' -H "x-case-token: $TOK" -d '{"command":"PREPARE_DRAFT","idempotency_key":"deploy-check"}'
code=$(curl -sS -o "$WORK/draft.json" -w '%{http_code}' --max-time 30 "$BASE/api/v1/cases/$ID/draft" -H "x-case-token: $TOK")
echo "GET /draft -> $code $(head -c 120 "$WORK/draft.json")"
echo "GET /coverage -> $(curl -sS -o /dev/null -w '%{http_code}' --max-time 30 "$BASE/api/v1/cases/$ID/coverage" -H "x-case-token: $TOK")"
if [[ "$code" != "200" ]]; then
  echo "!! GET /draft is not 200: rolling back"
  AWS_PROFILE=$MEMBER_PROFILE aws lambda update-function-code --function-name $FN --zip-file "fileb://$WORK/member-backup.zip" --query '[CodeSha256,LastUpdateStatus]' --output text
  AWS_PROFILE=$MEMBER_PROFILE aws lambda wait function-updated --function-name $FN
  echo "rollback done"; exit 1
fi
echo "OK: member Lambda now serves /draft, /coverage and /documents through CloudFront"
