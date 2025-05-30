// lib/core/models/api_error.dart

class ValidationError {
  final List<dynamic> loc; // List of string or int
  final String msg;
  final String type;

  ValidationError({
    required this.loc,
    required this.msg,
    required this.type,
  });

  factory ValidationError.fromJson(Map<String, dynamic> json) {
    return ValidationError(
      loc: List<dynamic>.from(json['loc'] as List<dynamic>),
      msg: json['msg'] as String,
      type: json['type'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'loc': loc,
      'msg': msg,
      'type': type,
    };
  }
}

class HttpValidationError {
  final List<ValidationError>? detail;

  HttpValidationError({this.detail});

  factory HttpValidationError.fromJson(Map<String, dynamic> json) {
    return HttpValidationError(
      detail: (json['detail'] as List<dynamic>?)
          ?.map((e) => ValidationError.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> data = {};
    if (detail != null) {
      data['detail'] = detail!.map((v) => v.toJson()).toList();
    }
    return data;
  }
}
