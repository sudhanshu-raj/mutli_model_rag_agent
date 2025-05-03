import time
from sumarizer import Summarizer
from database import Database
from vector_store import VectorStore
from qa_chain import QAChain
import json
from image_viewer import ImageViewer
import os
from gemini_direct import generate_image_title_dscrpt
from collections import defaultdict
from process_files import process_files,process_files_api
import database 

def get_db():
    return database.Database()

# here question type is either text or image
def answer_question(question, search_type,workspace_name=None):
    summarizer = Summarizer()
    vs = VectorStore()
    qa = QAChain()
    viewer = ImageViewer()

    # Generate query embedding
    query_embedding = summarizer.generate_embeddings(question)

    # Query vector store with score threshold
    if search_type == "text":
        if workspace_name:
            doc_ids = vs.filtered_query(query_embedding= query_embedding,filter_condition={"workspace_name": workspace_name}, collection_type="text")
        else:
            doc_ids = vs.text_query(query_embedding)
    elif search_type == "image":
        if workspace_name:
            doc_ids = vs.filtered_query(query_embedding= query_embedding,filter_condition={"workspace_name": workspace_name}, collection_type="image")
        else:
            doc_ids = vs.image_query(query_embedding)
    print("Matched documents:", doc_ids)

    contexts = []
    sources = []
    seen_docs = set()

    # Context collection phase
    for doc_id in doc_ids:
        try:
            if doc_id in seen_docs:
                continue
            seen_docs.add(doc_id)

            context = None
            metadata = {}
            content_type = "text"

            # Check SQL database first (PDF/DOCX)
            db=get_db()
            result=db.get_contentPath_fromDocument(doc_id)

            if result:  # Handle PDF/DOCX
                json_path = result
                with open(json_path, "r") as f:
                    context = json.load(f)
                metadata = context.get("metadata", {})
            else:  # Handle TXT/Image chunks
                if search_type=="image":
                    results = vs.image_collection.get(
                        ids=[doc_id],
                        include=["metadatas", "documents"]
                    )
                # means query is from text collection
                if search_type=="text":
                    results  = vs.text_collection.get(
                        ids=[doc_id],
                        include=["metadatas", "documents"]
                    )

                if results['documents']:
                    context = {
                        "text": {"content": results['documents'][0]},
                        "metadata": results['metadatas'][0]
                    }
                    # print("context extracted is ::", context)
                    metadata = context["metadata"]
                    if metadata.get("document_type") == "image":
                        content_type = "image"

            if context:
                # Context relevance validation
                if content_type == "text":
                    relevance = qa.validate_context_relevance(
                        context, question)
                    print(f"Relevance score for {doc_id}: {relevance:.2f}")
                    if relevance > 0.7:
                        contexts.append(context)
                        sources.append(metadata.get("source", "Unknown"))
                else:  # Always include images that pass score threshold
                    relevance = qa.validate_context_relevance(
                        context, question)
                    print(f"Relevance score for {doc_id}: {relevance:.2f}")
                    if relevance > 0.7:
                        contexts.append(context)
                        sources.append(metadata.get("original_path", "Unknown"))

        except Exception as e:
            print(f"Error processing {doc_id}: {str(e)}")
            continue
        finally:
            db.conn.close()


    # Text chunk regrouping (existing functionality) , this is only for txt or md files
    chunk_groups = defaultdict(list)
    for ctx in contexts:
        metadata = ctx.get("metadata", {}) or {}
        if isinstance(metadata, dict) and "chunk" in metadata:
            try:
                base_id = str(metadata["source"]).split("-")[0]
                chunk_groups[base_id].append(ctx)
            except KeyError:
                print(f"Skipping chunk with invalid metadata: {metadata}")
                continue

    # Process chunk groups, this also for only txt or md files
    for base_id, chunks in chunk_groups.items():
        try:
            print(f"Processing base_id={base_id}")
            #print(f"Chunks: {chunks['metadata']}")
            sorted_chunks = sorted(chunks,
                                   key=lambda x: x["metadata"]["chunk"])

            combined_text = "\n".join(
                [chunk["text"]["content"] for chunk in sorted_chunks]
            )
            main_metadata = sorted_chunks[0]["metadata"]
            print("main_metadata::", main_metadata)

            unified_context = {
                "text": {"content": combined_text},
                "metadata": {
                    "source": main_metadata["source"],
                    "title": main_metadata["title"],
                    "document_type": main_metadata["document_type"]
                }
            }

            contexts = [c for c in contexts if not (
                isinstance(c.get("metadata", {}).get("source"), str) and
                c["metadata"]["source"].startswith(base_id)
            )]
            
            contexts.append(unified_context)
            sources.append(main_metadata["source"])

        except Exception as e:
            print(f"Error processing chunks {base_id}: {e}")

    # Generate final answer
    if not contexts:
        return "No relevant information found in documents"

    # Prepare image results
    image_references = []
    for context in contexts:
        if context.get("metadata", {}).get("document_type") == "image":
            img_path = context["metadata"].get("source")
            if img_path and os.path.exists(img_path):
                image_references.append(img_path)

    # Generate text answer
    if search_type == "text":
        answer = qa.generate_answer(contexts, question)
    elif search_type == "image":
        # print("provided context is ::")
        # print(contexts)
        answer = qa.generate_answer_image(contexts, question)

    # Add sources and image references
    unique_sources = list({os.path.basename(s)
                          for s in sources if isinstance(s, str)})
    print(unique_sources)
    if unique_sources:
        answer += f"\n\nSources: {', '.join(unique_sources)}"
    print("Original sources::", sources)

    print("Query processed successfully")
    return answer


# Example Usage
if __name__ == "__main__":
    start_time = time.time()
    # from helper_functions import list_files_in_folder
    # files = list_files_in_folder(
    #     r"C:\Users\rajsu\OneDrive\Documents\myCredentials")
    file_paths = [
        # "C:\\Users\\rajsu\\Downloads\\Iphoneinvoicev2.pdf",
        #"C:\\Users\\rajsu\\Downloads\\my_resume.pdf",
        #"C:\\Users\\rajsu\\Downloads\\candidate1_resume.pdf",
        # "C:\\Users\\rajsu\\Downloads\\candidate2_resume.pdf",
        #"C:\\Users\\rajsu\\Downloads\\Railwire_Subscriber_Invoice.pdf",
        #"C:\\Users\\rajsu\\Downloads\\invoice_19531402117.pdf",
         #"C:\\Users\\rajsu\\Downloads\\Satyendra Rai - Resume - Software Engineer.txt",
        # "C:\\Users\\rajsu\\OneDrive\\Documents\\myCredentials\\all_in_one.txt",
        # "C:\\Users\\rajsu\\OneDrive\\Documents\\myCredentials\\gamingCredentials.txt",
        # "C:\\Users\\rajsu\\OneDrive\\Documents\\myCredentials\\mysql.txt",
        # "C:\\Users\\rajsu\\OneDrive\\Documents\\myCredentials\\steam credentials.txt",
        #"C:\\Users\\rajsu\\OneDrive\\Documents\\amity_projects_sem4\\admit_Card.pdf",
        # "C:\\Users\\rajsu\\Downloads\\legion_5_5i_15_9_ug_en.pdf",

        "C:\\Users\\rajsu\\Downloads\\cp_plus_manual.pdf"
    ]
    # for file in file_paths:
    #     process_pdf(file)
    image_path =r"C:\Users\rajsu\Documents\multi_model_ragagent\uploaded_files\images\premium_photo-1685148902854-9b9bb49fff08.jpg"
    title_descrpt = generate_image_title_dscrpt(image_path)
    print(f"title_descrpt:: {title_descrpt}")
    # doc_id = process_files_api(
    #     file_path=image_path,
    #     user_metadata={
    #         "title": "cooling pad for laptop",
    #         "description": "cooling pad for laptop",
    #         # "description": "cyber punk ",
    #     },
    #     workspace_name="images"
    # )
    # doc_id = process_pdf(
    #     file_path=r"C:\Users\rajsu\OneDrive\Documents\DSA2DEVELOPMENT\DSA_TO_DEVELOPMENT\spring_basics_explained.docx",
    #     workspace_name="notes"
    #     )
    # if doc_id:
    
    # print(answer_question(
    #     question="give me the important python commands",
    #     search_type= "text",
    #     # workspace_name="wifi-bill"
    # ))
    print(f"Time taken: {time.time()-start_time:.2f} seconds")
    # What are the key findings in this document
