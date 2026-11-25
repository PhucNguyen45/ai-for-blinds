import 'package:flutter/material.dart';

/// Lớp thao tác "chạm để nghe, chạm hai lần để dùng" cho người không nhìn,
/// chạy được cả khi KHÔNG bật TalkBack:
///
/// - chạm một lần vào nút: nghe tên nút (kèm tiếng tách và rung nhẹ), nút được viền trắng;
/// - chạm hai lần liền vào cùng nút: dùng nút đó;
/// - giữ và rê ngón tay: đi qua nút nào nghe tên nút đó.
///
/// Khi máy đã bật TalkBack (`MediaQuery.accessibleNavigation`), lớp này tự tắt:
/// nút trở thành nút thường có nhãn, TalkBack lo việc đọc tên và chạm hai lần,
/// để không bao giờ có hai giọng đọc chồng nhau (yêu cầu UI-16).
abstract class ExploreFeedback {
  /// Chạm một lần / rê tới một nút: phát âm, rung, đọc [spoken].
  void onFocus(String spoken);

  /// Chạm hai lần: phát âm và rung xác nhận (việc của nút do nút tự làm).
  void onActivate();
}

class ExploreScope extends StatefulWidget {
  const ExploreScope({
    super.key,
    required this.feedback,
    required this.child,
    this.doubleTapWindow = const Duration(milliseconds: 500),
  });

  final ExploreFeedback feedback;
  final Widget child;

  /// Hai lần chạm cách nhau không quá khoảng này thì tính là chạm hai lần.
  /// Rộng hơn TalkBack (khoảng 300 ms) cho học sinh nhỏ tuổi.
  final Duration doubleTapWindow;

  static ExploreScopeState? maybeOf(BuildContext context) =>
      context.dependOnInheritedWidgetOfExactType<_ExploreInherited>()?.state;

  @override
  State<ExploreScope> createState() => ExploreScopeState();
}

class ExploreScopeState extends State<ExploreScope> {
  final _targets = <ExploreTargetState>{};

  /// Nút đang được chọn (đã nghe tên, chờ chạm lần hai).
  final ValueNotifier<ExploreTargetState?> focused = ValueNotifier(null);

  ExploreTargetState? _lastTap;
  Duration? _lastTapTime;
  int? _pointer;
  bool _enabled = true;

  /// `false` khi TalkBack đang bật.
  bool get enabled => _enabled;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _enabled = !MediaQuery.accessibleNavigationOf(context);
    if (!_enabled) _reset();
  }

  @override
  void dispose() {
    focused.dispose();
    super.dispose();
  }

  void _register(ExploreTargetState t) => _targets.add(t);

  void _unregister(ExploreTargetState t) {
    _targets.remove(t);
    if (identical(focused.value, t)) focused.value = null;
    if (identical(_lastTap, t)) _lastTap = null;
  }

  /// Bỏ chọn (sau khi chụp bằng nút âm lượng, khi chuyển màn hình): viền cũ không còn đúng nữa.
  void clearFocus() {
    focused.value = null;
    _lastTap = null;
    _lastTapTime = null;
  }

  void _reset() {
    focused.value = null;
    _lastTap = null;
    _lastTapTime = null;
    _pointer = null;
  }

  /// Nút nhỏ nhất chứa điểm chạm (nút lồng trong vùng lớn thì ưu tiên nút).
  ExploreTargetState? _hit(Offset global) {
    ExploreTargetState? best;
    var bestArea = double.infinity;
    for (final t in _targets) {
      final r = t.globalRect;
      if (r == null || !r.contains(global)) continue;
      final area = r.width * r.height;
      if (area < bestArea) {
        best = t;
        bestArea = area;
      }
    }
    return best;
  }

  void _down(PointerDownEvent e) {
    if (!_enabled || _pointer != null) return;
    _pointer = e.pointer;
    final t = _hit(e.position);
    if (t == null) return;
    final last = _lastTapTime;
    if (identical(t, _lastTap) && last != null && e.timeStamp - last <= widget.doubleTapWindow) {
      _lastTap = null;
      _lastTapTime = null;
      _activate(t);
    } else {
      _lastTap = t;
      _lastTapTime = e.timeStamp;
      _focus(t);
    }
  }

  void _move(PointerMoveEvent e) {
    if (!_enabled || e.pointer != _pointer) return;
    final t = _hit(e.position);
    if (t != null && !identical(t, focused.value)) {
      // Rê tới nút mới: nghe tên; chạm hai lần sau đó mới dùng.
      _lastTap = null;
      _lastTapTime = null;
      _focus(t);
    }
  }

  void _up(PointerEvent e) {
    if (e.pointer == _pointer) _pointer = null;
  }

  void _focus(ExploreTargetState t) {
    focused.value = t;
    widget.feedback.onFocus(t.widget.spoken ?? t.widget.label);
  }

  void _activate(ExploreTargetState t) {
    focused.value = null;
    widget.feedback.onActivate();
    t.widget.onActivate();
  }

  @override
  Widget build(BuildContext context) {
    return _ExploreInherited(
      state: this,
      child: Listener(
        behavior: HitTestBehavior.translucent,
        onPointerDown: _down,
        onPointerMove: _move,
        onPointerUp: _up,
        onPointerCancel: _up,
        child: widget.child,
      ),
    );
  }
}

class _ExploreInherited extends InheritedWidget {
  const _ExploreInherited({required this.state, required super.child});
  final ExploreScopeState state;

  @override
  bool updateShouldNotify(_ExploreInherited old) => old.state != state;
}

/// Một nút trong lớp thao tác. [builder] nhận `focused` để vẽ viền chọn.
class ExploreTarget extends StatefulWidget {
  const ExploreTarget({
    super.key,
    required this.label,
    required this.onActivate,
    required this.builder,
    this.spoken,
    this.hint,
  });

  /// Nhãn ngắn cho TalkBack (yêu cầu UI-20).
  final String label;

  /// Câu app tự đọc khi chạm một lần; mặc định là [label].
  final String? spoken;

  /// Gợi ý TalkBack đọc sau nhãn.
  final String? hint;
  final VoidCallback onActivate;
  final Widget Function(BuildContext context, bool focused) builder;

  @override
  State<ExploreTarget> createState() => ExploreTargetState();
}

class ExploreTargetState extends State<ExploreTarget> {
  ExploreScopeState? _scope;

  Rect? get globalRect {
    final box = context.findRenderObject();
    if (box is! RenderBox || !box.attached || !box.hasSize) return null;
    return box.localToGlobal(Offset.zero) & box.size;
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final s = ExploreScope.maybeOf(context);
    if (!identical(s, _scope)) {
      _scope?._unregister(this);
      _scope = s;
      s?._register(this);
    }
  }

  @override
  void dispose() {
    _scope?._unregister(this);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final scope = _scope;
    final talkBack = MediaQuery.accessibleNavigationOf(context);
    Widget child = scope == null
        ? widget.builder(context, false)
        : ValueListenableBuilder<ExploreTargetState?>(
            valueListenable: scope.focused,
            builder: (context, f, _) => widget.builder(context, identical(f, this)),
          );
    // Không có lớp thao tác hoặc TalkBack đang bật: nút thường, chạm (TalkBack: chạm hai lần) là dùng.
    if (scope == null || talkBack) {
      child = GestureDetector(behavior: HitTestBehavior.opaque, onTap: widget.onActivate, child: child);
    }
    return Semantics(
      container: true,
      button: true,
      label: widget.label,
      hint: widget.hint,
      onTap: widget.onActivate,
      excludeSemantics: true,
      child: child,
    );
  }
}
