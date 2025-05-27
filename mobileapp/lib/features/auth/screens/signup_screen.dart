import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:spendshare/core/models/user.dart';
import 'package:spendshare/core/navigation/route_names.dart';
import 'package:spendshare/core/utils/form_constants.dart';
import 'package:spendshare/features/auth/notifiers/auth_provider.dart';
import 'package:spendshare/widgets/custom_text_field.dart';

class SignupScreen extends StatefulWidget {
  const SignupScreen({super.key});

  @override
  State<SignupScreen> createState() => _SignupScreenState();
}

class _SignupScreenState extends State<SignupScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _usernameController = TextEditingController(); // Assuming username is separate or can be email
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();

  final _usernameFocusNode = FocusNode();
  final _passwordFocusNode = FocusNode();
  final _confirmPasswordFocusNode = FocusNode();

  @override
  void dispose() {
    _emailController.dispose();
    _usernameController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _usernameFocusNode.dispose();
    _passwordFocusNode.dispose();
    _confirmPasswordFocusNode.dispose();
    super.dispose();
  }

  Future<void> _submitForm() async {
    if (_formKey.currentState!.validate()) {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      
      final userCreate = UserCreate(
        email: _emailController.text.trim(),
        username: _usernameController.text.trim().isNotEmpty 
                    ? _usernameController.text.trim() 
                    : _emailController.text.trim(), // Fallback to email if username is empty and API allows
        password: _passwordController.text.trim(),
        full_name: '', // Optional: Add a field for full name if needed
        is_active: true, // Default for new users
        is_superuser: false, // Default for new users
      );

      final success = await authProvider.signup(userCreate);

      if (success && mounted) {
        // Show a success message and prompt to login
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Signup successful! Please login.')),
        );
        // Navigate to Login screen after a short delay or directly
        Navigator.of(context).popUntil((route) => route.isFirst); // Go back to initial route (Login)
        // Or Navigator.of(context).pushReplacementNamed(RouteNames.login);
      } else if (!success && mounted && authProvider.errorMessage != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(authProvider.errorMessage!)),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Create Account'),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: formHorizontalPadding.copyWith(top: 40, bottom: 20),
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              CustomTextField(
                controller: _emailController,
                labelText: 'Email',
                prefixIcon: Icons.email_outlined,
                keyboardType: TextInputType.emailAddress,
                textInputAction: TextInputAction.next,
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Please enter your email';
                  }
                  if (!RegExp(r"^[a-zA-Z0-9.a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9]+\.[a-zA-Z]+").hasMatch(value)) {
                    return 'Please enter a valid email address';
                  }
                  return null;
                },
                onFieldSubmitted: (_) {
                  FocusScope.of(context).requestFocus(_usernameFocusNode);
                },
              ),
              const SizedBox(height: formVerticalSpacing),
              CustomTextField(
                controller: _usernameController,
                labelText: 'Username (Optional)',
                hintText: 'Defaults to email if left blank',
                prefixIcon: Icons.person_outline,
                focusNode: _usernameFocusNode,
                textInputAction: TextInputAction.next,
                // No specific validator for username, can be optional or have specific rules
                onFieldSubmitted: (_) {
                  FocusScope.of(context).requestFocus(_passwordFocusNode);
                },
              ),
              const SizedBox(height: formVerticalSpacing),
              CustomTextField(
                controller: _passwordController,
                labelText: 'Password',
                prefixIcon: Icons.lock_outline,
                obscureText: true,
                focusNode: _passwordFocusNode,
                textInputAction: TextInputAction.next,
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please enter a password';
                  }
                  if (value.length < 8) {
                    return 'Password must be at least 8 characters';
                  }
                  return null;
                },
                onFieldSubmitted: (_) {
                  FocusScope.of(context).requestFocus(_confirmPasswordFocusNode);
                },
              ),
              const SizedBox(height: formVerticalSpacing),
              CustomTextField(
                controller: _confirmPasswordController,
                labelText: 'Confirm Password',
                prefixIcon: Icons.lock_outline,
                obscureText: true,
                focusNode: _confirmPasswordFocusNode,
                textInputAction: TextInputAction.done,
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please confirm your password';
                  }
                  if (value != _passwordController.text) {
                    return 'Passwords do not match';
                  }
                  return null;
                },
                onFieldSubmitted: (_) => _submitForm(),
              ),
              const SizedBox(height: formVerticalSpacing * 1.5),
              if (authProvider.status == AuthStatus.loading)
                const Center(child: CircularProgressIndicator())
              else
                ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    minimumSize: const Size(double.infinity, formButtonHeight),
                  ),
                  onPressed: _submitForm,
                  child: const Text('Sign Up'),
                ),
              const SizedBox(height: formVerticalSpacing),
              if (authProvider.status == AuthStatus.error && authProvider.errorMessage != null && authProvider.status != AuthStatus.loading) // Don't show error while loading
                Padding(
                  padding: const EdgeInsets.only(bottom: formVerticalSpacing),
                  child: Text(
                    authProvider.errorMessage!,
                    style: TextStyle(color: Theme.of(context).colorScheme.error),
                    textAlign: TextAlign.center,
                  ),
                ),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: <Widget>[
                  const Text('Already have an account?'),
                  TextButton(
                    onPressed: () {
                      // Navigate back to Login screen
                      if (Navigator.of(context).canPop()) {
                        Navigator.of(context).pop();
                      } else {
                        // Fallback if it's the first route (e.g. deep link)
                        Navigator.of(context).pushReplacementNamed(RouteNames.login);
                      }
                    },
                    child: const Text('Login'),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
