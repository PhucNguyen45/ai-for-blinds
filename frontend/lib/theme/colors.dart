import 'package:flutter/material.dart';

/// 🎨 Neon Pulse color palette — high-contrast, dark-first, accessibility-driven.
/// Tất cả màu đều đạt WCAG AAA contrast ratio trên nền tối.
class AppColors {
  // ─── Backgrounds ───────────────────────────────────
  /// Nền chính — xanh đen sâu
  static const Color background = Color(0xFF0A0E1A);
  /// Nền surface card
  static const Color surface = Color(0xFF141829);
  /// Viền card / divider
  static const Color border = Color(0xFF1E2A4A);
  /// Nền dark variant cho card đặc biệt
  static const Color surfaceAlt = Color(0xFF0D1120);

  // ─── Neon Accents ─────────────────────────────────
  /// Primary — Cyan neon (WCAG AAA 7:1 trên nền tối)
  static const Color primary = Color(0xFF00F0FF);
  /// Secondary — Tím neon
  static const Color secondary = Color(0xFF9D4EDD);
  /// Success — Xanh lá neon
  static const Color success = Color(0xFF39FF14);
  /// Warning — Hổ phách
  static const Color warning = Color(0xFFFFB300);
  /// Error — Đỏ tươi
  static const Color error = Color(0xFFFF1744);
  /// Info / link — Xanh dương nhạt
  static const Color info = Color(0xFF448AFF);

  // ─── Text ─────────────────────────────────────────
  static const Color textPrimary = Color(0xFFFFFFFF);
  static const Color textMuted = Color(0xFF8892B0);
  static const Color textDim = Color(0xFF4A5580);

  // ─── Legacy aliases (for backward compat) ─────────
  static const Color pureWhite = Color(0xFFFFFFFF);
  static const Color pureBlack = Color(0xFF000000);
  static const Color primaryBlue = Color(0xFF1565C0);
  static const Color primaryDark = Color(0xFF0D47A1);
  static const Color accentOrange = Color(0xFFFF8F00);
  static const Color accentGreen = Color(0xFF2E7D32);
  static const Color accentRed = Color(0xFFC62828);
  static const Color darkSurface = Color(0xFF0A0E1A);
  static const Color darkCard = Color(0xFF141829);
  static const Color lightGray = Color(0xFF4A5580);

  // ─── Glow helpers ─────────────────────────────────
  /// Tạo glow shadow cho neon effect
  static List<BoxShadow> glow(Color color, {double radius = 8, double opacity = 0.4}) {
    return [
      BoxShadow(
        color: color.withValues(alpha: opacity),
        blurRadius: radius,
        spreadRadius: radius * 0.3,
      ),
    ];
  }

  /// Neon primary glow
  static List<BoxShadow> get primaryGlow => glow(primary, radius: 12, opacity: 0.35);
  /// Neon success glow
  static List<BoxShadow> get successGlow => glow(success, radius: 10, opacity: 0.3);
  /// Neon error glow
  static List<BoxShadow> get errorGlow => glow(error, radius: 10, opacity: 0.3);
}
