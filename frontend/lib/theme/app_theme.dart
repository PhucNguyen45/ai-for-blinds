import 'package:flutter/material.dart';
import 'colors.dart';

class AppTheme {
  // High-contrast colors (delegated to AppColors for single source of truth)
  static const Color primaryBlue = AppColors.primaryBlue;
  static const Color primaryDark = AppColors.primaryDark;
  static const Color accentOrange = AppColors.accentOrange;
  static const Color accentGreen = AppColors.accentGreen;
  static const Color accentRed = AppColors.accentRed;
  static const Color pureWhite = AppColors.pureWhite;
  static const Color pureBlack = AppColors.pureBlack;
  static const Color darkSurface = AppColors.darkSurface;
  static const Color darkCard = AppColors.darkCard;
  static const Color lightGray = AppColors.lightGray;

  /// Large, high-contrast light theme
  static ThemeData get lightHighContrast {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      colorScheme: ColorScheme.fromSeed(
        seedColor: primaryBlue,
        brightness: Brightness.light,
        contrastLevel: 1.0, // Maximum contrast
      ),
      scaffoldBackgroundColor: pureWhite,
      fontFamily: 'Roboto',

      // Large text theme for accessibility
      textTheme: const TextTheme(
        displayLarge: TextStyle(
          fontSize: 36,
          fontWeight: FontWeight.bold,
          color: pureBlack,
          height: 1.3,
        ),
        displayMedium: TextStyle(
          fontSize: 32,
          fontWeight: FontWeight.bold,
          color: pureBlack,
          height: 1.3,
        ),
        headlineLarge: TextStyle(
          fontSize: 28,
          fontWeight: FontWeight.w600,
          color: pureBlack,
          height: 1.3,
        ),
        headlineMedium: TextStyle(
          fontSize: 24,
          fontWeight: FontWeight.w600,
          color: pureBlack,
          height: 1.3,
        ),
        titleLarge: TextStyle(
          fontSize: 22,
          fontWeight: FontWeight.w500,
          color: pureBlack,
          height: 1.4,
        ),
        titleMedium: TextStyle(
          fontSize: 20,
          fontWeight: FontWeight.w500,
          color: pureBlack,
          height: 1.4,
        ),
        bodyLarge: TextStyle(
          fontSize: 20,
          fontWeight: FontWeight.normal,
          color: pureBlack,
          height: 1.5,
        ),
        bodyMedium: TextStyle(
          fontSize: 18,
          fontWeight: FontWeight.normal,
          color: pureBlack,
          height: 1.5,
        ),
        labelLarge: TextStyle(
          fontSize: 18,
          fontWeight: FontWeight.w600,
          color: pureBlack,
          height: 1.4,
        ),
        labelSmall: TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.normal,
          color: pureBlack,
          height: 1.4,
        ),
      ),

      // Large, easy-to-tap buttons
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          minimumSize: const Size(double.infinity, 64),
          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 18),
          textStyle: const TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.w600,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          elevation: 2,
        ),
      ),

      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size(double.infinity, 64),
          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 18),
          textStyle: const TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.w600,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
      ),

      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size(double.infinity, 64),
          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 18),
          textStyle: const TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.w600,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          side: const BorderSide(width: 3),
        ),
      ),

      // Large, tappable cards
      cardTheme: CardThemeData(
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      ),

      // Large sliders for accessibility
      sliderTheme: SliderThemeData(
        trackHeight: 8,
        thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 14),
        overlayShape: const RoundSliderOverlayShape(overlayRadius: 28),
        valueIndicatorTextStyle: const TextStyle(fontSize: 18),
      ),

      // Large switch - track outline for contrast
      switchTheme: SwitchThemeData(
        trackOutlineWidth: const WidgetStatePropertyAll(3),
      ),

      // AppBar
      appBarTheme: const AppBarTheme(
        elevation: 0,
        centerTitle: true,
        titleTextStyle: TextStyle(
          fontSize: 24,
          fontWeight: FontWeight.w600,
          color: pureWhite,
        ),
        iconTheme: IconThemeData(size: 28, color: pureWhite),
        toolbarHeight: 72,
      ),

      // Chip/choice chip
      chipTheme: ChipThemeData(
        labelStyle: const TextStyle(fontSize: 18),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),

      // Input decoration for text fields
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.grey.shade100,
        contentPadding: const EdgeInsets.all(20),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: Colors.grey.shade400, width: 2),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: Colors.grey.shade400, width: 2),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: primaryBlue, width: 3),
        ),
        labelStyle: const TextStyle(fontSize: 20, color: pureBlack),
        hintStyle: TextStyle(fontSize: 18, color: Colors.grey.shade600),
      ),

      // Snackbar
      snackBarTheme: SnackBarThemeData(
        contentTextStyle: const TextStyle(fontSize: 18),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  /// High-contrast dark theme (ideal for visually impaired users)
  static ThemeData get darkHighContrast {
    final light = lightHighContrast;
    return light.copyWith(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: pureBlack,
      colorScheme: ColorScheme.fromSeed(
        seedColor: primaryBlue,
        brightness: Brightness.dark,
        contrastLevel: 1.0,
      ),
      textTheme: light.textTheme.apply(
        bodyColor: pureWhite,
        displayColor: pureWhite,
      ),
      canvasColor: pureBlack,
      cardTheme: light.cardTheme.copyWith(
        color: darkCard,
      ),
      appBarTheme: light.appBarTheme.copyWith(
        backgroundColor: pureBlack,
      ),
      inputDecorationTheme: light.inputDecorationTheme.copyWith(
        fillColor: darkCard,
        labelStyle: const TextStyle(fontSize: 20, color: pureWhite),
        hintStyle: TextStyle(fontSize: 18, color: Colors.grey.shade500),
      ),
      dividerColor: Colors.grey.shade700,
    );
  }
}
