# $Header: //prod/main/ap/shrapnel/test/test_writev.py#3 $
# Copyright (c) 2006 IronPort Systems, Inc.
# All rights reserved.
# Unauthorized redistribution prohibited.

"""Unittests for writev socket call."""

__version__ = '$Revision: #3 $'

import socket
import sys
import unittest

import coro
import coro_unittest

current_buffer = ''
finished = None

send_buffer_size = 32768
recv_buffer_size = 32768

class TestServer:

    def serve(self, family, address):
        self.s = coro.make_socket(family, socket.SOCK_STREAM)
        self.s.setsockopt (socket.SOL_SOCKET, socket.SO_RCVBUF, recv_buffer_size)
        self.s.bind((address, 0))
        self.port = self.s.getsockname()[1]
        self.s.set_reuse_addr()
        self.s.listen(5)
        while 1:
            try:
                s, addr = self.s.accept()
            except coro.Shutdown:
                break
            session = TestSession(s, addr)
            coro.spawn(session.run)

class TestSession:

    def __init__(self, s, addr):
        self.s = s
        self.addr = addr

    def run(self):
        global current_buffer, finished
        current_buffer = ''
        received = 0
        while 1:
            block = self.s.recv(1024)
            if not block:
                break
            current_buffer = current_buffer + block
        self.s.close()
        finished.wake_all()
        finished = None

class Test(unittest.TestCase):

    def test_writev(self):
        """Test writev."""
        global send_buffer_size, recv_buffer_size

        big_block = '0123456789' * 1024 * 100

        def testit(family, address, block_sends, expected_buffer_result, expected_return):
            global finished
            finished = coro.condition_variable()
            s = coro.make_socket(family, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, send_buffer_size)
            coro.with_timeout(5, s.connect, (address, server.port))
            blocks = [ big_block[:size] for size in block_sends ]
            rc = coro.with_timeout(5, s.writev, blocks)
            s.close()
            if finished is not None:
                coro.with_timeout(5, finished.wait)
            self.assertEqual(expected_buffer_result, current_buffer)
            self.assertEqual(expected_return, rc)

        # Setting the send/recv buffer size to 1 causes writev to indicate it
        # was only able to send 1 byte before blocking.  This allows us to test
        # the "partial" buffer sent code path.
        to_test = [(socket.AF_INET, '127.0.0.1')]
        if coro.has_ipv6():
            to_test.append((socket.AF_INET6, '::1'))
        else:
            sys.stderr.write('Warning: No IPv6 support; skipping tests\n')
        for family, address in to_test:
            for bufsize in (32768, 1):
                send_buffer_size = bufsize
                recv_buffer_size = bufsize

                server = TestServer()
                server_thread = coro.spawn(server.serve, family, address)
                # Give the server a chance to start.
                coro.yield_slice()

                for greediness in (1024, 1):
                    coro.current().set_max_selfish_acts(greediness)
                    testit(family, address, (), '', 0)
                    testit(family, address, (5, 3, 7, 8), '01234012012345601234567', 23)
                    # bufsize==1 is too slow and not necessary
                    if bufsize != 1:
                        testit(family, address, (512 * 1024,), big_block[:512*1024], 512*1024)

                server_thread.raise_exception(coro.Shutdown)

if __name__ == '__main__':
    coro_unittest.run_tests()
