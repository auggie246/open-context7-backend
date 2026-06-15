import sys
from pathlib import Path

from app.ingest.models import parsed_doc_chunk_from_parser, stable_chunk_id
from app.ingest.parser import parse_document


def main() -> None:
    source_dir = Path(sys.argv[1])
    for path in sorted([*source_dir.glob("**/*.md"), *source_dir.glob("**/*.mdx")]):
        for chunk in parse_document(path):
            parsed = parsed_doc_chunk_from_parser(chunk)
            chunk_id = stable_chunk_id("/internal/platform", "main", parsed)
            _ = sys.stdout.write(f"{chunk_id} {parsed.source_path}#{parsed.chunk_index}\n")


if __name__ == "__main__":
    main()
