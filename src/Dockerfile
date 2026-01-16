FROM python:3.9-slim

WORKDIR /app

COPY app.py .
# Install Flask AND Gunicorn (Production Server)
RUN pip install flask gunicorn

# CMD is now Gunicorn, not "python app.py"
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
