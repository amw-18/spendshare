import 'package:flutter/material.dart';

class GroupCreateEditScreen extends StatelessWidget {
  final String? groupId; // Null if creating, has value if editing

  const GroupCreateEditScreen({super.key, this.groupId});

  @override
  Widget build(BuildContext context) {
    final isEditing = groupId != null;
    return Scaffold(
      appBar: AppBar(
        title: Text(isEditing ? 'Edit Group' : 'Create Group'),
      ),
      body: Center(
        child: Text('${isEditing ? 'Edit' : 'Create'} Group Screen - Placeholder'),
      ),
    );
  }
}
