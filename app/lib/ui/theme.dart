import 'package:flutter/material.dart';

/// Tương phản cao: nền đen, chữ trắng, điểm nhấn vàng (tỉ lệ tương phản > 15:1).
/// Không dùng gradient, bóng đổ, hay màu làm kênh thông tin duy nhất.
class AppTheme {
  AppTheme._();

  static const background = Colors.black;
  static const foreground = Colors.white;
  static const accent = Color(0xFFFFD60A); // vàng
  static const danger = Color(0xFFFF6B6B);

  /// Vùng chạm tối thiểu theo checklist trợ năng của nhóm.
  static const minTouch = 80.0;
  static const primaryTouch = 120.0;

  static ThemeData build() {
    final base = ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: background,
      colorScheme: const ColorScheme.dark(
        primary: accent,
        onPrimary: Colors.black,
        surface: background,
        onSurface: foreground,
        error: danger,
      ),
    );
    return base.copyWith(
      textTheme: base.textTheme.apply(bodyColor: foreground, displayColor: foreground).copyWith(
            bodyLarge: const TextStyle(fontSize: 22, height: 1.4, color: foreground),
            bodyMedium: const TextStyle(fontSize: 20, height: 1.4, color: foreground),
            titleLarge: const TextStyle(fontSize: 26, fontWeight: FontWeight.w700, color: foreground),
            labelLarge: const TextStyle(fontSize: 24, fontWeight: FontWeight.w700),
          ),
      appBarTheme: const AppBarTheme(
        backgroundColor: background,
        foregroundColor: foreground,
        toolbarHeight: 72,
        titleTextStyle: TextStyle(fontSize: 26, fontWeight: FontWeight.w700, color: foreground),
      ),
      sliderTheme: const SliderThemeData(trackHeight: 8, thumbShape: RoundSliderThumbShape(enabledThumbRadius: 18)),
    );
  }
}
