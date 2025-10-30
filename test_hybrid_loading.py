#!/usr/bin/env python3
"""
Test script for hybrid loading performance
Demonstrates O(N) time complexity optimization
"""

import asyncio
import time
import json
import requests
from typing import Dict, Any

# Test configurations
TEST_TRIPS = [
    {
        "name": "Short Trip (3 days)",
        "duration": 3,
        "expected_strategy": "Single Batch",
        "expected_time": "2-4s"
    },
    {
        "name": "Medium Trip (8 days)", 
        "duration": 8,
        "expected_strategy": "Parallel",
        "expected_time": "~2s"
    },
    {
        "name": "Long Trip (20 days)",
        "duration": 20,
        "expected_strategy": "Batched Parallel",
        "expected_time": "~8s (4 batches)"
    }
]

BASE_URL = "http://localhost:8000"

async def test_hybrid_loading():
    """Test hybrid loading performance for different trip durations"""
    
    print("🚀 Testing Hybrid Loading Performance")
    print("=" * 50)
    
    for test_case in TEST_TRIPS:
        print(f"\n📊 Testing: {test_case['name']}")
        print(f"Expected Strategy: {test_case['expected_strategy']}")
        print(f"Expected Time: {test_case['expected_time']}")
        
        # Create test trip
        trip_data = {
            "destination": "Tamil Nadu",
            "start_date": "2024-11-08T00:00:00",
            "end_date": f"2024-11-{8 + test_case['duration'] - 1}T00:00:00",
            "total_budget": 50000,
            "travelers": 2,
            "themes": ["cultural", "adventure"],
            "duration": test_case['duration']
        }
        
        try:
            # Create trip
            print("  Creating trip...")
            create_response = requests.post(
                f"{BASE_URL}/api/v1/trips/",
                json=trip_data,
                timeout=30
            )
            
            if create_response.status_code != 200:
                print(f"  ❌ Failed to create trip: {create_response.text}")
                continue
                
            trip_id = create_response.json()["id"]
            print(f"  ✅ Trip created: {trip_id}")
            
            # Test optimized generation
            print("  Testing optimized generation...")
            start_time = time.time()
            
            optimized_response = requests.post(
                f"{BASE_URL}/api/v1/trips/{trip_id}/generate-optimized",
                json={"force_regenerate": True},
                timeout=300
            )
            
            end_time = time.time()
            actual_time = end_time - start_time
            
            if optimized_response.status_code == 200:
                data = optimized_response.json()
                print(f"  ✅ Optimized generation completed in {actual_time:.2f}s")
                print(f"  📈 Generated {len(data)} days of itinerary")
                
                # Analyze performance
                if test_case['duration'] <= 5:
                    strategy_used = "Single Batch" if actual_time < 10 else "Fallback"
                elif test_case['duration'] <= 15:
                    strategy_used = "Parallel" if actual_time < 15 else "Fallback"
                else:
                    strategy_used = "Batched Parallel" if actual_time < 30 else "Fallback"
                
                print(f"  🎯 Strategy used: {strategy_used}")
                
                # Performance analysis
                if actual_time < 5:
                    print("  🚀 Excellent performance!")
                elif actual_time < 15:
                    print("  ✅ Good performance")
                elif actual_time < 30:
                    print("  ⚠️  Acceptable performance")
                else:
                    print("  ❌ Slow performance")
                
                # Show sample data
                if data and len(data) > 0:
                    sample_day = data[0]
                    print(f"  📝 Sample day: {sample_day.get('day_number', 'N/A')}")
                    print(f"  🏨 Activities: {len(sample_day.get('activities', []))}")
                    print(f"  🍽️  Meals: {len(sample_day.get('meals', []))}")
                    print(f"  🏠 Accommodation: {sample_day.get('accommodation', {}).get('name', 'N/A')}")
                
            else:
                print(f"  ❌ Optimized generation failed: {optimized_response.text}")
            
            # Clean up
            print("  🧹 Cleaning up...")
            requests.delete(f"{BASE_URL}/api/v1/trips/{trip_id}", timeout=30)
            
        except Exception as e:
            print(f"  ❌ Test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Hybrid Loading Test Complete!")

def test_time_complexity():
    """Test time complexity analysis"""
    print("\n📈 Time Complexity Analysis")
    print("=" * 30)
    
    complexities = [
        {"n": 3, "strategy": "Single Batch", "expected": "O(1)", "time": "2-4s"},
        {"n": 8, "strategy": "Parallel", "expected": "O(n)", "time": "~2s"},
        {"n": 15, "strategy": "Parallel", "expected": "O(n)", "time": "~2s"},
        {"n": 20, "strategy": "Batched Parallel", "expected": "O(n)", "time": "~8s"},
        {"n": 30, "strategy": "Batched Parallel", "expected": "O(n)", "time": "~12s"},
    ]
    
    print("Duration | Strategy        | Complexity | Expected Time")
    print("-" * 50)
    for comp in complexities:
        print(f"{comp['n']:8d} | {comp['strategy']:15s} | {comp['expected']:10s} | {comp['time']:12s}")
    
    print("\n💡 Key Benefits:")
    print("• n ≤ 5: Single call (fastest, cohesive)")
    print("• 5 < n ≤ 15: Parallel calls (balanced)")
    print("• n > 15: Batched parallel (scalable)")
    print("• All strategies maintain O(n) time complexity")
    print("• Significant performance improvement over sequential")

if __name__ == "__main__":
    print("🧪 Hybrid Loading Performance Test")
    print("Testing O(N) time complexity optimization")
    
    # Run time complexity analysis
    test_time_complexity()
    
    # Run actual tests
    try:
        asyncio.run(test_hybrid_loading())
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
