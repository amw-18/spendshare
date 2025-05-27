// lib/core/models/expense_participant.dart
import './user.dart'; // For UserRead
import './expense.dart'; // For ExpenseCreate

// ExpenseParticipantReadWithUser Schema
class ExpenseParticipantReadWithUser {
  final int userId;
  final int expenseId;
  final double shareAmount;
  final UserRead user; // Contains the full UserRead object

  ExpenseParticipantReadWithUser({
    required this.userId,
    required this.expenseId,
    required this.shareAmount,
    required this.user,
  });

  factory ExpenseParticipantReadWithUser.fromJson(Map<String, dynamic> json) {
    return ExpenseParticipantReadWithUser(
      userId: json['user_id'] as int,
      expenseId: json['expense_id'] as int,
      shareAmount: (json['share_amount'] as num).toDouble(),
      user: UserRead.fromJson(json['user'] as Map<String, dynamic>),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'user_id': userId,
      'expense_id': expenseId,
      'share_amount': shareAmount,
      'user': user.toJson(),
    };
  }
}

// ParticipantUpdate Schema (used in ExpenseUpdate)
class ParticipantUpdate {
  final int userId;
  final double? shareAmount;

  ParticipantUpdate({
    required this.userId,
    this.shareAmount,
  });

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> data = {'user_id': userId};
    if (shareAmount != null) data['share_amount'] = shareAmount;
    return data;
  }

  factory ParticipantUpdate.fromJson(Map<String, dynamic> json) {
    return ParticipantUpdate(
        userId: json['user_id'] as int,
        shareAmount: (json['share_amount'] as num?)?.toDouble());
  }
}

// Body_create_expense_with_participants_endpoint_api_v1_expenses_service__post Schema
// This class represents the request body for creating an expense with participants.
class CreateExpenseWithParticipantsBody {
  final ExpenseCreate expenseIn;
  final List<int> participantUserIds;

  CreateExpenseWithParticipantsBody({
    required this.expenseIn,
    required this.participantUserIds,
  });

  Map<String, dynamic> toJson() {
    return {
      'expense_in': expenseIn.toJson(),
      'participant_user_ids': participantUserIds,
    };
  }
}
