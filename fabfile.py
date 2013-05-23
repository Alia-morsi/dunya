from fabric.api import *
import os

def up(port="8001"):
    local("python manage.py runserver 0.0.0.0:%s"%port)

def setupdb():
    local("python manage.py syncdb --noinput")
    local("python manage.py migrate kombu.transport.django")
    local("python manage.py migrate djcelery")
    local("python manage.py migrate data")
    local("python manage.py migrate carnatic")
    local("python manage.py migrate dashboard")

def updatedb():
    with settings(warn_only=True):
        local("python manage.py schemamigration data --auto")
    with settings(warn_only=True):
        local("python manage.py schemamigration carnatic --auto")
    with settings(warn_only=True):
        local("python manage.py schemamigration dashboard --auto")
    local("python manage.py migrate data")
    local("python manage.py migrate carnatic")
    local("python manage.py migrate dashboard")

def dumpfixture(modname):
    redir = "%s/fixtures/initial_data.json" % modname
    if modname == "data":
        local("python manage.py dumpdata data data.SourceName --indent=4 > %s" % redir)
    elif modname == "carnatic":
        tables = ["Instrument", "Taala", "Raaga", "GeographicRegion", "Form", "Language", "MusicalSchool"]
        modellist = " ".join(["carnatic.%s" % t for t in tables])
        local("python manage.py dumpdata %s --indent=4 > %s" % (modellist, redir))

def dumpdata(fname="dunya_data.json"):
    with hide('running', 'status'):
        modules = ["browse", "carnatic", "data", "docserver", "social"]
        local("python manage.py dumpdata --indent=4 %s > %s" % (" ".join(modules), fname))
        print "dumped data to %s" % fname

def loaddata(fname="dunya_data.json"):
    print "Loading data from %s" % fname
    if os.path.exists(fname):
        local("python manage.py loaddata %s" % fname)
    else:
        print " (missing!)"

def test():
    local("python manage.py test browser")
