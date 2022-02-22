# Version 3.0.0

This version mostly focused on improving already built features,
but there is a lot of important additions as well.

The most notable new change would probably be the `PixelMatrix`
classes. These allow you to display an arbitrary matrix of pixels
as a widget. `DensePixelMatrix` scales the entire widget down by
a factor of 4 (in normal `PixelMatrix`, every pixel is made up of
2 block characters. In `DensePixelMatrix` all pixels make up only
half a block.

This would normally not constitute for a major release, however the
`Slider` refactor forced our hand. Some parts of its API have changed,
though mostly for the better.

> Items marked in bold are API breaking changes.

## Refactors
- **Refactor `Slider` widget** (788a709e2a3326fb725bf8600aa3d208a12b5874, #9)
- Update `Button` default chars (f370deaedd88f52c5008fcfe0a5ff1ae7efdf2c9)
- Change `WindowManager.framerate` 120 -> 60 (320d65c1c6988a727e724674d7dd16da0d8dcc5c)


## Additions
- Add `MarkupLanguage.prettify_markup` (d6733f5dc02817e8be1cadde17f2bb9ee94a4b94)
- Add `WindowManager.nullify_cache` & `Window.nullify_cache` (814d2055e89e40256fea1e9f9e7d7347b697c0f7)
- Add `!link` markup macro (0c05080928a5e9a6e65ba3d4148e0b794b556852)
- Add `StyledText` class (be2f5dec466d84458e376af5ea7e428920733247)
- Add `ColorPicker` widget, CLI app (5a09f43b950414e231ac0ebf85f5db17499d3785, 45b6d02d46c3eea30b2c4cabb96cd08cff3f688a)
- Add `PixelMatrix` & `LargePixelMatrix` widgets (84312c16a399c9e58c070c04d23d397610895aca)


## Bugfixes
- Fix selection lingering after mouse event (2a0b79b720c8a1522a66a92d611fdfa95276301b)
- Fix Right-click release events being misdetected (1b7b69a55a6c006991f333f266757b1a3d153f4a)
- Fix `Window._auto_min_width` disregarding sidelength (8b51ff0822f8e471f55bfeb1186fb8659cfd543f)
- Fix incorrect behaviour in `Container._update_width` (363093aa3812bad4bb92250c7900a0f9d7258f80)


