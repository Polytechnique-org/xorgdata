xorgdata
========

.. image:: https://secure.travis-ci.org/Polytechnique-org/xorgdata.png?branch=master
    :target: http://travis-ci.org/Polytechnique-org/xorgdata/

xorgdata handles the central data store for Polytechnique.org services


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
