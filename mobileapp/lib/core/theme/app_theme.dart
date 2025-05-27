import 'package:flutter/material.dart';

class AppTheme {
  // Primary Colors
  static const Color primaryColor = Color(0xFF3B82F6); // Tailwind Blue-500
  static const Color primaryVariantColor = Color(0xFF2563EB); // Tailwind Blue-600

  // Secondary Colors (Accent)
  static const Color secondaryColor = Color(0xFFF59E0B); // Tailwind Amber-500
  static const Color secondaryVariantColor = Color(0xFFD97706); // Tailwind Amber-600

  // Background Colors
  static const Color backgroundColor = Color(0xFF1F2937); // Tailwind Gray-800
  static const Color surfaceColor = Color(0xFF374151); // Tailwind Gray-700
  static const Color scaffoldBackgroundColor = Color(0xFF111827); // Tailwind Gray-900

  // Text Colors
  static const Color onPrimaryColor = Colors.white;
  static const Color onSecondaryColor = Colors.black;
  static const Color onBackgroundColor = Color(0xFFF3F4F6); // Tailwind Gray-100
  static const Color onSurfaceColor = Color(0xFFF3F4F6); // Tailwind Gray-100
  static const Color textColorPrimary = Color(0xFFF3F4F6); // Tailwind Gray-100
  static const Color textColorSecondary = Color(0xFF9CA3AF); // Tailwind Gray-400

  // Error Color
  static const Color errorColor = Color(0xFFEF4444); // Tailwind Red-500
  static const Color onErrorColor = Colors.white;

  // Font Family
  static const String fontFamily = 'PlusJakartaSans';

  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      fontFamily: fontFamily,
      primaryColor: primaryColor,
      // primarySwatch: MaterialColor(primaryColor.value, <int, Color>{
      //   50: primaryColor.withOpacity(0.1),
      //   100: primaryColor.withOpacity(0.2),
      //   200: primaryColor.withOpacity(0.3),
      //   300: primaryColor.withOpacity(0.4),
      //   400: primaryColor.withOpacity(0.5),
      //   500: primaryColor.withOpacity(0.6),
      //   600: primaryColor.withOpacity(0.7),
      //   700: primaryColor.withOpacity(0.8),
      //   800: primaryColor.withOpacity(0.9),
      //   900: primaryColor,
      // }),
      colorScheme: const ColorScheme.dark(
        primary: primaryColor,
        primaryContainer: primaryVariantColor, // Formerly primaryVariant
        secondary: secondaryColor,
        secondaryContainer: secondaryVariantColor, // Formerly secondaryVariant
        surface: surfaceColor,
        background: backgroundColor,
        error: errorColor,
        onPrimary: onPrimaryColor,
        onSecondary: onSecondaryColor,
        onSurface: onSurfaceColor,
        onBackground: onBackgroundColor,
        onError: onErrorColor,
      ),
      scaffoldBackgroundColor: scaffoldBackgroundColor,
      backgroundColor: backgroundColor,
      cardColor: surfaceColor,
      hintColor: textColorSecondary,
      dividerColor: Colors.grey[700],
      textTheme: _darkTextTheme,
      appBarTheme: AppBarTheme(
        elevation: 0,
        backgroundColor: surfaceColor, // Or scaffoldBackgroundColor for a more merged look
        foregroundColor: onSurfaceColor, // Text/icon color
        titleTextStyle: _darkTextTheme.headline6,
        iconTheme: const IconThemeData(color: onSurfaceColor),
      ),
      buttonTheme: ButtonThemeData(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.0)),
        buttonColor: primaryColor,
        textTheme: ButtonTextTheme.primary,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primaryColor,
          foregroundColor: onPrimaryColor,
          textStyle: _darkTextTheme.button,
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.0)),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          side: const BorderSide(color: primaryColor),
          foregroundColor: primaryColor,
          textStyle: _darkTextTheme.button,
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.0)),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: primaryColor,
          textStyle: _darkTextTheme.button,
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surfaceColor.withOpacity(0.5),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8.0),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8.0),
          borderSide: BorderSide(color: Colors.grey[600]!),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8.0),
          borderSide: const BorderSide(color: primaryColor, width: 2.0),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8.0),
          borderSide: const BorderSide(color: errorColor, width: 1.0),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8.0),
          borderSide: const BorderSide(color: errorColor, width: 2.0),
        ),
        labelStyle: TextStyle(color: textColorSecondary),
        hintStyle: TextStyle(color: textColorSecondary.withOpacity(0.7)),
      ),
      dialogTheme: DialogTheme(
        backgroundColor: surfaceColor,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12.0)),
        titleTextStyle: _darkTextTheme.headline6,
        contentTextStyle: _darkTextTheme.bodyText2,
      ),
      bottomNavigationBarTheme: BottomNavigationBarThemeData(
        backgroundColor: surfaceColor,
        selectedItemColor: primaryColor,
        unselectedItemColor: textColorSecondary,
        selectedLabelStyle: _darkTextTheme.caption?.copyWith(fontWeight: FontWeight.bold),
        unselectedLabelStyle: _darkTextTheme.caption,
      ),
      chipTheme: ChipThemeData(
        backgroundColor: primaryColor.withOpacity(0.1),
        disabledColor: Colors.grey[800]!,
        selectedColor: primaryColor,
        secondarySelectedColor: primaryColor,
        padding: const EdgeInsets.all(4.0),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.0)),
        labelStyle: _darkTextTheme.bodyText2?.copyWith(color: primaryColor),
        secondaryLabelStyle: _darkTextTheme.bodyText2?.copyWith(color: onPrimaryColor),
        brightness: Brightness.dark,
      ),
      snackBarTheme: SnackBarThemeData(
        backgroundColor: surfaceColor,
        contentTextStyle: _darkTextTheme.bodyText2?.copyWith(color: onSurfaceColor),
        actionTextColor: primaryColor,
      ),
    );
  }

  static final TextTheme _darkTextTheme = TextTheme(
    headline1: TextStyle(fontSize: 96, fontWeight: FontWeight.w300, letterSpacing: -1.5, color: textColorPrimary),
    headline2: TextStyle(fontSize: 60, fontWeight: FontWeight.w300, letterSpacing: -0.5, color: textColorPrimary),
    headline3: TextStyle(fontSize: 48, fontWeight: FontWeight.w400, color: textColorPrimary),
    headline4: TextStyle(fontSize: 34, fontWeight: FontWeight.w400, letterSpacing: 0.25, color: textColorPrimary),
    headline5: TextStyle(fontSize: 24, fontWeight: FontWeight.w400, color: textColorPrimary),
    headline6: TextStyle(fontSize: 20, fontWeight: FontWeight.w500, letterSpacing: 0.15, color: textColorPrimary), // Used for AppBar titles
    subtitle1: TextStyle(fontSize: 16, fontWeight: FontWeight.w400, letterSpacing: 0.15, color: textColorPrimary),
    subtitle2: TextStyle(fontSize: 14, fontWeight: FontWeight.w500, letterSpacing: 0.1, color: textColorSecondary),
    bodyText1: TextStyle(fontSize: 16, fontWeight: FontWeight.w400, letterSpacing: 0.5, color: textColorPrimary),
    bodyText2: TextStyle(fontSize: 14, fontWeight: FontWeight.w400, letterSpacing: 0.25, color: textColorSecondary), // Default text style
    button: TextStyle(fontSize: 14, fontWeight: FontWeight.w500, letterSpacing: 1.25, color: primaryColor), // For button text
    caption: TextStyle(fontSize: 12, fontWeight: FontWeight.w400, letterSpacing: 0.4, color: textColorSecondary),
    overline: TextStyle(fontSize: 10, fontWeight: FontWeight.w400, letterSpacing: 1.5, color: textColorSecondary),
  ).apply(
    fontFamily: fontFamily,
  );
}
