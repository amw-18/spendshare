import 'package:flutter/material.dart';
import './route_names.dart';

// Import screen placeholders - these will be created later
// Example: import '../../features/auth/screens/login_screen.dart';
// Example: import '../../features/dashboard/screens/dashboard_screen.dart';
// Example: import '../../features/splash/screens/splash_screen.dart'; // Assuming a splash screen
import '../../features/splash/screens/splash_screen.dart';
import '../../features/auth/screens/login_screen.dart';
import '../../features/auth/screens/signup_screen.dart';
import '../../features/dashboard/screens/dashboard_screen.dart';
import '../../features/groups/screens/groups_list_screen.dart';
import '../../features/groups/screens/group_create_edit_screen.dart';
import '../../features/groups/screens/group_detail_screen.dart';
import '../../features/expenses/screens/expense_create_edit_screen.dart';
import '../../features/expenses/screens/expense_detail_screen.dart';
import '../../features/profile/screens/profile_screen.dart';

class AppRoutes {
  static Route<dynamic> generateRoute(RouteSettings settings) {
    final args = settings.arguments; // Use if passing arguments

    Widget getScreenByName(String name) {
      // Placeholder function to return a generic screen
      // In a real app, you'd return actual screen widgets based on settings.name
      return Scaffold(
        appBar: AppBar(title: Text(name)),
        body: Center(
          child: Text('Screen: $name\n(Placeholder - Not Yet Implemented)'),
        ),
      );
    }

    switch (settings.name) {
      case RouteNames.splash:
        return MaterialPageRoute(builder: (_) => const SplashScreen());
      case RouteNames.login:
        return MaterialPageRoute(builder: (_) => const LoginScreen());
      case RouteNames.signup:
        return MaterialPageRoute(builder: (_) => const SignupScreen());
      case RouteNames.dashboard:
        return MaterialPageRoute(builder: (_) => const DashboardScreen());
      case RouteNames.groupList:
        return MaterialPageRoute(builder: (_) => const GroupsListScreen());
      case RouteNames.groupCreate:
        return MaterialPageRoute(builder: (_) => const GroupCreateEditScreen());
      case RouteNames.groupDetail: 
        if (args is String) {
          return MaterialPageRoute(builder: (_) => GroupDetailScreen(groupId: args));
        } else if (args is Map<String, dynamic> && args.containsKey('id')) {
          return MaterialPageRoute(builder: (_) => GroupDetailScreen(groupId: args['id'] as String));
        }
        return _errorRoute(settings.name);
      case RouteNames.groupEdit:
        if (args is String) {
          return MaterialPageRoute(builder: (_) => GroupCreateEditScreen(groupId: args));
        } else if (args is Map<String, dynamic> && args.containsKey('id')) {
          return MaterialPageRoute(builder: (_) => GroupCreateEditScreen(groupId: args['id'] as String));
        }
        return _errorRoute(settings.name);
      case RouteNames.expenseCreate:
        String? groupId;
        if (args is Map<String, dynamic> && args.containsKey('groupId')) {
          groupId = args['groupId'] as String?;
        }
        return MaterialPageRoute(builder: (_) => ExpenseCreateEditScreen(groupId: groupId));
      case RouteNames.expenseDetail:
        if (args is String) {
          return MaterialPageRoute(builder: (_) => ExpenseDetailScreen(expenseId: args));
        } else if (args is Map<String, dynamic> && args.containsKey('id')) {
          return MaterialPageRoute(builder: (_) => ExpenseDetailScreen(expenseId: args['id'] as String));
        }
        return _errorRoute(settings.name);
      case RouteNames.expenseEdit:
         if (args is String) {
          return MaterialPageRoute(builder: (_) => ExpenseCreateEditScreen(expenseId: args));
        } else if (args is Map<String, dynamic> && args.containsKey('id')) {
          return MaterialPageRoute(builder: (_) => ExpenseCreateEditScreen(expenseId: args['id'] as String));
        }
        return _errorRoute(settings.name);
      case RouteNames.profile:
        return MaterialPageRoute(builder: (_) => const ProfileScreen());
      // Add other routes here...
      default:
        return _errorRoute(settings.name);
    }
  }

  static Route<dynamic> _errorRoute(String? routeName) {
    return MaterialPageRoute(
      builder: (_) => Scaffold(
        appBar: AppBar(title: const Text('Error')),
        body: Center(
          child: Text('No route defined for ${routeName ?? 'Unknown Route'}'),
        ),
      ),
    );
  }
}
