"""Run every game's simulation and print the balance cross-tab.

    python run_all.py              # 20,000 games per modeled cell
    python run_all.py 5000         # quicker pass

The table itself lives in table.py, which crosses each game against its
difficulty dial and reports the NRJ tier and hero-card axes explicitly. This
module is kept as the documented entry point.

Results are model output, not play reports. Read README.md and the
NOT MODELED block table.py prints before trusting a number.
"""
import sys

import table

if __name__ == "__main__":
    table.main(int(sys.argv[1]) if len(sys.argv) > 1 else table.DEFAULT)
