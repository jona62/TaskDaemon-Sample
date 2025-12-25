#!/bin/bash

# Load test with increasing TPS phases using GNU parallel
# Each phase runs for 30 seconds, TPS increases by 10 each phase (10, 20, 30... 100)

run_phase() {
    local tps=$1
    local duration=30
    
    echo "=== Phase: ${tps} TPS for ${duration}s ==="
    
    for i in $(seq 1 $duration); do
        parallel -j$tps ./test.sh > /dev/null 2>&1 ::: $(seq 1 $tps) &
        sleep 1
    done
    wait
}

echo "=========================================="
echo "TaskDaemon Load Test - Ramping TPS"
echo "=========================================="

for tps in 100 110 120 130 140 150 160 170 180 190 200 210 220 230 240 250; do
    run_phase $tps
    sleep 2
done

echo "=========================================="
echo "Load test complete"
echo "=========================================="
