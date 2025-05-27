// lib/core/models/user.dart

// UserRead Schema
class UserRead {
  final int id;
  final String username;
  final String email;
  final bool isAdmin;

  UserRead({
    required this.id,
    required this.username,
    required this.email,
    required this.isAdmin,
  });

  factory UserRead.fromJson(Map<String, dynamic> json) {
    return UserRead(
      id: json['id'] as int,
      username: json['username'] as String,
      email: json['email'] as String,
      isAdmin: json['is_admin'] as bool,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'username': username,
      'email': email,
      'is_admin': isAdmin,
    };
  }
}

// UserCreate Schema
class UserCreate {
  final String username;
  final String email;
  final String password;

  UserCreate({
    required this.username,
    required this.email,
    required this.password,
  });

  Map<String, dynamic> toJson() {
    return {
      'username': username,
      'email': email,
      'password': password,
    };
  }
}

// UserUpdate Schema
class UserUpdate {
  final String? username;
  final String? email;
  final String? password;
  final bool? isAdmin;

  UserUpdate({
    this.username,
    this.email,
    this.password,
    this.isAdmin,
  });

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> data = {};
    if (username != null) data['username'] = username;
    if (email != null) data['email'] = email;
    if (password != null) data['password'] = password;
    if (isAdmin != null) data['is_admin'] = isAdmin;
    return data;
  }
}
