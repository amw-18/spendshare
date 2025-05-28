import 'package:flutter/material.dart';
import 'package:spendshare/core/navigation/route_names.dart'; // For navigation

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _navigateToNextScreen();
  }

  Future<void> _navigateToNextScreen() async {
    // Simulate a delay for splash screen (e.g., loading initial data, checking auth status)
    await Future.delayed(const Duration(seconds: 2));

    // TODO: Implement logic to check authentication status
    // For now, navigate to login screen
    if (mounted) { // Check if the widget is still in the tree
      Navigator.of(context).pushReplacementNamed(RouteNames.login);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      // backgroundColor is handled by theme.scaffoldBackgroundColor
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation<Color>(theme.colorScheme.primary),
            ),
            const SizedBox(height: 24), // Consistent spacing
            Text(
              'SpendShare',
              style: theme.textTheme.headlineMedium?.copyWith(color: theme.colorScheme.onBackground),
            ),
            const SizedBox(height: 8), // Consistent spacing
            Text(
              'Loading...',
              style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onBackground.withOpacity(0.7)),
            ),
          ],
        ),
      ),
    );
  }
}
