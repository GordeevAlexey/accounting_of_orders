
FROM python:3.10.4
WORKDIR /accounting_of_orders
COPY . .
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --no-cache-dir --upgrade -r requirements.txt
CMD ["python3", "main.py"]