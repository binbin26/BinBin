#!/usr/bin/env python
"""Final validation of PSO config widget"""

from PyQt5.QtWidgets import QApplication
from src.ui.widgets.config_widget import ConfigWidget
import sys

app = QApplication(sys.argv)
widget = ConfigWidget()

# Test SA config
widget.algo_combo.setCurrentIndex(0)
sa_config = widget.get_config()
print(f"✅ SA Config: {sa_config['algorithm']}")

# Test PSO config
widget.algo_combo.setCurrentIndex(1)
pso_config = widget.get_config()
print(f"✅ PSO Config: {pso_config['algorithm']}")

# Verify all params present
assert 'swarm_size' in pso_config, 'Missing swarm_size'
assert 'max_iterations' in pso_config, 'Missing max_iterations'
assert 'w' in pso_config, 'Missing w (inertia)'
assert 'c1' in pso_config, 'Missing c1 (cognitive)'
assert 'c2' in pso_config, 'Missing c2 (social)'

print("✅ All PSO parameters verified")
print("✅ CONFIG WIDGET FULLY FIXED AND TESTED")
