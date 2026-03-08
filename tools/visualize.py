"""Stub – forwards to entropy_table.commands.visualize.

Re-exports the public API so that `from tools.visualize import ...` and
`python -m tools.visualize` both continue to work.
"""
import sys
from entropy_table.commands.visualize import (  # noqa: F401 – re-exports
    DomainNode,
    RelationEdge,
    main,
    render_dot,
    render_mermaid,
)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
