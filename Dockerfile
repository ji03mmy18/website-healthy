FROM python:3.12-slim

# 設置工作目錄
WORKDIR /app

# 複製需要的文件
COPY main.py requirements.txt ./

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 運行程式
CMD ["python", "main.py"]