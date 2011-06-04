#!/usr/bin/python

import liblo, sys, os, getopt

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from urlparse import urlparse, parse_qs

# use globals for server settings

HTTP_IP = ''
HTTP_PORT = 8080

OSC_IP = 'localhost'
OSC_PORT = 10000

global OSC_target


def usage():
    """Print out usage options."""

    print """
    Simple HTTP-to-OpenSoundControl server.

    Parses querystring from '/send-osc/' request and sends them via OSC messages, otherwise acts as file server (be careful, this way you are exposing your filesystem --> ment only for closed LAN usage).

    Example: for request '/send-osc/?user1=bob&user2=alice' server will send OSC messages '/user1':'bob' and '/user2':'alice'.
    
    Options:
        [-h | --help]                    : prints this help
        [-l | --listen] IP_ADDR[:PORT]   : start http server on IP_ADDR:PORT; default: listens on all interfaces on port 8080
        [-o | --osc_dest] IP_ADDR[:PORT] : send OSC messages to IP_ADDR:PORT; default: sends to localhost on port 10000
        
    """
    return    


def init(argv=None):
    """Parses arguments and sets global options."""

    # set globals
    global HTTP_IP
    global HTTP_PORT    
    global OSC_IP
    global OSC_PORT

    # get args
    try:
        args, opts = getopt.getopt(argv, 'hl:o:', ['help', 'listen=', 'osc_dest='])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)

    for o, a in args:

        # help
        if o in ('-h', '--help'):
            usage()
            sys.exit()

        # http server listen
        elif o in ('-l', '--listen'):
            try:
                HTTP_IP, HTTP_PORT = a.split(':')
                HTTP_PORT = int(HTTP_PORT)
            except:
                HTTP_IP = a

        # osc destionation
        elif o in ('-o', '--osc_dest'):
            try:
                OSC_IP, OSC_PORT = a.split(':')
                OSC_PORT = int(OSC_PORT)
            except:
                OSC_IP = a

        else:
            assert False, "unhandled option"
            
    return


class MyHandler(BaseHTTPRequestHandler):
    """HTTP handler for simple file serving and parsing '/send-osc/' request to OSC."""
    
    def do_GET(self):

        # parse GET path
        url_object = urlparse(self.path)

        # if 'submit' parse querystring and send OSC messages
        if (url_object[2] == '/send-osc/'):

            # parse querystring ...
            params = parse_qs(url_object[4])
            print

            # ... and send values via OSC
            for key, values in params.iteritems():
                key = '/' + key
                for value in values:
                    liblo.send(OSC_target, key, value)
                    print "Sent OSC message: '%s':'%s'" % (key, value,)
                
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            return

        # else serve files
        try:
            f = open(os.curdir + os.sep + self.path)

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f.read())
            f.close()

        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)


def main(argv=None):
    """Main function, parses options and starts http server."""

    global OSC_target

    # set global parametars
    init(argv)

    # prepare OSC 
    try:
        OSC_target = liblo.Address(OSC_IP, OSC_PORT)
        print 'Sending OSC messages to %s:%d' % (OSC_IP, OSC_PORT)
    except liblo.AddressError, err:
        print str(err)

    # start HTTP server
    try:
        server = HTTPServer((HTTP_IP, HTTP_PORT), MyHandler)
        print 'Server listening on %s:%d' % (HTTP_IP, HTTP_PORT,)
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()


if __name__ == '__main__':
    main(sys.argv[1:])

