from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
PROJECT_ROOT = ROOT.parent

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from phase2_compliance.chat_service import ComplianceChatService  # noqa: E402


def main() -> None:
    store_path = ROOT / "data" / "threads.json"
    service = ComplianceChatService(project_root=PROJECT_ROOT, thread_store_path=store_path)

    demo_queries = [
        ("thread-1", "What is the expense ratio of HDFC Large Cap Fund?"),
        ("thread-1", "Which fund is best for me?"),
        ("thread-2", "Tell me cricket score"),
    ]

    print("Running Phase 2 compliance demo...\n")
    for thread_id, query in demo_queries:
        result = service.handle_user_message(thread_id=thread_id, user_query=query)
        print(json.dumps(result, indent=2))
        print("-" * 60)


if __name__ == "__main__":
    main()
