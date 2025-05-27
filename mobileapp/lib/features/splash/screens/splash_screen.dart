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
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: const <Widget>[
            CircularProgressIndicator(),
            SizedBox(height: 20),
            Text('SpendShare', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
            Text('Loading...'),
          ],
        ),
      ),
    );
  }
}
