import numpy as np
import faiss
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import logging
import json # For parsing stored embeddings

from app.utils.embedding import get_embedding # Fallback if needed
from app.crud.crud_book import book as crud_book
from app.db.models.book import Book

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self):
        self.index: Optional[faiss.Index] = None
        self.book_id_to_faiss_idx: Dict[int, int] = {}
        self.faiss_idx_to_book_id: Dict[int, int] = {}
        self.is_built = False
        self.dimension: Optional[int] = None # OpenAI ada-002 is 1536

    def build_index(self, db: Session):
        """
        Build or rebuild the FAISS index from books using stored embeddings.
        """
        logger.info("Building FAISS index from stored embeddings...")
        books_from_db = crud_book.get_multi(db, limit=100000) # Get all books

        if not books_from_db:
            logger.info("No books found in DB to build index.")
            self.index = None
            self.book_id_to_faiss_idx = {}
            self.faiss_idx_to_book_id = {}
            self.is_built = False
            return

        embeddings_list: List[List[float]] = []
        valid_books_for_index: List[Book] = []

        for book_item in books_from_db:
            if book_item.embedding:
                try:
                    embedding_vector = json.loads(book_item.embedding) # Parse JSON string
                    if not isinstance(embedding_vector, list) or not all(isinstance(n, (int, float)) for n in embedding_vector):
                        raise ValueError("Parsed embedding is not a list of numbers.")
                    embeddings_list.append(embedding_vector)
                    valid_books_for_index.append(book_item)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Book ID {book_item.id} ('{book_item.title}'): Error parsing stored embedding: {e}. Skipping.")
            else:
                logger.warning(f"Book ID {book_item.id} ('{book_item.title}') has no stored embedding. Skipping.")
                # Optionally, generate embedding here if missing (adds overhead to build_index):
                # text_content = f"{book_item.title} {book_item.author} {book_item.description or ''}".strip()
                # if text_content:
                #     try:
                #         logger.info(f"Generating missing embedding for book ID {book_item.id}")
                #         embedding_vector = get_embedding(text_content)
                #         book_item.embedding = json.dumps(embedding_vector)
                #         db.add(book_item) # Save the newly generated embedding
                #         db.commit() 
                #         embeddings_list.append(embedding_vector)
                #         valid_books_for_index.append(book_item)
                #     except Exception as gen_e:
                #         logger.error(f"Failed to generate missing embedding for book {book_item.id}: {gen_e}")
                # else:
                #     logger.warning(f"Book ID {book_item.id} also has no content for on-the-fly embedding generation.")

        if not embeddings_list:
            logger.info("No valid embeddings found in books to build index after processing.")
            self.index = None
            self.book_id_to_faiss_idx = {}
            self.faiss_idx_to_book_id = {}
            self.is_built = False
            return
        
        current_dimension = len(embeddings_list[0])
        if self.dimension is None:
            self.dimension = current_dimension
        elif self.dimension != current_dimension:
            logger.error(
                f"Embedding dimension mismatch during index build. Expected {self.dimension}, found {current_dimension}. "
                f"This suggests an issue with embedding consistency in the DB. Re-initializing index with new dimension."
            )
            self.dimension = current_dimension

        self.index = faiss.IndexFlatL2(self.dimension)
        self.book_id_to_faiss_idx = {}
        self.faiss_idx_to_book_id = {}
        
        try:
            np_embeddings = np.array(embeddings_list, dtype=np.float32)
            if np_embeddings.shape[1] != self.dimension:
                logger.error(f"Numpy array dimension ({np_embeddings.shape[1]}) does not match expected dimension ({self.dimension}). Index build failed.")
                self.is_built = False
                return
            self.index.add(np_embeddings)
        except ValueError as ve:
            logger.error(f"ValueError adding embeddings to FAISS index (likely due to inconsistent dimensions): {ve}. Index build failed.", exc_info=True)
            self.is_built = False
            return

        for i, book_obj in enumerate(valid_books_for_index):
            self.book_id_to_faiss_idx[book_obj.id] = i
            self.faiss_idx_to_book_id[i] = book_obj.id
        
        self.is_built = True
        logger.info(f"FAISS index built successfully with {self.index.ntotal} items from stored embeddings.")

    def semantic_search(self, db: Session, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform semantic search using FAISS.
        Builds index on first call if not already built.
        """
        if not self.is_built or self.index is None:
            logger.info("FAISS index not built or is None. Attempting to build now.")
            self.build_index(db)
            if not self.is_built or self.index is None:
                logger.error("Failed to build FAISS index for semantic search.")
                return []
        
        if self.index.ntotal == 0:
            logger.info("FAISS index is empty. No items to search.")
            return []

        query_embedding_vector = get_embedding(query)
        
        if self.dimension is None:
             logger.error("Index dimension is not set. Cannot perform search. Attempting to rebuild index.")
             self.build_index(db)
             if not self.is_built or self.index is None or self.dimension is None:
                logger.error("Failed to set index dimension after rebuild. Search aborted.")
                return []

        if len(query_embedding_vector) != self.dimension:
            logger.error(
                f"Query embedding dimension ({len(query_embedding_vector)}) mismatch with index dimension ({self.dimension}). "
                f"Cannot perform search. Check OpenAI model or index integrity."
            )
            return [] # Do not attempt rebuild here, as query dimension is the problem

        distances, faiss_indices = self.index.search(
            np.array([query_embedding_vector], dtype=np.float32),
            min(k, self.index.ntotal) 
        )
        
        results = []
        for i, faiss_idx in enumerate(faiss_indices[0]):
            if faiss_idx == -1: 
                continue
            book_id = self.faiss_idx_to_book_id.get(int(faiss_idx))
            if book_id:
                book_obj = crud_book.get(db, book_id=book_id)
                if book_obj:
                    score = float(1 / (1 + distances[0][i])) if distances[0][i] >= 0 else 0.0
                    results.append({
                        "book": book_obj,
                        "score": score
                    })
                    
        return sorted(results, key=lambda x: x["score"], reverse=True)

search_service = SearchService() 