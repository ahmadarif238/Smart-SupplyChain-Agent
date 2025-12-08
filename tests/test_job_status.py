#!/usr/bin/env python3
"""
Quick diagnostic to verify the job status endpoint is responsive
Run this in a new terminal after starting the backend
"""

import requests
import time
import json

API_BASE = "http://127.0.0.1:8000"

def test_endpoint_speed():
    """Test if /agent/job/{job_id} returns quickly"""
    print("🧪 Testing Job Status Endpoint Speed...\n")
    
    # Start a job
    print("1️⃣ Starting agent job...")
    try:
        resp = requests.post(f"{API_BASE}/agent/run_once", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        job_id = data.get("job_id")
        print(f"   ✅ Job created: {job_id}\n")
    except Exception as e:
        print(f"   ❌ Failed to start job: {e}")
        return
    
    # Test status endpoint speed multiple times
    print("2️⃣ Testing status endpoint response time (should be < 100ms)...\n")
    times = []
    
    for i in range(5):
        try:
            start = time.time()
            resp = requests.get(f"{API_BASE}/agent/job/{job_id}", timeout=5)
            resp.raise_for_status()
            elapsed = (time.time() - start) * 1000  # Convert to ms
            
            status = resp.json().get("status")
            print(f"   Attempt {i+1}: {elapsed:.1f}ms - Status: {status}")
            times.append(elapsed)
            time.sleep(0.5)
        except Exception as e:
            print(f"   ❌ Attempt {i+1} FAILED: {e}")
            return
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"   Min: {min(times):.1f}ms")
    print(f"   Max: {max(times):.1f}ms")
    print(f"   Avg: {sum(times)/len(times):.1f}ms")
    
    if max(times) < 100:
        print(f"\n✅ SUCCESS: All responses under 100ms (well under 5s timeout)")
    else:
        print(f"\n⚠️ WARNING: Some responses slow (> 100ms)")

if __name__ == "__main__":
    test_endpoint_speed()
