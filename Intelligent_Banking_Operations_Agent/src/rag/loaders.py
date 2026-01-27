from __future__ import annotations

from pathlib import Path
from typing import Iterable


def load_policy_texts(policies_dir: str) -> list[dict]:
	"""Load policy documents as a list of dicts: {doc_id, title, text}.

	For the hackathon scaffold we read .txt files; PDFs can be added later.
	"""
	root = Path(policies_dir)
	if not root.exists():
		return []
	docs: list[dict] = []
	for path in root.glob("*.txt"):
		text = path.read_text(encoding="utf-8", errors="ignore")
		docs.append({"doc_id": path.stem, "title": path.stem, "text": text})
	return docs


