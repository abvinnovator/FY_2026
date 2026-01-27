from __future__ import annotations

from dataclasses import dataclass
from typing import List

from src.rag.retriever import PolicyRetriever


@dataclass
class ComplianceResult:
	citations: list[str]
	snippets: list[str]


class ComplianceRAGAgent:
	"""Lightweight policy retriever wrapper for grounding explanations."""

	def __init__(self, retriever: PolicyRetriever):
		self.retriever = retriever

	def cite(self, query_text: str, k: int = 3) -> ComplianceResult:
		results = self.retriever.query(query_text, k=k)
		citations: list[str] = []
		snippets: list[str] = []
		for r in results:
			citations.append(r["metadata"].get("title", r["doc_id"]))
			snippets.append(r["text"][:400])
		return ComplianceResult(citations=citations, snippets=snippets)


