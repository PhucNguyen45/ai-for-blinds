import 'dart:async';

import 'package:flutter/material.dart';

import '../app_services.dart';
import '../library/library_data.dart';
import '../reader/reader_controller.dart';
import '../strings.dart';
import 'explore.dart';
import 'theme.dart';
import 'widgets.dart';

Color _bookColor(String key) => switch (key) {
  'ask' => AppTheme.ask,
  'guide' => AppTheme.guide,
  _ => AppTheme.lib,
};

/// Thư viện sách đã số hóa (hiện là BẢN MẪU đóng gói trong app, xem `assets/library/`).
class LibraryScreen extends StatefulWidget {
  const LibraryScreen({super.key, required this.services});
  final AppServices services;

  @override
  State<LibraryScreen> createState() => _LibraryScreenState();
}

class _LibraryScreenState extends State<LibraryScreen> {
  late final Future<List<Book>> _books = widget.services.library.load();
  ReaderController get _c => widget.services.controller;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _c.announce(S.libraryOpen));
  }

  Future<void> _back() async {
    await _c.stopSpeaking();
    if (mounted) Navigator.of(context).pop();
  }

  Future<void> _open(Book book) async {
    await _c.stopSpeaking();
    if (!mounted) return;
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => BookScreen(services: widget.services, book: book),
      ),
    );
    if (mounted) await _c.announce(S.libraryOpen);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: ExploreScope(
        feedback: widget.services,
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(8, 6, 8, 8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                ScreenHeader(
                  title: S.library,
                  intro: S.libraryOpen,
                  badge: S.sampleBadge,
                  onIntro: () => _c.announce(S.libraryOpen),
                ),
                const SizedBox(height: 6),
                Expanded(
                  child: FutureBuilder<List<Book>>(
                    future: _books,
                    builder: (context, snap) {
                      final books = snap.data ?? const <Book>[];
                      if (snap.connectionState != ConnectionState.done) {
                        return const Center(child: CircularProgressIndicator(color: AppTheme.guide));
                      }
                      if (books.isEmpty) {
                        return const Center(
                          child: Text(S.libraryEmpty, style: TextStyle(fontSize: 20, color: AppTheme.mute)),
                        );
                      }
                      return Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          for (final b in books)
                            SizedBox(
                              height: 150,
                              child: _BookCard(book: b, onOpen: () => _open(b)),
                            ),
                          // Ghi chú bản mẫu ở đáy phần trống; màn hình chật thì bị cắt bớt, không tràn.
                          const Expanded(
                            child: ClipRect(
                              child: Align(
                                alignment: Alignment.bottomCenter,
                                child: Padding(
                                  padding: EdgeInsets.fromLTRB(10, 8, 10, 10),
                                  child: Text(
                                    S.libraryNote,
                                    textAlign: TextAlign.center,
                                    style: TextStyle(fontSize: 15, height: 1.4, color: AppTheme.mute),
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ],
                      );
                    },
                  ),
                ),
                BackBar(onActivate: _back),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// Thẻ sách: bìa màu có biểu tượng, tên sách lớn, số trang.
class _BookCard extends StatelessWidget {
  const _BookCard({required this.book, required this.onOpen});
  final Book book;
  final VoidCallback onOpen;

  @override
  Widget build(BuildContext context) {
    final color = _bookColor(book.color);
    return ExploreTarget(
      label: book.title,
      spoken: '${book.title}. ${book.pages.length} trang. ${S.openHint}',
      onActivate: onOpen,
      builder: (context, focused) => FocusFrame(
        focused: focused,
        child: Container(
          decoration: BoxDecoration(
            color: AppTheme.surfaceHigh,
            borderRadius: BorderRadius.circular(AppTheme.radius),
            border: Border.all(color: AppTheme.line, width: 1.5),
          ),
          clipBehavior: Clip.antiAlias,
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Container(
                width: 92,
                color: color,
                child: Stack(
                  children: [
                    Positioned(
                      left: 10,
                      top: 0,
                      bottom: 0,
                      child: Container(width: 3, color: AppTheme.ink.withValues(alpha: 0.18)),
                    ),
                    const Center(child: Icon(Icons.auto_stories_rounded, size: 40, color: AppTheme.ink)),
                  ],
                ),
              ),
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(16, 10, 8, 10),
                  child: LayoutBuilder(
                    builder: (context, box) => FittedBox(
                      fit: BoxFit.scaleDown,
                      alignment: Alignment.centerLeft,
                      child: SizedBox(
                        width: box.maxWidth,
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              book.title,
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(
                                fontSize: 21,
                                height: 1.2,
                                fontWeight: FontWeight.w800,
                                color: AppTheme.paper,
                              ),
                            ),
                            const SizedBox(height: 6),
                            Text(book.subtitle, style: const TextStyle(fontSize: 15, color: AppTheme.mute)),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
              ),
              const Padding(
                padding: EdgeInsets.only(right: 10),
                child: Icon(Icons.chevron_right_rounded, size: 30, color: AppTheme.mute),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Đọc một cuốn sách: trang hiện tại ở giữa, ba nút Trang trước / Đọc trang / Trang sau, Quay lại ở mép dưới.
class BookScreen extends StatefulWidget {
  const BookScreen({super.key, required this.services, required this.book});
  final AppServices services;
  final Book book;

  static const readingId = 'book';

  @override
  State<BookScreen> createState() => _BookScreenState();
}

class _BookScreenState extends State<BookScreen> {
  int _index = 0;
  ReaderController get _c => widget.services.controller;
  BookPage get _page => widget.book.pages[_index];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _read(withTitle: true));
  }

  String _pageIntro() => 'Trang ${_page.number}. ${_page.title}.';

  Future<void> _read({bool withTitle = false}) => _c.readText(
    _page.text,
    id: BookScreen.readingId,
    intro: withTitle ? '${widget.book.title}. ${_pageIntro()}' : _pageIntro(),
  );

  Future<void> _go(int delta) async {
    final next = _index + delta;
    if (next < 0) return _c.announce(S.firstPage);
    if (next >= widget.book.pages.length) return _c.announce(S.lastPage);
    setState(() => _index = next);
    await _read();
  }

  Future<void> _back() async {
    await _c.stopSpeaking();
    if (mounted) Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    final b = widget.book;
    return Scaffold(
      body: ExploreScope(
        feedback: widget.services,
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(8, 6, 8, 8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                ScreenHeader(
                  title: b.title,
                  intro: '${b.title}. ${_pageIntro()} Trang ${_index + 1} trên ${b.pages.length}.',
                  badge: '${_index + 1}/${b.pages.length}',
                  onIntro: () => _read(withTitle: true),
                ),
                Expanded(child: _pageTarget()),
                SizedBox(
                  height: 104,
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Expanded(
                        child: _NavTile(
                          label: S.prevPage,
                          icon: Icons.chevron_left_rounded,
                          color: AppTheme.surfaceHigh,
                          onActivate: () => unawaited(_go(-1)),
                        ),
                      ),
                      Expanded(
                        child: _NavTile(
                          label: S.readPage,
                          icon: Icons.play_arrow_rounded,
                          color: AppTheme.guide,
                          onActivate: () => unawaited(_read()),
                        ),
                      ),
                      Expanded(
                        child: _NavTile(
                          label: S.nextPage,
                          icon: Icons.chevron_right_rounded,
                          color: AppTheme.surfaceHigh,
                          onActivate: () => unawaited(_go(1)),
                        ),
                      ),
                    ],
                  ),
                ),
                BackBar(onActivate: _back),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _pageTarget() {
    return ListenableBuilder(
      listenable: _c,
      builder: (context, _) => ExploreTarget(
        label: 'Trang ${_page.number}',
        spoken: '${_pageIntro()} Chạm hai lần để nghe.',
        onActivate: () => unawaited(_read()),
        builder: (context, focused) => FocusFrame(
          focused: focused,
          radius: 26,
          child: Container(
            decoration: BoxDecoration(
              color: AppTheme.surface,
              borderRadius: BorderRadius.circular(26),
              border: Border.all(color: AppTheme.line, width: 1.5),
            ),
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  children: [
                    Container(
                      width: 8,
                      height: 40,
                      decoration: BoxDecoration(
                        color: _bookColor(widget.book.color),
                        borderRadius: BorderRadius.circular(4),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Trang ${_page.number}',
                            style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppTheme.mute),
                          ),
                          Text(
                            _page.title,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w800, color: AppTheme.paper),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 12),
                  child: Divider(height: 1, color: AppTheme.line),
                ),
                Expanded(
                  child: ReadingText(
                    sentences: splitSentences(_page.text),
                    active: _c.readingId == BookScreen.readingId ? _c.sentenceIndex : -1,
                    fontSize: 21,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _NavTile extends StatelessWidget {
  const _NavTile({required this.label, required this.icon, required this.color, required this.onActivate});
  final String label;
  final IconData icon;
  final Color color;
  final VoidCallback onActivate;

  @override
  Widget build(BuildContext context) {
    final fg = color == AppTheme.guide ? AppTheme.ink : AppTheme.paper;
    return ExploreTarget(
      label: label,
      spoken: '$label. Chạm hai lần.',
      onActivate: onActivate,
      builder: (context, focused) => FocusFrame(
        focused: focused,
        child: Container(
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(AppTheme.radius),
            border: color == AppTheme.guide ? null : Border.all(color: AppTheme.line, width: 1.5),
          ),
          child: Center(
            child: FittedBox(
              fit: BoxFit.scaleDown,
              child: Padding(
                padding: const EdgeInsets.all(6),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(icon, size: 34, color: fg),
                    Text(
                      label,
                      style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800, color: fg),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
