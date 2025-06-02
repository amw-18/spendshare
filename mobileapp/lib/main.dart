import 'package:flutter/material.dart';
import 'package:provider/provider.dart'; 
import 'core/theme/app_theme.dart';
import 'core/navigation/app_routes.dart';
import 'core/navigation/route_names.dart';
import 'features/auth/notifiers/auth_provider.dart'; 
import 'features/splash/screens/splash_screen.dart'; 
import 'features/auth/screens/login_screen.dart'; 
import 'features/dashboard/screens/dashboard_screen.dart'; 

void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        // Add other providers here if needed
      ],
      child: const SpendShareApp(),
    ),
  );
}

class SpendShareApp extends StatelessWidget {
  const SpendShareApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SpendShare',
      theme: AppTheme.darkTheme,
      debugShowCheckedModeBanner: false, 
      home: Consumer<AuthProvider>(
        builder: (context, auth, child) {
          if (auth.status == AuthStatus.initial || auth.status == AuthStatus.checking) {
            return const SplashScreen(); 
          } else if (auth.status == AuthStatus.authenticated) {
            return const DashboardScreen(); 
          } else {
            return const LoginScreen(); 
          }
        },
      ),
      onGenerateRoute: AppRoutes.generateRoute, 
      initialRoute: RouteNames.splash, 
    );
  }
}

/*
class MyHomePage extends StatefulWidget {
  const MyHomePage({super.key, required this.title});

  final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  int _counter = 0;

  void _incrementCounter() {
    setState(() {
      _counter++;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.title),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            const Text(
              'You have pushed the button this many times:',
            ),
            Text(
              '$_counter',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _incrementCounter,
        tooltip: 'Increment',
        child: const Icon(Icons.add),
      ),
    );
  }
}
*/
