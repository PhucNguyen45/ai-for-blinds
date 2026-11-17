import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'theme.dart';

/// Nút lớn cho người không nhìn: cao tối thiểu 80, viền dày, chữ 24,
/// rung khi chạm, nhãn và gợi ý riêng cho TalkBack.
class BigButton extends StatelessWidget {
  const BigButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.hint,
    this.icon,
    this.height = AppTheme.minTouch,
    this.emphasized = false,
  });

  final String label;
  final String? hint;
  final IconData? icon;
  final VoidCallback? onPressed;
  final double height;
  final bool emphasized;

  @override
  Widget build(BuildContext context) {
    final fg = emphasized ? Colors.black : AppTheme.foreground;
    final bg = emphasized ? AppTheme.accent : AppTheme.background;
    return Semantics(
      button: true,
      enabled: onPressed != null,
      label: label,
      hint: hint,
      excludeSemantics: true,
      onTap: onPressed == null ? null : _tap,
      child: SizedBox(
        height: height,
        width: double.infinity,
        child: Material(
          color: bg,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: const BorderSide(color: AppTheme.accent, width: 3),
          ),
          child: InkWell(
            borderRadius: BorderRadius.circular(16),
            onTap: onPressed == null ? null : _tap,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
              // Nút hẹp (3 nút một hàng): biểu tượng trên, chữ dưới.
              // FittedBox chỉ thu nhỏ khi chữ hệ thống phóng quá to, để không bao giờ tràn.
              child: LayoutBuilder(
                builder: (context, box) {
                  final narrow = box.maxWidth < 180;
                  final text = Text(
                    label,
                    textAlign: TextAlign.center,
                    maxLines: 2,
                    style: TextStyle(fontSize: narrow ? 20 : 24, fontWeight: FontWeight.w700, color: fg),
                  );
                  final content = narrow
                      ? Column(mainAxisSize: MainAxisSize.min, children: [
                          if (icon != null) Icon(icon, size: 30, color: fg),
                          text,
                        ])
                      : Row(mainAxisSize: MainAxisSize.min, children: [
                          if (icon != null) ...[Icon(icon, size: 32, color: fg), const SizedBox(width: 8)],
                          Flexible(child: text),
                        ]);
                  return Center(child: FittedBox(fit: BoxFit.scaleDown, child: content));
                },
              ),
            ),
          ),
        ),
      ),
    );
  }

  void _tap() {
    HapticFeedback.mediumImpact();
    onPressed?.call();
  }
}
