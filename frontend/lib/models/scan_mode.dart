import 'package:flutter/material.dart';

/// Enum representing the available scan modes.
enum ScanMode {
  ocr,
  describe,
  chart,
  detect,
  money;

  String get label {
    switch (this) {
      case ScanMode.ocr:
        return 'Đọc văn bản';
      case ScanMode.describe:
        return 'Mô tả ảnh';
      case ScanMode.chart:
        return 'Đọc biểu đồ';
      case ScanMode.detect:
        return 'Phát hiện vật thể';
      case ScanMode.money:
        return 'Nhận dạng tiền';
    }
  }

  String get subtitle {
    switch (this) {
      case ScanMode.ocr:
        return 'Trích xuất chữ từ tài liệu';
      case ScanMode.describe:
        return 'AI mô tả nội dung ảnh';
      case ScanMode.chart:
        return 'Chuyển biểu đồ thành âm thanh';
      case ScanMode.detect:
        return 'YOLO nhận diện đồ vật';
      case ScanMode.money:
        return 'Xác định mệnh giá tiền Việt Nam';
    }
  }

  IconData get icon {
    switch (this) {
      case ScanMode.ocr:
        return Icons.text_fields_rounded;
      case ScanMode.describe:
        return Icons.image_search_rounded;
      case ScanMode.chart:
        return Icons.bar_chart_rounded;
      case ScanMode.detect:
        return Icons.search_rounded;
      case ScanMode.money:
        return Icons.attach_money_rounded;
    }
  }
}
