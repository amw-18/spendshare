import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:spendshare/features/auth/notifiers/auth_provider.dart';
import 'package:spendshare/core/models/user.dart';
import 'package:spendshare/core/utils/form_constants.dart'; // For consistent padding

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context);
    final UserRead? currentUser = authProvider.currentUser;

    return Scaffold(
      appBar: AppBar(
        title: const Text('My Profile'),
        centerTitle: true,
      ),
      body: currentUser == null
          ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 16),
                  Text('Loading profile...'),
                ],
              ),
            )
          : SingleChildScrollView(
              padding: formHorizontalPadding.copyWith(top: 20, bottom: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  _buildProfileHeader(context, currentUser),
                  const SizedBox(height: formVerticalSpacing * 1.5),
                  _buildSectionTitle(context, 'Account Information'),
                  _buildInfoCard(context, currentUser),
                  const SizedBox(height: formVerticalSpacing * 1.5),
                  // Placeholder for future actions like 'Edit Profile', 'Change Password'
                  _buildSectionTitle(context, 'Actions'),
                  Card(
                    elevation: 1,
                    child: Column(
                      children: [
                        _buildActionItem(context, Icons.edit, 'Edit Profile', () {
                           ScaffoldMessenger.of(context).showSnackBar(
                             const SnackBar(content: Text('Edit Profile - Coming Soon!')),
                           );
                        }),
                        const Divider(height: 0),
                        _buildActionItem(context, Icons.lock_outline, 'Change Password', () {
                           ScaffoldMessenger.of(context).showSnackBar(
                             const SnackBar(content: Text('Change Password - Coming Soon!')),
                           );
                        }),
                      ],
                    )
                  ),
                  const SizedBox(height: formVerticalSpacing * 2),
                  Center(
                    child: ElevatedButton.icon(
                      icon: const Icon(Icons.logout),
                      label: const Text('Logout'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Theme.of(context).colorScheme.error,
                        foregroundColor: Theme.of(context).colorScheme.onError,
                      ),
                      onPressed: () async {
                        await authProvider.logout();
                        // Navigator.of(context).pushNamedAndRemoveUntil(RouteNames.login, (route) => false);
                        // The Consumer in main.dart should handle navigation
                      },
                    ),
                  ),
                ],
              ),
            ),
    );
  }

  Widget _buildProfileHeader(BuildContext context, UserRead user) {
    return Center(
      child: Column(
        children: [
          CircleAvatar(
            radius: 50,
            backgroundColor: Theme.of(context).colorScheme.primaryContainer,
            child: Text(
              user.username.isNotEmpty ? user.username[0].toUpperCase() : 'U',
              style: TextStyle(
                fontSize: 40,
                fontWeight: FontWeight.bold,
                color: Theme.of(context).colorScheme.onPrimaryContainer,
              ),
            ),
          ),
          const SizedBox(height: 12),
          Text(
            user.fullName ?? user.username,
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          if (user.fullName != null && user.fullName!.isNotEmpty) 
            Text(
              '@${user.username}',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                color: Theme.of(context).colorScheme.secondary,
              ),
            ),
          Text(
            user.email,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionTitle(BuildContext context, String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0, top: 8.0),
      child: Text(
        title,
        style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.bold,
            ),
      ),
    );
  }

  Widget _buildInfoCard(BuildContext context, UserRead user) {
    return Card(
      elevation: 1,
      child: Padding(
        padding: const EdgeInsets.all(0), // No padding for the card itself, ListTile will handle
        child: Column(
          children: <Widget>[
            _buildInfoRow(context, Icons.person_outline, 'Username', user.username),
            const Divider(height: 0),
            _buildInfoRow(context, Icons.email_outlined, 'Email', user.email),
            if (user.fullName != null && user.fullName!.isNotEmpty) ...[
              const Divider(height: 0),
              _buildInfoRow(context, Icons.badge_outlined, 'Full Name', user.fullName!),
            ],
            const Divider(height: 0),
            _buildInfoRow(context, Icons.fingerprint, 'User ID', user.id.toString()),
            if (user.isActive != null) ...[
              const Divider(height: 0),
              _buildInfoRow(context, Icons.check_circle_outline, 'Active Status', user.isActive! ? 'Active' : 'Inactive',
                valueColor: user.isActive! ? Colors.green.shade600 : Colors.red.shade600
              ),
            ],
            if (user.isSuperuser != null) ...[
              const Divider(height: 0),
              _buildInfoRow(context, Icons.admin_panel_settings_outlined, 'Admin Status', user.isSuperuser! ? 'Admin' : 'User'),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(BuildContext context, IconData icon, String label, String value, {Color? valueColor}) {
    return ListTile(
      leading: Icon(icon, color: Theme.of(context).colorScheme.primary),
      title: Text(label, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
      subtitle: Text(
        value,
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
          color: valueColor ?? Theme.of(context).colorScheme.onSurfaceVariant,
        ),
      ),
      dense: true,
    );
  }

  Widget _buildActionItem(BuildContext context, IconData icon, String label, VoidCallback onTap) {
    return ListTile(
      leading: Icon(icon, color: Theme.of(context).colorScheme.primary),
      title: Text(label, style: Theme.of(context).textTheme.titleMedium),
      trailing: const Icon(Icons.chevron_right),
      onTap: onTap,
    );
  }
}
