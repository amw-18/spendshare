// lib/core/models/token.dart

class Token {
  final String accessToken;
  final String tokenType;

  Token({
    required this.accessToken,
    required this.tokenType,
  });

  factory Token.fromJson(Map<String, dynamic> json) {
    return Token(
      accessToken: json['access_token'] as String,
      tokenType: json['token_type'] as String? ?? 'bearer', // Default to 'bearer' if null or missing
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'access_token': accessToken,
      'token_type': tokenType,
    };
  }
}
