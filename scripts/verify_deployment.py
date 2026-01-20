import subprocess
import sys
import time

def run_script(script_path, description):
    print(f"\n{'='*60}")
    print(f"RUNNING: {description}")
    print(f"SCRIPT:  {script_path}")
    print(f"{'='*60}\n")
    
    start = time.time()
    result = subprocess.run(["uv", "run", script_path], capture_output=True, text=True)
    duration = time.time() - start
    
    print(result.stdout)
    if result.stderr:
        print("--- STDERR ---")
        print(result.stderr)
        
    if result.returncode == 0:
        print(f"✅ PASS ({duration:.2f}s)")
        return True
    else:
        print(f"❌ FAIL (Exit Code: {result.returncode})")
        return False

def verify_all():
    print("🚀 STARTING FULL DEPLOYMENT VERIFICATION 🚀")
    
    scripts = [
        ("scripts/measure_latency_baseline.py", "1. Latency Baselining (Game 775296)"),
        ("scripts/verify_deep_layer.py", "2. Deep Layer Integration (Fatigue Model)"),
        ("scripts/hunt_overreactions.py", "3. Signal Validation (Retail Panic)"),
        ("scripts/run_shadow_campaign.py", "4. Shadow Campaign (2024 World Series)")
    ]
    
    passed = 0
    failed = 0
    
    for script, desc in scripts:
        if run_script(script, desc):
            passed += 1
        else:
            failed += 1
            
    print(f"\n{'-'*60}")
    print(f"SUMMARY: {passed} Passed, {failed} Failed")
    print(f"{'-'*60}")
    
    if failed == 0:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    verify_all()
