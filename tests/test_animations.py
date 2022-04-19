import pytest

import pytermgui as ptg
from pytermgui.animations import _remove_flag, Animation, Direction


class MyTarget:
    test_attr: int = 5


def _reset():
    ptg.animator._animations = []


def test_flags():
    target = MyTarget()

    with pytest.raises(ValueError):
        _remove_flag(target, "nothing")

    animation = ptg.animator.animate_attr(target=target, attr="test_attr", duration=100)

    assert hasattr(target, "__ptg_animated__")
    assert "test_attr" in target.__ptg_animated__

    animation.finish()
    assert not hasattr(target, "__ptg_animated__")


def test_is_animated():
    target = MyTarget()

    assert not ptg.is_animated(target, "test_attr")

    ptg.animator.animate_attr(target=target, attr="test_attr", duration=100)

    assert ptg.is_animated(target, "test_attr")


def test_animate_float():
    _reset()

    elapsed = 0
    animation = ptg.animator.animate_float(duration=1000, direction=-1)

    print(ptg.animator._animations)
    for _ in range(10):
        elapsed += 0.1
        ptg.animator.step(0.1)
        assert round(animation.state, 4) == round(1 - elapsed, 4)


def test_animate_attr():
    _reset()

    target = MyTarget()
    ptg.animator.animate_attr(
        target=target, attr="test_attr", start=0, end=10, duration=1000
    )

    for i in range(1, 10):
        ptg.animator.step(0.1)
        assert target.test_attr == i


def test_animate_attr_manual_step():
    target = MyTarget()

    animation = ptg.animator.animate_attr(
        target=target, attr="test_attr", start=0, end=10, duration=100, direction=-1
    )

    for i in range(1, 10):
        animation.step(0.1)


def test_animator_not_active():
    _reset()

    assert not ptg.animator.is_active

    ptg.animator.animate_float(duration=100)
    assert ptg.animator.is_active


def test_animation_finishes_on_step():
    _reset()

    def _on_step(anim: Animation) -> bool:
        return anim.direction == Direction.BACKWARD

    ptg.animator.schedule(
        Animation(
            duration=100,
            direction=Direction.FORWARD,
            loop=True,
            state=0.0,
            _remaining=0,
            on_step=_on_step,
            on_finish=lambda _: None,
        )
    )

    ptg.animator.animate_attr(
        target=MyTarget(),
        attr="test_attr",
        duration=1000,
        loop=True,
        on_step=_on_step,
        on_finish=lambda _: None,
    )

    ptg.animator.step(1)
    assert not ptg.animator.is_active
