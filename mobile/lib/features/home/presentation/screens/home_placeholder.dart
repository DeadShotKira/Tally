import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../theme/theme_provider.dart';
import '../../../../shared/widgets/buttons.dart';
import '../../../../shared/widgets/cards.dart';
import '../../../auth/presentation/controllers/auth_controller.dart';

class HomePlaceholderScreen extends ConsumerWidget {
  const HomePlaceholderScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final authState = ref.watch(authControllerProvider);
    final themeMode = ref.watch(themeNotifierProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Tally Dashboard'),
        actions: [
          IconButton(
            icon: Icon(
              themeMode == ThemeMode.dark ? Icons.light_mode_outlined : Icons.dark_mode_outlined,
            ),
            onPressed: () => ref.read(themeNotifierProvider.notifier).toggleTheme(context),
            tooltip: 'Toggle Theme',
          ),
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (context) => const SettingsPlaceholderScreenDummy(),
                ),
              );
            },
            tooltip: 'Settings',
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // User summary card
              AppCard(
                gradientColors: theme.brightness == Brightness.dark
                    ? [const Color(0xFF1E293B), const Color(0xFF0F172A)]
                    : [const Color(0xFF0D9488), const Color(0xFF4F46E5)],
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Avatar(
                          name: authState.session?.user.email ?? 'User',
                          radius: 28,
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Welcome Back',
                                style: TextStyle(
                                  color: theme.brightness == Brightness.dark
                                      ? Colors.white
                                      : Colors.white.withOpacity(0.8),
                                  fontSize: 14,
                                ),
                              ),
                              Text(
                                authState.session?.user.email ?? 'Unknown User',
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                ),
                                overflow: TextOverflow.ellipsis,
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              SectionHeader(title: 'Tally Batch 1 Foundations'),

              AppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Ready Modules',
                      style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 12),
                    _buildFeatureItem(context, 'Core UI Design System', true),
                    _buildFeatureItem(context, 'Theme persistence (Light/Dark/System)', true),
                    _buildFeatureItem(context, 'GoRouter configuration & Auth guards', true),
                    _buildFeatureItem(context, 'State management with Riverpod', true),
                    _buildFeatureItem(context, 'Supabase authentication workflow', true),
                    _buildFeatureItem(context, 'Polished Auth UI flow', true),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              PrimaryButton(
                text: 'Sign Out',
                onPressed: () {
                  ref.read(authControllerProvider.notifier).logout();
                },
                icon: Icons.logout,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFeatureItem(BuildContext context, String title, bool isDone) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6.0),
      child: Row(
        children: [
          Icon(
            isDone ? Icons.check_circle_outline : Icons.radio_button_unchecked,
            color: isDone ? Colors.teal : Colors.grey,
            size: 20,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              title,
              style: TextStyle(
                fontSize: 14,
                decoration: isDone ? TextDecoration.none : TextDecoration.lineThrough,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// Simple dummy inline screen to support settings navigation
class SettingsPlaceholderScreenDummy extends ConsumerWidget {
  const SettingsPlaceholderScreenDummy({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final themeMode = ref.watch(themeNotifierProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          SectionHeader(title: 'Theme Preference'),
          AppCard(
            child: Column(
              children: [
                RadioListTile<ThemeMode>(
                  title: const Text('System Default'),
                  value: ThemeMode.system,
                  groupValue: themeMode,
                  onChanged: (mode) {
                    if (mode != null) {
                      ref.read(themeNotifierProvider.notifier).setThemeMode(mode);
                    }
                  },
                ),
                RadioListTile<ThemeMode>(
                  title: const Text('Light Theme'),
                  value: ThemeMode.light,
                  groupValue: themeMode,
                  onChanged: (mode) {
                    if (mode != null) {
                      ref.read(themeNotifierProvider.notifier).setThemeMode(mode);
                    }
                  },
                ),
                RadioListTile<ThemeMode>(
                  title: const Text('Dark Theme'),
                  value: ThemeMode.dark,
                  groupValue: themeMode,
                  onChanged: (mode) {
                    if (mode != null) {
                      ref.read(themeNotifierProvider.notifier).setThemeMode(mode);
                    }
                  },
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          SectionHeader(title: 'App Version'),
          const AppCard(
            child: Padding(
              padding: EdgeInsets.symmetric(vertical: 4.0),
              child: ListTile(
                title: Text('Tally Finance Client'),
                subtitle: Text('v1.0.0 (Batch 1 Foundations)'),
                leading: Icon(Icons.info_outline),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
