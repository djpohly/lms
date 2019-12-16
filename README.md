# lms

Command line interface for Schoology, using [Click](https://click.palletsprojects.com).


## Configuration

Configuration for `lms` lives in `$XDG_CONFIG_HOME/lms.conf`.  This is
(currently) an INI-style file read by the Python
[configparser](https://docs.python.org/3/library/configparser.html)
module.  Example, with documentation:

````ini
# Overall configuration options go in the lms section
[lms]
# Which LMS to use
# Options: schoology
backend = schoology

# Backend-specific options for Schoology
[schoology]
# Consumer key and secret for OAuth authentication
# Obtain these from https://schoology.myschool.edu/api
key = 31415926535897932384626433832795028841971
secret = 31415926535897932384626433832795
````


## Things I would like to be able to do

  - Easily upload files (such as in-class programming examples) directly from the command line
  - Enter grades in bulk


## Miscellaneous ideas

  - Create more robust "backend" interface to make it easy to support for other learning management systems.
  - Full-screen TUI so you can manage your classroom like it's 1989
    - Option to update display at 300 baud for added realism
