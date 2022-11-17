from pytermgui import Window

&from pytermgui import WindowManager

window = Window("This is my test window")
window.set_title("[surface+2]Welcome to the docs!")
&with WindowManager() as manager:
&  manager.layout.add_slot()
&  manager.add(window)
