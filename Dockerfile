# syntax=docker/dockerfile:1

#################################################
#              Stage 1: Builder                #
#################################################
FROM python:3.12-slim AS builder

# 1) Обновляем apt и ставим всё, что нужно для сборки PyMuPDF, faiss и других C-расширений
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      libmupdf-dev \
      pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2) Копируем только requirements и собираем wheel-файлы
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

#################################################
#             Stage 2: Final Image             #
#################################################
FROM python:3.12-slim

WORKDIR /app

# 3) Копируем и устанавливаем только что собранные колёса
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*

# 4) Затем копируем весь ваш код (data/ у нас в .dockerignore)
COPY . .

# 5) И точка входа
CMD ["python", "bot.py"]
