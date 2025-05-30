// lib/core/models/group.dart

// GroupCreate Schema
class GroupCreate {
  final String name;
  final String? description;

  GroupCreate({
    required this.name,
    this.description,
  });

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> data = {'name': name};
    if (description != null) data['description'] = description;
    return data;
  }
}

// GroupRead Schema
class GroupRead {
  final int id;
  final String name;
  final String? description;
  final int createdByUserId;
  // Consider adding a list of members or expenses if frequently needed together
  // final List<UserRead>? members;
  // final List<ExpenseRead>? expenses;

  GroupRead({
    required this.id,
    required this.name,
    this.description,
    required this.createdByUserId,
    // this.members,
    // this.expenses,
  });

  factory GroupRead.fromJson(Map<String, dynamic> json) {
    return GroupRead(
      id: json['id'] as int,
      name: json['name'] as String,
      description: json['description'] as String?,
      createdByUserId: json['created_by_user_id'] as int,
      // members: (json['members'] as List<dynamic>?)
      //     ?.map((e) => UserRead.fromJson(e as Map<String, dynamic>))
      //     .toList(), 
      // expenses: (json['expenses'] as List<dynamic>?)
      //     ?.map((e) => ExpenseRead.fromJson(e as Map<String, dynamic>))
      //     .toList(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'created_by_user_id': createdByUserId,
      // 'members': members?.map((e) => e.toJson()).toList(),
      // 'expenses': expenses?.map((e) => e.toJson()).toList(),
    };
  }
}

// GroupUpdate Schema
class GroupUpdate {
  final String? name;
  // OpenAPI spec only showed name as updatable. Add description if needed.
  // final String? description;

  GroupUpdate({
    this.name,
    // this.description,
  });

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> data = {};
    if (name != null) data['name'] = name;
    // if (description != null) data['description'] = description;
    return data;
  }
}
