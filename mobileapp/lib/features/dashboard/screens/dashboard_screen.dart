import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:spendshare/features/auth/notifiers/auth_provider.dart';
import 'package:spendshare/core/navigation/route_names.dart';
import 'package:spendshare/core/utils/form_constants.dart'; // For consistent padding

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    // In a real app, you'd fetch user details to display name, etc.
    // For now, using a generic welcome or fetching from authProvider if available.
    final userName = authProvider.currentUser?.username ?? 'User';

    return Scaffold(
      appBar: AppBar(
        title: const Text('Dashboard'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Logout',
            onPressed: () async {
              await authProvider.logout();
              // The Consumer in main.dart should handle navigation to LoginScreen
              // If not, uncomment and adjust:
              // Navigator.of(context).pushNamedAndRemoveUntil(RouteNames.login, (route) => false);
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: formHorizontalPadding.copyWith(top: 20, bottom: 20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              'Welcome, $userName!',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    color: Theme.of(context).colorScheme.onBackground,
                  ),
            ),
            const SizedBox(height: formVerticalSpacing * 1.5),
            
            // Placeholder for an overview/summary section
            _buildSectionTitle(context, 'Overview'),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Center(
                  child: Text(
                    'Summary of your spending will appear here.',
                    style: Theme.of(context).textTheme.bodyMedium,
                    textAlign: TextAlign.center,
                  ),
                ),
              ),
            ),
            const SizedBox(height: formVerticalSpacing * 1.5),

            // Navigation Section
            _buildSectionTitle(context, 'Quick Actions'),
            GridView.count(
              crossAxisCount: 2,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(), // to disable GridView's scrolling
              crossAxisSpacing: 16,
              mainAxisSpacing: 16,
              children: <Widget>[
                _buildActionCard(
                  context,
                  icon: Icons.group,
                  label: 'My Groups',
                  routeName: RouteNames.groupsList,
                ),
                _buildActionCard(
                  context,
                  icon: Icons.add_circle_outline,
                  label: 'New Group',
                  routeName: RouteNames.groupCreateEdit, // Assuming this route exists for new group
                ),
                _buildActionCard(
                  context,
                  icon: Icons.receipt_long,
                  label: 'All Expenses',
                  // TODO: Define a route for viewing all expenses if different from group details
                  // routeName: RouteNames.allExpensesList, 
                  onTap: () {
                     ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('All Expenses - Coming Soon!')),
                    );
                  }
                ),
                _buildActionCard(
                  context,
                  icon: Icons.post_add,
                  label: 'Add Expense',
                  // This might navigate to a screen to select a group first, or a general expense add screen
                  // routeName: RouteNames.expenseCreateEdit, 
                  onTap: () {
                    // Example: Navigate to create expense, might need group context
                    // For now, a placeholder or direct navigation if applicable
                    // Navigator.of(context).pushNamed(RouteNames.expenseCreateEdit);
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Add Expense - Coming Soon!')),
                    );
                  }
                ),
              ],
            ),
            const SizedBox(height: formVerticalSpacing * 1.5),

            _buildSectionTitle(context, 'Settings'),
             _buildActionCard(
                  context,
                  icon: Icons.person_outline,
                  label: 'My Profile',
                  routeName: RouteNames.profile,
                  isFullWidth: true, // Make it take full width if it's the only one in a row
                ),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionTitle(BuildContext context, String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0),
      child: Text(
        title,
        style: Theme.of(context).textTheme.titleLarge?.copyWith(
              color: Theme.of(context).colorScheme.onBackground,
              fontWeight: FontWeight.bold,
            ),
      ),
    );
  }

  Widget _buildActionCard(BuildContext context, {
    required IconData icon,
    required String label,
    String? routeName,
    VoidCallback? onTap,
    bool isFullWidth = false,
  }) {
    final cardContent = Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: <Widget>[
        Icon(icon, size: 40.0, color: Theme.of(context).colorScheme.primary),
        const SizedBox(height: 10.0),
        Text(
          label,
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.labelLarge?.copyWith(
            color: Theme.of(context).colorScheme.onSurface, // Ensure text is readable on card
          ),
        ),
      ],
    );

    final card = Card(
      elevation: 2.0,
      child: InkWell(
        onTap: onTap ?? (routeName != null ? () => Navigator.of(context).pushNamed(routeName) : null),
        borderRadius: BorderRadius.circular(8.0), // Match card's default border radius
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Center(child: cardContent),
        ),
      ),
    );

    if (isFullWidth) {
      return SizedBox(
        width: double.infinity,
        child: card,
      );
    }
    return card;
  }
}
