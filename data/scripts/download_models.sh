#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
MODELS_DIR="$ROOT_DIR/models"
DATA_DIR="$ROOT_DIR/data"

echo "=== Tải model weights cho SgBe Vision ==="
echo ""

# Create directories
mkdir -p "$MODELS_DIR"/{paddleocr,whisper,yolo}
mkdir -p "$DATA_DIR"/{sgk,embeddings,audio_samples}

# ── YOLOv8 ──
echo "[1/3] YOLOv8 nano..."
YOLO_PATH="$MODELS_DIR/yolo/yolov8n.pt"
if [ ! -f "$YOLO_PATH" ]; then
    wget -q --show-progress "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt" -O "$YOLO_PATH"
    echo "  ✅ YOLOv8: $YOLO_PATH"
else
    echo "  ⏭️  YOLOv8 đã tồn tại"
fi

# ── Whisper (phoWhisper) ──
echo "[2/3] PhoWhisper base..."
WHISPER_DIR="$MODELS_DIR/whisper"
# faster-whisper downloads automatically on first use
# Just create a marker
echo "  📝 PhoWhisper sẽ được download tự động khi chạy STT lần đầu"
touch "$WHISPER_DIR/.downloaded_on_demand"

# ── PaddleOCR ──
echo "[3/3] PaddleOCR models..."
# PaddleOCR also downloads models on first run
echo "  📝 PaddleOCR sẽ được download tự động khi chạy OCR lần đầu"
touch "$MODELS_DIR/paddleocr/.downloaded_on_demand"

echo ""
echo "=== Hoàn tất ==="
echo "YOLOv8: $(ls -lh "$YOLO_PATH" 2>/dev/null | awk '{print $5}')"
echo "Các model Whisper/PaddleOCR sẽ tự động tải khi chạy lần đầu."
