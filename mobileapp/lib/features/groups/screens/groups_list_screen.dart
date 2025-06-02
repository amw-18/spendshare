import 'package:flutter/material.dart';

class GroupsListScreen extends StatelessWidget {
  const GroupsListScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Groups'),
      ),
      body: const Center(
        child: Text('Groups List Screen - Placeholder'),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          // TODO: Navigate to GroupCreateScreen
        },
        child: const Icon(Icons.add),
        tooltip: 'Create Group',
      ),
    );
  }
}
