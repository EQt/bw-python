from ._bigwig import lib, ffi
from collections import namedtuple
import array

Interval = namedtuple('Interval', ['chrom', 'start', 'end', 'value'])

class BigWig(object):
    """
    >>> b = BigWig("libBigWig/test/test.bw")
    >>> b
    BigWig('libBigWig/test/test.bw')
    >>> for interval in b("1", 0, 99):
    ...     interval
    Interval(chrom='1', start=0, end=1, value=0.10000000149011612)
    Interval(chrom='1', start=1, end=2, value=0.20000000298023224)
    Interval(chrom='1', start=2, end=3, value=0.30000001192092896)

    # default is to include all values
    >>> b.values("1", 0, 9)
    array('f', [0.10000000149011612, 0.20000000298023224, 0.30000001192092896, nan, nan, nan, nan, nan, nan])
    >>> b.values("1", 0, 9, False)
    array('f', [0.10000000149011612, 0.20000000298023224, 0.30000001192092896])

    >>> b.stats("1", 0, 9)
    0.2000000054637591

    >>> b.stats("1", 0, 9, stat="stdev")
    0.10000000521540645

    >>> b.stats("1", 0, 4, stat="coverage")
    0.75
    >>> b.stats("1", 0, 4, stat="coverage", nBins=2)
    array('d', [1.0, 0.5])

    #b.stats("chr1", 0, 10)

    >>> b.close()
    """

    def __init__(self, path):
        self.bw = lib.bwOpen(path.encode(), ffi.NULL, "r".encode())
        self.path = path

    def close(self):
        return lib.bwClose(self.bw)

    @property
    def chroms(self):
        seqs = self.bw.cl
        return [(ffi.string(seqs.chrom[i]).decode(),
                 seqs.len[i]) for i in range(seqs.nKeys)]

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, self.path)

    def __call__(self, chrom, start, end, includeNA=False):
        intervals = lib.bwGetValues(self.bw, chrom.encode(), start, end, int(includeNA))
        for i in range(intervals.l):
            yield Interval(chrom, intervals.start[i], intervals.start[i] + 1, intervals.value[i])
        lib.bwDestroyOverlappingIntervals(intervals)

    def values(self, chrom, start, end, includeNA=True):
        intervals = lib.bwGetValues(self.bw, chrom.encode(), start, end, int(includeNA))
        a = array.array('f')
        if intervals != ffi.NULL and intervals.l != 0:
            a.frombytes(ffi.buffer(intervals.value[0:intervals.l]))
        lib.bwDestroyOverlappingIntervals(intervals)
        return a

    def stats(self, chrom, start, end, stat="mean", nBins=1):
        ops = ("mean", "stdev", "max", "min", "coverage")
        assert stat in ops, stat
        itype = ops.index(stat)
        res = lib.bwStats(self.bw, chrom.encode(), start, end, nBins, itype)
        if res == ffi.NULL:
            return [] if nBins > 1 else None
        a = array.array('d')
        a.fromstring(ffi.buffer(res[0:nBins]))
        ffi.gc(res, lib.free)
        if nBins == 1:
            return a[0]
        return a

if __name__ == "__main__":
    import doctest
    import sys
    sys.stderr.write(str(doctest.testmod()) + "\n")
