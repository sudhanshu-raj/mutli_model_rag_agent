import chromadb
from chromadb.config import Settings
import logging
import os
from embedding_model import MultiModalEmbedder
import config as cfg
from sumarizer import Summarizer
logger = logging.getLogger(__name__)

CHROMA_DATA_DIR = cfg.CHROMA_DATA_DIR  # Ensure this is correctly imported

class VectorStore:
    def __init__(self):
        # Initialize embedder
        self.embedder = MultiModalEmbedder()

        # Create persistent storage directory
        self.persist_dir = CHROMA_DATA_DIR
        os.makedirs(self.persist_dir, exist_ok=True)

        # Configure client with persistent settings
        self.client = chromadb.Client(Settings(
            persist_directory=self.persist_dir,
            is_persistent=True
        ))

        # Create separate collections
        self.text_collection = self.client.get_or_create_collection(
            name="text_documents",
            metadata={"hnsw:space": "cosine"}
        )
        self.image_collection = self.client.get_or_create_collection(
            name="image_documents",
            metadata={"hnsw:space": "cosine"}
        )

    def add_text_embedding(self, doc_id, embedding, text, metadata):
        """Store with text content and metadata"""
        try:
            self.text_collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata]
            )
            # self.client.persist()  # Explicitly save changes
        except Exception as e:
            logger.error(f"Error adding embedding: {str(e)}")

    def add_image_embedding(self, doc_id, embedding, text, metadata):
        try:
            self.image_collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata]
            )
        except Exception as e:
            logger.error(f"Error adding embedding: {str(e)}")

    def add_embedding(self, doc_id, embedding, text, metadata):
        """Store with text content and metadata"""
        try:
            self.text_collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata]
            )
            # self.client.persist()  # Explicitly save changes
        except Exception as e:
            logger.error(f"Error adding embedding: {str(e)}")

    def query(self, query_embedding, n_results=5):

        # Query both collections
        text_results = self.text_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        image_results = self.image_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        # Get sorted document IDs
        return self._merge_results(text_results, image_results)[:n_results]

    def _merge_results(self, text_res, image_res):
        """Combine and sort results by score, return only doc_ids"""
        processed = []

        # Process text results with scores
        for ids, distances in zip(text_res['ids'], text_res['distances']):
            for doc_id, distance in zip(ids, distances):
                processed.append((doc_id, 1 - distance))  # (doc_id, score)

        # Process image results with scores
        for ids, distances in zip(image_res['ids'], image_res['distances']):
            for doc_id, distance in zip(ids, distances):
                processed.append((doc_id, 1 - distance))  # (doc_id, score)

        # Sort by score descending, then extract IDs
        processed.sort(key=lambda x: x[1], reverse=True)
        return [doc_id for doc_id, score in processed]

    def image_query(self, query_embedding, n_results=5):
        """Search only image embeddings"""
        results = self.image_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        processed = []
        # Process text results with scores
        for ids, distances in zip(results['ids'], results['distances']):
            for doc_id, distance in zip(ids, distances):
                processed.append((doc_id, 1 - distance))  # (doc_id, score)
        # Sort by score descending, then extract IDs
        processed.sort(key=lambda x: x[1], reverse=True)
        return [doc_id for doc_id, score in processed]

    def text_query(self, query_embedding, n_results=5):
        """Search only text/document embeddings"""
        results = self.text_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        processed = []
        # Process text results with scores
        for ids, distances in zip(results['ids'], results['distances']):
            for doc_id, distance in zip(ids, distances):
                processed.append((doc_id, 1 - distance))  # (doc_id, score)
        # Sort by score descending, then extract IDs
        processed.sort(key=lambda x: x[1], reverse=True)
        return [doc_id for doc_id, score in processed]
    
    # Filtered query with metadata conditions
    def filtered_query(self, query_embedding=None, filter_condition=None, collection_type="text", n_results=5):
        """
        Search documents with metadata filtering
        """
        collection = self.text_collection if collection_type == "text" else self.image_collection
        
        try:
            # If no embedding provided, use get() with where filter
            if query_embedding is None and filter_condition:
                result = collection.get(
                    where=filter_condition,
                    limit=n_results,
                    include=["documents", "metadatas"]
                )
                return result["ids"]  # Just return the IDs
                
            # Otherwise use query() with embedding
            query_params = {"n_results": n_results}
            
            if query_embedding:
                query_params["query_embeddings"] = [query_embedding]
                
            if filter_condition:
                query_params["where"] = filter_condition
                
            # Execute the query
            results = collection.query(**query_params)
            
            processed = []
            for ids, distances in zip(results['ids'], results['distances']):
                for doc_id, distance in zip(ids, distances):
                    processed.append((doc_id, 1 - distance))
                    
            processed.sort(key=lambda x: x[1], reverse=True)
            return [doc_id for doc_id, score in processed]
            
        except Exception as e:
            print(f"Error in filtered query: {str(e)}")
            return []
    
    def delete_from_text_collection(self, doc_id):
        """Delete document(s) from text collection"""
        # Ensure doc_id is a list
        ids = doc_id if isinstance(doc_id, list) else [doc_id]
        # Check if IDs exist first
        existing_ids = self.text_collection.get(ids=ids, include=[])["ids"]
        if existing_ids:
            self.text_collection.delete(ids=existing_ids)
            print(f"Successfully deleted IDs: {existing_ids} from vector")
        else:
            print(f"No matching IDs found: {ids}")

    def delete_from_image_collection(self, doc_id):
        """Delete document(s) from image collection"""
        # Ensure doc_id is a list
        ids = doc_id if isinstance(doc_id, list) else [doc_id]
        # Check if IDs exist first
        existing_ids = self.image_collection.get(ids=ids, include=[])["ids"]
        if existing_ids:
            self.image_collection.delete(ids=existing_ids)
            print(f"Successfully deleted IDs: {existing_ids} from image vector")
        else:
            print(f"No matching IDs found: {ids}")

    # Get the document content and metadata by ID(doc_id)
    def get_document_by_id(self, doc_id, collection_type="text"):
        """
        Retrieve human-readable document information by ID
        
        Args:
            doc_id: The document ID to retrieve
            collection_type: Either "text" or "image"
        
        Returns:
            Dictionary with document content and metadata
        """
        collection = self.text_collection if collection_type == "text" else self.image_collection
        
        try:
            # Get full document info
            result = collection.get(
                ids=[doc_id],
                include=["documents", "metadatas"]
            )
            
            if result["ids"]:
                return {
                    "id": result["ids"][0],
                    "content": result["documents"][0],
                    "metadata": result["metadatas"][0]
                }
            else:
                return None
        except Exception as e:
            print(f"Error retrieving document {doc_id}: {str(e)}")
            return None

    # Get all documents in the text collection or image collection    
    def get_all_documents_data(self, collection_type="text"):
        """
        Retrieve all documents in the text collection
        
        Returns:
            List of dictionaries with document content and metadata
        """

        collection = self.text_collection if collection_type == "text" else self.image_collection
        try:
            # Get all documents from the text collection
            result = collection.get(
                include=["documents", "metadatas", "embeddings"]
            )
            
            # Check if any documents were found
            if not result["ids"]:
                print("No documents found in text collection")
                return []
            
            # Format the results into a list of dictionaries
            documents = []
            for i, doc_id in enumerate(result["ids"]):
                documents.append({
                    "id": doc_id,
                    "content": result["documents"][i],
                    "metadata": result["metadatas"][i],
                    "embedding_size": len(result["embeddings"][i]) if "embeddings" in result else None
                })
                
            print(f"Found {len(documents)} documents in text collection")
            return documents
        
        except Exception as e:
            print(f"Error retrieving documents from text collection: {str(e)}")
            return []

if __name__=="__main__":
    vector_store = VectorStore()
    summarizer = Summarizer()
    query="do you have my java backend certificate"
    # query_embeddings=summarizer.generate_embeddings(query)

    # filtered_docs=vector_store.filtered_query(query_embedding=query_embeddings,filter_condition={"workspace_name": "certificates"}, collection_type="text")
    # all_docs = [vector_store.get_document_by_id(doc_id) for doc_id in filtered_docs]


    # doc_ids_to_delete=["b1200ec3-9e9b-45e1-94da-cc77a1ff295e","50efaac3-c7b0-4224-8042-97ee8b2c8a64","5924c436-ee43-4b0a-b6f8-b5f2d264431c","5ad5ab97-9bbb-479c-8db8-836fe5dc83de"]
    vector_store.delete_from_text_collection("9971867e-3b92-429a-9c9f-4399f7841da2-0")
    
    #all_docs = vector_store.get_all_documents_data("text")

    # print("\nTotal documents found:", len(all_docs))

    # # Print the first few documents
    # for i, doc in enumerate(all_docs):  # Show first 3 docs
    #     print(f"\nDocument {i+1}:")
    #     print(f"  ID: {doc['id']}")
    #     print(f"  Content preview: {doc['content'][:100]}..." if doc['content'] else "  No content")
    #     print(f"  Metadata: {doc['metadata']}")
    
    #vector_store.delete_from_image_collection(["27c0dd1a-2a2d-496d-94ea-18202896c1a4","fa7b1826-fa89-4ca9-970b-3316e371ad4a"])


