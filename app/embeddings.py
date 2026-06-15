import hashlib
import sys


class DeterministicEmbeddingClient:
    def __init__(self, size: int = 32) -> None:
        self._size: int = size

    def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [digest[index % len(digest)] / 255 for index in range(self._size)]


def main() -> None:
    text = sys.argv[sys.argv.index("--text") + 1]
    _ = sys.stdout.write(str(DeterministicEmbeddingClient().embed(text)))


if __name__ == "__main__":
    main()
