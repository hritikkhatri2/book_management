import numpy as np
import faiss
from typing import List, Dict, Any
from app.utils.embedding import get_embedding
from app.crud.crud_book import book as crud_book
from sqlalchemy.orm import Session


class SearchService:
    def __init__(self):
        self.index = None
        self.book_ids = []
        
    def build_index(self, db: Session):
        """
        Build the FAISS index from all books in the database.
        """
        books = crud_book.get_multi(db)
        if not books:
            return
            
        # Get embeddings for all books
        texts = [f"{b.title} {b.author} {b.description or ''}" for b in books]
        embeddings = [get_embedding(text) for text in texts]
        
        # Store book IDs for later lookup
        self.book_ids = [b.id for b in books]
        
        # Create and train the index
        dimension = len(embeddings[0])
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(embeddings, dtype=np.float32))
        
    def semantic_search(self, db: Session, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform semantic search using FAISS.
        """
        if not self.index:
            self.build_index(db)
            if not self.index:
                return []
                
        # Get query embedding
        query_embedding = get_embedding(query)
        
        # Search the index
        distances, indices = self.index.search(
            np.array([query_embedding], dtype=np.float32),
            k
        )
        
        # Get the corresponding books
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.book_ids):
                book = crud_book.get(db, self.book_ids[idx])
                if book:
                    results.append({
                        "book": book,
                        "score": float(1 / (1 + distances[0][i]))
                    })
                    
        return sorted(results, key=lambda x: x["score"], reverse=True)


search_service = SearchService() 