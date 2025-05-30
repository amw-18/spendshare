import 'package:flutter/material.dart';

class GroupDetailScreen extends StatelessWidget {
  final String groupId;

  const GroupDetailScreen({super.key, required this.groupId});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Group Details'),
      ),
      body: Center(
        child: Text('Group Detail Screen for ID: $groupId - Placeholder'),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          // TODO: Navigate to ExpenseCreateScreen for this group
        },
        child: const Icon(Icons.add_card_outlined),
        tooltip: 'Add Expense',
      ),
    );
  }
}
