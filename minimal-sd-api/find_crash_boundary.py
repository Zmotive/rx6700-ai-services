#!/usr/bin/env python3
"""
Find the exact boundary where Stable Diffusion crashes.
Tests various resolution combinations to determine if crashes are:
1. Pure pixel count (total area)
2. Aspect ratio dependent
3. Individual dimension dependent (width or height threshold)
"""

import requests
import time
import json
from datetime import datetime

API_URL = "http://localhost:8000/generate"

def test_resolution(width, height, description=""):
    """Test a specific resolution"""
    pixels = width * height
    print(f"\n{'='*60}")
    print(f"Testing: {width}×{height} = {pixels:,} pixels")
    if description:
        print(f"Purpose: {description}")
    print(f"{'='*60}")
    
    payload = {
        "prompt": "boundary test, simple landscape",
        "width": width,
        "height": height,
        "num_inference_steps": 20,
        "seed": 12345
    }
    
    try:
        print(f"⏳ Starting generation...")
        start_time = time.time()
        response = requests.post(API_URL, json=payload, timeout=300)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            print(f"✅ SUCCESS in {elapsed:.1f}s")
            return {"width": width, "height": height, "pixels": pixels, 
                    "status": "success", "time": elapsed}
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            return {"width": width, "height": height, "pixels": pixels, 
                    "status": "http_error", "code": response.status_code}
    except requests.exceptions.Timeout:
        print(f"⏱️  TIMEOUT after 300s")
        return {"width": width, "height": height, "pixels": pixels, "status": "timeout"}
    except requests.exceptions.ConnectionError as e:
        print(f"💥 CONNECTION ERROR - Container likely crashed")
        print(f"   Error details: {e}")
        print("\n⚠️  STOPPING TEST - Please check container logs with:")
        print("   docker logs minimal-sd-api")
        print("\nAfter confirming the crash type, comment out this test and re-run.")
        return {"width": width, "height": height, "pixels": pixels, "status": "crash", "error": str(e)}
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return {"width": width, "height": height, "pixels": pixels, 
                "status": "error", "error": str(e)}

def main():
    """Run boundary tests"""
    results = []
    
    print("🔍 CRASH BOUNDARY INVESTIGATION")
    print("=" * 60)
    print("Known safe:  832×832  = 692,224 pixels ✅ (stable)")
    print("Unstable:    864×864  = 746,496 pixels ⚠️  (works sometimes)")
    print("Known crash: 880×880  = 774,400 pixels ❌")
    print("Known crash: 1024×1024 = 1,048,576 pixels ❌")
    print("=" * 60)
    print("\n⚠️  NOTE: Script will STOP on first crash to verify error type.")
    print("After checking logs, comment out failed test and re-run.")
    print("=" * 60)
    print("\n🎯 Goal: Find stable maximum where rectangles can exceed square limits")
    
    # Phase 1: Test rectangle limits with safe dimension
    print("\n📊 PHASE 1: Rectangle Limit Tests")
    print("Testing how far rectangles can push beyond square limits...")
    print("Strategy: Keep one dimension at safe 768, push the other higher")
    
    tests_phase1 = [
        (768, 768, "Baseline - known stable"),
        (768, 832, "Wider - safe × stable max square"),
        (832, 768, "Taller - stable max square × safe"),
        (768, 864, "Wider - safe × unstable square limit"),
        (864, 768, "Taller - unstable square limit × safe"),
        # (768, 880, "Wider - safe × known crash"),  # UNCOMMENT after 864 test
        # (880, 768, "Taller - known crash × safe"),  # UNCOMMENT after 864 test
        # (768, 896, "Wider - safe × 896"),  # UNCOMMENT to push further
        # (896, 768, "Taller - 896 × safe"),  # UNCOMMENT to push further
    ]
    
    for width, height, desc in tests_phase1:
        result = test_resolution(width, height, desc)
        results.append(result)
        
        # Stop immediately on crash for verification
        if result["status"] == "crash":
            print("\n" + "="*60)
            print("🛑 CRASH DETECTED - STOPPING FOR VERIFICATION")
            print("="*60)
            print(f"Failed at: {width}×{height} = {result['pixels']:,} pixels")
            print("\n📋 Next steps:")
            print("1. Check container logs: docker logs minimal-sd-api")
            print("2. Verify error type (munmap_chunk, malloc, etc.)")
            print("3. If same error as before, comment out this test in script")
            print("4. Uncomment next test and re-run")
            print("\n💾 Partial results saved...")
            break  # Stop immediately
    
    # Only proceed to Phase 2 if Phase 1 completed without crashes
    if any(r["status"] == "crash" for r in results):
        print("\n⚠️  Skipping Phase 2 due to crash in Phase 1")
        print("Please verify the crash, update script, and re-run.")
    else:
        # Phase 2: Find exact stable square limit
        print("\n\n📊 PHASE 2: Stable Square Limit")
        print("Finding reliable square size (not unstable edge cases)...")
        
        # Binary search between known stable (832) and unstable (864)
        safe_size = 832
        unstable_size = 864
        
        # Test a few sizes to find consistent boundary
        test_sizes = [840, 848, 856]
        
        for size in test_sizes:
            if size > safe_size and size < unstable_size:
                result = test_resolution(size, size, f"Testing {size}×{size} for stability")
                results.append(result)
                
                if result["status"] == "success":
                    print(f"✅ {size}×{size} works")
                    safe_size = size
                elif result["status"] == "crash":
                    print(f"❌ {size}×{size} crashes - stopping")
                    unstable_size = size
                    break
        
        print(f"\n🎯 STABLE SQUARE LIMIT: {safe_size}×{safe_size} = {safe_size * safe_size:,} pixels")
        
        if not any(r["status"] == "crash" for r in results):
            # Phase 3: Test maximum rectangle dimensions
            print("\n\n📊 PHASE 3: Maximum Rectangle Dimensions")
            print("Testing how far we can push rectangles with one safe dimension...")
            
            # Find how high we can go with width=768
            tests_phase3 = [
                (768, safe_size, f"Rectangle: 768 × {safe_size}"),
                (safe_size, 768, f"Rectangle: {safe_size} × 768"),
            ]
            
            # Try pushing one dimension higher if rectangles worked
            if any(r["width"] != r["height"] and r["status"] == "success" for r in results):
                tests_phase3.extend([
                    (768, 896, "Can we exceed square limit in one dimension?"),
                    (896, 768, "Can we exceed square limit in other dimension?"),
                ])
            
            for width, height, desc in tests_phase3:
                if (width, height) not in [(r["width"], r["height"]) for r in results]:
                    result = test_resolution(width, height, desc)
                    results.append(result)
                    if result["status"] == "crash":
                        print("\n🛑 Crash in rectangle testing - stopping")
                        break
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"crash_boundary_analysis_{timestamp}.json"
    
    # Determine thresholds from results
    successes = [r for r in results if r["status"] == "success"]
    safe_size = 768  # Default fallback
    if successes:
        max_square = max([r for r in successes if r["width"] == r["height"]], 
                        key=lambda x: x["pixels"], default=None)
        if max_square:
            safe_size = max_square["width"]
    
    with open(filename, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "safe_threshold": safe_size,
            "results": results
        }, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    successes = [r for r in results if r["status"] == "success"]
    failures = [r for r in results if r["status"] != "success"]
    
    if successes:
        max_success = max(successes, key=lambda x: x["pixels"])
        print(f"✅ Largest working: {max_success['width']}×{max_success['height']} = {max_success['pixels']:,} pixels")
    
    if failures:
        min_failure = min(failures, key=lambda x: x["pixels"])
        print(f"❌ Smallest failing: {min_failure['width']}×{min_failure['height']} = {min_failure['pixels']:,} pixels")
    
    print(f"\n📁 Results saved to: {filename}")
    
    # Analyze pattern
    print("\n🔍 PATTERN ANALYSIS:")
    square_successes = [r for r in successes if r["width"] == r["height"]]
    rect_successes = [r for r in successes if r["width"] != r["height"]]
    
    if square_successes and rect_successes:
        max_square = max(square_successes, key=lambda x: x["pixels"])
        max_rect = max(rect_successes, key=lambda x: x["pixels"])
        
        if max_rect["pixels"] > max_square["pixels"]:
            print("🔸 Rectangles can handle MORE pixels than squares!")
            print(f"   Square max: {max_square['pixels']:,}")
            print(f"   Rectangle max: {max_rect['pixels']:,}")
            print("   → Crash depends on DIMENSIONS, not just pixel count")
        else:
            print("🔹 Pixel count is the limiting factor")
            print("   → Crash threshold is approximately the same regardless of aspect ratio")

if __name__ == "__main__":
    main()
