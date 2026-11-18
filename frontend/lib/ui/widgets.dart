import 'dart:math' as math;

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../services/speech.dart';
import '../strings.dart';
import 'explore.dart';
import 'theme.dart';

/// Viền chọn: vẽ trong khoảng đệm quanh nút (trên nền tối), nên thấy rõ cả với nút màu sáng.
/// Khoảng đệm luôn có sẵn để nút không nhảy kích thước khi được chọn.
class FocusFrame extends StatelessWidget {
  const FocusFrame({super.key, required this.focused, required this.child, this.radius = AppTheme.radius});

  final bool focused;
  final Widget child;
  final double radius;

  static const gap = 5.0;

  @override
  Widget build(BuildContext context) {
    final reduce = MediaQuery.disableAnimationsOf(context);
    return AnimatedContainer(
      duration: reduce ? Duration.zero : const Duration(milliseconds: 140),
      padding: const EdgeInsets.all(gap),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(radius + gap),
        border: Border.all(color: focused ? AppTheme.paper : Colors.transparent, width: 3),
      ),
      child: AnimatedScale(
        scale: focused && !reduce ? 0.97 : 1,
        duration: const Duration(milliseconds: 140),
        child: child,
      ),
    );
  }
}

/// Ba nút lớn ở mép dưới màn hình chính: mỗi nút một màu, biểu tượng trên, chữ dưới.
class ColorTile extends StatelessWidget {
  const ColorTile({
    super.key,
    required this.label,
    required this.spoken,
    required this.icon,
    required this.color,
    required this.onActivate,
    this.height = AppTheme.tileHeight,
  });

  final String label;
  final String spoken;
  final IconData icon;
  final Color color;
  final VoidCallback onActivate;
  final double height;

  @override
  Widget build(BuildContext context) {
    return ExploreTarget(
      label: label,
      spoken: spoken,
      onActivate: onActivate,
      builder: (context, focused) => FocusFrame(
        focused: focused,
        child: Container(
          height: height - FocusFrame.gap * 2,
          decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(AppTheme.radius)),
          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 8),
          child: Center(
            child: FittedBox(
              fit: BoxFit.scaleDown,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 50,
                    height: 50,
                    decoration: BoxDecoration(color: AppTheme.ink.withValues(alpha: 0.12), shape: BoxShape.circle),
                    child: Icon(icon, size: 30, color: AppTheme.ink),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    label,
                    style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: AppTheme.ink),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Nút góc trên (Cài đặt, Trợ giúp): nền tối trong mờ nổi trên hình camera.
class GlassButton extends StatelessWidget {
  const GlassButton({
    super.key,
    required this.label,
    required this.spoken,
    required this.icon,
    required this.onActivate,
  });

  final String label;
  final String spoken;
  final IconData icon;
  final VoidCallback onActivate;

  @override
  Widget build(BuildContext context) {
    return ExploreTarget(
      label: label,
      spoken: spoken,
      onActivate: onActivate,
      builder: (context, focused) => FocusFrame(
        focused: focused,
        radius: 20,
        child: Container(
          height: AppTheme.minTouch - FocusFrame.gap * 2,
          decoration: BoxDecoration(
            color: AppTheme.ink.withValues(alpha: 0.72),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: AppTheme.paper.withValues(alpha: 0.28), width: 1.5),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 12),
          child: Center(
            child: FittedBox(
              fit: BoxFit.scaleDown,
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(icon, size: 26, color: AppTheme.paper),
                  const SizedBox(width: 10),
                  Text(
                    label,
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppTheme.paper),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Hàng bấm được trong danh sách (Cài đặt, Thư viện, câu hỏi gợi ý).
class RowButton extends StatelessWidget {
  const RowButton({
    super.key,
    required this.title,
    required this.spoken,
    required this.icon,
    required this.accent,
    required this.onActivate,
    this.subtitle,
    this.value,
  });

  final String title;
  final String spoken;
  final IconData icon;
  final Color accent;
  final VoidCallback onActivate;
  final String? subtitle;

  /// Giá trị hiện tại (vd "Bình thường", "Bật"), hiện thành nhãn vàng ở cuối hàng.
  final String? value;

  @override
  Widget build(BuildContext context) {
    return ExploreTarget(
      label: value == null ? title : '$title: $value',
      spoken: spoken,
      onActivate: onActivate,
      builder: (context, focused) => FocusFrame(
        focused: focused,
        radius: 22,
        child: Container(
          constraints: const BoxConstraints(minHeight: AppTheme.minTouch - FocusFrame.gap * 2),
          decoration: BoxDecoration(
            color: AppTheme.surfaceHigh,
            borderRadius: BorderRadius.circular(22),
            border: Border.all(color: AppTheme.line, width: 1.5),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          child: Row(
            children: [
              Container(
                width: 46,
                height: 46,
                decoration: BoxDecoration(color: accent, borderRadius: BorderRadius.circular(14)),
                child: Icon(icon, size: 26, color: AppTheme.ink),
              ),
              const SizedBox(width: 14),
              // Chữ xuống dòng theo đúng bề rộng hàng, rồi thu nhỏ nếu hàng thấp hơn
              // (màn hình nhỏ, chữ hệ thống phóng 200%): không bao giờ tràn.
              Expanded(
                child: LayoutBuilder(
                  builder: (context, box) => FittedBox(
                    fit: BoxFit.scaleDown,
                    alignment: Alignment.centerLeft,
                    child: SizedBox(
                      width: box.maxWidth,
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            title,
                            maxLines: subtitle == null ? 2 : 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w700, color: AppTheme.paper),
                          ),
                          if (subtitle != null)
                            Text(
                              subtitle!,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(fontSize: 15, color: AppTheme.mute),
                            ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
              if (value != null) ...[
                const SizedBox(width: 10),
                ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 132),
                  child: FittedBox(
                    fit: BoxFit.scaleDown,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(color: AppTheme.guide, borderRadius: BorderRadius.circular(999)),
                      child: Text(
                        value!,
                        style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w800, color: AppTheme.ink),
                      ),
                    ),
                  ),
                ),
              ] else
                const Icon(Icons.chevron_right_rounded, size: 30, color: AppTheme.mute),
            ],
          ),
        ),
      ),
    );
  }
}

/// Dải "Quay lại" chiếm cả mép dưới của mọi màn hình con: luôn cùng một chỗ.
class BackBar extends StatelessWidget {
  const BackBar({super.key, required this.onActivate, this.height = 96});

  final VoidCallback onActivate;
  final double height;

  @override
  Widget build(BuildContext context) {
    return ExploreTarget(
      label: S.back,
      spoken: S.backSay,
      onActivate: onActivate,
      builder: (context, focused) => FocusFrame(
        focused: focused,
        child: Container(
          height: height - FocusFrame.gap * 2,
          decoration: BoxDecoration(color: AppTheme.paper, borderRadius: BorderRadius.circular(AppTheme.radius)),
          child: const Center(
            child: FittedBox(
              fit: BoxFit.scaleDown,
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.arrow_back_rounded, size: 32, color: AppTheme.ink),
                  SizedBox(width: 10),
                  Text(
                    S.back,
                    style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: AppTheme.ink),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Đầu màn hình con. Chạm một lần nghe lại lời giới thiệu màn hình.
class ScreenHeader extends StatelessWidget {
  const ScreenHeader({
    super.key,
    required this.title,
    required this.intro,
    required this.onIntro,
    this.badge,
    this.trailing,
  });

  final String title;
  final String intro;
  final VoidCallback onIntro;
  final String? badge;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return ExploreTarget(
      label: title,
      spoken: intro,
      onActivate: onIntro,
      builder: (context, focused) => FocusFrame(
        focused: focused,
        radius: 18,
        child: ConstrainedBox(
          constraints: const BoxConstraints(minHeight: 58),
          child: Row(
            children: [
              const SizedBox(width: 4),
              Expanded(
                child: Text(
                  title,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 26,
                    fontWeight: FontWeight.w800,
                    height: 1.15,
                    color: AppTheme.paper,
                  ),
                ),
              ),
              if (badge != null) ...[const SizedBox(width: 8), Tag(text: badge!)],
              if (trailing != null) ...[const SizedBox(width: 10), trailing!],
            ],
          ),
        ),
      ),
    );
  }
}

/// Nhãn nhỏ viền vàng (loại hình, "Bản mẫu").
class Tag extends StatelessWidget {
  const Tag({super.key, required this.text, this.color = AppTheme.guide});
  final String text;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: color, width: 1.5),
      ),
      child: Text(
        text,
        style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: color),
      ),
    );
  }
}

/// Bong bóng phụ đề: luôn hiện câu app đang nói (học theo Envision).
class CaptionBubble extends StatelessWidget {
  const CaptionBubble({super.key, required this.caption});
  final ValueListenable<Caption> caption;

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<Caption>(
      valueListenable: caption,
      builder: (context, c, _) {
        final idle = c.text.isEmpty;
        return Container(
          constraints: const BoxConstraints(minHeight: 64),
          padding: const EdgeInsets.fromLTRB(8, 8, 14, 8),
          decoration: BoxDecoration(color: AppTheme.paper, borderRadius: BorderRadius.circular(20)),
          child: Row(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: c.speaking ? AppTheme.guide : AppTheme.ink.withValues(alpha: 0.08),
                  borderRadius: BorderRadius.circular(13),
                ),
                child: Icon(
                  c.speaking ? Icons.graphic_eq_rounded : Icons.volume_up_rounded,
                  size: 26,
                  color: AppTheme.ink,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  idle ? S.captionIdle : c.text,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 16,
                    height: 1.3,
                    fontWeight: FontWeight.w600,
                    color: c.speaking ? AppTheme.ink : const Color(0xFF55534C),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

/// Đoạn văn đọc từng câu: câu đang đọc tô vàng (học theo Lookout), tự cuộn theo giọng đọc.
class ReadingText extends StatefulWidget {
  const ReadingText({
    super.key,
    required this.sentences,
    required this.active,
    this.fontSize = 22,
    this.color = AppTheme.paper,
  });

  final List<String> sentences;

  /// Câu đang đọc; -1 khi không đọc.
  final int active;
  final double fontSize;
  final Color color;

  @override
  State<ReadingText> createState() => _ReadingTextState();
}

class _ReadingTextState extends State<ReadingText> {
  final _scroll = ScrollController();
  double _width = 0;

  @override
  void dispose() {
    _scroll.dispose();
    super.dispose();
  }

  @override
  void didUpdateWidget(ReadingText old) {
    super.didUpdateWidget(old);
    if (widget.active != old.active && widget.active >= 0) {
      WidgetsBinding.instance.addPostFrameCallback((_) => _follow());
    } else if (!listEquals(widget.sentences, old.sentences) && _scroll.hasClients) {
      _scroll.jumpTo(0);
    }
  }

  TextStyle get _base =>
      TextStyle(fontSize: widget.fontSize, height: 1.5, fontWeight: FontWeight.w500, color: widget.color);

  TextSpan _span() => TextSpan(
    style: _base,
    children: [
      for (var i = 0; i < widget.sentences.length; i++) ...[
        if (i > 0) const TextSpan(text: ' '),
        TextSpan(
          text: widget.sentences[i],
          style: i == widget.active
              ? const TextStyle(backgroundColor: AppTheme.guide, color: AppTheme.ink, fontWeight: FontWeight.w600)
              : null,
        ),
      ],
    ],
  );

  /// Cuộn để câu đang đọc nằm ở khoảng một phần tư trên của khung.
  void _follow() {
    if (!mounted || !_scroll.hasClients || _width <= 0) return;
    var offset = 0;
    for (var i = 0; i < widget.active && i < widget.sentences.length; i++) {
      offset += widget.sentences[i].length + 1;
    }
    final painter = TextPainter(
      text: _span(),
      textDirection: TextDirection.ltr,
      textScaler: MediaQuery.textScalerOf(context),
    )..layout(maxWidth: _width);
    final y = painter.getOffsetForCaret(TextPosition(offset: offset), Rect.zero).dy;
    painter.dispose();
    final pos = _scroll.position;
    final target = (y - pos.viewportDimension * 0.25).clamp(0.0, pos.maxScrollExtent);
    if (MediaQuery.disableAnimationsOf(context)) {
      _scroll.jumpTo(target);
    } else {
      _scroll.animateTo(target, duration: const Duration(milliseconds: 350), curve: Curves.easeOutCubic);
    }
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, box) {
        _width = box.maxWidth;
        return SingleChildScrollView(controller: _scroll, child: Text.rich(_span()));
      },
    );
  }
}

/// Bốn góc vàng ôm trang sách trong khung camera (học theo khung tài liệu của Lookout).
class PageBrackets extends StatelessWidget {
  const PageBrackets({super.key, this.color = AppTheme.guide});
  final Color color;

  @override
  Widget build(BuildContext context) => CustomPaint(painter: _BracketPainter(color), child: const SizedBox.expand());
}

class _BracketPainter extends CustomPainter {
  _BracketPainter(this.color);
  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final p = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 5
      ..strokeCap = StrokeCap.round;
    final arm = math.min(46.0, size.shortestSide * 0.18);
    const r = 14.0;
    // Viền tối dưới nét vàng: góc vẫn nổi khi trang sách trắng, sáng.
    final shadow = Paint()
      ..color = AppTheme.ink.withValues(alpha: 0.55)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 10
      ..strokeCap = StrokeCap.round;
    void corner(Offset o, double dx, double dy) {
      final path = Path()
        ..moveTo(o.dx, o.dy + dy * arm)
        ..lineTo(o.dx, o.dy + dy * r)
        ..quadraticBezierTo(o.dx, o.dy, o.dx + dx * r, o.dy)
        ..lineTo(o.dx + dx * arm, o.dy);
      canvas.drawPath(path, shadow);
      canvas.drawPath(path, p);
    }

    corner(Offset.zero, 1, 1);
    corner(Offset(size.width, 0), -1, 1);
    corner(Offset(0, size.height), 1, -1);
    corner(Offset(size.width, size.height), -1, -1);
  }

  @override
  bool shouldRepaint(_BracketPainter old) => old.color != color;
}

/// Nút chụp tròn vẽ trong vùng chụp (chỉ để nhìn: cả vùng chụp là nút).
/// Khi đang chờ máy chủ, vòng ngoài thành vòng quay vàng.
class ShutterRing extends StatelessWidget {
  const ShutterRing({super.key, required this.busy});
  final bool busy;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 84,
      height: 84,
      child: Stack(
        alignment: Alignment.center,
        children: [
          if (busy)
            const SizedBox.expand(child: CircularProgressIndicator(strokeWidth: 5, color: AppTheme.guide))
          else
            Container(
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: AppTheme.paper, width: 5),
              ),
            ),
          AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            width: busy ? 34 : 62,
            height: busy ? 34 : 62,
            decoration: BoxDecoration(color: AppTheme.guide, borderRadius: BorderRadius.circular(busy ? 10 : 31)),
          ),
        ],
      ),
    );
  }
}

/// Nhãn trạng thái giữa đáy vùng chụp.
class StatusPill extends StatelessWidget {
  const StatusPill({super.key, required this.text, this.color = AppTheme.guide});
  final String text;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
      decoration: BoxDecoration(
        color: AppTheme.ink.withValues(alpha: 0.86),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: color, width: 2.5),
      ),
      child: Text(
        text,
        textAlign: TextAlign.center,
        style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: color),
      ),
    );
  }
}
