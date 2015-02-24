#! /usr/bin/python -t

import cashe
import os
import tempfile
import shutil

import unittest

_tmptest = True

def _cleanup(tdir):
    if _tmptest:
        shutil.rmtree(tdir)

# Data to sha256 checksums ...
d2s = {
    'a'     :'ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb',
    'aa'    :'961b6dd3ede3cb8ecbaacbd68de040cd78eb2ed5889130cceb4c49268ea4d506',
    'b'     :'3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d',
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
        # print "JDBG: ls:", list(x.ls())

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



# Main
if __name__ == '__main__':
    unittest.main()

