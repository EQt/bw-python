import sys
import glob
import subprocess
import os.path as op
import os
from cffi import FFI
from distutils.ccompiler import gen_preprocess_options, show_compilers


def find_curl():
    """Return prefix to libcurl (or None if not found)"""
    p = subprocess.Popen("curl-config --prefix",
                         stderr=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         shell=True)
    prefix = p.stdout.read().strip()
    err = p.stderr.read().decode().strip()
    if err:
        sys.stdout.write(err)
        sys.stdout.write('\n')
        return None
    return prefix


HERE = op.dirname(op.abspath(op.dirname(__file__))) or "."
compiler_args = []
curl_prefix = find_curl()
if not curl_prefix:
    compiler_args += gen_preprocess_options(macros=[('NOCURL', 1)],
                                            include_dirs=[])
ffi = FFI()

# include "curl/curl.h"
# include "{path}/bw/curl_constants.h"
# include "{path}/libBigWig/bwValues.h"

sources = glob.glob("{path}/libBigWig/*.c".format(path=HERE))
ffi.set_source("bw._bigwig", """
#include "{path}/libBigWig/bigWig.h"
#include <stdlib.h>
""".format(path=HERE),
               libraries=["c", "curl"] if curl_prefix else [],
               sources=sources,
               include_dirs=["/usr/local/include/",
                             "%s/include/" % curl_prefix if curl_prefix else ""],
               extra_compile_args=compiler_args)

if curl_prefix:
    ffi.cdef(open("{path}/bw/curl_constants.h".format(path=HERE)).read())
else:
    ffi.cdef("typedef int CURLcode;")

ffi.cdef("""
typedef void CURL;

typedef struct {
    int64_t nKeys; /**<The number of chromosomes */
    char **chrom; /**<A list of null terminated chromosomes */
    uint32_t *len; /**<The lengths of each chromosome */
} chromList_t;

typedef struct { ...; } bwRTree_t;
typedef struct { ...; } URL_t;
typedef struct { ...; } bwOverlapBlock_t;
typedef struct { ...; } bwRTreeNode_t;
typedef struct {
    chromList_t *cl;
    ...;
} bigWigFile_t;


typedef struct {
    uint32_t l; /**<Number of intervals held*/
    uint32_t m; /**<Maximum number of values/intervals the struct can hold*/
    uint32_t *start; /**<The start positions (o-based half open)*/
    uint32_t *end; /**<The end positions (0-based half open)*/
    float *value; /**<The value associated with each position*/
} bwOverlappingIntervals_t;


bigWigFile_t *bwOpen(char *fname, CURLcode (*callBack)(CURL*),
                     const char* mode);
void bwClose(bigWigFile_t *fp);

bwOverlappingIntervals_t *bwGetValues(bigWigFile_t *fp, char *chrom,
                                      uint32_t start, uint32_t end,
                                      int includeNA);
void bwDestroyOverlappingIntervals(bwOverlappingIntervals_t *o);

enum bwStatsType {
    doesNotExist = -1,
    mean = 0,
    average = 0,
    stdev = 1,
    dev = 1,
    max = 2,
    min = 3,
    cov = 4,
    coverage = 4,
};

double *bwStats(bigWigFile_t *fp, char *chrom, uint32_t start, uint32_t end,
                uint32_t nBins,
                enum bwStatsType type);


uint32_t bwGetTid(bigWigFile_t *fp, char *chrom);

void free(void *);

bwOverlappingIntervals_t *bwGetOverlappingIntervals(bigWigFile_t *fp,
                                                    char *chrom,
                                                    uint32_t start,
                                                    uint32_t end);

""")


if __name__ == "__main__":
    show_compilers()
    ffi.compile()
