#!/usr/bin/env python3
"""
Ingest PDF files from data/raw into persistent Chroma vector DB.
"""
import argparse
import hashlib
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import chromadb
from pypdf import PdfReader

from config.settings import config
from retrieval.embedder import BGEEmbedder
from shared.logger import get_logger

logger = get_logger(__name__)


def normalize_text(text: str) -> str:
    """Normalize whitespace and remove noisy line breaks."""
    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """Split text into overlapping character chunks."""
    if not text:
        return []

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_len:
            break
        start = end - chunk_overlap

    return chunks


def read_pdf_text(pdf_path: Path) -> str:
    """Extract text from all pages in a PDF file."""
    reader = PdfReader(str(pdf_path))
    pages = []

    for idx, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        page_text = normalize_text(page_text)
        if page_text:
            pages.append(page_text)
        else:
            logger.warning("No extractable text in %s page %s", pdf_path.name, idx)

    return "\n".join(pages)


def make_chunk_id(pdf_path: Path, chunk_index: int, content: str) -> str:
    """Create deterministic chunk id to support upsert updates."""
    digest = hashlib.sha1(content.encode("utf-8")).hexdigest()[:12]
    return f"{pdf_path.stem}_{chunk_index}_{digest}"


def collect_pdf_chunks(raw_dir: Path, chunk_size: int, chunk_overlap: int) -> List[Tuple[str, str, dict]]:
    """Read all PDFs and return list of (id, text, metadata)."""
    pdf_files = sorted(raw_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning("No PDF files found in %s", raw_dir)
        return []

    all_rows: List[Tuple[str, str, dict]] = []

    for pdf_path in pdf_files:
        logger.info("Reading PDF: %s", pdf_path.name)
        text = read_pdf_text(pdf_path)
        if not text:
            logger.warning("Skipping empty PDF: %s", pdf_path.name)
            continue

        chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        logger.info("%s -> %s chunks", pdf_path.name, len(chunks))

        for idx, chunk in enumerate(chunks):
            chunk_id = make_chunk_id(pdf_path, idx, chunk)
            metadata = {
                "source": str(pdf_path),
                "file_name": pdf_path.name,
                "chunk_index": idx,
            }
            all_rows.append((chunk_id, chunk, metadata))

    return all_rows


def ingest_documents(raw_dir: Path, vector_dir: Path, collection_name: str, reset: bool) -> int:
    """Ingest PDFs to Chroma persistent collection."""
    os.makedirs(vector_dir, exist_ok=True)

    embedder = BGEEmbedder(
        model_name=config.rag.embedding_model,
        device=config.rag.embedding_device,
    )

    client = chromadb.PersistentClient(path=str(vector_dir))

    if reset:
        try:
            client.delete_collection(collection_name)
            logger.info("Deleted existing collection: %s", collection_name)
        except Exception:
            logger.info("Collection %s did not exist. Continuing...", collection_name)

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"description": "Battery analysis document embeddings"},
    )

    rows = collect_pdf_chunks(
        raw_dir=raw_dir,
        chunk_size=config.rag.chunk_size,
        chunk_overlap=config.rag.chunk_overlap,
    )
    if not rows:
        return 0

    ids = [row[0] for row in rows]
    docs = [row[1] for row in rows]
    metadatas = [row[2] for row in rows]

    logger.info("Generating embeddings for %s chunks...", len(docs))
    embeddings = embedder.encode(docs)

    logger.info("Upserting to Chroma collection: %s", collection_name)
    collection.upsert(
        ids=ids,
        documents=docs,
        metadatas=metadatas,
        embeddings=embeddings.tolist(),
    )

    total_count = collection.count()
    logger.info("Ingestion completed. Collection count=%s", total_count)
    return total_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest PDFs from data/raw into vector store")
    parser.add_argument(
        "--raw-dir",
        default="./data/raw",
        help="Directory that contains source PDF files",
    )
    parser.add_argument(
        "--vector-dir",
        default=config.rag.vector_store_path,
        help="Persistent vector DB directory",
    )
    parser.add_argument(
        "--collection-name",
        default="battery_documents",
        help="Chroma collection name",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete and recreate collection before ingest",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    raw_dir = Path(args.raw_dir)
    vector_dir = Path(args.vector_dir)

    if not raw_dir.exists():
        logger.error("Raw directory does not exist: %s", raw_dir)
        return 1

    try:
        count = ingest_documents(
            raw_dir=raw_dir,
            vector_dir=vector_dir,
            collection_name=args.collection_name,
            reset=args.reset,
        )
        if count == 0:
            logger.warning("No chunks ingested. Check PDF files in %s", raw_dir)
        return 0
    except Exception as e:
        logger.error("Ingestion failed: %s", str(e), exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
