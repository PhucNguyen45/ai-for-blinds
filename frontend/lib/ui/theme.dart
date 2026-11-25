import 'package:flutter/material.dart';

/// Bảng màu và cỡ chữ của SgBe.
///
/// - Nền gần đen, chữ trắng ngà, điểm nhấn **vàng gạch dẫn đường** (màu gạch lát vỉa hè
///   dành cho người khiếm thị). Mọi cặp chữ/nền đạt tương phản trên 7:1 (WCAG AAA).
/// - Mỗi nút chính một màu (vàng, xanh trời, xanh lá) kèm biểu tượng và chữ:
///   màu chỉ giúp người nhìn kém tìm nhanh, không bao giờ là cách phân biệt duy nhất.
/// - Phông Be Vietnam Pro (đóng gói sẵn, chạy không cần mạng), thiết kế cho dấu tiếng Việt.
class AppTheme {
  AppTheme._();

  static const font = 'BeVietnamPro';

  static const ink = Color(0xFF0B0B0C); // nền
  static const surface = Color(0xFF17171A); // thẻ
  static const surfaceHigh = Color(0xFF222227); // hàng bấm được
  static const line = Color(0xFF3A3A41);
  static const paper = Color(0xFFF5F4EE); // chữ chính
  static const mute = Color(0xFFB4B2A8); // chữ phụ, ~9:1 trên nền
  static const guide = Color(0xFFFFD400); // vàng dẫn đường: chụp, đọc lại, câu đang đọc
  static const ask = Color(0xFF8EC9FF); // Hỏi
  static const lib = Color(0xFF86E3AE); // Thư viện
  static const danger = Color(0xFFFF8A7A);

  // Tên cũ, giữ cho mã đang dùng.
  static const background = ink;
  static const foreground = paper;
  static const accent = guide;

  /// Vùng chạm tối thiểu theo yêu cầu UI-21.
  static const minTouch = 80.0;
  static const tileHeight = 116.0;
  static const radius = 24.0;

  static ThemeData build() {
    final base = ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      fontFamily: font,
      scaffoldBackgroundColor: ink,
      colorScheme: const ColorScheme.dark(
        primary: guide,
        onPrimary: ink,
        secondary: ask,
        onSecondary: ink,
        tertiary: lib,
        onTertiary: ink,
        surface: ink,
        onSurface: paper,
        surfaceContainer: surface,
        surfaceContainerHigh: surfaceHigh,
        outline: line,
        error: danger,
        onError: ink,
      ),
    );
    return base.copyWith(
      textTheme: base.textTheme
          .apply(bodyColor: paper, displayColor: paper, fontFamily: font)
          .copyWith(
            bodyLarge: const TextStyle(fontFamily: font, fontSize: 22, height: 1.45, color: paper),
            bodyMedium: const TextStyle(fontFamily: font, fontSize: 20, height: 1.45, color: paper),
            titleLarge: const TextStyle(fontFamily: font, fontSize: 26, fontWeight: FontWeight.w800, color: paper),
            labelLarge: const TextStyle(fontFamily: font, fontSize: 22, fontWeight: FontWeight.w700),
          ),
      appBarTheme: const AppBarTheme(
        backgroundColor: ink,
        foregroundColor: paper,
        toolbarHeight: 72,
        titleTextStyle: TextStyle(fontFamily: font, fontSize: 24, fontWeight: FontWeight.w800, color: paper),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surface,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: line, width: 2),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: guide, width: 3),
        ),
      ),
      sliderTheme: const SliderThemeData(
        trackHeight: 10,
        thumbShape: RoundSliderThumbShape(enabledThumbRadius: 18),
        activeTrackColor: guide,
        thumbColor: guide,
        inactiveTrackColor: line,
      ),
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith((s) => s.contains(WidgetState.selected) ? ink : mute),
        trackColor: WidgetStateProperty.resolveWith((s) => s.contains(WidgetState.selected) ? guide : surfaceHigh),
      ),
      pageTransitionsTheme: const PageTransitionsTheme(
        builders: {TargetPlatform.android: FadeForwardsPageTransitionsBuilder()},
      ),
    );
  }
}
