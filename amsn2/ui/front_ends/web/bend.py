import os
import socket
import errno
import logging
import urlparse
import gobject

READ_CHUNK_SIZE = 4096
BASEPATH="amsn2/ui/front_ends/web/static"

class TinyHTTPServer(object):
    def __init__(self, backend, socket, peer):
        self._backend = backend
        self._socket = socket
        self._peer = peer

        self._rbuf = ""
        self._wbuf = ""
        self._read = 0
        self._written = 0

        self._read_delimiter = "\r\n\r\n"
        self._rcb = self.on_headers

        self._is_alive = True

        print socket
        print self
        gobject.io_add_watch(socket, gobject.IO_IN, self.on_read)

    def close(self):
        if self._is_alive:
            self._is_alive = False
            self._socket.close()
            print "closing %s" % (self)
            self._socket = None

    def write(self, data):
        if self._is_alive:
            self._wbuf += data
            gobject.io_add_watch(self._socket, gobject.IO_OUT, self.on_write)
            self.on_write(self._socket, gobject.IO_OUT)

    def on_headers(self, headers):
        eol = headers.find("\r\n")
        start_line = headers[:eol]
        method, uri, version = start_line.split(" ")
        print "method=%s, uri=%s, version=%s" % (method, uri, version)
        if not version.startswith("HTTP/"):
            self.close()
            return
        print uri
        if uri == "/" and method == "GET":
            self.send_file("amsn2.html")
            return
        scheme, netloc, path, query, fragment = urlparse.urlsplit(uri)
        print "scheme=%s, netloc=%s, path=%s, query=%s, fragment=%s" % (scheme, netloc, path, query, fragment)

    def on_read(self, s, c):
        try:
            chunk = self._socket.recv(READ_CHUNK_SIZE)
        except socket.error, e:
            if e[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
                return self._is_alive
            else:
                logging.warning("Read error on %d: %s",
                                self._socket.fileno(), e)
                self.close()
                return self._is_alive
        if not chunk:
            self.close()
            return self._is_alive

        self._rbuf += chunk
        self._read += len(chunk)
        if self._read >= 16777216:
            logging.error("Reached maximum read buffer size")
            self.close()
            return self._is_alive

        pos = self._rbuf.find(self._read_delimiter)
        if pos != -1:
            pos += len(self._read_delimiter)
            r = self._rbuf[:pos]
            self._rbuf = self._rbuf[pos:]
            self._rcb(r)
        return self._is_alive

    def on_write(self, s, c):
        print self
        while self._wbuf:
            try:
                b = self._socket.send(self._wbuf)
                self._wbuf = self._wbuf[b:]
            except socket.error, e:
                if e[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
                    break
                else:
                    logging.warning("Write error on %d: %s",
                                    self._socket.fileno(), e)
                    self.close()
                    return self._is_alive
        return self._is_alive

    def send_file(self, path):
        f = open(os.path.join(BASEPATH, path), "r")
        r = f.read()
        f.close()
        self.write("HTTP/1.1 200 OK\r\nContent-Length: %d\r\n\r\n%s"
                   % (len(r), r))
        self.close()



class Backend(object):
    """
    This is the main comunication module,
    all comunication to the JS frontend will be issued from here
    """
    def __init__(self, core):
        self._core = core
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setblocking(0)
        self._socket.bind(("127.0.0.1", 8080))
        self._socket.listen(1)

        gobject.io_add_watch(self._socket, gobject.IO_IN, self.on_accept)

    def on_accept(self, s, c):
        w = s.accept()
        TinyHTTPServer(self, *w)
        return True


        """
        self.listeners = {}
        self._outq = Queue.Queue(0)
        self._inq = Queue.Queue(0)


        def worker(inq, outq):
            class Root(object):
                def __init__(self, inq, outq):
                    self._inq = inq
                    self._outq = outq

                @cherrypy.expose
                def index(self):
                    raise cherrypy.HTTPRedirect("static/amsn2.html")

                @cherrypy.expose
                def signin(self, u=None, p=None):
                    self._inq.put_nowait(["signin", u, p])

                @cherrypy.expose
                def out(self):
                    l = []
                    while True:
                        try:
                            l.append(self._outq.get_nowait())
                        except Queue.Empty:
                            break;
                    logging.error("OOOOOO")
                    return l

            current_dir = os.path.dirname(os.path.abspath(__file__))
            cherrypy.config.update({'log.error_file': 'amsn2-web-error.log',
                                   'log.access_file': 'amsn2-web-access.log',
                                   'log.screen': False})

            conf = {'/static': {'tools.staticdir.on': True,
                    'tools.staticdir.dir': os.path.join(current_dir, 'static')},
                   }
            cherrypy.quickstart(Root(inq, outq), '/', config=conf)
        t = threading.Thread(target=worker, args=[self._inq, self._outq])
        t.daemon = True
        t.start()
        """

    def add_listener(self, event, listener):
        return
        """
        if not self.listeners.has_key(event):
            self.listeners[event] = []
        self.listeners[event].append(listener)
        """

    def del_listener(self, event, listener):
        #TODO
        pass

    def check_event(self):
        """
        # This function is called to check for events
        while True:
            try:
                e = self._inq.get_nowait()
                self.emit_event(e[0], e[1:])
            except Queue.Empty:
                break;
        # Return true to continue checking events
        """
        return True

    def emit_event(self, event, *args, **kwargs):
        """
        if event in self.listeners.keys():
            for func in self.listeners[event]:
                try:
                    func(*args, **kwargs)
                except:
                    pass
        """

    def send(self, event, *args, **kwargs):
        # The backend sent a message to the JS client
        # select the JS function to call depending on the type of event
        call = event + "(["
        for value in args:
            call += "'" + str(value).encode('string_escape') + "',"
        call = call.rstrip(",") + "]);"
        #self._outq.put_nowait(call)
        print call
