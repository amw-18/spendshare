import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:spendshare/core/navigation/route_names.dart';
import 'package:spendshare/core/utils/form_constants.dart';
import 'package:spendshare/features/auth/notifiers/auth_provider.dart';
import 'package:spendshare/widgets/custom_text_field.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();

  final _passwordFocusNode = FocusNode();

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    _passwordFocusNode.dispose();
    super.dispose();
  }

  Future<void> _submitForm() async {
    if (_formKey.currentState!.validate()) {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final success = await authProvider.login(
        _usernameController.text.trim(),
        _passwordController.text.trim(),
      );

      if (success && mounted) {
        // Navigate to Dashboard or home screen
        // The Consumer in main.dart should handle this navigation based on auth.status
        // So, no explicit navigation here might be needed if main.dart handles it.
        // However, if SplashScreen is the only one checking, you might need:
        // Navigator.of(context).pushReplacementNamed(RouteNames.dashboard);
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
        title: const Text('Login to SpendShare'),
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
              // TODO: Add App Logo or Welcome Text if desired
              // const Text('Welcome Back!', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
              // const SizedBox(height: formVerticalSpacing * 2),

              CustomTextField(
                controller: _usernameController,
                labelText: 'Username or Email',
                prefixIcon: Icons.person_outline,
                keyboardType: TextInputType.emailAddress,
                textInputAction: TextInputAction.next,
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Please enter your username or email';
                  }
                  // Add more specific email/username validation if needed
                  return null;
                },
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
                textInputAction: TextInputAction.done,
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please enter your password';
                  }
                  if (value.length < 8) {
                    return 'Password must be at least 8 characters';
                  }
                  return null;
                },
                onFieldSubmitted: (_) => _submitForm(),
              ),
              const SizedBox(height: formVerticalSpacing * 0.5),
              // TODO: Add 'Forgot Password?' TextButton if needed
              // Align(alignment: Alignment.centerRight, child: TextButton(onPressed: () {}, child: Text('Forgot Password?'))),
              const SizedBox(height: formVerticalSpacing * 1.5),
              if (authProvider.status == AuthStatus.loading)
                const Center(child: CircularProgressIndicator())
              else
                ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    minimumSize: const Size(double.infinity, formButtonHeight),
                  ),
                  onPressed: _submitForm,
                  child: const Text('Login'),
                ),
              const SizedBox(height: formVerticalSpacing),
              if (authProvider.status == AuthStatus.error && authProvider.errorMessage != null)
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
                  const Text("Don't have an account?"),
                  TextButton(
                    onPressed: () {
                      Navigator.of(context).pushNamed(RouteNames.signup);
                    },
                    child: const Text('Sign Up'),
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
