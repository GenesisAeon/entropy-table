"""Stub – re-exports entropy_table.commands.metrics for backward compat."""
import sys
from entropy_table.commands.metrics import *  # noqa: F401, F403
from entropy_table.commands.metrics import (  # noqa: F401
    compute_metrics,
    main,
    render_markdown,
)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
