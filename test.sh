#!/bin/bash

curl -s -X POST http://localhost:8081/prime \
  -H "Content-Type: application/json" \
  -d '{"limit": 10000000}'
