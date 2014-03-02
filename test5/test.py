
def abbreviate_name():
    """
    abc
    """

    # split full name into invididual names
    full_name = 'foo bar'
    names = full_name.split()
    abbrev_name = ""

    for index , name in enumerate(names):
        if index == 0:
            abbrev_name += name + " "
        else:
            abbrev_name += name[0] + ". "

