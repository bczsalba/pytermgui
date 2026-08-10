from pytermgui import tim

tim.alias("my-tag1", "@surface primary+1")

# Recursive tags also work!
tim.alias("my-tag2", "my-tag1 italic")

tim.print(
    "[my-tag1]My first tag\n\n"
    + "[/my-tag1]By default, aliases generate an unsetter\n\n"
    + "[my-tag2]My second tag"
)
