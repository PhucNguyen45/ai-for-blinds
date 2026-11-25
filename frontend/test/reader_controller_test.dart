import 'dart:async';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:sgbe/api/models.dart';
import 'package:sgbe/reader/reader_controller.dart';
import 'package:sgbe/services/earcons.dart';
import 'package:sgbe/strings.dart';

import 'fakes.dart';

void main() {
  late FakeApi api;
  late FakeSpeaker speaker;
  late FakeEarcons earcons;
  late ReaderController c;
  final image = Uint8List.fromList([1, 2, 3]);

  setUp(() {
    api = FakeApi();
    speaker = FakeSpeaker();
    earcons = FakeEarcons();
    c = ReaderController(
      api: () => api,
      speaker: speaker,
      earcons: earcons,
      pageType: () => 'map',
      waitingInterval: const Duration(milliseconds: 10),
      stillWorkingAfter: const Duration(milliseconds: 30),
    );
  });

  test('thành công: âm chụp, báo đang đọc, âm xong, đọc mô tả, về sẵn sàng', () async {
    await c.describe(image);

    expect(earcons.played.first, Earcon.shutter);
    expect(earcons.played.last, Earcon.done);
    expect(speaker.spoken.first, S.working);
    expect(speaker.spoken.last, 'Trang có một lược đồ.');
    expect(c.status, ReaderStatus.idle);
    expect(c.last?.imageId, 'b9b1d4985e464bbb');
    expect(api.lastPageType, 'map');
  });

  test('có chỗ không đọc được: đọc thêm gợi ý chụp lại', () async {
    api.next = FakeApi.ok(description: 'Trang mờ.', unreadable: true);
    await c.describe(image);
    expect(speaker.spoken.join(' '), endsWith('Trang mờ. ${S.unreadableHint}'));
    expect(c.shownText, 'Trang mờ. ${S.unreadableHint}');
  });

  test('lỗi: âm lỗi và đọc nguyên câu báo của máy chủ', () async {
    api.next = const ApiFail('VLM_TIMEOUT', 'Máy chủ xử lý quá lâu. Bạn thử chụp lại nhé.');
    await c.describe(image);
    expect(earcons.played.last, Earcon.error);
    expect(speaker.spoken.last, 'Máy chủ xử lý quá lâu. Bạn thử chụp lại nhé.');
    expect(c.status, ReaderStatus.error);
    expect(await c.primaryAction(), isTrue, reason: 'sau lỗi phải chụp lại được');
  });

  test('đang gửi: không gửi trùng, chạm thì báo chờ, có âm chờ và lời nhắc', () async {
    api.gate = Completer<void>();
    final first = c.describe(image);
    await Future<void>.delayed(const Duration(milliseconds: 60));

    expect(c.status, ReaderStatus.sending);
    await c.describe(image);
    expect(api.describeCalls, 1);
    expect(await c.primaryAction(), isFalse);
    expect(speaker.spoken, contains(S.stillWorking));
    expect(earcons.played, contains(Earcon.waiting));

    api.gate!.complete();
    await first;
    expect(c.status, ReaderStatus.idle);
  });

  test('đang nói mà chạm: dừng đọc, không chụp', () async {
    // Mọi câu nói bị giữ lại (giả lập mô tả dài đang được đọc).
    speaker.hold = Completer<void>();
    unawaited(c.describe(image));
    await Future<void>.delayed(const Duration(milliseconds: 20));
    expect(c.status, ReaderStatus.speaking);
    expect(speaker.spoken.last, 'Trang có một lược đồ.');

    expect(await c.primaryAction(), isFalse);
    expect(speaker.stops, greaterThan(0));
    expect(c.status, ReaderStatus.idle);
  });

  test('đọc lại khi chưa chụp gì', () async {
    await c.repeat();
    expect(speaker.spoken.single, S.nothingToRepeat);
  });

  test('đọc lại mô tả gần nhất', () async {
    await c.describe(image);
    speaker.spoken.clear();
    await c.repeat();
    expect(speaker.spoken.single, 'Trang có một lược đồ.');
  });

  test('đọc từng câu: mỗi câu một lần nói, xong thì bỏ tô vàng', () async {
    api.next = FakeApi.ok(description: 'Câu một. Câu hai? Câu ba!');
    final seen = <int>[];
    c.addListener(() => seen.add(c.sentenceIndex));
    await c.describe(image);
    expect(speaker.spoken.sublist(1), ['Câu một.', 'Câu hai?', 'Câu ba!']);
    expect(c.pageSentences.length, 3);
    expect(seen, containsAllInOrder([0, 1, 2]));
    expect(c.sentenceIndex, -1);
    expect(c.readingId, ReaderController.pageId);
  });

  test('chạm khi đang đọc (announce): dừng ngay, không đọc tiếp câu sau', () async {
    api.next = FakeApi.ok(description: 'Câu một. Câu hai.');
    speaker.hold = Completer<void>();
    unawaited(c.describe(image));
    await Future<void>.delayed(const Duration(milliseconds: 20));
    expect(speaker.spoken.last, 'Câu một.');
    final h = speaker.hold!;
    speaker.hold = null;
    await c.announce('Đọc lại.');
    h.complete();
    await Future<void>.delayed(const Duration(milliseconds: 20));
    expect(speaker.spoken.last, 'Đọc lại.');
    expect(speaker.spoken, isNot(contains('Câu hai.')));
    expect(c.status, ReaderStatus.idle);
  });

  test('hỏi tiếp: gửi image_id và lịch sử, đọc câu trả lời', () async {
    await c.describe(image);
    await c.ask('Hình có gì?');
    expect(api.lastAskImageId, 'b9b1d4985e464bbb');
    expect(api.lastHistory, isEmpty);
    expect(speaker.spoken.last, 'Trả lời.');
    await c.ask('Còn gì nữa?');
    expect(api.lastHistory.single.question, 'Hình có gì?');
    expect(c.turns.length, 2);
  });

  test('hỏi khi chưa chụp: nhắc chụp trước, không gọi máy chủ', () async {
    await c.ask('Hình có gì?');
    expect(api.lastQuestion, isNull);
    expect(speaker.spoken.single, S.askNeedPage);
    expect(earcons.played.single, Earcon.error);
  });

  test('hỏi lỗi: đọc câu lỗi, lỗi thuộc phần câu trả lời (màn hình chụp không hiện lỗi)', () async {
    await c.describe(image);
    api.nextAsk = const ApiFail('NETWORK', 'Mất mạng.');
    await c.ask('Hình có gì?');
    expect(speaker.spoken.last, 'Mất mạng.');
    expect(c.status, ReaderStatus.error);
    expect(c.errorScope, ReaderController.answerId);
  });

  test('tách câu tiếng Việt', () {
    expect(splitSentences('Trang 42. Có hình vẽ… Hết!\nDòng mới'), ['Trang 42.', 'Có hình vẽ…', 'Hết!', 'Dòng mới']);
    expect(splitSentences('Số 3.5 giữ nguyên.'), ['Số 3.5 giữ nguyên.']);
    expect(splitSentences('   '), isEmpty);
  });
}
