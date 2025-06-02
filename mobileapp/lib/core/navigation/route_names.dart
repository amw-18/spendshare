class RouteNames {
  static const String splash = '/splash'; // Initial route
  static const String login = '/login';
  static const String signup = '/signup';
  static const String dashboard = '/dashboard';
  
  // Groups
  static const String groupList = '/groups';
  static const String groupCreate = '/groups/create';
  static const String groupDetail = '/groups/detail'; // e.g., /groups/detail/:id
  static const String groupEdit = '/groups/edit'; // e.g., /groups/edit/:id
  static const String groupAddMembers = '/groups/add-members'; // e.g., /groups/add-members/:id

  // Expenses
  static const String expenseCreate = '/expenses/create'; // Can take groupId as argument
  static const String expenseDetail = '/expenses/detail'; // e.g., /expenses/detail/:id
  static const String expenseEdit = '/expenses/edit'; // e.g., /expenses/edit/:id

  // Profile/Settings
  static const String profile = '/profile';
  static const String settings = '/settings';
}
