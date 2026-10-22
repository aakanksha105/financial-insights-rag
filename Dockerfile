FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .
COPY app.py ./
COPY data/sample ./data/sample
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser
ENV PORT=8080 PYTHONUNBUFFERED=1
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import os,urllib.request; urllib.request.urlopen('http://localhost:'+os.getenv('PORT','8080')+'/_stcore/health')"
CMD ["sh", "-c", "streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT:-8080} --server.headless=true --server.maxUploadSize=10 --browser.gatherUsageStats=false"]
