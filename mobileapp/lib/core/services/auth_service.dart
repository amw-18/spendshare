import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/user.dart';
import '../models/token.dart';
import '../models/api_error.dart';

class AuthService {
  // Default base URL for development (e.g., Android emulator accessing localhost)
  static const String _defaultApiBaseUrl = 'http://10.0.2.2:8000/api/v1';
  
  // Get API_BASE_URL from environment variable, fallback to default if not set.
  // To set this when running: flutter run --dart-define=API_BASE_URL=your_actual_url
  static final String _apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: _defaultApiBaseUrl,
  );
  
  static const String _tokenKey = 'spendshare_auth_token';

  Future<dynamic> login(String username, String password) async {
    final Uri loginUrl = Uri.parse('$_apiBaseUrl/users/token');
    
    try {
      final response = await http.post(
        loginUrl,
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: {
          'username': username,
          'password': password,
          'grant_type': 'password', // Assuming password grant type
          // 'scope': '', // Add if required by your API
          // 'client_id': '', // Add if required
          // 'client_secret': '', // Add if required
        },
      );

      if (response.statusCode == 200) {
        final token = Token.fromJson(jsonDecode(response.body));
        await _saveToken(token.accessToken);
        return token;
      } else {
        // Attempt to parse as HttpValidationError
        try {
          return HttpValidationError.fromJson(jsonDecode(response.body));
        } catch (e) {
          // If parsing fails, return a generic error message or the raw response body
          return 'Login failed: ${response.statusCode} ${response.body}';
        }
      }
    } catch (e) {
      // Network error or other issues
      return 'An error occurred: ${e.toString()}';
    }
  }

  Future<dynamic> signup(UserCreate userCreate) async {
    final Uri signupUrl = Uri.parse('$_apiBaseUrl/users/');
    
    try {
      final response = await http.post(
        signupUrl,
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode(userCreate.toJson()),
      );

      if (response.statusCode == 200 || response.statusCode == 201) { // 201 for created
        return UserRead.fromJson(jsonDecode(response.body));
      } else {
        try {
          return HttpValidationError.fromJson(jsonDecode(response.body));
        } catch (e) {
          return 'Signup failed: ${response.statusCode} ${response.body}';
        }
      }
    } catch (e) {
      return 'An error occurred: ${e.toString()}';
    }
  }

  Future<dynamic> getCurrentUser() async {
    final token = await getToken();
    if (token == null) {
      return 'No token found. User not authenticated.';
    }

    final Uri usersMeUrl = Uri.parse('$_apiBaseUrl/users/me');
    try {
      final response = await http.get(
        usersMeUrl,
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        return UserRead.fromJson(jsonDecode(response.body));
      } else {
        try {
          return HttpValidationError.fromJson(jsonDecode(response.body));
        } catch (e) {
          return 'Failed to fetch user: ${response.statusCode} ${response.body}';
        }
      }
    } catch (e) {
      return 'An error occurred while fetching user: ${e.toString()}';
    }
  }

  Future<void> _saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, token);
  }

  Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_tokenKey);
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
    // TODO: Notify state management to update UI (e.g., navigate to login)
  }

  Future<bool> isAuthenticated() async {
    final token = await getToken();
    return token != null && token.isNotEmpty;
    // TODO: Optionally, add token validation (e.g., check expiry if token contains it)
  }
}
