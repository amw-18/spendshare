import 'package:flutter/material.dart';

class ExpenseDetailScreen extends StatelessWidget {
  final String expenseId;

  const ExpenseDetailScreen({super.key, required this.expenseId});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Expense Details'),
      ),
      body: Center(
        child: Text('Expense Detail Screen for ID: $expenseId - Placeholder'),
      ),
    );
  }
}
