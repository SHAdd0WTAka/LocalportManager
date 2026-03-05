FROM python:3.11-slim

LABEL org.opencontainers.image.source="https://github.com/SHAdd0WTAka/LocalportManager"
LABEL org.opencontainers.image.description="Zero-dependency local reverse proxy"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

COPY localportmanager.py .
COPY README.md .
COPY LICENSE .

RUN chmod +x localportmanager.py

EXPOSE 1355

ENTRYPOINT ["python", "/app/localportmanager.py"]
CMD ["proxy"]
