#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test ChartWidget - Gantt Chart Implementation
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication

# Import ChartWidget
from src.ui.widgets.chart_widget import ChartWidget


def test_chart_widget():
    """Test ChartWidget with both 2-arg and 6-arg update_plot calls."""
    
    app = QApplication(sys.argv)
    
    # Create widget
    widget = ChartWidget()
    print("✅ ChartWidget created successfully")
    
    # Test 2-arg update_plot (backward compatibility)
    widget.update_plot(1, 100.5)
    print("✅ update_plot(iteration=1, cost=100.5) works")
    
    widget.update_plot(10, 95.3)
    print("✅ update_plot(iteration=10, cost=95.3) works")
    
    # Test 6-arg update_plot (with SA parameters)
    widget.update_plot(20, 85.2, 45.0, 0.0, 75.5, 3)
    print("✅ update_plot(iteration, cost, temperature, 0, acceptance_rate, updates) works (SA mode)")
    
    # Test 6-arg with PSO parameters
    widget.update_plot(30, 75.1, 0.0, 0.6, 65.2, 5)
    print("✅ update_plot(iteration, cost, 0, inertia, acceptance_rate, updates) works (PSO mode)")
    
    # Test update_batch
    batch_data = [
        {'iteration': 40, 'cost': 70.5, 'temperature': 35.0, 'acceptance_rate': 55.0},
        {'iteration': 50, 'cost': 65.2, 'temperature': 25.0, 'acceptance_rate': 45.0},
    ]
    widget.update_batch(batch_data)
    print("✅ update_batch() works")
    
    # Test update_final
    widget.update_final(100, 60.1, None, {'iterations': 100, 'best_cost': 60.1})
    print("✅ update_final() works")
    
    # Test clear
    widget.clear()
    print("✅ clear() works")
    
    # Test get_data
    widget.update_plot(1, 100.0)
    data = widget.get_data()
    assert 'iterations' in data
    assert 'costs' in data
    print("✅ get_data() works")
    
    # Test plot_comparison
    sa_history = [100, 90, 85, 80, 75, 70, 68, 65]
    pso_history = [100, 88, 82, 78, 72, 69, 66, 63]
    widget.plot_comparison(sa_history, pso_history)
    print("✅ plot_comparison() works")
    
    # Test set_data
    widget.set_data([1, 2, 3, 4, 5], [100, 90, 85, 82, 80])
    print("✅ set_data() works")
    
    # Test set_theme
    widget.set_theme('light')
    print("✅ set_theme('light') works")
    
    widget.set_theme('dark')
    print("✅ set_theme('dark') works")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    
    # Don't show GUI, just exit
    sys.exit(0)


if __name__ == '__main__':
    test_chart_widget()
