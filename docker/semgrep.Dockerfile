FROM python:3.10-slim
RUN pip install --no-cache-dir semgrep
ENTRYPOINT ["semgrep"] 