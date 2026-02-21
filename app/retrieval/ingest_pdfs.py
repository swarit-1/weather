"""
Ingest multiple PDFs into the same local vector DB (VectorRecords in local_embeddings.json).

Usage:
  # From project root, with .env containing OPENAI_API_KEY or LLM_API_KEY:
  pip install -r app/retrieval/requirements-pdf-embeddings.txt

  # Ingest 2 PDFs into the default store (app/retrieval/local_embeddings.json):
  python -m app.retrieval.ingest_pdfs path/to/doc1.pdf path/to/doc2.pdf

  # Custom store path:
  python -m app.retrieval.ingest_pdfs doc1.pdf doc2.pdf --store ./my_embeddings.json

  # Tag the first PDF as heat/grid_ops and the second as wind/field_ops (for retrieval testing):
  python -m app.retrieval.ingest_pdfs heat_playbook.pdf wind_playbook.pdf \\
    --tags "heat,grid_ops" "wind,field_ops"
"""

import argparse
from pathlib import Path

from app.retrieval.pdf_to_embeddings import run
from app.retrieval.rag_schema import VectorRecordTags

DEFAULT_STORE = Path(__file__).resolve().parent / "local_embeddings.json"


def _parse_tags(s: str) -> VectorRecordTags:
    """Parse 'event_type,role_tag' or 'event_type,severity_min,role_tag'. Defaults: normal, low, general."""
    parts = [p.strip().lower() for p in s.split(",") if p.strip()]
    event_set = {"normal", "heat", "wind", "storm", "critical"}
    role_set = {"grid_ops", "field_ops", "comms", "general"}
    severity_set = {"low", "medium", "high", "critical"}
    event_types = [parts[0]] if parts and parts[0] in event_set else ["normal"]
    severity_min = "low"
    role_tag = "general"
    if len(parts) >= 3:
        severity_min = parts[1] if parts[1] in severity_set else severity_min
        role_tag = parts[2] if parts[2] in role_set else role_tag
    elif len(parts) >= 2:
        if parts[1] in role_set:
            role_tag = parts[1]
        elif parts[1] in severity_set:
            severity_min = parts[1]
    return VectorRecordTags(
        event_types=event_types,
        severity_min=severity_min,
        role_tag=role_tag,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest 2+ PDFs into the same local vector DB (VectorRecords)."
    )
    parser.add_argument(
        "pdfs",
        nargs="+",
        help="Paths to PDF files (order preserved; use --tags in same order if provided)",
    )
    parser.add_argument(
        "--store",
        default=None,
        help=f"Output JSON path for vector DB (default: {DEFAULT_STORE})",
    )
    parser.add_argument(
        "--tags",
        nargs="+",
        default=None,
        metavar="SPEC",
        help='Per-PDF tags: "event_type,role_tag" or "event_type,severity_min,role_tag". '
             'E.g. "heat,grid_ops" "wind,field_ops". If fewer than PDFs, rest use normal,general.',
    )
    parser.add_argument("--similarity-threshold", type=float, default=0.92)
    parser.add_argument("--chunk-size", type=int, default=512)
    parser.add_argument("--overlap", type=int, default=50)
    args = parser.parse_args()

    store_path = args.store or str(DEFAULT_STORE)
    tag_specs = args.tags or []

    total_added = 0
    for i, pdf in enumerate(args.pdfs):
        path = Path(pdf)
        if not path.exists():
            print(f"Skip (not found): {pdf}")
            continue
        tags = _parse_tags(tag_specs[i]) if i < len(tag_specs) else VectorRecordTags(
            event_types=["normal"], severity_min="low", role_tag="general"
        )
        title = path.stem
        added = run(
            pdf_path=str(path),
            store_path=store_path,
            similarity_threshold=args.similarity_threshold,
            chunk_size=args.chunk_size,
            overlap=args.overlap,
            tags=tags,
            title=title,
            url="",
        )
        total_added += added
        print(f"  {path.name}: +{added} records (tags: event_types={tags.event_types}, role_tag={tags.role_tag})")

    print(f"Total new records: {total_added}. Store: {store_path}")


if __name__ == "__main__":
    main()
