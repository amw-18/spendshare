import 'package:flutter/material.dart';

class AppTheme {
  // Primary Backgrounds
  static const Color scaffoldBackgroundColor = Color(0xFF161122);
  static const Color backgroundColor = Color(0xFF1C152B);
  static const Color surfaceColor = Color(0xFF211a32);

  // Accent Color
  static const Color primaryColor = Color(0xFF7847ea);
  static const Color primaryVariantColor = Color(0xFF6c3ddb); // Accent Hover/Darker Shade
  static const Color secondaryColor = Color(0xFF7847ea); // Kept same as primary for now
  static const Color secondaryVariantColor = Color(0xFF6c3ddb);

  // Text Colors
  static const Color onPrimaryColor = Colors.white; // Text on Accent Color
  static const Color onBackgroundColor = Colors.white; // Text on Section Backgrounds
  static const Color onSurfaceColor = Colors.white; // Text on Card/AppBar Backgrounds
  static const Color textColorPrimary = Colors.white; // Primary headings, key text
  static const Color textColorSecondary = Color(0xFFE5E7EB); // Secondary text (text-gray-300 equiv)
  static const Color textColorMutedLavender = Color(0xFFA393C8); // New muted purple/lavender text

  // Border Colors
  static const Color borderColorSubtle = Color(0xFF2f2447);
  static const Color borderColorMorePronounced = Color(0xFF433465);

  // Error Color
  static const Color errorColor = Color(0xFFEF4444); // Tailwind Red-500 (Kept as is)
  static const Color onErrorColor = Colors.white;

  // Input Fill Color
  static const Color inputFillColor = Color(0xFF100c1c);


  // Font Family
  static const String fontFamily = 'PlusJakartaSans';

  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      fontFamily: fontFamily,
      
      primaryColor: primaryColor,
      scaffoldBackgroundColor: scaffoldBackgroundColor, 
      backgroundColor: backgroundColor, 
      
      colorScheme: const ColorScheme.dark(
        primary: primaryColor,
        primaryContainer: primaryVariantColor,
        secondary: secondaryColor,
        secondaryContainer: secondaryVariantColor, 
        surface: surfaceColor, 
        background: backgroundColor, 
        error: errorColor,
        onPrimary: onPrimaryColor,
        onSecondary: onPrimaryColor, 
        onSurface: onSurfaceColor,
        onBackground: onBackgroundColor,
        onError: onErrorColor,
      ),
      
      cardColor: surfaceColor, 
      hintColor: textColorMutedLavender.withOpacity(0.7), // Adjusted hint color for global theme
      dividerColor: borderColorSubtle, 

      textTheme: _darkTextTheme,

      appBarTheme: AppBarTheme(
        backgroundColor: scaffoldBackgroundColor,
        elevation: 0,
        foregroundColor: textColorPrimary,
        titleTextStyle: _darkTextTheme.headline5,
        iconTheme: const IconThemeData(color: textColorPrimary),
        shape: Border(bottom: BorderSide(color: borderColorSubtle.withOpacity(0.7), width: 1.0)),
      ),

      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ButtonStyle(
          backgroundColor: MaterialStateProperty.resolveWith<Color?>(
            (Set<MaterialState> states) {
              if (states.contains(MaterialState.hovered)) return primaryVariantColor;
              return primaryColor; // Default color
            },
          ),
          foregroundColor: MaterialStateProperty.all<Color>(onPrimaryColor),
          shape: MaterialStateProperty.all<OutlinedBorder>(const StadiumBorder()),
          padding: MaterialStateProperty.all<EdgeInsetsGeometry>(
            const EdgeInsets.symmetric(horizontal: 24, vertical: 14), // Adjusted for ~48px height
          ),
          textStyle: MaterialStateProperty.all<TextStyle?>(_darkTextTheme.button),
          overlayColor: MaterialStateProperty.resolveWith<Color?>( // Ensures hover effect on text too
            (Set<MaterialState> states) {
              if (states.contains(MaterialState.hovered)) return primaryVariantColor;
              return null;
            }
          ),
        ),
      ),
      
      cardTheme: CardTheme(
        color: surfaceColor,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12.0),
          side: BorderSide(color: borderColorMorePronounced, width: 1.0),
        ),
        elevation: 0, // Base elevation, hover can be handled at widget level
        margin: EdgeInsets.zero, // Or specific small margin if needed globally
      ),

      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: inputFillColor,
        contentPadding: const EdgeInsets.symmetric(horizontal: 12.0, vertical: 8.0),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8.0),
          borderSide: BorderSide(color: borderColorSubtle, width: 1.0),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8.0),
          borderSide: BorderSide(color: borderColorSubtle, width: 1.0),
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
        labelStyle: TextStyle(color: textColorMutedLavender, fontSize: 14, fontWeight: FontWeight.w500), // text-sm font-medium
        hintStyle: TextStyle(color: textColorMutedLavender.withOpacity(0.7)),
      ),

      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          side: const BorderSide(color: primaryColor),
          foregroundColor: primaryColor,
          textStyle: _darkTextTheme.button?.copyWith(color: primaryColor), // Ensure text color is primary
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.0)), // Consistent with inputs
        ),
      ),

      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: primaryColor,
          textStyle: _darkTextTheme.labelLarge, // Using labelLarge for TextButtons
        ),
      ),

      dialogTheme: DialogTheme(
        backgroundColor: surfaceColor,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12.0),
          side: BorderSide(color: borderColorSubtle, width: 1.0) // Adding subtle border to dialogs
        ),
        titleTextStyle: _darkTextTheme.headline5, 
        contentTextStyle: _darkTextTheme.bodyMedium, // Using bodyMedium for dialog content
      ),

      bottomNavigationBarTheme: BottomNavigationBarThemeData(
        backgroundColor: scaffoldBackgroundColor, // Match AppBar for consistency
        selectedItemColor: primaryColor,
        unselectedItemColor: textColorMutedLavender, // Muted for unselected items
        selectedLabelStyle: _darkTextTheme.caption?.copyWith(fontWeight: FontWeight.bold, color: primaryColor),
        unselectedLabelStyle: _darkTextTheme.caption?.copyWith(color: textColorMutedLavender),
        elevation: 0, // Remove default shadow
        type: BottomNavigationBarType.fixed, // Ensure labels are always visible
      ),

      chipTheme: ChipThemeData(
        backgroundColor: primaryColor.withOpacity(0.15), // Slightly more pronounced
        disabledColor: surfaceColor.withOpacity(0.5),
        selectedColor: primaryColor,
        padding: const EdgeInsets.symmetric(horizontal: 12.0, vertical: 8.0), // More padding
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.0)), // Consistent rounding
        labelStyle: _darkTextTheme.bodySmall?.copyWith(color: primaryColor, fontWeight: FontWeight.w600),
        secondaryLabelStyle: _darkTextTheme.bodySmall?.copyWith(color: onPrimaryColor, fontWeight: FontWeight.w600),
        brightness: Brightness.dark,
        side: BorderSide(color: primaryColor.withOpacity(0.5)) // Subtle border for chips
      ),

      snackBarTheme: SnackBarThemeData(
        backgroundColor: surfaceColor, // Consistent surface color
        contentTextStyle: _darkTextTheme.bodyMedium?.copyWith(color: onSurfaceColor),
        actionTextColor: primaryColor,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.0)), // Rounded corners
        behavior: SnackBarBehavior.floating, // Floating style
      ),
      
      // Ensure buttonTheme (legacy) is somewhat consistent if still used by older packages
      buttonTheme: ButtonThemeData(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.0)),
        buttonColor: primaryColor,
        textTheme: ButtonTextTheme.primary, // Ensures text is onPrimaryColor
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
      ),
    );
  }

  static final TextTheme _darkTextTheme = TextTheme(
    // H1: Approx. 48px, Extrabold, Tighter Tracking, Primary Text Color
    headlineLarge: TextStyle(fontSize: 48, fontWeight: FontWeight.w800, letterSpacing: -1.5, color: AppTheme.textColorPrimary),
    // H2: Approx. 36px, Bold, Tight Tracking, Primary Text Color
    headlineMedium: TextStyle(fontSize: 36, fontWeight: FontWeight.w700, letterSpacing: -0.5, color: AppTheme.textColorPrimary),
    // H3: Approx. 30px, Bold, Normal Tracking, Primary Text Color
    headlineSmall: TextStyle(fontSize: 30, fontWeight: FontWeight.w700, letterSpacing: 0.0, color: AppTheme.textColorPrimary),

    // Title Large: Approx 22px, Bold, Primary Text Color
    titleLarge: TextStyle(fontSize: 22, fontWeight: FontWeight.w700, letterSpacing: 0.15, color: AppTheme.textColorPrimary),
    // Title Medium: Approx 16px, Semibold, Secondary Text Color
    titleMedium: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, letterSpacing: 0.15, color: AppTheme.textColorSecondary),
    // Title Small: Approx 14px, Semibold, Secondary Text Color
    titleSmall: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, letterSpacing: 0.1, color: AppTheme.textColorSecondary),

    // Body Large / Primary Body Text: Approx. 18px, Normal, Secondary Text Color, Relaxed Line Height
    bodyLarge: TextStyle(fontSize: 18, fontWeight: FontWeight.w400, letterSpacing: 0.5, color: AppTheme.textColorSecondary, height: 1.6),
    // Body Medium / Secondary Body Text: Approx. 16px, Normal, Muted Lavender Text Color, Relaxed Line Height
    bodyMedium: TextStyle(fontSize: 16, fontWeight: FontWeight.w400, letterSpacing: 0.25, color: AppTheme.textColorMutedLavender, height: 1.5),
    // Body Small / Default for some components: Approx 14px, Normal, Muted Lavender
    bodySmall: TextStyle(fontSize: 14, fontWeight: FontWeight.w400, letterSpacing: 0.25, color: AppTheme.textColorMutedLavender, height: 1.5),


    // Label Large (e.g., Buttons): Approx 16px, Bold, Accent Color (for text on buttons, or primary for text buttons)
    labelLarge: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, letterSpacing: 0.5, color: AppTheme.primaryColor), // For TextButtons primarily
    // Label Medium: Approx 12px, Semibold
    labelMedium: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, letterSpacing: 0.5, color: AppTheme.textColorSecondary),
    // Label Small: Approx 10px, Medium
    labelSmall: TextStyle(fontSize: 10, fontWeight: FontWeight.w500, letterSpacing: 0.5, color: AppTheme.textColorSecondary),


    // --- Old Material 2 Style names, mapped to new roles or adjusted ---
    // headline1 -> H1 (now headlineLarge)
    headline1: TextStyle(fontSize: 48, fontWeight: FontWeight.w800, letterSpacing: -1.5, color: AppTheme.textColorPrimary),
    // headline2 -> H2 (now headlineMedium)
    headline2: TextStyle(fontSize: 36, fontWeight: FontWeight.w700, letterSpacing: -0.5, color: AppTheme.textColorPrimary),
    // headline3 -> H3 (now headlineSmall)
    headline3: TextStyle(fontSize: 30, fontWeight: FontWeight.w700, letterSpacing: 0.0, color: AppTheme.textColorPrimary),
    
    // headline4: Adjusted to be smaller than H3, ~24px, Bold
    headline4: TextStyle(fontSize: 24, fontWeight: FontWeight.w700, letterSpacing: 0.25, color: AppTheme.textColorPrimary),
    // headline5: Adjusted for AppBars, ~20px, Bold
    headline5: TextStyle(fontSize: 20, fontWeight: FontWeight.w700, letterSpacing: 0.15, color: AppTheme.textColorPrimary), // Used for AppBar titles, Dialog Titles
    // headline6: Adjusted smaller, ~18px, Semibold
    headline6: TextStyle(fontSize: 18, fontWeight: FontWeight.w600, letterSpacing: 0.15, color: AppTheme.textColorPrimary),

    // subtitle1 -> Primary Subtitle (now closer to titleLarge)
    subtitle1: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, letterSpacing: 0.15, color: AppTheme.textColorPrimary), // Was titleLarge role
    // subtitle2 -> Secondary Subtitle (now closer to titleMedium)
    subtitle2: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, letterSpacing: 0.1, color: AppTheme.textColorSecondary), // Was titleMedium role

    // bodyText1 -> Primary Body Text (now bodyLarge)
    bodyText1: TextStyle(fontSize: 18, fontWeight: FontWeight.w400, letterSpacing: 0.5, color: AppTheme.textColorSecondary, height: 1.6),
    // bodyText2 -> Secondary Body Text (now bodyMedium) - Default text style
    bodyText2: TextStyle(fontSize: 16, fontWeight: FontWeight.w400, letterSpacing: 0.25, color: AppTheme.textColorMutedLavender, height: 1.5),
    
    // button: For ElevatedButton, OutlinedButton text. Philosophy implies bold for primary CTAs.
    button: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, letterSpacing: 0.5, color: AppTheme.onPrimaryColor), // Text on colored buttons is onPrimaryColor.
    
    // caption: Small helper text
    caption: TextStyle(fontSize: 12, fontWeight: FontWeight.w400, letterSpacing: 0.4, color: AppTheme.textColorMutedLavender),
    // overline: Very small, spaced-out text
    overline: TextStyle(fontSize: 10, fontWeight: FontWeight.w400, letterSpacing: 1.5, color: AppTheme.textColorMutedLavender),
  ).apply(
    fontFamily: fontFamily,
  );
}
