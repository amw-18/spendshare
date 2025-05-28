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
    final theme = Theme.of(context);

    // InputDecoration will be merged with the global inputDecorationTheme
    // We only define properties here that are specific to this instance
    // or need to be slightly different from the global theme.
    return TextFormField(
      controller: controller,
      decoration: InputDecoration(
        labelText: labelText, // labelStyle will come from inputDecorationTheme.labelStyle
        hintText: hintText,   // hintStyle will come from inputDecorationTheme.hintStyle
        prefixIcon: prefixIcon != null 
            ? Icon(prefixIcon, color: theme.inputDecorationTheme.prefixIconColor ?? theme.colorScheme.onSurface.withOpacity(0.7)) 
            : null,
        // Other properties like border, fillColor, filled are inherited from inputDecorationTheme
      ),
      obscureText: obscureText,
      keyboardType: keyboardType,
      validator: validator,
      focusNode: focusNode,
      onFieldSubmitted: onFieldSubmitted,
      textInputAction: textInputAction,
      // Style for the text being input by the user
      style: theme.textTheme.bodyLarge?.copyWith(
        color: theme.colorScheme.onSurface, // Text color on the input field surface
      ),
    );
  }
}
