from __future__ import annotations


def build_search_text(primary_name: str, common_name: str | None, catalogue_ids: list[str]) -> str:
    parts: list[str] = [primary_name]
    if common_name:
        parts.append(common_name)
    parts.extend(catalogue_ids)
    seen: set[str] = set()
    tokens: list[str] = []
    for part in parts:
        for token in str(part).lower().replace(",", " ").split():
            if token and token not in seen:
                seen.add(token)
                tokens.append(token)
    return " ".join(tokens)[:1024]
