def abbreviate_name(full_name):
    """
    abc
    """

    # split full name into invididual names
    names = full_name.split()
    abbrev_name = ""
    abc = 10
    bcd = 50

    for index , name in enumerate(names):
        if index == 0:
            abbrev_name += name + " "
        else:
            abbrev_name += name[0] + ". "

    return abbrev_name
