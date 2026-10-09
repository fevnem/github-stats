# github-stats — any container host, any VPS.
# No dependencies, so the image stays tiny and the build needs no network.
FROM python:3.12-alpine

WORKDIR /app
COPY github_stats/ ./github_stats/
COPY server.py ./

# Drop privileges: nothing here needs root.
RUN adduser -D -H -u 10001 stats
USER stats

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s \
  CMD python3 -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/').read()" || exit 1

CMD ["python3", "server.py", "--host", "0.0.0.0", "--port", "8000"]
