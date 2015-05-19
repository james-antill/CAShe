# CAShe

CAShe is a CAS (Content Addressable Storage) cache for your data/caches.
Everything that is stored in the CAShe can be deleted at any time, although
that will mainly happen when cleanup operations are called or if failures
happend.

Much like squid is a HTTP cache for multiple computers/applications, CAShe can
act as a CAS cache for multiple applications or even for the same application
which clears it's own cache of data.

There is a "**cashe**" command line interface, so a user can easily see how
much data is stored in CAShe and manually insert/remove data from it. It's
expected that most usres/applications would use the default system CAShe path,
but there is nothing stopping an application having their own (although there
is no direct support for multiple sotres).

See DESIGN for an explanation of how it works, and why, so you can reimplement
compatibly.
