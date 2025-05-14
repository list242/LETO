# qa_service.py

import os
from pathlib import Path
import pickle
import fitz  # PyMuPDF для чтения PDF
import nltk
from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer
from transformers import pipeline
import faiss
import numpy as np

# 1) Конфиги путей и моделей
TXT_PATH    = Path("data") / "instrukcia.txt"
PDF_PATH    = Path("data") / "instrukcia.pdf"
PICKLE_CH   = Path("data") / "chunks.pkl"
EMB_PATH    = Path("data") / "embeddings.npy"
INDEX_PATH  = Path("data") / "index.faiss"
SBERT_MODEL = "distiluse-base-multilingual-cased"
QA_MODEL    = "distilbert-base-multilingual-cased-distilled-squad"

# 2) Загрузка токенизатора NLTK
nltk.download("punkt", quiet=True)

def load_raw_text() -> str:
    """
    Читает сырой текст из PDF (если есть) или из TXT.
    """
    if PDF_PATH.exists():
        doc = fitz.open(str(PDF_PATH))
        pages = [page.get_text() for page in doc]
        return "\n".join(pages)
    elif TXT_PATH.exists():
        return TXT_PATH.read_text(encoding="utf-8")
    else:
        raise FileNotFoundError(
            "Ни instrukcia.pdf, ни instrukcia.txt не найдены в папке data/"
        )

def load_chunks(max_words: int = 300) -> list[str]:
    """
    Делит исходный текст на чанки по max_words слов.
    Сохраняет результат в PICKLE_CH для ускорения.
    """
    if os.path.exists(PICKLE_CH):
        return pickle.load(open(PICKLE_CH, "rb"))

    text = load_raw_text()
    sents = sent_tokenize(text, language="russian")
    chunks, buf, cnt = [], [], 0

    for sent in sents:
        words = sent.split()
        if cnt + len(words) > max_words:
            chunks.append(" ".join(buf))
            buf, cnt = [], 0
        buf.extend(words)
        cnt += len(words)

    if buf:
        chunks.append(" ".join(buf))

    pickle.dump(chunks, open(PICKLE_CH, "wb"))
    return chunks

def build_or_load_index(chunks: list[str]):
    """
    Строит Faiss-индекс и эмбеддинги или загружает существующие.
    """
    if INDEX_PATH.exists() and EMB_PATH.exists():
        index = faiss.read_index(str(INDEX_PATH))
        embeddings = np.load(str(EMB_PATH))
    else:
        model = SentenceTransformer(SBERT_MODEL)
        embeddings = model.encode(chunks, convert_to_numpy=True, show_progress_bar=True)
        faiss.normalize_L2(embeddings)
        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings)
        faiss.write_index(index, str(INDEX_PATH))
        np.save(str(EMB_PATH), embeddings)
    return index, embeddings

# 3) Инициализация всего необходимого один раз при старте
_chunks = load_chunks()
_index, _embs = build_or_load_index(_chunks)
_sbert = SentenceTransformer(SBERT_MODEL)
_qa    = pipeline(
    "question-answering",
    model=QA_MODEL,
    tokenizer=QA_MODEL
)

def answer_question(question: str, top_k: int = 3) -> tuple[str, float]:
    """
    Основная функция для отвечания на вопрос.
    Возвращает кортеж (answer, score).
    """
    # Вектор вопроса
    qv = _sbert.encode([question], normalize_embeddings=True)
    D, I = _index.search(qv, top_k)

    # Ищем лучший ответ среди top_k чанков
    best = {"score": 0.0, "answer": "Извините, не нашлось ответа."}
    for idx in I[0]:
        ctx = _chunks[idx]
        out = _qa(question=question, context=ctx)
        if out["score"] > best["score"]:
            best = out

    return best["answer"], float(best["score"])
