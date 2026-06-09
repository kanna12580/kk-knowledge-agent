from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import get_settings


class VectorStoreError(RuntimeError):
    pass


class ChromaVectorStore:
    def __init__(self, persist_dir: str, collection_name: str) -> None:
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self._client: Any | None = None
        self._collection: Any | None = None

    @property
    def collection(self) -> Any:
        if self._collection is None:
            try:
                import chromadb
                from chromadb.config import Settings as ChromaSettings
            except ImportError as exc:
                raise VectorStoreError("chromadb is not installed.") from exc

            Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(name=self.collection_name)
        return self._collection

    def add_chunks(
        self,
        vector_ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        if not vector_ids:
            return

        try:
            self.collection.add(
                ids=vector_ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
        except Exception as exc:
            raise VectorStoreError("Failed to write vectors to ChromaDB.") from exc

    def delete_by_document_id(self, document_id: int) -> None:
        self._delete_where({"document_id": document_id})

    def delete_by_knowledge_base_id(self, knowledge_base_id: int) -> None:
        self._delete_where({"knowledge_base_id": knowledge_base_id})

    def query_chunks(
        self,
        query_embedding: list[float],
        knowledge_base_id: int,
        top_k: int,
    ) -> dict[str, Any]:
        try:
            return self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where={"knowledge_base_id": knowledge_base_id},
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            raise VectorStoreError("Failed to query vectors from ChromaDB.") from exc

    def _delete_where(self, where: dict[str, Any]) -> None:
        try:
            self.collection.delete(where=where)
        except Exception as exc:
            raise VectorStoreError("Failed to delete vectors from ChromaDB.") from exc


@lru_cache
def get_vector_store() -> ChromaVectorStore:
    settings = get_settings()
    return ChromaVectorStore(
        persist_dir=settings.chroma_persist_dir,
        collection_name=settings.chroma_collection_name,
    )


def add_chunks(
    vector_ids: list[str],
    embeddings: list[list[float]],
    documents: list[str],
    metadatas: list[dict[str, Any]],
) -> None:
    get_vector_store().add_chunks(vector_ids, embeddings, documents, metadatas)


def delete_by_document_id(document_id: int) -> None:
    get_vector_store().delete_by_document_id(document_id)


def delete_by_knowledge_base_id(knowledge_base_id: int) -> None:
    get_vector_store().delete_by_knowledge_base_id(knowledge_base_id)


def query_chunks(query_embedding: list[float], knowledge_base_id: int, top_k: int) -> dict[str, Any]:
    return get_vector_store().query_chunks(query_embedding, knowledge_base_id, top_k)
