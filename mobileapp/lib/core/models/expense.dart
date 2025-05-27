// lib/core/models/expense.dart
import './expense_participant.dart'; // For ExpenseParticipantReadWithUser and ParticipantUpdate

// ExpenseCreate Schema
class ExpenseCreate {
  final String description;
  final double amount;
  final int? groupId; // Optional
  // paid_by_user_id is usually set by the backend based on authenticated user

  ExpenseCreate({
    required this.description,
    required this.amount,
    this.groupId,
  });

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> data = {
      'description': description,
      'amount': amount,
    };
    if (groupId != null) data['group_id'] = groupId;
    return data;
  }
}

// ExpenseRead Schema
class ExpenseRead {
  final int id;
  final String description;
  final double amount;
  final DateTime date;
  final int? groupId;
  final int? paidByUserId;
  final List<ExpenseParticipantReadWithUser> participantDetails;

  ExpenseRead({
    required this.id,
    this.description = "", // Default from schema
    required this.amount,
    required this.date,
    this.groupId,
    this.paidByUserId,
    this.participantDetails = const [], // Default from schema
  });

  factory ExpenseRead.fromJson(Map<String, dynamic> json) {
    return ExpenseRead(
      id: json['id'] as int,
      description: json['description'] as String? ?? "",
      amount: (json['amount'] as num).toDouble(),
      date: DateTime.parse(json['date'] as String),
      groupId: json['group_id'] as int?,
      paidByUserId: json['paid_by_user_id'] as int?,
      participantDetails: (json['participant_details'] as List<dynamic>? ?? [])
          .map((e) => ExpenseParticipantReadWithUser.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'description': description,
      'amount': amount,
      'date': date.toIso8601String(),
      'group_id': groupId,
      'paid_by_user_id': paidByUserId,
      'participant_details': participantDetails.map((e) => e.toJson()).toList(),
    };
  }
}

// ExpenseUpdate Schema
class ExpenseUpdate {
  final String? description;
  final double? amount;
  final int? paidByUserId; // Note: API might restrict changing this
  final int? groupId;
  final List<ParticipantUpdate>? participants; // List of participants to update

  ExpenseUpdate({
    this.description,
    this.amount,
    this.paidByUserId,
    this.groupId,
    this.participants,
  });

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> data = {};
    if (description != null) data['description'] = description;
    if (amount != null) data['amount'] = amount;
    if (paidByUserId != null) data['paid_by_user_id'] = paidByUserId;
    if (groupId != null) data['group_id'] = groupId;
    if (participants != null) {
      data['participants'] = participants!.map((p) => p.toJson()).toList();
    }
    return data;
  }
}

// Now that ExpenseCreate is defined, we can update the placeholder in expense_participant.dart
// This is a conceptual note; the actual update would be in expense_participant.dart file itself.
// Consider adding a method to CreateExpenseWithParticipantsBody in expense_participant.dart
// to correctly use ExpenseCreate's toJson if not already handled.
