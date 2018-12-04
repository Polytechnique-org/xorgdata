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

    # Create a superuser to access the database through Django /admin web interface
    python manage.py createsuperuser
