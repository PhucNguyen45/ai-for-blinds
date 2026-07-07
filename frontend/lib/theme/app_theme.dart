import 'package:flutter/material.dart';
import 'colors.dart';

/// 🎨 Neon Pulse theme system.
/// Dark-first, high-contrast, với glow tokens cho neon effects.
class AppTheme {
  // Re-export colors cho tiện import
  static const Color background = AppColors.background;
  static const Color surface = AppColors.surface;
  static const Color border = AppColors.border;
  static const Color primary = AppColors.primary;
  static const Color secondary = AppColors.secondary;
  static const Color success = AppColors.success;
  static const Color warning = AppColors.warning;
  static const Color error = AppColors.error;
  static const Color textPrimary = AppColors.textPrimary;
  static const Color textMuted = AppColors.textMuted;

  // Legacy aliases
  static const Color pureWhite = AppColors.pureWhite;
  static const Color pureBlack = AppColors.pureBlack;
  static const Color primaryBlue = AppColors.primaryBlue;
  static const Color primaryDark = AppColors.primaryDark;
  static const Color accentOrange = AppColors.accentOrange;
  static const Color accentGreen = AppColors.accentGreen;
  static const Color accentRed = AppColors.accentRed;
  static const Color darkSurface = AppColors.darkSurface;
  static const Color darkCard = AppColors.darkCard;
  static const Color lightGray = AppColors.lightGray;

  /// Default theme — **Dark-first** với neon glow
  static ThemeData get darkHighContrast {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: AppColors.background,
      fontFamily: 'Roboto',

      colorScheme: ColorScheme.dark(
        primary: AppColors.primary,
        secondary: AppColors.secondary,
        surface: AppColors.surface,
        error: AppColors.error,
        onPrimary: AppColors.pureBlack,
        onSecondary: AppColors.pureWhite,
        onSurface: AppColors.textPrimary,
        onError: AppColors.pureWhite,
        brightness: Brightness.dark,
      ),

      // ─── Typography: Lớn, rõ, high-contrast ─────
      textTheme: const TextTheme(
        displayLarge: TextStyle(
          fontSize: 42, fontWeight: FontWeight.bold,
          color: AppColors.textPrimary, height: 1.2,
        ),
        displayMedium: TextStyle(
          fontSize: 36, fontWeight: FontWeight.bold,
          color: AppColors.textPrimary, height: 1.2,
        ),
        headlineLarge: TextStyle(
          fontSize: 30, fontWeight: FontWeight.w700,
          color: AppColors.textPrimary, height: 1.3,
        ),
        headlineMedium: TextStyle(
          fontSize: 26, fontWeight: FontWeight.w700,
          color: AppColors.textPrimary, height: 1.3,
        ),
        titleLarge: TextStyle(
          fontSize: 24, fontWeight: FontWeight.w600,
          color: AppColors.textPrimary, height: 1.4,
        ),
        titleMedium: TextStyle(
          fontSize: 22, fontWeight: FontWeight.w600,
          color: AppColors.textPrimary, height: 1.4,
        ),
        bodyLarge: TextStyle(
          fontSize: 22, fontWeight: FontWeight.normal,
          color: AppColors.textPrimary, height: 1.6,
        ),
        bodyMedium: TextStyle(
          fontSize: 20, fontWeight: FontWeight.normal,
          color: AppColors.textPrimary, height: 1.6,
        ),
        labelLarge: TextStyle(
          fontSize: 20, fontWeight: FontWeight.w600,
          color: AppColors.textPrimary, height: 1.4,
        ),
        labelSmall: TextStyle(
          fontSize: 16, fontWeight: FontWeight.normal,
          color: AppColors.textMuted, height: 1.4,
        ),
      ),

      // ─── AppBar: minimal, không elevation ─────
      appBarTheme: const AppBarTheme(
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: true,
        backgroundColor: Colors.transparent,
        foregroundColor: AppColors.textPrimary,
        titleTextStyle: TextStyle(
          fontSize: 24, fontWeight: FontWeight.w600,
          color: AppColors.textPrimary,
        ),
        iconTheme: IconThemeData(size: 28, color: AppColors.textPrimary),
        toolbarHeight: 64,
      ),

      // ─── Bottom Navigation ────────────────────
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: AppColors.surface,
        selectedItemColor: AppColors.primary,
        unselectedItemColor: AppColors.textMuted,
        type: BottomNavigationBarType.fixed,
        elevation: 0,
        selectedLabelStyle: TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
        unselectedLabelStyle: TextStyle(fontSize: 12),
      ),

      // ─── Buttons: full-width, large ───────────
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.primary,
          foregroundColor: AppColors.pureBlack,
          minimumSize: const Size(double.infinity, 64),
          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 18),
          textStyle: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
          ),
          elevation: 0,
          shadowColor: AppColors.primary.withValues(alpha: 0.3),
        ),
      ),

      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size(double.infinity, 64),
          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 18),
          textStyle: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
          ),
        ),
      ),

      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size(double.infinity, 64),
          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 18),
          textStyle: const TextStyle(fontSize: 22, fontWeight: FontWeight.w600),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
          ),
          side: const BorderSide(color: AppColors.border, width: 2),
        ),
      ),

      // ─── Cards ───────────────────────────────
      cardTheme: CardThemeData(
        color: AppColors.surface,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(24),
          side: const BorderSide(color: AppColors.border, width: 1),
        ),
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      ),

      // ─── Sliders (large) ─────────────────────
      sliderTheme: SliderThemeData(
        trackHeight: 10,
        thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 18),
        overlayShape: const RoundSliderOverlayShape(overlayRadius: 32),
        activeTrackColor: AppColors.primary,
        inactiveTrackColor: AppColors.border,
        thumbColor: AppColors.primary,
        valueIndicatorColor: AppColors.primary,
        valueIndicatorTextStyle: const TextStyle(
          fontSize: 18, fontWeight: FontWeight.w600, color: AppColors.pureBlack,
        ),
      ),

      // ─── Chips ───────────────────────────────
      chipTheme: ChipThemeData(
        backgroundColor: AppColors.surface,
        labelStyle: const TextStyle(fontSize: 18, color: AppColors.textPrimary),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(100),
          side: const BorderSide(color: AppColors.border),
        ),
      ),

      // ─── Input fields ────────────────────────
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.surfaceAlt,
        contentPadding: const EdgeInsets.all(20),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: AppColors.border, width: 2),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: AppColors.border, width: 2),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: AppColors.primary, width: 2),
        ),
        labelStyle: const TextStyle(fontSize: 20, color: AppColors.textMuted),
        hintStyle: const TextStyle(fontSize: 18, color: AppColors.textDim),
      ),

      // ─── Snackbar ────────────────────────────
      snackBarTheme: SnackBarThemeData(
        backgroundColor: AppColors.surface,
        contentTextStyle: const TextStyle(
          fontSize: 18, color: AppColors.textPrimary,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: AppColors.border),
        ),
        behavior: SnackBarBehavior.floating,
      ),

      // ─── Divider ─────────────────────────────
      dividerColor: AppColors.border,
      dividerTheme: const DividerThemeData(
        color: AppColors.border,
        thickness: 1,
        space: 1,
      ),

      // ─── Switch ──────────────────────────────
      switchTheme: SwitchThemeData(
        trackOutlineWidth: const WidgetStatePropertyAll(2),
        thumbColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) return AppColors.primary;
          return AppColors.textMuted;
        }),
        trackColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) return AppColors.primary.withValues(alpha: 0.3);
          return AppColors.border;
        }),
      ),
    );
  }

  /// Light variant — pure high-contrast (chỉ dùng khi user override)
  static ThemeData get lightHighContrast {
    final dark = darkHighContrast;
    return dark.copyWith(
      brightness: Brightness.light,
      scaffoldBackgroundColor: AppColors.pureWhite,
      colorScheme: ColorScheme.light(
        primary: AppColors.primaryBlue,
        secondary: AppColors.secondary,
        surface: AppColors.pureWhite,
        error: AppColors.accentRed,
        onPrimary: AppColors.pureWhite,
        onSecondary: AppColors.pureWhite,
        onSurface: AppColors.pureBlack,
        onError: AppColors.pureWhite,
        brightness: Brightness.light,
      ),
      textTheme: dark.textTheme.apply(
        bodyColor: AppColors.pureBlack,
        displayColor: AppColors.pureBlack,
      ),
      cardTheme: dark.cardTheme.copyWith(
        color: AppColors.pureWhite,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(24),
          side: const BorderSide(color: Colors.grey, width: 2),
        ),
      ),
      bottomNavigationBarTheme: dark.bottomNavigationBarTheme.copyWith(
        backgroundColor: AppColors.pureWhite,
      ),
      dividerColor: Colors.grey.shade300,
    );
  }
}
