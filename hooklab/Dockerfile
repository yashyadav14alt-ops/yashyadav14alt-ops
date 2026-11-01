FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY static ./static
RUN mkdir -p /app/data && useradd --create-home --uid 10001 hooklab && chown -R hooklab:hooklab /app
USER hooklab
ENV HOOKLAB_DB=/app/data/hooklab.db
EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
