import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:sgbe/library/library_data.dart';
import 'package:sgbe/services/settings_store.dart';
import 'package:sgbe/services/speech.dart';

import 'fakes.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('phụ đề: hiện câu đang nói, dừng thì mờ đi nhưng vẫn giữ chữ', () async {
    final inner = FakeSpeaker();
    final s = CaptionedSpeaker(inner);
    expect(s.caption.value.text, isEmpty);
    await s.speak('Xin chào.');
    expect(s.caption.value.text, 'Xin chào.');
    expect(s.caption.value.speaking, isFalse, reason: 'đã nói xong');
    await s.stop();
    expect(s.caption.value.text, 'Xin chào.');
    expect(inner.spoken, ['Xin chào.']);
  });

  test('tốc độ đọc: bốn mức, vòng lại từ đầu, tốc độ chỉnh tinh thì lấy mức gần nhất', () async {
    SharedPreferences.setMockInitialValues({});
    final st = await SettingsStore.load();
    expect(st.ratePreset.name, 'Bình thường');
    expect(st.nextRatePreset.name, 'Nhanh');
    await st.setSpeechRate(0.8);
    expect(st.nextRatePreset.name, 'Chậm');
    await st.setSpeechRate(0.62);
    expect(st.ratePreset.name, 'Nhanh');
    expect(st.soundOn && st.vibrateOn, isTrue, reason: 'mặc định bật');
    expect(st.tutorialDone, isFalse, reason: 'lần đầu phải nghe hướng dẫn');
  });

  test('thư viện mẫu đóng gói trong app đọc được, sách nào cũng có trang và lời mô tả', () async {
    final books = await const AssetLibrarySource().load();
    expect(books, isNotEmpty);
    for (final b in books) {
      expect(b.pages, isNotEmpty, reason: b.title);
      for (final p in b.pages) {
        expect(p.text.length, greaterThan(40), reason: '${b.title} trang ${p.number}');
      }
    }
  });
}
