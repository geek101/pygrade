
import time


def abbreviate_name(abc, abc1,\
                ):
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

    while True:
        time.sleep(1)



