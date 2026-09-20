#!/bin/bash

echo "Running tests to generate coverage report..."
# Force PYTHONPATH=. so python can find the 'app' package
PYTHONPATH=. pytest --cov=app --cov-report=xml

echo "Starting SonarScanner via Docker..."
# Added --network="host" so the container can connect to http://localhost:9000 on Linux
docker run --rm \
  --network="host" \
  -v "$(pwd):/usr/src" \
  sonarsource/sonar-scanner-cli:latest