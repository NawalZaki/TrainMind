
import json

from app.tools import analyze_curriculum_tool


def main():
    print("Analyzing curriculum...")

    result = analyze_curriculum_tool(
        topic="Retrieval-Augmented Generation (RAG)"
    )

    if result.get("error"):
        print("\nAnalysis error:")
        print(result["error"])
        return

    print("\n=== SUPPORTED LEVELS ===")
    print(
        json.dumps(
            result["analysis"].get("supported_levels", {}),
            indent=2,
            ensure_ascii=False,
        )
    )

    print("\n=== CORE CONCEPTS ===")
    print(
        json.dumps(
            result["analysis"].get("core_concepts", []),
            indent=2,
            ensure_ascii=False,
        )
    )

    print("\n=== EXPLICIT PREREQUISITES ===")
    print(
        json.dumps(
            result["analysis"].get("explicit_prerequisites", []),
            indent=2,
            ensure_ascii=False,
        )
    )

    print("\n=== LIMITATIONS ===")
    print(
        json.dumps(
            result["analysis"].get("limitations", []),
            indent=2,
            ensure_ascii=False,
        )
    )

    print("\n=== SOURCES ===")
    for item in result["results"]:
        metadata = item.get("metadata", {})
        print(
            f"- {metadata.get('source')}, "
            f"page {metadata.get('page')}"
        )


if __name__ == "__main__":
    main()
