from setuptools import setup

setup(
    name='lms',
    version='0.1',
    py_modules=['main'],
    install_requires=[
        'Click',
        'click_repl',
        'schoolopy',
        'xdg',
        'cached_property',
    ],
    entry_points='''
        [console_scripts]
        lms=main:cli
    ''',
)
