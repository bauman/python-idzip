python-idzip
============

Seekable, gzip compatible, compression format

Gzip allows to store extra fields in the gzip header. Idzip stores offsets for the efficient seeking there. 


Install
===============
python setup.py install

or 

[python-idzip RHEL6 signed RPM] (http://pkgs.bauman.in/repoview/python-idzip.html)

Acknowledgement
===============

based on https://code.google.com/p/idzip/

The file format was designed by Rik Faith for dictzip. Idzip just uses multiple gzip members to have no file size limit.

Idzip means Improved Dictzip. 



added a Writer class

Sizing
==========
downloaded

http://textfiles.com/stories/bureau.txt


cat several copies together up to 20GB > input.txt

gzfile generated using standard gzip

dzfile generated using this library

```
    total 50172612
    -rw-rw-r--. 1 dan dan 21313751280 May 10 15:58 input.txt
    -rw-rw-r--. 1 dan dan  8576570661 May 10 17:21 dzfile.txt.dz
    -rw-rw-r--. 1 dan dan  8076548622 May 10 16:28 gzfile.txt.gz
```


Size is almost the same as standard gzip


Seek Timing
==========
``` python
    seekpos = 21313751280 - 15
    from time import time
    
    start=time()
    original = open("/home/dan/ziptest/input.txt")
    original.seek(seekpos)
    original.close()
    print "Raw Seek to end", time() - start, "seconds"
    
    
    import gzip
    start=time()
    verify = gzip.open("/home/dan/ziptest/gzfile.txt.gz", "rb")
    verify.seek(seekpos)
    verify.close()
    print "Standard GZIP Seek to end", time() - start, "seconds"
    
    
    import idzip
    start=time()
    verify = idzip.open("/home/dan/ziptest/input.txt.dz")
    verify.seek(seekpos)
    verify.close()
    print "idzip Seek to end", time() - start, "seconds"

```

```
    Raw Seek to end 0.000866889953613 seconds
    Standard GZIP Seek to end 255.133864164 seconds
    idzip Seek to end 0.0381989479065 seconds
```




Stream Writer 
===========

class allows streaming.

``` python
    from idzip import Writer
    
    outfile = "/home/dan/ziptest/input1.txt.dz"
    writer = Writer(outfile, sync_size=1048576*100)
    infile = open("/home/dan/ziptest/input.txt", "rb")
    while True:
        data = infile.read(1048576+1)
        if not data:
        break
        writer.write(data)
    writer.close()
    infile.close()
```