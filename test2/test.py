def abbreviate_name(full_name, abc):
    """
    abc
    """

    # split full name into invididual names
    names = full_name.split()
    abbrev_name = ""
    bcd = abc + 1

    for index , name in enumerate(names):
        if index == 0:
            abbrev_name += name + " "
        else:
            abbrev_name += name[0] + ". "

    return abc
