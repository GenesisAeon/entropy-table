"""Stub – re-exports entropy_table.commands.analyze_health for backward compat."""
import sys
from entropy_table.commands.analyze_health import (  # noqa: F401
    DEFAULT_REPORT_PATH,
    analyze_health,
    main,
    parse_args,
    render_markdown,
)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
