from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter

from src.settings import settings


def parse_html(html_path: str) -> list[dict[str, str]]:
    """
    Парсит HTML файл и извлекает вопросы и ответы.

    Args:
        html_path: Путь к HTML файлу

    Returns:
        list[dict]: Список словарей с полями text, chunk_id, source, date
    """
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")
    articles = soup.find_all("article", class_="kb-item")

    chunks = []
    for article in articles:
        chunk_id = article.get("data-id", "")
        date = article.get("data-date", "")
        source = article.get("data-source", "")

        h2 = article.find("h2")
        question = h2.get_text(strip=True) if h2 else ""

        answer_div = article.find("div", class_="answer")
        answer = ""
        if answer_div:
            paragraphs = answer_div.find_all("p")
            answer = " ".join(p.get_text(strip=True) for p in paragraphs)

        text = f"{question}\n{answer}".strip()
        if text:
            chunks.append(
                {
                    "text": text,
                    "chunk_id": chunk_id,
                    "source": source,
                    "date": date,
                }
            )

    return chunks


def split_chunks(chunks: list[dict[str, str]]) -> list[dict[str, str]]:
    """
    Разбивает чанки на более мелкие части с перекрытием.

    Args:
        chunks: Список исходных чанков

    Returns:
        list[dict]: Список разбитых чанков с метаданными
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        length_function=len,
    )

    split_chunks_list = []
    for chunk in chunks:
        texts = text_splitter.split_text(chunk["text"])
        for i, text in enumerate(texts):
            split_chunks_list.append(
                {
                    "text": text,
                    "chunk_id": f"{chunk['chunk_id']}_{i}",
                    "source": chunk["source"],
                    "date": chunk["date"],
                }
            )

    return split_chunks_list

