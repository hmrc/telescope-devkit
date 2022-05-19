#!/usr/bin/env bash
for lg in /aws/ecs/containerinsights/protected-mdtp/performance \
              /aws/ecs/containerinsights/protected-rate-mdtp/performance \
              /aws/ecs/containerinsights/public-mdtp/performance \
              /aws/ecs/containerinsights/public-monolith-mdtp/performance \
              /aws/ecs/containerinsights/public-rate-mdtp/performance \
              /aws/fluentbit/docker-partial-logs \
              /aws/fluentbit/ingress-gateway-envoy-protected \
              /aws/fluentbit/ingress-gateway-envoy-protected-rate \
              /aws/fluentbit/ingress-gateway-envoy-public \
              /aws/fluentbit/ingress-gateway-envoy-public-monolith \
              /aws/fluentbit/ingress-gateway-envoy-public-rate \
              /aws/route53/resolver/deskpro_vpc \
              /aws/route53/resolver/hmrc_core_connectivity-v2_vpc \
              /aws/route53/resolver/hmrc_core_connectivity_vpc \
              /aws/route53/resolver/isc_vpc \
              /aws/route53/resolver/mdtp_vpc \
              /aws/route53/resolver/perftest_vpc \
              /aws/route53/resolver/psn_vpc \
              /vpc/platsec_central_flow_log \
              CloudTrail/DefaultLogGroup \
              deskpro-flow-logs \
              hmrc_core_connectivity-flow-logs \
              isc-flow-logs \
              mdtp-flow-logs \
              psn-flow-logs;
do
  FILTER_NAME="$(echo $lg | awk -F'/' '{print $NF}')-log-handler-lambda-subscription"
  echo "$lg $FILTER_NAME"
  aws-profile -p webops-integration-engineer-RoleTelemetryAdministrator aws logs delete-subscription-filter --log-group-name "$lg" --filter-name "$FILTER_NAME"
done;
