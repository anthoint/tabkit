from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import config
from backend.main import main


if __name__ == "__main__":
    if len(sys.argv) > 1:
        config.set_mode(sys.argv[1])
    main()
