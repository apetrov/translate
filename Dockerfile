FROM python:3.12

COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt

CMD ["make", "run"]
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
