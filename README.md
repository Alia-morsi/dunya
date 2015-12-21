The CompMusic Browser
=====================

Introduction
------------
Dunya is a prototype being developed in the context of CompMusic, a
research project that studies several world music traditions from the
point of view of the information technologies, with the aim to
facilitate the cataloging and discovery of music recordings within
large repositories. For more information: http://compmusic.upf.edu

License
=======
Dunya is Copyright 2013 Music Technology Group - Universitat Pompeu Fabra

Dunya is released under the terms of the GNU Affero General Public
License (v3 or later). See the COPYING file for more information.

If you would prefer to get a (non FOSS) commercial license, please
contact us at mtg@upf.edu

Installation
============

On ubuntu-like machines you can run `bash setup.sh` to install dependencies from
apt, create symlinks into the python environment, and install all python packages.
Otherwise, read on

Dependencies
------------

    sudo apt-get install python-numpy python-scipy python-matplotlib libsndfile1-dev lame libjpeg8-dev

* Create a virtualenv

        virtualenv --no-site-packages env
        source env/bin/activate
        pip install --upgrade distribute
        pip install -r requirements

* Also install essentia + python libraries

We install essentia into the virtualenv that we created for python. This lets the automatic celery jobs upgrade essentia
when we make changes to it without needing root.

        git clone git@github.com:CompMusic/essentia.git
        cd essentia
        git checkout -t origin/deploy
        sudo apt-get install build-essential libyaml-dev libfftw3-dev libavcodec-dev libavformat-dev python-dev libsamplerate0-dev libtag1-dev python-numpy-dev python-numpy
        ./waf configure --mode=release --with-python --prefix=/srv/dunya/env
        ./waf
        sudo ./waf install

* Using essentia, numpy, and scipy in virtualenv

        ln -s /usr/local/lib/python2.7/dist-packages/essentia/ env/lib/python2.7/site-packages
        ln -s /usr/lib/python2.7/dist-packages/numpy* env/lib/python2.7/site-packages
        ln -s /usr/lib/python2.7/dist-packages/scipy* env/lib/python2.7/site-packages

* Installing Pillow with jpeg support

        sudo apt-get install libjpeg8-dev
        ln -s /usr/lib/x86_64-linux-gnu/libjpeg.so* env/lib
        ln -s /usr/lib/x86_64-linux-gnu/libz.so* env/lib
        ln -s /usr/lib/x86_64-linux-gnu/libfreetype.so* env/lib
        pip install pillow

* If you install matplotlib with apt:

        pip install python-dateutil
        ln -s /usr/lib/pymodules/python2.7/matplotlib* env/lib/python2.7/site-packages/
        ln -s /usr/lib/pymodules/python2.7/pylab* env/lib/python2.7/site-packages/

Database
--------

Copy the file `dunya/local_settings.py.dist` to `dunya/local_settings.py` and
edit it to point to your database. We currently use postgres for its
unaccent support.

Create the database:

    createdb dunya

and also create the unaccent extension:

    echo 'create extension unaccent;' | psql dunya

To add tables to the database run

    fab setupdb

Alternatively, you may want to create a postgres dump, since the django json dump
is over 500mb. Set up postgres and run

    # on the server
    pg_dump -O dunya > dunya_pg.sql

    # on the new machine
    psql dunya < dunya_pg.sql

Where `dunya` is the name of the database

* If you want to manually add data to an empty database, follow these steps:
    1.  To setup and configure your database, run:
            fab setupdb

    2.  Inside your database, add a row to the `django_site` table:
        Example:
            id |         domain          |            name
            1  | dunya.compmusic.upf.edu | dunya.compmusic.upf.edu

    3.  You need to have a collection of albums and audio files somewhere on your drive.
        You will need to enter the path to this folder. You can download sample collections
        from one of 'kora' if you have access to it.

    4.  Assuming you have a MusicBrainz account, create a public collection and make
        sure the name contains the name of the music style that the collection is
        related to. For example, for Carnatic style the word 'carnatic' should be included
        somewhere in the collection name (ie 'carnatic_coll_23423')
        Add the releases for which you have a copy (step 3) into this collection.

    5. Run the development server and direct your browser to localhost:XXXX/dashboard

    6. Enter the corresponding data for the 'add collection' form.
        - You can retrieve the collection id from the link of the page
            (http://musicbrainz.org/collection/{collection_id})
       Note:
        At the moment, if you are adding a collection for Carnatic style, you can choose
        all the checkers except the ones containing Makam.

    7. Click on Submit.

Updating file locations
-----------------------

Dunya has files in 3 locations:

* Audio files
* Derived files (images, wav files, features)
* Media files (see below section)

The database stores the location of all files in docserver. If you copied audio and
derived files from the server then you need to update the location. Run

    python manage.py moveaudiodata <collectionid> <audiodir>

where `collectionid` is the musicbrainz id of the collection and `audiodir` is the
location where the audio now lives.
This takes a while (For just carnatic we have close to 1.5m rows to update). In the
future we may suggest a method that accesses the database directly instead of
using django.

Media files (entity images)
---------------------------

On the server, these files are stored in `/mnt/compmusic/compmusicweb/dunya`.
You need to copy the directory to the `MEDIA_ROOT` location in `local_settings.py`

Rabbitmq
--------

This is not needed if you don't want to use the extractors.

We use rabbitmq for sending job commands to workers. On the server you will need to run
(password values aren't important)

    rabbitmqctl add_user dunyauser dunyapassword
    rabbitmqctl add_vhost CompMusic
    rabbitmqctl set_permissions -p CompMusic dunyauser ".*" ".*" ".*"

* Rabbitmq configuration

In `dunya/local_settings.py` you will need to add connection details:

    BROKER_URL = 'amqp://dunyauser:dunyapassword@sitar.s.upf.edu:5672/CompMusic'

Solr
----

This is not needed if you are not developing search. You can use the main solr
server configured in `local_settings.py.dist`.

Search, search autocompletion, and similar concerts use solr to make things faster

Download the solr package from https://github.com/alastair/solr-mvn-template

Copy in the configuration files from `dunya/solr`

run

    mvn jetty:run-war

To import data into solr

    python manage.py solrdelete
    python manage.py solrimport

Modify  `SOLR_URL` in `local_settings.py.dist` to point to your solr server.
For example, if you are running solr on port 8080 in your localhost:

    SOLR_URL = 'http://localhost:8080'


Less stylesheets
----------------
We use the less css compiler for stylesheets. You'll need `lessc` installed in order
to update them. This might be as simple as one of these:

    npm install -g less
    sudo apt-get install node-less

You can also install node and less directly into your virtualenv if system versions
of node are too old:

    wget http://nodejs.org/dist/v0.10.25/node-v0.10.25.tar.gz
    tar xfz node-v0.10.25.tar.gz
    cd node-v0.10.25
    ./configure --prefix=/srv/dunya/env
    make && make install
    hash -r
    npm install -g less

Compile all the less files to css by running

    fab lesscompress

Running
=======

To run the server:

    source env/bin/activate
    fab up

To run jobs, make sure rabbitmq is running on the server

And on each client you run celery, either for executing the feature processing algorithms or the
information import from MusicBrainz.

    celery -A dunya worker -l info

    celery -A dunya worker -l info -Q import

To make a complete dump of the database to a file called `dunya_data.json` or to
load it again, run

    fab dumpdata
    fab loaddata

Updating Fixtures
=================

Some data in Dunya should only rarely change (e.g., Raaga, Taala, Form, Location, Language lists).
We store this data in _fixtures,_ and it is automatically loaded when you create a new database.
Fixure files are in `fixtures/initial_data.json` in the app (e.g., `data` and `carnatic`).

If you make a new fixture table, you can easily import data into it by creating a CSV file with
the data in the first column and running

    python tools/import_csv.py -t <fixturename> <csvfile>

You'll need to edit `import_csv.py` to tell it about your table.
You should then dump the fixtures to file and commit them for other people to use
(you'll need to edit the `dumpfixture` method in `fabfile.py` to tell it about the
new fixture, too.

    fab dumpfixture:carnatic


Development
===========

In the data module there are 5 abstract classes:

 * Artist
 * Composer
 * Work
 * Concert
 * Recording

These classes store fields that are common to all cultures.

They also store lookup properties that are common over all styles, e.g.,
`concert.performers()`

Each style has replicas of these classes that can inherit from these
abstract classes.

The abstract classes also provide the `get_absolute_url()` method, to be used
when referring to an object.

both `get_absolute_url` and property lookups require data (class names, url fragments) that
are common to the specific culture. Because of this, you need to create a StyleBase class
which implements two methods. Here is an example:

    class CarnaticBase(object):
        def get_style(self):
            return "carnatic"
        def get_object_map(self):
            return {"performance": InstrumentPerformance,
                    "concert": Concert
            }

You need an object map for each of the abstract classes.

A specific culture has a concrete class inheriting from the base class ''first'' and
then the abstract data class

    class Concert(CarnaticBase, data.models.BaseConcert):

Any fields that are specific to this culture can be added to this specific class.

Templates
=========

To get the application chrome, add this to the top of the template

    {% extends "browse/base.html" %}

and put the contents of the template inside

    {% block wrap %}
    ...
    {% endblock %}

Template files should be saved in `modulename/templates/modulename/templatename.html` and can be
refered to in a view as `modulename/templatename.html`

Template fragments
==================

Commonly used parts of code are added to template fragments.

We need a better description about how to name these and what the arguments should be.

Inline links
============
When linking to an entity, never construct a link manually. Instead, make sure the template contains

    {% load extras %}

and use the provided `{% inline_x thex %}` methods. These will automatically create a link and
the best form of the objects name.

Server configuration
====================

Find an nginx configuration file in the `admin/` directory.
Use this configuration for supervisor.

    [program:dunya]
    environment=LANG='en_US.UTF-8',LC_ALL='en_US.UTF-8'
    user=dunya
    directory=/srv/dunya
    command=/srv/dunya/env/bin/python manage.py runfcgi daemonize=false socket=/tmp/dunya.sock
    umask=0
    redirect_stderr=true
    stopasgroup=true

Workers
=======

Dunya must also be installed on worker machines to run remote processes. This machine
will need access to the main database, configured in `local_settings.py`

Essentia should be installed into the virtual environment, `/srv/dunya/env`. The
whole dunya directory should be owned by a user that has write permission to the
directory. Celery should run as this user too.

You need to make sure that this user can connect to github via ssh. Either log in as the
use and run `ssh github.com`, or use https.

The celery configuration should have a queue and hostname configured that are the
same (`-Q` and `-n`). These settings are needed for remote control of a single worker.
The machines must also listen on the standard `celery` queue for all other work.

    [program:dunyacelery]
    # We need to set the path to include the virtualenv so that e.g. essentia gets the right pythonpath
    # Supervisor doesn't overwrite HOME or USER, so we need to add it so that os.path.expanduser works
    # set LD_LIBRARY_PATH so the python module _essentia.so can find libessentia.so
    environment=LANG='en_US.UTF-8',LC_ALL='en_US.UTF-8',PATH='/srv/dunya/env/bin:/usr/local/bin:/bin:/usr/bin',HOME='/home/dunya',USER='dunya',LD_LIBRARY_PATH='/srv/dunya/env/lib'
    user=dunya
    directory=/srv/dunya
    command=/srv/dunya/env/bin/celery -A dunya -n kora worker -l info -Q kora,celery
    redirect_stderr=true
    stopasgroup=true
    autorestart=true

One machine must listen on the `import` queue. This is used for processes that run from
the dashboard.
