import os
import PyPDF2
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
import pickle
from .models import LessonModel
from langchain.text_splitter import RecursiveCharacterTextSplitter

# --- Configuration ---
INDEX_DIR = "vector_indexes"
MODEL_NAME = 'all-MiniLM-L6-v2'  # A good starting model for embeddings

# Ensure the directory for storing indexes exists
os.makedirs(INDEX_DIR, exist_ok=True)

# Load the embedding model once to be reused
print("Loading sentence transformer model...")
embedding_model = SentenceTransformer(MODEL_NAME)
print("Sentence transformer model loaded.")

def chunk_text(text, chunk_size=1000, chunk_overlap=200):
    """Splits text into overlapping chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return text_splitter.split_text(text)

def create_and_save_index(lesson_id):
    """
    Processes a lesson's PDF, creates a FAISS index, and saves it.
    This function is called when a lesson is saved with a PDF.
    """
    try:
        lesson = LessonModel.objects.get(id=lesson_id)
        if not lesson.pdf_file:
            print(f"No PDF for lesson {lesson_id}. Skipping indexing.")
            return

        print(f"Starting indexing for lesson {lesson_id}...")

        # 1. Read PDF content
        with open(lesson.pdf_file.path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            pdf_text = "".join(page.extract_text() or "" for page in reader.pages)

        if not pdf_text.strip():
            print(f"PDF for lesson {lesson_id} is empty or could not be read. Skipping.")
            return

        # 2. Chunk the extracted text
        text_chunks = chunk_text(pdf_text)

        # 3. Create vector embeddings for each chunk
        embeddings = embedding_model.encode(text_chunks, convert_to_tensor=False)
        embeddings = np.array(embeddings).astype('float32') # FAISS requires float32

        # 4. Create and populate the FAISS Index
        d = embeddings.shape[1]  # Get the dimension of the vectors
        index = faiss.IndexFlatL2(d)
        index.add(embeddings)

        # 5. Save the index and the corresponding text chunks to disk
        index_path = os.path.join(INDEX_DIR, f"lesson_{lesson_id}.index")
        chunks_path = os.path.join(INDEX_DIR, f"lesson_{lesson_id}_chunks.pkl")

        faiss.write_index(index, index_path)
        with open(chunks_path, "wb") as f:
            pickle.dump(text_chunks, f)

        print(f"Successfully indexed lesson {lesson_id}. Index and chunks saved.")

    except LessonModel.DoesNotExist:
        print(f"Lesson with id {lesson_id} not found.")
    except Exception as e:
        print(f"An error occurred during indexing for lesson {lesson_id}: {e}")

def search_index(lesson_id, question, k=3):
    """
    Searches the FAISS index for a given lesson to find relevant text chunks.
    """
    index_path = os.path.join(INDEX_DIR, f"lesson_{lesson_id}.index")
    chunks_path = os.path.join(INDEX_DIR, f"lesson_{lesson_id}_chunks.pkl")

    if not os.path.exists(index_path):
        return "This lesson's PDF has not been indexed yet. Please upload it again or wait a moment and retry."

    # Load the pre-built index and text chunks
    index = faiss.read_index(index_path)
    with open(chunks_path, "rb") as f:
        text_chunks = pickle.load(f)

    # Convert the question to a vector
    question_embedding = embedding_model.encode([question])
    question_embedding = np.array(question_embedding).astype('float32')

    # Perform the similarity search
    distances, indices = index.search(question_embedding, k)

    # Combine the most relevant chunks into a single context string
    relevant_chunks = [text_chunks[i] for i in indices[0]]
    context = "\n\n---\n\n".join(relevant_chunks)

    return context