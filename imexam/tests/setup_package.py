def get_package_data():
    return {_ASTROPY_PACKAGE_NAME_ + '.tests': ['coveragerc']}  # noqa


def requires_2to3():
    return False
