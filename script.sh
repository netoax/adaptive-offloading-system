#!/bin/sh
# FLINK_DIR="/usr/local/Cellar/apache-flink"
# FLINK_VERSION=1.10.0
# echo "starting apache flink cluster"
# sh "$FLINK_DIR/$FLINK_VERSION/libexec/bin/start-cluster.sh"

response=$(curl -s -X POST -H "Expect:" -F "jarfile=@./artifacts/application.jar" http://localhost:8081/jars/upload)
jobId=$(echo $response | jq '.filename')
echo $jobId