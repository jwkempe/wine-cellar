"""Connection-pool recycling: dead pooled connections must never reach a request."""

import psycopg2
import pytest

import database


class FakeCursor:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def execute(self, query, *args):
        if self.conn.dead:
            raise psycopg2.OperationalError("server closed the connection unexpectedly")


class FakeConn:
    def __init__(self, dead=False):
        self.dead = dead
        self.closed = 0

    def cursor(self):
        return FakeCursor(self)

    def rollback(self):
        pass

    def commit(self):
        pass


class FakePool:
    maxconn = 5

    def __init__(self, conns):
        self.queue = list(conns)
        self.closed = []

    def getconn(self):
        return self.queue.pop(0)

    def putconn(self, conn, close=False):
        if close:
            self.closed.append(conn)
        else:
            self.queue.append(conn)


def test_checkout_skips_and_closes_dead_connections():
    alive = FakeConn()
    pool = FakePool([FakeConn(dead=True), FakeConn(dead=True), alive])
    assert database._checkout(pool) is alive
    assert len(pool.closed) == 2


def test_checkout_raises_when_no_connection_is_alive():
    pool = FakePool([FakeConn(dead=True) for _ in range(FakePool.maxconn + 1)])
    with pytest.raises(psycopg2.OperationalError):
        database._checkout(pool)
