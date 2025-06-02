import 'package:flutter/material.dart';
import 'package:spendshare/core/models/token.dart';
import 'package:spendshare/core/models/user.dart';
import 'package:spendshare/core/services/auth_service.dart';
import 'package:spendshare/core/models/api_error.dart';

enum AuthStatus { initial, loading, authenticated, error, unauthenticated, checking }

class AuthProvider with ChangeNotifier {
  final AuthService _authService = AuthService();

  AuthStatus _status = AuthStatus.initial;
  AuthStatus get status => _status;

  String? _errorMessage;
  String? get errorMessage => _errorMessage;

  Token? _token;
  Token? get token => _token;

  UserRead? _currentUser;
  UserRead? get currentUser => _currentUser;

  AuthProvider() {
    _checkAuthStatus();
  }

  Future<void> _fetchCurrentUser() async {
    final userResult = await _authService.getCurrentUser();
    if (userResult is UserRead) {
      _currentUser = userResult;
    } else if (userResult is String) {
      _errorMessage = userResult; // Could be 'No token' or other fetch error
      // If fetching user fails (e.g. token expired), treat as unauthenticated
      // Potentially logout or clear token here if API indicates invalid token
      // For now, just log error, status might already be unauthenticated or error
      print('Error fetching user: $_errorMessage');
      // If token was present but user fetch failed, consider logging out
      // await logout(); // This would change status to unauthenticated
    } else if (userResult is HttpValidationError) {
      _errorMessage = userResult.detail?.map((e) => e.msg).join('\n') ?? 'Failed to fetch user details.';
      print('Validation error fetching user: $_errorMessage');
      // await logout();
    }
    // No need to notifyListeners here as it's called by the invoking methods
  }

  Future<void> _checkAuthStatus() async {
    _status = AuthStatus.checking; // Indicate that we are checking
    notifyListeners();

    final isAuthenticated = await _authService.isAuthenticated();
    if (isAuthenticated) {
      final tokenString = await _authService.getToken();
      _token = Token(accessToken: tokenString!, tokenType: 'bearer'); // Assuming type
      await _fetchCurrentUser(); // Fetch user details
      if (_currentUser != null) {
        _status = AuthStatus.authenticated;
      } else {
        // Token exists but user fetch failed (e.g. token invalid/expired)
        await _authService.logout(); // Clear the invalid token
        _token = null;
        _status = AuthStatus.unauthenticated;
        _errorMessage = _errorMessage ?? "Session expired. Please login again.";
      }
    } else {
      _status = AuthStatus.unauthenticated;
    }
    notifyListeners();
  }

  Future<bool> login(String username, String password) async {
    _status = AuthStatus.loading;
    _errorMessage = null;
    _currentUser = null; // Clear previous user data
    notifyListeners();

    final result = await _authService.login(username, password);

    if (result is Token) {
      _token = result;
      await _fetchCurrentUser(); // Fetch user details after getting token
      if (_currentUser != null) {
        _status = AuthStatus.authenticated;
        notifyListeners();
        return true;
      } else {
        // Login gave token, but couldn't fetch user details. Treat as error.
        _status = AuthStatus.error;
        _errorMessage = _errorMessage ?? 'Failed to retrieve user details after login.';
        // Optionally logout here if user details are critical
        // await _authService.logout(); 
        // _token = null;
      }
    } else if (result is HttpValidationError) {
      _errorMessage = result.detail?.map((e) => e.msg).join('\n') ?? 'Login failed.';
      _status = AuthStatus.error;
    } else if (result is String) { // Generic error string
      _errorMessage = result;
      _status = AuthStatus.error;
    } else {
      _errorMessage = 'An unknown error occurred during login.';
      _status = AuthStatus.error;
    }
    notifyListeners();
    return false;
  }

  Future<bool> signup(UserCreate userCreate) async {
    _status = AuthStatus.loading;
    _errorMessage = null;
    notifyListeners();

    final result = await _authService.signup(userCreate);

    if (result is UserRead) { 
      // _currentUser = result; // Signup in our case doesn't auto-login or return token
      _status = AuthStatus.unauthenticated; // Stay unauthenticated, prompt for login
      _errorMessage = "Signup successful! Please login."; // Inform user
      notifyListeners();
      return true; 
    } else if (result is HttpValidationError) {
      _errorMessage = result.detail?.map((e) => e.msg).join('\n') ?? 'Signup failed.';
      _status = AuthStatus.error;
    } else if (result is String) {
      _errorMessage = result;
      _status = AuthStatus.error;
    } else {
      _errorMessage = 'An unknown error occurred during signup.';
      _status = AuthStatus.error;
    }
    notifyListeners();
    return false;
  }

  Future<void> logout() async {
    await _authService.logout();
    _token = null;
    _currentUser = null;
    _status = AuthStatus.unauthenticated;
    _errorMessage = null; // Clear any previous errors
    notifyListeners();
  }
}
