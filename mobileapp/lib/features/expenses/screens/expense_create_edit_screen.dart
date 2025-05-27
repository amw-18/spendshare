import 'package:flutter/material.dart';

class ExpenseCreateEditScreen extends StatelessWidget {
  final String? expenseId; // Null if creating, has value if editing
  final String? groupId; // Optional: if creating an expense for a specific group

  const ExpenseCreateEditScreen({super.key, this.expenseId, this.groupId});

  @override
  Widget build(BuildContext context) {
    final isEditing = expenseId != null;
    return Scaffold(
      appBar: AppBar(
        title: Text(isEditing ? 'Edit Expense' : 'Create Expense'),
      ),
      body: Center(
        child: Text('${isEditing ? 'Edit' : 'Create'} Expense Screen - Placeholder (Group ID: ${groupId ?? 'N/A'})'),
      ),
    );
  }
}
