#! /usr/bin/python -t

import os
import sys
import tempfile
import shutil
import time

import unittest

sys.path.insert(0, '.')
import cashe

_tmptest = True

def _cleanup(tdir):
    if _tmptest:
        shutil.rmtree(tdir)

# Data to sha256 checksums ...
d2s = {
    'a'     :'ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb',
    'a'*2   :'961b6dd3ede3cb8ecbaacbd68de040cd78eb2ed5889130cceb4c49268ea4d506',
    'a'*3   :'9834876dcfb05cb167a5c24953eba58c4ac89b1adf57f28f2f9d09af107ee8f0',
    'a'*4   :'61be55a8e2f6b4e172338bddf184d6dbee29c98853e0a0485ecee7f27b9af0b4',
    'a'*5   :'ed968e840d10d2d313a870bc131a4e2c311d7ad09bdf32b3418147221f51a6e2',
    'a'*6   :'ed02457b5c41d964dbd2f2a609d63fe1bb7528dbe55e1abf5b52c249cd735797',
    'a'*7   :'e46240714b5db3a23eee60479a623efba4d633d27fe4f03c904b9e219a7fbe60',
    'a'*8   :'1f3ce40415a2081fa3eee75fc39fff8e56c22270d1a978a7249b592dcebd20b4',
    'a'*9   :'f2aca93b80cae681221f0445fa4e2cae8a1f9f8fa1e1741d9639caad222f537d',

    'b'     :'3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d',
    'b'*2   :'3b64db95cb55c763391c707108489ae18b4112d783300de38e033b4c98c3deaf',
    'b'*3   :'3e744b9dc39389baf0c5a0660589b8402f3dbb49b89b3e75f2c9355852a3c677',
    'b'*4   :'81cc5b17018674b401b42f35ba07bb79e211239c23bffe658da1577e3e646877',
    'b'*5   :'5e846c64f2db12266e6b658a8e5b5b42cc225419b3ee1fca88acbb181ddfdb52',
    'b'*6   :'4625fd63b0e96fc0d656ae7381605e48d4a0f63a319fc743adf22688613883c7',
    'b'*7   :'ea415a61bd19915084366a0a2fdaebe070a9c3168877ecdb5e36f4905b5f8aa3',
    'b'*8   :'fb398cc690e15ddba43ee811b6c0d3ec190901ad3df377fec9a1f9004b919a06',
    }

# End of setup

def fwrite(path, data):
    fo = open(path, "w")
    fo.write(data)

class Cashe_tests(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

        if _tmptest:
            self.tdir = tempfile.mkdtemp()
        else:
            self.tdir = "saved-tests-dir"

    def stopTest(self):
        if _tmptest:
            _cleanup(self.tdir)

    def assertPathExists(self, path):
        if os.path.exists(path):
            return
        self.fail("Path doesn't exist: " + path)

    def assertPathNotExists(self, path):
        if not os.path.exists(path):
            return
        self.fail("Path doesn't exist: " + path)

    def assertPathLinks(self, path, links):
        self.assertPathExists(path)
        sd = os.stat(path)
        if links == sd.st_nlink:
            return
        self.fail("Path %s links don't match, expected=%u found=%u" %
                  (path, links, sd.st_nlink))

    def assertFileEqual(self, path1, path2):
        d1 = open(path1).read()
        d2 = open(path2).read()
        if d1 == d2:
            return
        self.fail("Paths %s and %s do not match" %
                  (path1, path2))

    # -------------------------------------------------------------------------
    # Tests...
    # -------------------------------------------------------------------------

    def test1_init(self):
        x = cashe.CAShe(self.tdir + "/test1")

    def test2_save_1(self):
        x = cashe.CAShe(self.tdir + "/test2")

        data = x.path + "/data2.1"
        fwrite(data, "a")
        self.assertPathLinks(data, 1)

        co = x.get('sha256', d2s['a'])
        co.save(data, checksum=False)
        print co.filename
        self.assertPathLinks(data, 2)
        self.assertPathLinks(co.filename, 2)

    def test2_save_2(self):
        x = cashe.CAShe(self.tdir + "/test2")

        data = x.path + "/data2.2"
        fwrite(data, "b")
        self.assertPathLinks(data, 1)

        co = x.get('sha256', d2s['b'])
        ret = co.save(data)
        print ret, co.filename
        self.assertPathLinks(data, 2)
        self.assertPathLinks(co.filename, 2)

    def test2_save_3(self):
        x = cashe.CAShe(self.tdir + "/test2")

        datai = x.path + "/data2.3"
        datao = x.path + "/data2.3-out"
        fwrite(datai, "b")
        self.assertPathLinks(datai, 1)
        self.assertPathNotExists(datao)

        co = x.get('sha256', d2s['a'])
        ret = co.save(datai, checksum=False)
        self.assertFileEqual(datai, co.filename)
        self.assertPathLinks(datai, 2)
        self.assertPathLinks(co.filename, 2)
        self.assertEqual(1, len(list(x.ls())))

        ret = co.load(datao)
        self.assertFileEqual(datai, co.filename)
        self.assertFileEqual(datao, co.filename)
        self.assertPathLinks(datai, 3)
        self.assertPathLinks(datao, 3)
        self.assertPathLinks(co.filename, 3)
        self.assertEqual(1, len(list(x.ls())))
        self.assertTrue(co.exists)

        ret = co.load(datao, checksum=True)
        self.assertPathLinks(datai, 2)
        self.assertPathNotExists(co.filename)
        self.assertEqual(0, len(list(x.ls())))
        self.assertFalse(co.exists)
        os.unlink(datao)

        co = x.get('sha256', d2s['b'])
        self.assertFalse(co.exists)
        ret = co.save(datai, checksum=False)
        self.assertFileEqual(datai, co.filename)
        self.assertPathLinks(datai, 2)
        self.assertPathLinks(co.filename, 2)
        self.assertTrue(co.exists)
        self.assertEqual(1, len(list(x.ls())))

        co = x.get('sha256', d2s['b'])
        ret = co.load(datao, checksum=True)
        self.assertEqual(len(co), 1)
        self.assertFileEqual(datai, datao)
        self.assertFileEqual(datai, co.filename)
        self.assertPathLinks(datai, 3)
        self.assertPathLinks(datao, 3)
        self.assertPathLinks(co.filename, 3)
        self.assertTrue(co.exists)
        self.assertEqual(1, len(list(x.ls())))

    def test3_save_3(self):
        x = cashe.CAShe(self.tdir + "/test3")
        x.link = False

        datai = x.path + "/data3.3"
        datao = x.path + "/data3.3-out"
        fwrite(datai, "b")
        self.assertPathLinks(datai, 1)
        self.assertPathNotExists(datao)

        co = x.get('sha256', d2s['a'])
        ret = co.save(datai, checksum=False)
        self.assertFileEqual(datai, co.filename)
        self.assertPathLinks(datai, 1)
        self.assertPathLinks(co.filename, 1)
        self.assertEqual(1, len(list(x.ls())))

        ret = co.load(datao)
        self.assertFileEqual(datai, co.filename)
        self.assertFileEqual(datao, co.filename)
        self.assertPathLinks(datai, 1)
        self.assertPathLinks(datao, 1)
        self.assertPathLinks(co.filename, 1)
        self.assertEqual(1, len(list(x.ls())))
        self.assertTrue(co.exists)

        ret = co.load(datao, checksum=True)
        self.assertPathLinks(datai, 1)
        self.assertPathNotExists(co.filename)
        self.assertEqual(0, len(list(x.ls())))
        self.assertFalse(co.exists)
        os.unlink(datao)

        co = x.get('sha256', d2s['b'])
        self.assertFalse(co.exists)
        ret = co.save(datai, checksum=False)
        self.assertFileEqual(datai, co.filename)
        self.assertPathLinks(datai, 1)
        self.assertPathLinks(co.filename, 1)
        self.assertTrue(co.exists)
        self.assertEqual(1, len(list(x.ls())))

        co = x.get('sha256', d2s['b'])
        ret = co.load(datao, checksum=True)
        self.assertEqual(len(co), 1)
        self.assertFileEqual(datai, datao)
        self.assertFileEqual(datai, co.filename)
        self.assertPathLinks(datai, 1)
        self.assertPathLinks(datao, 1)
        self.assertPathLinks(co.filename, 1)
        self.assertTrue(co.exists)
        self.assertEqual(1, len(list(x.ls())))
        # print "JDBG: ls:", list(x.ls())

    def test2_ls(self):
        x = cashe.CAShe(self.tdir + "/test2")

        datai = x.path + "/data2.4a"
        datao = x.path + "/data2.4a-out"
        fwrite(datai, "a")
        co = x.get('sha256', d2s['a'])
        co.save(datai)
        co.load(datao)
        self.assertPathLinks(datai, 3)
        self.assertPathLinks(datao, 3)
        self.assertPathLinks(co.filename, 3)
        self.assertEqual(1, len(list(x.ls())))
        self.assertTrue(co.exists)

        datai = x.path + "/data2.4aa"
        datao = x.path + "/data2.4aa-out"
        fwrite(datai, "aa")
        self.assertPathLinks(datai, 1)
        self.assertPathNotExists(datao)

        self.assertEqual(len(co), 1)

        co = x.get('sha256', d2s['aa'])
        ret = co.save(datai)
        ret = co.load(datao)
        self.assertPathLinks(datai, 3)
        self.assertPathLinks(datao, 3)
        self.assertPathLinks(co.filename, 3)
        self.assertEqual(2, len(list(x.ls())))
        self.assertTrue(co.exists)

        self.assertEqual(len(co), 2)

    def test3_1_cleanup(self):
        x = cashe.CAShe(self.tdir + "/test3")

        def _put(d, tm):
            datai = x.path + "/data3.1" + d
            fwrite(datai, d)

            co = x.get('sha256', d2s[d])
            co.save(datai, link=False)
            # We need ordering
            os.utime(co.filename, (tm, tm))
            del co.size
        now = time.time() - 100
        for num in range(1, 9):
            _put("a"*num, now + num)
            _put("b"*num, now + num + 0.5)
        fwrite(x.path + "/config", "lo = 40 \n hi = 40\n")
        self.assertEqual(16, len(list(x.ls())))
        self.assertEqual((40, 40, 8 * 60 * 60 * 24, "atime"), x._get_config())
        x.cleanup()
        self.assertEqual(5, len(list(x.ls())))
        fwrite(x.path + "/config", "lo = 4 \n hi = 4\n")
        self.assertEqual((4, 4, 8 * 60 * 60 * 24, "atime"), x._get_config())
        x.cleanup()
        self.assertEqual(0, len(list(x.ls())))

    def test3_2_cleanup(self):
        x = cashe.CAShe(self.tdir + "/test3")

        def _put(d, tm):
            datai = x.path + "/data3.1" + d
            fwrite(datai, d)

            co = x.get('sha256', d2s[d])
            co.save(datai, link=False)
            # We need ordering
            os.utime(co.filename, (tm, tm))
            del co.size
        now = time.time() - 100
        for num in range(1, 9):
            _put("a"*num, (now - num) + 0.5)
            _put("b"*num,  now - num)
        fwrite(x.path + "/config", "lo = 40 \n hi = 40\n")
        self.assertEqual(16, len(list(x.ls())))
        self.assertEqual((40, 40, 8 * 60 * 60 * 24, "atime"), x._get_config())
        x.cleanup()
        self.assertEqual(11, len(list(x.ls())))
        fwrite(x.path + "/config", "lo = 4 \n hi = 4\n")
        self.assertEqual((4, 4, 8 * 60 * 60 * 24, "atime"), x._get_config())
        x.cleanup()
        self.assertEqual(3, len(list(x.ls())))



# Main
if __name__ == '__main__':
    unittest.main()

