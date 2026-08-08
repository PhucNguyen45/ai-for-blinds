import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

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

/// Widget for selecting the scan mode: OCR / Describe / Chart.
/// Three big buttons arranged in a row, each with icon + label + subtitle.
/// Highlights the currently selected mode.
class ModeSelector extends StatelessWidget {
  /// The currently selected mode.
  final ScanMode selectedMode;

  /// Callback when a mode is selected.
  final ValueChanged<ScanMode> onModeChanged;

  const ModeSelector({
    super.key,
    required this.selectedMode,
    required this.onModeChanged,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Semantics(
              label: 'Chọn chế độ quét.',
              child: Text(
                'Chế độ quét',
                style: theme.textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(8),
            child: Semantics(
              label: 'Chọn chế độ quét.',
              child: Text(
                'Chọn chế độ quét:',
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
            ),
          ),
          ...ScanMode.values.map((mode) {
            final isSelected = mode == selectedMode;
            return Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              child: _ModeButton(
                mode: mode,
                isSelected: isSelected,
                isDark: isDark,
                onTap: () => onModeChanged(mode),
              ),
            );
          }),
        ],
      ),
    );
  }
}

class _ModeButton extends StatelessWidget {
  final ScanMode mode;
  final bool isSelected;
  final bool isDark;
  final VoidCallback onTap;

  const _ModeButton({
    required this.mode,
    required this.isSelected,
    required this.isDark,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final Color bgColor = isSelected
        ? const Color(0xFF1565C0)
        : (isDark ? const Color(0xFF1E1E1E) : Colors.grey.shade200);
    final Color textColor = isSelected ? Colors.white : Colors.black87;

    return Semantics(
      button: true,
      label: '${mode.label}. ${mode.subtitle}. ${isSelected ? 'Đang chọn.' : ''}',
      child: GestureDetector(
        onTap: () {
          HapticFeedback.lightImpact();
          onTap();
        },
        child: Container(
          width: double.infinity,
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: bgColor,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: isSelected
                  ? const Color(0xFF1565C0)
                  : (isDark ? Colors.grey.shade700 : Colors.grey.shade400),
              width: 2,
            ),
          ),
          child: Column(
            children: [
              Icon(
                mode.icon,
                size: 36,
                color: isSelected ? Colors.white : const Color(0xFF1565C0),
              ),
              const SizedBox(height: 8),
              Text(
                mode.label,
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                  color: textColor,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 2),
              Text(
                mode.subtitle,
                style: TextStyle(
                  fontSize: 12,
                  color: isSelected
                      ? Colors.white.withValues(alpha: 0.8)
                      : Colors.grey.shade600,
                ),
                textAlign: TextAlign.center,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
