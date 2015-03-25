#! /usr/bin/python -tt

__version__ = '0.99.1'
__version_info__ = tuple([ int(num) for num in __version__.split('.')])

import sys # Only needed for stderr and exit()

import os
import os.path
import shutil
import tempfile
import errno

_checksum_aliases = {'sha'    : 'sha1',
                     'sha2'   : 'sha256'}
_checksum_d_len   = {"md5"    : 32,
                     "sha1"   : 40,
                     "sha256" : 64,
                     "sha512" : 128}

try:
    import hashlib
    # Add sha384 ?? When we don't support it above?
    _available_checksums = set(['md5', 'sha1', 'sha256', 'sha512'])
except ImportError:
    # Python-2.4.z ... gah!
    import sha
    import md5
    _available_checksums = set(['md5', 'sha1'])
    class hashlib:

        @staticmethod
        def new(algo):
            if algo == 'md5':
                return md5.new()
            if algo == 'sha1':
                return sha.new()
            raise ValueError, "Bad checksum type"

# some checksum types might be disabled
for ctype in list(_available_checksums):
    try:
        hashlib.new(ctype)
    except:
        print >> sys.stderr, 'Checksum type %s disabled' % repr(ctype)
        _available_checksums.remove(ctype)
for ctype in 'sha256', 'sha1':
    if ctype in _available_checksums:
        _default_checksums = [ctype]
        break
else:
    raise ImportError, 'broken hashlib'
del ctype

def _listdir(D):
    try:
        return os.listdir(D)
    except OSError, e:
        if e.errno in (errno.ENOENT, errno.ENOTDIR, errno.EACCES):
            return []
        raise

def _unlink_f(filename):
    """ Call os.unlink, but don't die if the file isn't there. This is the main
        difference between "rm -f" and plain "rm". """
    try:
        os.unlink(filename)
        return True
    except OSError, e:
        if e.errno not in (errno.ENOENT, errno.EPERM, errno.EACCES, errno.EROFS):
            raise
    return False

def _try_rmdir(dirname):
    """ Call os.rmdir, but don't die if the dir. isn't empty. """
    try:
        os.rmdir(dirname)
        return True
    except OSError, e:
        if e.errno != errno.ENOTEMPTY:
            raise
    return False

def _stat_f(filename, ignore_EACCES=False):
    """ Call os.stat(), but don't die if the file isn't there. Returns None. """
    try:
        return os.stat(filename)
    except OSError, e:
        if e.errno in (errno.ENOENT, errno.ENOTDIR):
            return None
        if ignore_EACCES and e.errno == errno.EACCES:
            return None
        raise

def _link_xdev(src, dst):
    try:
        os.link(src, dst)
    except OSError, e:
        if e.errno == errno.EEXIST:
            dname = os.path.dirname(dst)
            out = tempfile.NamedTemporaryFile(dir=dname)
            _unlink_f(out.name)
            out.delete = False
            if _link_xdev(src, out.name):
                # From man 2 rename:
                #  If  oldpath  and  newpath are existing hard links referring
                # to the same file, then rename() does nothing, and returns
                # a success status.
                # ...yes, this is stupid.
                _unlink_f(dst)
                os.rename(out.name, dst)
                return True
            return False
        if e.errno == errno.EXDEV:
            return False
        if e.errno == errno.EMLINK: # FIXME: should probably start new?
            return False
        raise
    return True

def _copy_atomic(src, dst):
    dname = os.path.dirname(dst)
    try:
        out = tempfile.NamedTemporaryFile(dir=dname)
    except OSError, e:
        if e.errno == errno.ENOENT:
            os.makedirs(dname)
            return _copy_atomic(src, dst)
        raise
    shutil.copy(src, out.name)
    os.rename(out.name, dst)
    out.delete = False


class Checksums:
    """ Generate checksum(s), on given pieces of data. Producing the
        Length and the result(s) when complete. """

    def __init__(self, checksums=None, ignore_missing=False, ignore_none=False):
        if checksums is None:
            checksums = _default_checksums
        self._sumalgos = []
        self._sumtypes = []
        self._len = 0

        done = set()
        for sumtype in checksums:
            if sumtype == 'sha':
                sumtype = 'sha1'
            if sumtype in done:
                continue

            if sumtype in _available_checksums:
                sumalgo = hashlib.new(sumtype)
            elif ignore_missing:
                continue
            else:
                raise MiscError, 'Error Checksumming, bad checksum type %s' % sumtype
            done.add(sumtype)
            self._sumtypes.append(sumtype)
            self._sumalgos.append(sumalgo)
        if not done and not ignore_none:
            raise MiscError, 'Error Checksumming, no valid checksum type'

    def __len__(self):
        return self._len

    # Note that len(x) is assert limited to INT_MAX, which is 2GB on i686.
    length = property(fget=lambda self: self._len)

    def update(self, data):
        self._len += len(data)
        for sumalgo in self._sumalgos:
            sumalgo.update(data)

    def read(self, fo, size=2**16):
        data = fo.read(size)
        self.update(data)
        return data

    def hexdigests(self):
        ret = {}
        for sumtype, sumdata in zip(self._sumtypes, self._sumalgos):
            ret[sumtype] = sumdata.hexdigest()
        return ret

    def hexdigest(self, checksum=None):
        if checksum is None:
            if not self._sumtypes:
                return None
            checksum = self._sumtypes[0]
        if checksum == 'sha':
            checksum = 'sha1'
        return self.hexdigests()[checksum]

    def digests(self):
        ret = {}
        for sumtype, sumdata in zip(self._sumtypes, self._sumalgos):
            ret[sumtype] = sumdata.digest()
        return ret

    def digest(self, checksum=None):
        if checksum is None:
            if not self._sumtypes:
                return None
            checksum = self._sumtypes[0]
        if checksum == 'sha':
            checksum = 'sha1'
        return self.digests()[checksum]


class AutoFileChecksums:
    """ Generate checksum(s), on given file/fileobject. Pretending to be a file
        object (overrrides read). """

    def __init__(self, fo, checksums, ignore_missing=False, ignore_none=False):
        self._fo       = fo
        self.checksums = Checksums(checksums, ignore_missing, ignore_none)

    def __getattr__(self, attr):
        return getattr(self._fo, attr)

    def read(self, size=-1):
        return self.checksums.read(self._fo, size)

def _file2hexdigest(checksum_type, filename, datasize=None, utime=None):
    data = Checksums([checksum_type])
    CHUNK = 1024 * 8
    try:
        fo = open(filename)
        while data.read(fo, CHUNK):
            if datasize is not None and data.length > datasize:
                break
        fo.close()
        if utime is not None:
            try:
                os.utime(filename, utime)
            except:
                pass
    except Exception, e:
        # print "JDBG:", "E", e
        return None
    return data.hexdigest(checksum_type)

def _valid_checksum_data(checksum_data):
    for i in checksum_data:
        if i in "0123456789abcdef":
            continue
        return False
    return True

class CASheObj(object):
    __slots__ = ['checksum_type', 'checksum_data']

    def __init__(self, checksum_type, checksum_data):
        checksum_type = _checksum_aliases.get(checksum_type, checksum_type)

        if checksum_type not in _checksum_d_len:
            raise TypeError, "Not a valid Checksum Type: %s" % checksum_type

        if len(checksum_data) != _checksum_d_len[checksum_type]:
            raise TypeError, ("Not a valid Checksum Length: %s (%d != %d)" %
                              (checksum_type, len(checksum_data), _checksum_d_len[checksum_type]))

        checksum_data = checksum_data.lower()
        if not _valid_checksum_data(checksum_data):
            raise TypeError, ("Not a valid Checksum: %s (%s)" %
                              (checksum_type, checksum_data))

        self.checksum_type = checksum_type
        self.checksum_data = checksum_data

    def __eq__(self, other):
        if self.checksum_type != other.checksum_type:
            return False
        if self.checksum_data != other.checksum_data:
            return False
        return True
    def x__ne__x(self, other):
        if self == other:
            return False
        return True

    def __str__(self):
        return "%s:%s" % (self.checksum_type, self.checksum_data)

    def __repr__(self):
        return "<%s : %s (%s)>" % (self.__class__.__name__, str(self),hex(id(self)))


class CASheFileObj(CASheObj):
    __slots__ = ['_exists', '_filename', '_stat', 'link', 'root']

    def __init__(self, root, checksum_type, checksum_data, *args, **kwargs):
        CASheObj.__init__(self, checksum_type, checksum_data, *args, **kwargs)
        self.root = root
        self.link = True

    def __len__(self):
        " Same as .size "
        return self.size

    def __nonzero__(self):
        """ Always True, even if the len() is unknown (and thus 0). """
        return True

    def _getFilename(self):
        if getattr(self, "_filename", None) is None:
            self._filename = "%s/%s/%s/%s" % (self.root, self.checksum_type,
                                              self.checksum_data[:4],
                                              self.checksum_data)
        return self._filename
    filename = property(fget=lambda self: self._getFilename(),
                        doc="Full path to filename for the cached object")
    def _getDirname(self):
        return "%s/%s/%s" % (self.root, self.checksum_type,
                             self.checksum_data[:4])
    dirname = property(fget=lambda self: self._getDirname(),
                       doc="Full path to dirname for the cached object")

    def _getCheckedFilename(self):
        checksum_data = _file2hexdigest(self.checksum_type, self.filename,
                                        utime=(self.atime, self.mtime))
        if checksum_data is None or checksum_data != self.checksum_data:
            self.unlink()
            return None

        self.exists = True
        return self.filename
    checked_filename = property(fget=lambda self: self._getCheckedFilename(),
                                doc="Full path to filename for the cached object, checked")


    def _getExists(self):
        if getattr(self, "_exists", None) is None:
            return self.size
        return self._exists
    def _setExists(self, value):
        if not value:
            if hasattr(self, "_exists"):
                del self._exists
            self._delStatVal()
        else:
            self._exists = value
        return value
    exists = property(fget=lambda self: self._getExists(),
                      fset=lambda self, value: self._setExists(value),
                      fdel=lambda self: self._setExists(None),
                      doc="Does the checksummed object exist in the cache (cached)")

    def _delStatVal(self):
        self._stat = None
    def _getStatVal(self, mem, zero=0):
        if getattr(self, "_stat", None) is None:
            self._stat = _stat_f(self.filename)
            if self._stat is None:
                return zero
            self.exists = True
        return getattr(self._stat, mem)
    def _getSize(self):
        return self._getStatVal("st_size")        
    size = property(fget=lambda self: self._getSize(),
                    fdel=lambda self: self._delStatVal(),
                    doc="Size of the checksummed object in the cache (cached)")
    def _getATime(self):
        return self._getStatVal("st_atime")
    atime = property(fget=lambda self: self._getATime(),
                     fdel=lambda self: self._delStatVal(),
                     doc="Access time of the checksummed object in the cache (cached)")
    def _getCTime(self):
        return self._getStatVal("st_ctime")
    ctime = property(fget=lambda self: self._getCTime(),
                     fdel=lambda self: self._delStatVal(),
                     doc="Change time of the checksummed object in the cache (cached)")
    def _getMTime(self):
        return self._getStatVal("st_mtime")
    mtime = property(fget=lambda self: self._getMTime(),
                     fdel=lambda self: self._delStatVal(),
                     doc="Modified time of the checksummed object in the cache (cached)")
    def _getNlink(self):
        return self._getStatVal("st_nlink")
    nlink = property(fget=lambda self: self._getNlink(),
                     fdel=lambda self: self._delStatVal(),
                     doc="Number of links to the checksummed object in the cache (cached)")

    def save(self, filename, checksum=True, link=None):
        """ Save the file, as an object, into the CAShe storage.

        :param filename: a string specifying the path to link/read from
        :param checksum: a boolean specifying if we should perform a
                         checksum of the data (default True)
        :param link: should we try using link to store the data
        """
        if False:
            print "JDBG:", "save:", filename, checksum, link, self.link
        if link is None:
            link = self.link
        try:
            if not link:
                tst = False
            else:
                tst = _link_xdev(filename, self.filename)
        except OSError, e:
            if e.errno == errno.ENOENT:
                os.makedirs(os.path.dirname(self.filename))
                return self.save(filename, checksum=checksum)
            raise

        if not tst:
            _copy_atomic(filename, self.filename)
        if checksum:
            return self.checked_filename # Sets exists internally

        self.exists = True
        return self.filename

    def load(self, filename, checksum=False, link=None):
        """ Load the object, from the CAShe storage, to a file.

        :param filename: a string specifying the path to link/write to
        :param checksum: a boolean specifying if we should perform a
                         checksum of the data (default False)
        :param link: should we try using link to retrieve the data
        """
        if False:
            print "JDBG:", "load:", filename, checksum, link, self.link
        if checksum: # FIXME: This can load it twice ... meh.
            if self.checked_filename is None:
                return None

        if link is None:
            link = self.link
        src = self.filename
        try:
            if link and _link_xdev(src, filename):
                return src
        except OSError, e:
            if e.errno == errno.ENOENT:
                return None
            raise

        _copy_atomic(src, filename)
        self.exists = True
        return filename

    def get(self, *args, **kwargs):
        " Same as .load() "
        self.load(*args, **kwargs)

    def put(self, *args, **kwargs):
        " Same as .save() "
        self.save(*args, **kwargs)

    def unlink(self):
        """ Remove the checksummed object from the cache. """
        if _unlink_f(self.filename):
            _try_rmdir(self.dirname)
        self.exists = False

class CAShe(object):
    # __slots__ = ['_objs', 'path', 'link']

    def __init__(self, path="."):
        self.path = path
        if not os.path.exists(path):
            os.makedirs(path)

        self._objs = {}
        for T in _checksum_d_len:
            self._objs[T] = {}

        self.link = True

    def __contains__(self, other):
        T = other.checksum_type
        if T not in self._objs:
            return False

        D = other.checksum_data
        if D not in self._objs[T]:
            return False

        return True

    def get(self, checksum_type, checksum_data):
        """ Get an object for the specified checksum.

        :param checksum_type: a string specifying the type of checksum,
                              Eg. md5, sha256
        :param checksum_data: a string specifying the hexdigest of the checksum.
        """
        T = _checksum_aliases.get(checksum_type, checksum_type)
        if T not in self._objs:
            raise TypeError, "Not a valid Checksum Type: %s" % T

        if checksum_data not in self._objs[T]:
            obj = CASheFileObj(self.path, checksum_type, checksum_data)
            obj.link = self.link
            self._objs[T][obj.checksum_data] = obj
        return self._objs[T][checksum_data]

    def rm(self, obj):
        """ Remove an object from the cache.

        :param obj: an object returned by .get()
        """
        obj.unlink()
        del self._objs[obj.checksum_type][obj.checksum_data]

    def ls(self, checksum_type=None):
        """ Yield all objects stored in the cache.

        :param checksum_type: a string specifying the type of checksum, or None
                              for all checksums. Eg. md5, sha256.
        """
        checksum_type = _checksum_aliases.get(checksum_type, checksum_type)

        for T in sorted(self._objs):
            if checksum_type is not None and checksum_type != T:
                continue

            subdirname = "%s/%s" % (self.path, T)

            for subfilename in _listdir(subdirname):
                if len(subfilename) != 4:
                    continue
                if not _valid_checksum_data(subfilename):
                    continue

                dirname = "%s/%s" % (subdirname, subfilename)
                for filename in _listdir(dirname):
                    if not filename.startswith(subfilename):
                        continue
                    if len(filename) != _checksum_d_len[T]:
                        continue
                    if not _valid_checksum_data(filename):
                        continue
                    yield self.get(T, filename)

    def _get_config_def(self):
        lo = 500 * 1000 * 1000
        hi = 2   * 1000 * 1000 * 1000
        age = 8 * 60 * 60 * 24
        sort_by = "atime"
        return (lo, hi, age, sort_by)

    def _get_config(self):
        try:
            data = open(self.path + "/config").readlines()
        except:
            return self._get_config_def()

        data = [x.lstrip() for x in data]
        data = [x for x in data if x and x[0] != '#']
        if not data:
            return self._get_config_def()

        lo, hi, age, sort_by = self._get_config_def()

        for line in data:
            vals = line.split('=')
            if len(vals) != 2:
                continue # ignore errors ftw
            key,val = vals
            key = key.strip()
            val = val.strip()

            mul = 1

            if key == 'age':
                if val.endswith('w'):
                    mul = 60*60*24*7
                    val = val[:-1]
                elif val.endswith('d'):
                    mul = 60*60*24
                    val = val[:-1]
                elif val.endswith('h'):
                    mul = 60*60
                    val = val[:-1]
                elif val.endswith('m'):
                    mul = 60
                    val = val[:-1]

                try:
                    val = float(val)
                except:
                    continue
                age = int(val * mul)
                continue

            if key == 'time':
                val = val.lower()
                if val in ("atime", "ctime", "mtime"):
                    sort_by = val
                continue

            if val.endswith('k') or val.endswith('K'):
                mul = 1000
                val = val[:-1]
            elif val.endswith('m') or val.endswith('M'):
                mul = 1000*1000
                val = val[:-1]
            elif val.endswith('g') or val.endswith('G'):
                mul = 1000*1000*1000
                val = val[:-1]
            elif val.endswith('t') or val.endswith('T'):
                mul = 1000*1000*1000*1000
                val = val[:-1]
            elif val.endswith('p') or val.endswith('P'): # lol
                mul = 1000*1000*1000*1000*1000
                val = val[:-1]

            try:
                val = float(val)
            except:
                continue

            if key in ('older', 'lo', 'low'):
                lo = int(val * mul)
            if key in ('newer', 'hi', 'high'):
                hi = int(val * mul)

        if hi < lo:
            hi = lo
        return (lo, hi, age, sort_by)

    @staticmethod
    def _is_new(obj, sort_by, age, now):
        if getattr(obj, sort_by) < (now - age):
            return False
        return True

    def cleanup(self):
        """ Remove objects from the cache to being it within the configured
        limits (the "config" file at the root of the cashe).
        """
        import time
        (lo, hi, age, sort_by) = self._get_config()

        # http://www.grantjenks.com/docs/sortedcontainers/ ??
        def _rm_objs(objs, size, cutoff):
            deleted_num  = 0
            deleted_size = 0

            objs.sort(key=lambda x: getattr(x, sort_by), reverse=True)
            while size > cutoff:
                obj = objs.pop()
                size -= obj.size
                deleted_num  += 1
                deleted_size += obj.size
                # print "JDBG:", obj
                self.rm(obj)
            return (deleted_num, deleted_size)

        objs = []
        size = 0
        lo_objs = []
        lo_size = 0
        now = time.time()

        for obj in self.ls():
            if obj.nlink > 1:
                continue

            if not self._is_new(obj, sort_by, age, now):
                lo_objs.append(obj)
                lo_size += obj.size
            else:
                objs.append(obj)
                size += obj.size

        if (size + lo_size) < lo: # Under lo watermark, keep everything
            return 0, 0

        if size < lo: # Delete some, but not all of old objs
            return _rm_objs(lo_objs, lo_size, lo - size)

        # Over lo watermark with new objs, delete all old
        (deleted_num, deleted_size) = _rm_objs(lo_objs, lo_size, 0)
        assert len(lo_objs) == 0

        if size < hi:
            return (deleted_num, deleted_size)

        # Now we need to cap the new objs to hi watermark
        (hdeleted_num, hdeleted_size) = _rm_objs(objs, size, hi)
        return (deleted_num  + hdeleted_num,
                deleted_size + hdeleted_size)

def _main():
    """ CAShe test function. """
    import time
    import optparse
    try:
        import xattr
        if not hasattr(xattr, 'get'):
            xattr = None # This is a "newer" API.
    except ImportError:
        xattr = None


    def _ui_time(tm):
        return time.strftime("%Y-%m-%d %H:%M", time.gmtime(tm))
    def _ui_num(num):
        num = str(num)
        if len(num) ==  4:
            return "  %s.%sK" % (num[0], num[1:3])
        if len(num) ==  5:
            return " %s.%sK" % (num[0:2], num[2:4])
        if len(num) ==  6:
            return "%s.%sK" % (num[0:3], num[3:5])
        if len(num) ==  7:
            return "  %s.%sM" % (num[0], num[1:3])
        if len(num) ==  8:
            return " %s.%sM" % (num[0:2], num[2:4])
        if len(num) ==  9:
            return "%s.%sM" % (num[0:3], num[3:5])
        if len(num) == 10:
            return "  %s.%sG" % (num[0], num[1:3])
        if len(num) == 11:
            return " %s.%sG" % (num[0:2], num[2:4])
        if len(num) == 12:
            return "%s.%sG" % (num[0:3], num[3:5])
        return num
    def _ui_age(num):
        ret = ""

        weeks = num / (60 * 60 * 24 * 7)
        num %= (60 * 60 * 24 * 7)
        if weeks:
            ret +=  "%u week(s)" % weeks
            if num:
                ret +=  " "

        days = num / (60 * 60 * 24)
        num %= (60 * 60 * 24)
        if days:
            ret +=  "%u day(s)" % days
            if num:
                ret +=  " "

        if not num:
            return ret

        hours = num / (60 * 60)
        num %= (60 * 60)

        minutes = num / (60)
        num %= (60)

        ret +=  "%02u:%02u:%02u" % (hours, minutes, num)
        return ret
    def _get_T_D(cmds):
        T = None
        D = None
        if len(cmds) >= 2:
            cmds[1] = _checksum_aliases.get(cmds[1], cmds[1])
            if cmds[1] in objs._objs:
                T = cmds.pop(1)
        if len(cmds) >= 2:
            D = cmds[1]
        return T, D
    def _get_objs(objs, opts, T, D, osort_by=None):
        if osort_by is None:
            osort_by = opts.sort_by
        for obj in sorted(objs.ls(checksum_type=T),
                          key=lambda x: getattr(x, osort_by)):
            if D is not None and not obj.checksum_data.startswith(D):
                continue
            yield obj
    all_cmds = ("summary", "list", "info", "check",
                "load", "save", "save-fast", "unlink",
                "cleanup", "ls-extra", "rm-extra", "list-files", "recent", 
                "rsync-from", "rsync-to", "rsync2",
                "config", "help")
    argp = optparse.OptionParser(
            description='Access CAShe storage from the command line',
        version="%prog-" + __version__)
    epilog = "\n    ".join(["\n\nCOMMANDS:"]+sorted(all_cmds)) + "\n"
    argp.format_epilog = lambda y: epilog
    argp.add_option('-v',
            '--verbose', default=False, action='store_true',
            help='verbose output from commands')
    argp.add_option(
            '--path', default="/var/cache/CAShe",
            help='path to the CAShe storage, defaults to the system cache')
    argp.add_option('-p',
            '--preserve', default=False, action='store_true',
            help='preserve filetimes when using rsync')
    argp.add_option(
            '--sort-by', default="filename",
            help='what to sort list/info command by')
    argp.add_option('--link', default=True, action='store_true',
            help='try to link in load/save operations (default)')
    argp.add_option('--copy-only', dest='link', action='store_false',
            help='try to link in load/save operations')
    (opts, cmds) = argp.parse_args()

    if opts.sort_by not in ("filename", "size",
                            "atime", "ctime", "mtime", "nlink", "time"):
        opts.sort_by = "filename"    

    objs = CAShe(opts.path)
    if not opts.link:
        objs.link = False

    cmd = "summary"
    if len(cmds) >= 1:
        if cmds[0] in all_cmds:
            cmd = cmds[0]
        else:
            cmd = "help"


    (lo, hi, age, tsort_by) = objs._get_config()
    if opts.sort_by == "time":
        opts.sort_by = tsort_by
    if cmd == "config":
        (dlo, dhi, dage, dtsort_by) = objs._get_config_def()
        def _dtxt(dconfig, config):
            if dconfig == config:
                return "def"
            return "usr"
        print "    Storage(%s):" % _dtxt(dlo, lo), _ui_num(lo)
        print "New Storage(%s):" % _dtxt(dhi, hi), _ui_num(hi)
        print "        Age(%s):" % _dtxt(dage, age), _ui_age(age)
        print "       Time(%s):" % _dtxt(dtsort_by, tsort_by), tsort_by
        print "       Path(%s):" %_dtxt("/var/cache/CAShe", objs.path),objs.path

    if cmd == "help":
        argp.print_help()

    if cmd == "summary":
        T = None
        D = None
        if len(cmds) >= 2:
            T = cmds[1]
        if len(cmds) >= 3:
            D = cmds[2]

        now = time.time()
        summary_data = {'used-objs' : 0,
                        'used-size' : 0,
                        'free-objs': 0,
                        'free-objs-old': 0,
                        'free-size': 0,
                        'free-size-old': 0,
                        }
        Ts = {"." : summary_data.copy()}
        for obj in _get_objs(objs, opts, T, D, osort_by="filename"):
            if obj.checksum_type not in Ts:
                Ts[obj.checksum_type] = summary_data.copy()

            if obj.nlink > 1:
                Ts[obj.checksum_type]['used-objs'] += 1
                Ts[obj.checksum_type]['used-size'] += obj.size
                Ts['.']['used-objs'] += 1
                Ts['.']['used-size'] += obj.size
            elif not objs._is_new(obj, tsort_by, age, now):
                Ts[obj.checksum_type]['free-objs-old'] += 1
                Ts[obj.checksum_type]['free-size-old'] += obj.size
                Ts['.']['free-objs-old'] += 1
                Ts['.']['free-size-old'] += obj.size
            else:
                Ts[obj.checksum_type]['free-objs'] += 1
                Ts[obj.checksum_type]['free-size'] += obj.size
                Ts['.']['free-objs'] += 1
                Ts['.']['free-size'] += obj.size

        def _prnt_summary(data):
            if opts.verbose:
                print "  Used Objs:", _ui_num(data['used-objs'])
                print "  Used Size:", _ui_num(data['used-size'])
                print "  Free Objs:", _ui_num(data['free-objs'])
                print "  Free Size:", _ui_num(data['free-size'])
            if opts.verbose or data['free-objs-old']:
                print "   OLD Objs:", _ui_num(data['free-objs-old'])
                print "   OLD Size:", _ui_num(data['free-size-old'])
            objs = data['free-objs'] + data['used-objs']
            size = data['free-size'] + data['used-size']
            print "       Objs:", _ui_num(objs)
            print "       Size:", _ui_num(size)
        if True:
            for T in sorted(Ts):
                if T == '.': continue
                print "Type:", T
                _prnt_summary(Ts[T])
        print "--All--:", len(Ts) - 1
        _prnt_summary(Ts['.'])

    if cmd == "list":
        now = time.time()
        T, D = _get_T_D(cmds)

        for obj in _get_objs(objs, opts, T, D):
            if obj.nlink > 1:
                prefix = " "
            elif objs._is_new(obj, tsort_by, age, now):
                prefix = "*"
            else:
                prefix = "!"
            print "%s%-6s %-64s %s" % (prefix, obj.checksum_type,
                                       obj.checksum_data, _ui_num(obj.size))

    if cmd == "check":
        now = time.time()
        T, D = _get_T_D(cmds)

        for obj in _get_objs(objs, opts, T, D):
            if obj.nlink > 1:
                prefix = " "
            elif objs._is_new(obj, tsort_by, age, now):
                prefix = "*"
            else:
                prefix = "!"
            print "%s%-6s %-64s %s" % (prefix, obj.checksum_type,
                                       obj.checksum_data,
                                       obj.checked_filename is not None)

    if cmd == "info":
        now = time.time()
        T, D = _get_T_D(cmds)

        done = False
        for obj in _get_objs(objs, opts, T, D):
            if done: print ''
            done = True
            print "Type:", obj.checksum_type
            print "Data:", obj.checksum_data
            print "   Size:", _ui_num(obj.size)
            print "  Links:", _ui_num(obj.nlink - 1)
            suffix = ""
            if tsort_by == "mtime" and objs._is_new(obj, tsort_by, age, now):
                suffix = " (old)"
            print " M-Time:", _ui_time(obj.mtime) + suffix
            suffix = ""
            if tsort_by == "atime" and objs._is_new(obj, tsort_by, age, now):
                suffix = " (old)"
            print " A-Time:", _ui_time(obj.atime) + suffix
            suffix = ""
            if tsort_by == "ctime" and objs._is_new(obj, tsort_by, age, now):
                suffix = " (old)"
            if opts.verbose or tsort_by == "ctime":
                print " C-Time:", _ui_time(obj.ctime) + suffix
            if opts.verbose:
                print "   File:", obj.filename
            if xattr:
                # See: http://www.freedesktop.org/wiki/CommonExtendedAttributes
                try:
                    xd = xattr.get(obj.filename, 'user.xdg.origin.url')
                    print ".origin:", xd
                except IOError, e:
                    ok = False
                    if e.errno in (errno.ENODATA,
                                   errno.EOPNOTSUPP, errno.E2BIG, errno.ERANGE):
                        ok = True
                    for me in ("ENOATTR", "ENOTSUPP"):
                        if hasattr(errno, me) and e.errno == getattr(errno, me):
                            ok = True
                            break
                    if not ok:
                        raise

    if cmd == "load":
        if len(cmds) != 4:
            print >>sys.stderr, argp.prog, "load <type> <data> <filename>"
            sys.exit(1)
        obj = objs.get(cmds[1], cmds[2])
        obj.load(cmds[3])

    if cmd == "save":
        if len(cmds) == 3:
            data     = _file2hexdigest(cmds[1], cmds[2])
            filename = cmds[2]
            checksum = False
        elif len(cmds) == 4 and len(cmds[2]) == _checksum_d_len[cmds[1]]:
            data     = cmds[2]
            filename = cmds[3]
            checksum = True
        elif len(cmds) >= 4:
            for filename in cmds[2:]:
                data = _file2hexdigest(cmds[1], filename)
                obj  = objs.get(cmds[1], data)
                obj.save(filename, checksum=False)
            data     = None
        else:
            print >>sys.stderr, argp.prog, "save <type> [data] <filename> [...]"
            sys.exit(1)

        if data is not None:
            obj = objs.get(cmds[1], data)
            obj.save(filename, checksum=checksum)

    if cmd == "save-fast":
        if len(cmds) != 4:
            print >>sys.stderr, argp.prog, "save-fast <type> <data> <filename>"
            sys.exit(1)
        obj = objs.get(cmds[1], cmds[2])
        obj.save(cmds[3], checksum=False)

    if cmd == "unlink":
        if len(cmds) != 3:
            print >>sys.stderr, argp.prog, "unlink <type> <data>"
            sys.exit(1)
        obj = objs.get(cmds[1], cmds[2])
        obj.unlink()

    if cmd == "cleanup":
        objs, size = objs.cleanup()
        print "--All--:"
        print "  Objs:", _ui_num(objs)
        print "  Size:", _ui_num(size)
    if cmd in ("ls-extra", "rm-extra"):
        def _y_extras():
            for T in sorted(objs._objs):
                subdirname = "%s/%s" % (objs.path, T)

                for subfilename in _listdir(subdirname):
                    path = "%s/%s" % (subdirname, subfilename)
                    if len(subfilename) != 4:
                        yield path
                        continue
                    if not _valid_checksum_data(subfilename):
                        yield path
                        continue
                    for filename in _listdir(path):
                        path = "%s/%s/%s" % (subdirname, subfilename, filename)
                        if not filename.startswith(subfilename):
                            yield path
                            continue
                        if len(filename) != _checksum_d_len[T]:
                            yield path
                            continue
                        if not _valid_checksum_data(filename):
                            yield path
                            continue
    if cmd == "ls-extra":
        for f in _y_extras():
            print f
    if cmd == "rm-extra":
        for f in _y_extras():
            try:
                if _unlink_f(f):
                    print "rm", f
                else:
                    print " ** ", f
                    continue
            except OSError, e:
                if e.errno == errno.EISDIR:
                    shutil.rmtree(f, ignore_errors=True)
                    print "rm -r", f
            _try_rmdir(os.path.dirname(f))

    if cmd == "list-files":
        if opts.sort_by not in ("atime", "ctime", "mtime"):
            opts.sort_by = "mtime"
        T, D = _get_T_D(cmds)

        for obj in _get_objs(objs, opts, T, D):
            print obj.filename
    if cmd == "recent":
        if opts.sort_by not in ("atime", "ctime", "mtime"):
            opts.sort_by = "mtime"
        T, D = _get_T_D(cmds)

        num = 10 # 20 for a normal term. but sha256 wraps the line
        a1 = []
        a2 = []
        for obj in _get_objs(objs, opts, T, D):
            a1.append(obj)
            if len(a1) > num:
                a2 = a1
                a1 = []
        for obj in a2[len(a1):]:
            print obj.filename
        for obj in a1:
            print obj.filename

    def _rsync_cmd(src, dst, src_local=False):
        # --ignore-existing vs. --size-only ?
        # "--ignore-missing-args" is what we want, but is fairly new
        # rcmd = ["rsync", "--recursive", "--size-only", "--links"]
        rcmd = ["rsync", "--recursive", "--ignore-existing", "--links"]
        if opts.verbose:
            rcmd.extend(["--verbose", "--progress"])
        if opts.preserve:
            rcmd.extend(["--preserve"])
        done = False
        for chk in _checksum_d_len:
            chkdir = "%s/%s" % (src, chk)
            if src_local and not os.path.exists(chkdir):
                continue
            done = True
            rcmd.append(chkdir)
        if not done:
            if opts.verbose:
                print "empty CAShe:", src
            return 0
        rcmd.append(dst)
        if opts.verbose:
            print " ".join(rcmd)
        return os.spawnlp(os.P_WAIT, rcmd[0], *rcmd)

    if cmd in ("rsync-to", "rsync2"):
        if len(cmds) != 2:
            print >>sys.stderr, argp.prog, cmd, "<destination>"
            sys.exit(1)

        if cmds[1].endswith(":"):
            cmds[1] = cmds[1] + objs.path

        ret = _rsync_cmd(objs.path, cmds[1], src_local=True)
        if ret:
            sys.exit(ret)

    if cmd == "rsync-from":
        if len(cmds) != 2:
            print >>sys.stderr, argp.prog, cmd, "<source>"
            sys.exit(1)

        if cmds[1].endswith(":"):
            cmds[1] = cmds[1] + objs.path

        ret = _rsync_cmd(cmds[1], objs.path)
        if ret:
            sys.exit(ret)

    if cmd == "checksum-file":
        if len(cmds) != 3:
            print >>sys.stderr, argp.prog, "checksum-file <type> <filename>"
            sys.exit(1)
        data = _file2hexdigest(cmds[1], cmds[2])
        if data is not None:
            obj = objs.get(cmds[1], data)
            print os.path.basename(cmds[2]), data, obj.exists

if __name__ == '__main__':
    _main()
