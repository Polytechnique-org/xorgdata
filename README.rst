xorgdata
========

.. image:: https://secure.travis-ci.org/Polytechnique-org/xorgdata.png?branch=master
    :target: http://travis-ci.org/Polytechnique-org/xorgdata/

xorgdata handles the central data store for Polytechnique.org services.
It pulls data from AX's website and pushes it to Polytechnique.org's services.

.. note::

    This is currently a work in progress.

Development environment
-----------------------

Here are some commands to set up a development environment:

.. code-block:: sh

    # Create a new virtual env
    pew new xorgdata

    # Install dependencies
    make update

    # Create a development database
    make createdb

    # Fill the development database with some test data
    python manage.py importcsv tests/files/exportusers-afbo-Polytechnique-X-20010203.csv
    python manage.py importcsv tests/files/exportuserdegrees-afbo-Polytechnique-X-20010203.csv
    python manage.py importcsv tests/files/exportuserjobs-afbo-Polytechnique-X-20010203.csv
    python manage.py importcsv tests/files/exportgroups-afbo-Polytechnique-X-20010203.csv
    python manage.py importcsv tests/files/exportgroupmembers-afbo-Polytechnique-X-20010203.csv

    # Create a superuser to access the database through Django /admin web interface
    python manage.py createsuperuser

Custom Django management commands
---------------------------------

This project uses the following custom commands:

* `manage.py importcsv file.csv`: import a file that is provided by AX's contractor (AlumnForce).
  Such a file consists in an incremental update of the alumni directory.
* `manage.py afsync --push-export`: fetch and import incremental updates from AlumnForce's server. If successful, export the imported data to xorgauth.
  This command is suited to be run in a scheduled task (aka. a cron job).
* `manage.py importallusers file.csv`: import a file that has been exported from AX's website (https://ax.polytechnique.org).
  Such a file contains data for all the users of the directory.
