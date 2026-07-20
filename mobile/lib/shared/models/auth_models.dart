/// Domain models for authentication and settings context.

class UserProfile {
  final String id;
  final String email;

  const UserProfile({
    required this.id,
    required this.email,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      id: json['id'] as String,
      email: json['email'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
    };
  }
}

class UserSettings {
  final String privacyMode;
  final bool aiEnabled;
  final String theme;

  const UserSettings({
    required this.privacyMode,
    required this.aiEnabled,
    required this.theme,
  });

  factory UserSettings.fromJson(Map<String, dynamic> json) {
    return UserSettings(
      privacyMode: json['privacy_mode'] as String? ?? 'maximum_privacy',
      aiEnabled: json['ai_enabled'] as bool? ?? false,
      theme: json['theme'] as String? ?? 'system',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'privacy_mode': privacyMode,
      'ai_enabled': aiEnabled,
      'theme': theme,
    };
  }
}

class AuthSession {
  final UserProfile user;
  final UserSettings settings;

  const AuthSession({
    required this.user,
    required this.settings,
  });

  factory AuthSession.fromJson(Map<String, dynamic> json) {
    return AuthSession(
      user: UserProfile.fromJson(json['user'] as Map<String, dynamic>),
      settings: UserSettings.fromJson(json['settings'] as Map<String, dynamic>),
    );
  }
}
