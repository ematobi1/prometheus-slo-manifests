FROM python:3.12-slim
WORKDIR /app
COPY exporter.py .
USER nobody
EXPOSE 8000
CMD ["python", "-u", "exporter.py"]
