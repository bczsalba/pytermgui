import pytermgui as ptg
import shutil  # For terminal size check


def button_press(manager: ptg.WindowManager) -> None:
    modal = container.select(7)

container = ptg.Container()

# Add buttons and calculate total height
total_height = 0
for i in range(70):
    button = ptg.Button(f"BUTTON {i+1}")
    container.lazy_add(button)

    # Calculate total height of the container
    if hasattr(button, "size"):
        size = button.size
        if isinstance(size, tuple):
            total_height += size[1]  # Assuming size[1] is height
        elif isinstance(size, int):
            total_height += size
        else:
            total_height += 1  # Default fallback

# Check terminal height
terminal_height = shutil.get_terminal_size().lines
print(f"Terminal height: {terminal_height}")
print(f"Container height: {total_height}")

# Raise error if container height exceeds terminal height
if total_height > terminal_height:
    raise ValueError(
        f"Container height ({total_height}) exceeds terminal height ({terminal_height})"
    )

window = ptg.Window(container)

with ptg.WindowManager() as manager:
    manager.layout.add_slot("Body")
    manager.add(window)
