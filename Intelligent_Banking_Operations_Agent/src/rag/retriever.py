from __future__ import annotations

from pathlib import Path
from typing import Iterable

from chromadb import PersistentClient


class PolicyRetriever:
	"""Very small wrapper around Chroma for policy retrieval."""

	def __init__(self, persist_directory: str):
		self.client = PersistentClient(path=persist_directory)
		self.collection = self.client.get_or_create_collection(name="policies")

	def add_documents(self, docs: list[dict]) -> None:
		if not docs:
			return
		ids = [d["doc_id"] for d in docs]
		txts = [d["text"] for d in docs]
		metas = [{"title": d.get("title", d["doc_id"]) } for d in docs]
		self.collection.add(ids=ids, documents=txts, metadatas=metas)

	def query(self, text: str, k: int = 3) -> list[dict]:
		res = self.collection.query(query_texts=[text], n_results=k)
		if not res or not res.get("ids"):
			return []
		out: list[dict] = []
		for i in range(len(res["ids"][0])):
			out.append(
				{
					"doc_id": res["ids"][0][i],
					"text": res["documents"][0][i],
					"metadata": res["metadatas"][0][i],
				}
			)
		return out


