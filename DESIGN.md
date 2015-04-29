Design of CAShe
===============

Overview
--------

CAShe storage is for storing/retrieving any piece of data that has a checksum,
thus. that data can be shared among many locations/programs. The main assumed
usage is using the CAS cache so we don't need to download network data.

CAShe has a single configuration file (called "config") which *can* be in the
top level directory, apart from that everything is cached data and can be
deleted without negatively affecting anything (apart from the obvious need to
reload that data if it's requested). However it's often going to be much more
efficient to use the "cashe" command, or the automatic cleanup API in a program using it (like "yum").

File system
-----------

On the filesystem the checksum objects are stored in a simple directory
structure, so that multiple programs can store/retrieve them at once. All
files are of the form root/checksum/first-4-hexdigest/hexdigest, where:

  * checksum is currently one of "md5", "sha1", "sha256", "sha512". Other
    implementtions can use different checksums, but they will be unrecognized
    by the current implementation and thus. removed as extra files by the cashe
    command (but not the normal cleanup function). They also won't be sync'd.
  * first-4-hexdigest is the first 4 bytes of the hex representation of the digest.
  * hexdigest is the hex representation of the digest.

For example the default file location for a file containing the four bytes
"abcd" would be /var/cache/CAShe/md5/e2fc/e2fc714c4727ee9395f324cd2e7f331f.


Storing and retrieving files
----------------------------

CAShe storage extensively uses hardlinks, by default, so that all the programs
using it will save the disk space as well as the network bandwidth. This works
best when the program using CAShe has it's cache also in /var/cache (as yum
does).

When writing files into the CAShe storage, after trying to hardlink them to
their location, they should be copied to a temporary file and renamed into
place when the file is complete (matches the checksum). This makes sure that
another program/user does not ever see a bad CAShe object.

When retrieving a checksumed object from CAShe, you just look to see if the
file exists corresponding to the checksum you had. If it does you can just
hardlink it out and only if that fails copy it. Due to this it is assumed that
the data is correct in the CAShe store, and we don't need to read the data and
ensure it matches its checksum (and the default implementation does this).
Although the cashe command has the ability the check all the objects within it.

Here is a simple example of retrieving data from CAShe using the API:

    objs = cashe.CAShe()
    obj = objs.get('md5', 'e2fc714c4727ee9395f324cd2e7f331f')
    if obj.load("myfile"):
        print "loaded 'abcd' data from CAShe"

Here is a simple example of storing data into CAShe using the API:

    objs = cashe.CAShe()
    obj = objs.get('md5', 'e2fc714c4727ee9395f324cd2e7f331f')
    open("myfile", "w").write("abcd")
    if obj.save("myfile"):
        print "saved 'abcd' data into CAShe"

Automatic cleanup
-----------------

Obviously the user does not want the CAShe storage to grow without bound, so
when you delete an object that might have originally come from CAShe storage
you should call the automatic cleanup function of the API.

This will stat(2)
all the files in the CAShe storage, deleting those that are not hardlinked and
have not been accessed/modified/changed in a configurable amount of time (for a
configurable cache size). This might not be a cheap operation.

Configuration file
------------------

The "config" file at the root of the CAShe storage directory is a simple
"key = value" file that is used for cleanup operations (at least never needed
for save/load), it lets the admin set:

  * age: seconds/minutes/hours/days/weeks from now for a file to be deemed old.
  * time: atime (default), ctime, mtime is used as the sort for older files.
  * older: bytes/KB/MB/GB size to keep of old files.
  * newer: bytes/KB/MB/GB size to keep of old+new files (can't be smaller than older).

Background
----------

This is a bit of the history, and thus. reasoning, for why CAShe is designed the
way it is.

From the very begining yum would retrieve checksummed objects for each
repository that it used, check that the objects are valid and then use. This
worked fairly well initially, although never
perfectly, but as more features were added more problems arose.

The first two big problems were that it was somewhat common to have the same
object in multiple repositories, which then had to be downloaded multiple times.
Also users had decided that removing everything from the yum cache was the
easiest way to trigger a refresh (this was fixed, but everyone still does it
6+ years later).

Another similar problem was that if a user/sysadmin had more than one machine
it was very useful if each machine didn't have to download the data that
another machine had already downloaded.

Then the --releasever option was added, which meant that yum had to store
copies of each repository for each release version that was being used. This
meant even more copies of repositories that shared data.

Then on-root users wanted direct access to a cache, instead of just looking at
root users cache as they had done previously. So now we had at least double the
number of repositories again.

More recently people have started using --installroot to create temporary
distribution installs. However when this happens the yum cache is within the
chroot of the install, meaning the usecase of create; use; delete will never
be able to reuse cached network data. Mock solved this inefficiency directly,
and there were other ways to improve the situation but none could work by
default.

The most recent problem is that Fedora moved away from a single yum package
manager, to a group of package managers all using similar infrastructure. So
now users have to download all of their network data for each package managers
they are using (or the system is using for them).

Most of these problems are now solved with CAShe. All programs can share it.
All objects are stored/retrieved using just their checksum. All non-root users
can retrieve from it (but can't store, or they'd own the files). The cache lives
outside the installation so it can be reused many times. If you have
multiple machines they can all share a single CAShe directly over a network
filesystem or a sysadmin can manually sync data using the "cashe" command. Also
users can now completely destroy the yum cache without horribly affecting it.
