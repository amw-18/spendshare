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
    final theme = Theme.of(context);

    return Scaffold(
      // AppBar styling is now primarily from theme
      appBar: AppBar(
        title: const Text('Dashboard'), // Text style will be from theme.appBarTheme.titleTextStyle
        centerTitle: true, // Keep if desired
        actions: [
          IconButton(
            icon: const Icon(Icons.logout), // Icon color from theme.appBarTheme.iconTheme
            tooltip: 'Logout',
            onPressed: () async {
              await authProvider.logout();
              // Navigation handled by Consumer in main.dart
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: formHorizontalPadding.copyWith(top: 24, bottom: 24), // Adjusted padding
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              'Welcome, $userName!',
              style: theme.textTheme.headlineSmall?.copyWith(
                    color: theme.colorScheme.onBackground, // Ensure text color is appropriate for background
                  ),
            ),
            const SizedBox(height: formVerticalSpacing * 1.5), // Keep or adjust spacing
            
            _buildSectionTitle(context, 'Overview'),
            // Card styling is from theme.cardTheme
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0), // Keep padding for content inside card
                child: Center(
                  child: Text(
                    'Summary of your spending will appear here.',
                    style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurface),
                    textAlign: TextAlign.center,
                  ),
                ),
              ),
            ),
            const SizedBox(height: formVerticalSpacing * 1.5), // Keep or adjust

            _buildSectionTitle(context, 'Quick Actions'),
            GridView.count(
              crossAxisCount: 2,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisSpacing: 16, // Keep specific layout spacing
              mainAxisSpacing: 16, // Keep specific layout spacing
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
                  routeName: RouteNames.groupCreateEdit,
                ),
                _buildActionCard(
                  context,
                  icon: Icons.receipt_long,
                  label: 'All Expenses',
                  onTap: () {
                     ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('All Expenses - Coming Soon!', style: theme.snackBarTheme.contentTextStyle)),
                    );
                  }
                ),
                _buildActionCard(
                  context,
                  icon: Icons.post_add,
                  label: 'Add Expense',
                  onTap: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Add Expense - Coming Soon!', style: theme.snackBarTheme.contentTextStyle)),
                    );
                  }
                ),
              ],
            ),
            const SizedBox(height: formVerticalSpacing * 1.5), // Keep or adjust

            _buildSectionTitle(context, 'Settings'),
             _buildActionCard(
                  context,
                  icon: Icons.person_outline, // Example Icon
                  label: 'My Profile',
                  routeName: RouteNames.profile, // Example Route
                  isFullWidth: true,
                ),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionTitle(BuildContext context, String title) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0), // Keep or adjust
      child: Text(
        title,
        style: theme.textTheme.titleLarge?.copyWith(
              color: theme.colorScheme.onBackground,
              // fontWeight: FontWeight.bold, // titleLarge from theme should have appropriate weight
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
    final theme = Theme.of(context);
    final cardContent = Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: <Widget>[
        Icon(icon, size: 40.0, color: theme.colorScheme.primary), // Icon size can be specific
        const SizedBox(height: 10.0), // Keep or adjust
        Text(
          label,
          textAlign: TextAlign.center,
          style: theme.textTheme.labelLarge?.copyWith( // Using labelLarge for button-like text
            color: theme.colorScheme.onSurface,
          ),
        ),
      ],
    );

    // Card styling from theme.cardTheme (elevation, shape, color)
    final card = Card(
      child: InkWell(
        onTap: onTap ?? (routeName != null ? () => Navigator.of(context).pushNamed(routeName) : null),
        // borderRadius should match Card's shape from theme if possible, or define explicitly if cardTheme is not rounded
        borderRadius: (theme.cardTheme.shape as RoundedRectangleBorder?)?.borderRadius as BorderRadiusGeometry? ?? BorderRadius.circular(12.0),
        child: Padding(
          padding: const EdgeInsets.all(16.0), // Keep padding for content
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
