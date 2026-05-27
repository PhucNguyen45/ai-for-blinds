import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:ai_for_blinds/app.dart';
import 'package:ai_for_blinds/services/tts_service.dart';

void main() {
  testWidgets('App renders main navigation buttons', (WidgetTester tester) async {
    await tester.pumpWidget(
      ChangeNotifierProvider(
        create: (_) => TtsService(),
        child: const BlindScholarApp(),
      ),
    );

    // Verify the app bar title is present
    expect(find.text('BlindScholar'), findsOneWidget);

    // Verify the 4 main feature buttons are present
    expect(find.text('Book Scanner'), findsOneWidget);
    expect(find.text('Text Reader'), findsOneWidget);
    expect(find.text('Voice Notes'), findsOneWidget);
    expect(find.text('Settings'), findsOneWidget);
  });
}
