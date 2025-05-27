// lib/widgets/custom_text_field.dart
import 'package:flutter/material.dart';
import 'package:spendshare/core/theme/app_theme.dart'; // For hintStyle if needed

class CustomTextField extends StatelessWidget {
  final TextEditingController controller;
  final String labelText;
  final String? hintText;
  final IconData? prefixIcon;
  final bool obscureText;
  final TextInputType keyboardType;
  final String? Function(String?)? validator;
  final FocusNode? focusNode;
  final Function(String)? onFieldSubmitted;
  final TextInputAction? textInputAction;

  const CustomTextField({
    super.key,
    required this.controller,
    required this.labelText,
    this.hintText,
    this.prefixIcon,
    this.obscureText = false,
    this.keyboardType = TextInputType.text,
    this.validator,
    this.focusNode,
    this.onFieldSubmitted,
    this.textInputAction,
  });

  @override
  Widget build(BuildContext context) {
    // Using InputDecorationTheme from AppTheme by default
    // Specific overrides can be done here if needed
    return TextFormField(
      controller: controller,
      decoration: InputDecoration(
        labelText: labelText,
        hintText: hintText,
        prefixIcon: prefixIcon != null ? Icon(prefixIcon) : null,
        // border: OutlineInputBorder( // Defined in AppTheme
        //   borderRadius: BorderRadius.circular(8.0),
        // ),
        // fillColor: AppTheme.surfaceColor.withOpacity(0.5), // Defined in AppTheme
        // filled: true, // Defined in AppTheme
        // labelStyle: TextStyle(color: AppTheme.textColorSecondary), // Defined in AppTheme
        // hintStyle: TextStyle(color: AppTheme.textColorSecondary.withOpacity(0.7)), // Defined in AppTheme
      ),
      obscureText: obscureText,
      keyboardType: keyboardType,
      validator: validator,
      focusNode: focusNode,
      onFieldSubmitted: onFieldSubmitted,
      textInputAction: textInputAction,
      style: TextStyle(color: AppTheme.textColorPrimary), // Ensure input text color is readable
    );
  }
}
