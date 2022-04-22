import time
import pytermgui as ptg
from dataclasses import dataclass


@dataclass
class MyAnimatedObject:
    attr: int

    def __str__(self):
        return f"({self.attr}, {id(self)})"


looped = ptg.animator.animate_float(duration=100, loop=True)
backward = ptg.animator.animate_float(
    duration=100,
    direction=-1,
    on_finish=lambda anim: {
        setattr(anim, "_remaining", anim.duration),
        ptg.animator.schedule(anim),
    },
)
forward = ptg.animator.animate_float(
    duration=100,
    direction=1,
    on_finish=lambda anim: {
        setattr(anim, "_remaining", anim.duration),
        ptg.animator.schedule(anim),
    },
)

obj = MyAnimatedObject(0)
obj2 = MyAnimatedObject(1000)

attr_forward = ptg.animator.animate_attr(
    target=obj, attr="attr", end=1000, duration=1000
)

attr_backward = ptg.animator.animate_attr(
    target=obj2, attr="attr", end=0, duration=1000
)

counter = 0
while True:
    if counter >= 1.0:
        counter = 0

    print(f"\x1b[KLOOPED:     {looped.direction} {looped.state!r}")
    print(f"\x1b[KBACKWARD:   {backward.direction} {backward.state!r}")
    print(f"\x1b[KBACKWARD:   {forward.direction} {forward.state!r}")
    print(f"\x1b[KATTR_FORE:  {attr_forward.direction} {attr_forward.state} {obj}")
    print(f"\x1b[KATTR_BACK:  {attr_backward.direction} {attr_backward.state} {obj2}")
    print(f"\x1b[6A")

    ptg.animator.step(0.001)
    time.sleep(0.001)
