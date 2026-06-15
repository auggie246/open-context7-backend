from collections.abc import Sequence


def maybe_rerank[T](chunks: Sequence[T], *, enabled: bool, fast: bool) -> list[T]:
    _ = enabled
    _ = fast
    return list(chunks)
