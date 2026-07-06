# Data Scripts

## download_models.sh

Tự động download model weights:
- YOLOv8 nano (yolov8n.pt)
- PhoWhisper (download lần đầu khi chạy STT)
- PaddleOCR (download lần đầu khi chạy OCR)

```bash
bash data/scripts/download_models.sh
```

## seed_rag.py

Index nội dung SGK vào ChromaDB để phục vụ RAG Q&A.

Yêu cầu cấu trúc thư mục:
```
data/sgk/
├── 10/
│   ├── Sinh hoc/
│   │   └── Bai 18 - Nguyen phan.txt
│   └── Toan/
│       └── Chuong 1 - Menh de.txt
├── 11/
│   └── ...
└── 12/
    └── ...
```

```bash
python data/scripts/seed_rag.py
```
