# cython:  c_string_encoding=utf8

cdef extern from "stdio.h":
    pass

cdef extern from "stdlib.h":
    void free(void *)

cdef extern from "string.h":
    void *memcpy(void *s1, void *s2, int n)

cdef extern from "Python.h":
    object PyBytes_FromStringAndSize(char *s, int len)
    object PyBytes_FromString(char *s)
    int PyBytes_Size(object s)

    ctypedef int size_t
    void* PyMem_Malloc(size_t n)
    void PyMem_Free(void* buf)


cdef extern from "xpa.h":

    ctypedef struct XPARec

    XPARec *XPAOpen(char *mode)

    void XPAClose(XPARec *xpa)


    int XPANSLookup(XPARec *xpa,
                    char *template, char *type,
                    char ***classes, char ***names,
                    char ***methods, char ***infos)


    int XPAGet(XPARec *xpa,
               char *template, char *paramlist, char *mode,
               char **bufs, size_t *lens, char **names, char **messages,
               int n)

    int XPASet(XPARec *xpa,
               char *template, char *paramlist, char *mode,
               char *buf, int len, char **names, char **messages,
               int n)


class XpaException(Exception):
    pass


#this is the lookup only part of xpaaccess
#it returns a list of the XPA_METHODS which are registered
def nslookup(template="*"):
    cdef char **classes
    cdef char **names
    cdef char **methods
    cdef char **infos
    cdef int i, n
    cdef int iter

    #first run
    n = XPANSLookup(NULL, template, "g", &classes, &names, &methods, &infos)

    l = []

    for i from 0 <= i < n:
        #print "%s %s %s %s" % (classes[i], names[i], methods[i], infos[i])
        s = PyBytes_FromString(methods[i])
        l.append(s)
        free(classes[i])
        free(names[i])
        free(methods[i])
        free(infos[i])

    if n > 0:
        free(classes)
        free(names)
        free(methods)
        free(infos)


    return l



cdef _get(XPARec *xpa, char *template, char *param):
    cdef int  i, got
    cdef size_t  lens[1]
    cdef char *bufs[1]
    cdef char *names[1]
    cdef char *messages[1]

    got = XPAGet(NULL, template, param, NULL, bufs, lens, names, messages, 1)

    if got == 1 and messages[0] == NULL:
        buf = PyBytes_FromStringAndSize( bufs[0], lens[0] )
        #print buf
        free(bufs[0])
        free(names[0])
    else:
        if messages[0] != NULL:
            mesg = PyBytes_FromString( messages[0] )
            free(messages[0]);
        else:
            mesg = "Unknown XPA Error : XPAGet returned 0!"

        if ( names[0] ):
            free(names[0])
        if( bufs[0] ):
            free(bufs[0])
        raise XpaException(mesg)
    return buf

def get(template=b"*", param=b""):
    return _get(NULL, template, param)


cdef _set(XPARec *xpa, char *template, char *param, buf):
    cdef int  got
    cdef int  length
    cdef char *names[1]
    cdef char *messages[1]


    if buf:
        length = PyBytes_Size(buf)
    else:
        buf = b""
        length = 0

    got = XPASet(xpa, template, param, NULL, buf, length, names, messages, 1)

    if got == 1 and messages[0] == NULL:
        free(names[0])
    else:
        if messages[0] != NULL:
            mesg = PyBytes_FromString( messages[0] )
            free(messages[0]);
        else:
            mesg = "Unknown XPA Error (XPASet returned 0)!"

        if ( names[0] ):
            free(names[0])

        raise XpaException(mesg)


def set(template=b"*", param=b"", buf=None):
    _set(NULL, template, param, buf)


cdef class xpa:
    cdef XPARec *_xpa
    cdef char *_template

    cdef _set_template(self, template):
        cdef int n
        n = PyBytes_Size(template)
        self._template = <char *>PyMem_Malloc(n+1)
        memcpy(self._template, <char *>template, n+1)

    def __init__(self, template):
        self._set_template(template)
        self._xpa = XPAOpen("")

    def __del__(self):
        XPAClose(self._xpa)
        PyMem_Free(self._template)

    def get(self, param=b""):
        return _get(self._xpa, self._template, param)


    def set(self, param=b"", buf=None):
        _set(self._xpa, self._template, param, buf)
