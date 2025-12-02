"""
Benchmark Performance Test - Đo lường tốc độ của SA, PSO và các phiên bản tối ưu.
"""

import time
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.models.course import Course
from src.models.room import Room
from src.models.proctor import Proctor
from src.core.solvers.sa_solver import SASolver
from src.core.solvers.pso_solver import PSOSolver
from src.core.solvers.fast_sa_solver import FastSASolver
from src.core.solvers.fast_pso_solver import FastPSOSolver


def create_test_data(num_courses=10, num_rooms=5, num_proctors=3):
    """Tạo dữ liệu test."""
    courses = []
    for i in range(num_courses):
        course = Course(
            course_id=f"MH{i:03d}",
            name=f"Course {i}",
            student_count=30 + (i * 5),
            location="HCM",
            exam_format="written",
            duration=90
        )
        courses.append(course)
    
    rooms = []
    for i in range(num_rooms):
        room = Room(
            room_id=f"P{i:02d}",
            capacity=50 + (i * 10),
            location="HCM"
        )
        rooms.append(room)
    
    proctors = []
    for i in range(num_proctors):
        proctor = Proctor(
            proctor_id=f"GT{i:02d}",
            name=f"Proctor {i}",
            location="HCM"
        )
        proctors.append(proctor)
    
    return courses, rooms, proctors


def benchmark_solver(name, solver_class, courses, rooms, proctors, config):
    """Generic benchmark function."""
    print(f"\n{'='*60}")
    print(f"BENCHMARK: {name}")
    print(f"{'='*60}")
    
    solver = solver_class(courses, rooms, config, proctors)
    
    start = time.time()
    solver.run()
    elapsed = time.time() - start
    
    iterations = config.get('max_iterations', config.get('swarm_size', 0) * config.get('max_iterations', 0))
    if 'swarm_size' in config:
        evaluations = config['swarm_size'] * config['max_iterations']
        evals_per_sec = evaluations / elapsed if elapsed > 0 else 0
        print(f"⏱️ Execution time: {elapsed:.2f}s")
        print(f"📊 Total evaluations: {evaluations}")
        print(f"📊 Evals/sec: {evals_per_sec:.2f}")
    else:
        iters_per_sec = config['max_iterations'] / elapsed if elapsed > 0 else 0
        print(f"⏱️ Execution time: {elapsed:.2f}s")
        print(f"📊 Iterations/sec: {iters_per_sec:.2f}")
    
    print(f"📈 Best cost: {solver.best_solution.fitness_score:.2f}")
    
    return elapsed


if __name__ == "__main__":
    print("\n🔬 PERFORMANCE BENCHMARK TEST - SA vs PSO (Original vs Optimized)")
    print("="*60)
    
    # Create test data
    courses, rooms, proctors = create_test_data(num_courses=20, num_rooms=8, num_proctors=5)
    print(f"✓ Test data created: {len(courses)} courses, {len(rooms)} rooms, {len(proctors)} proctors")
    
    # Test 1: Small Scale
    print("\n" + "="*60)
    print("TEST 1: Small Scale (200 iterations)")
    print("="*60)
    
    sa_config = {
        'initial_temperature': 1000.0,
        'min_temperature': 0.1,
        'cooling_rate': 0.995,
        'max_iterations': 200,
        'neighbor_type': 'random'
    }
    
    pso_config = {
        'swarm_size': 30,
        'max_iterations': 200,
        'w': 0.7,
        'c1': 1.5,
        'c2': 1.5
    }
    
    sa_time = benchmark_solver("SA (Original)", SASolver, courses, rooms, proctors, sa_config)
    fast_sa_time = benchmark_solver("SA (Optimized)", FastSASolver, courses, rooms, proctors, sa_config)
    pso_time = benchmark_solver("PSO (Original)", PSOSolver, courses, rooms, proctors, pso_config)
    fast_pso_time = benchmark_solver("PSO (Optimized)", FastPSOSolver, courses, rooms, proctors, pso_config)
    
    # Test 2: Medium Scale
    print("\n" + "="*60)
    print("TEST 2: Medium Scale (500 iterations)")
    print("="*60)
    
    sa_config['max_iterations'] = 500
    pso_config['max_iterations'] = 500
    pso_config['swarm_size'] = 50
    
    sa_time2 = benchmark_solver("SA (Original)", SASolver, courses, rooms, proctors, sa_config)
    fast_sa_time2 = benchmark_solver("SA (Optimized)", FastSASolver, courses, rooms, proctors, sa_config)
    pso_time2 = benchmark_solver("PSO (Original)", PSOSolver, courses, rooms, proctors, pso_config)
    fast_pso_time2 = benchmark_solver("PSO (Optimized)", FastPSOSolver, courses, rooms, proctors, pso_config)
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY - PERFORMANCE IMPROVEMENT")
    print("="*60)
    
    print(f"\n✅ SA - 200 iterations:")
    print(f"   Original: {sa_time:.2f}s")
    print(f"   Optimized: {fast_sa_time:.2f}s")
    print(f"   Speedup: {sa_time/fast_sa_time:.1f}x faster")
    
    print(f"\n✅ PSO - 200 iterations (6000 evals):")
    print(f"   Original: {pso_time:.2f}s")
    print(f"   Optimized: {fast_pso_time:.2f}s")
    print(f"   Speedup: {pso_time/fast_pso_time:.1f}x faster")
    
    print(f"\n✅ SA - 500 iterations:")
    print(f"   Original: {sa_time2:.2f}s")
    print(f"   Optimized: {fast_sa_time2:.2f}s")
    print(f"   Speedup: {sa_time2/fast_sa_time2:.1f}x faster")
    
    print(f"\n✅ PSO - 500 iterations (25000 evals):")
    print(f"   Original: {pso_time2:.2f}s")
    print(f"   Optimized: {fast_pso_time2:.2f}s")
    print(f"   Speedup: {pso_time2/fast_pso_time2:.1f}x faster")
    
    print("\n" + "="*60)
    print("✅ OPTIMIZATION TEST COMPLETE")
    print("="*60)
