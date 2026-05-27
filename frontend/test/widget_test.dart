import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:ai_for_blinds/screens/home_screen.dart';
import 'package:ai_for_blinds/services/audio_service.dart';

void main() {
  testWidgets('Home screen shows app title and 4 feature buttons',
      (WidgetTester tester) async {
    await tester.pumpWidget(
      ChangeNotifierProvider(
        create: (_) => AudioService(),
        child: const MaterialApp(
          home: HomeScreen(),
        ),
      ),
    );

    // Verify the app bar title is SgBe Vision
    expect(find.text('SgBe Vision'), findsOneWidget);

    // Verify all 4 feature buttons are present (Vietnamese labels)
    expect(find.text('Quét tài liệu'), findsOneWidget);
    expect(find.text('Hỏi đáp kiến thức'), findsOneWidget);
    expect(find.text('Ôn tập'), findsOneWidget);
    expect(find.text('Cài đặt'), findsOneWidget);
  });
}
