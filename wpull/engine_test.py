# encoding=utf-8
import random

from trollius import From
import trollius

from wpull.engine import BaseEngine
from wpull.testing.async import AsyncTestCase
import wpull.testing.async


DEFAULT_TIMEOUT = 10


class MockEngineError(Exception):
    pass


class MockEngine(BaseEngine):
    def __init__(self, test_stop=False, test_exception=False):
        super().__init__()
        self.items = [1, 2, 3, 4]
        self.processed_items = []
        self._test_stop = test_stop
        self._test_exception = test_exception

    @trollius.coroutine
    def _get_item(self):
        if self.items:
            return self.items.pop(0)

    @trollius.coroutine
    def _process_item(self, item):
        if self._test_stop:
            self._stop()

        self.processed_items.append(item)

        if item == 4:
            self.items.append(5)

            if self._test_exception:
                raise MockEngineError()

        yield From(trollius.sleep(random.uniform(0.01, 0.5)))

    @trollius.coroutine
    def run(self):
        yield From(self._run_workers())

    @property
    def concurrent(self):
        return self._concurrent

    @concurrent.setter
    def concurrent(self, num):
        self._concurrent = num


class TestEngine(AsyncTestCase):
    @wpull.testing.async.async_test(timeout=DEFAULT_TIMEOUT)
    def test_base_engine(self):
        engine = MockEngine()
        yield From(engine.run())

        self.assertFalse(engine.items)
        self.assertEqual([1, 2, 3, 4, 5], engine.processed_items)

    @wpull.testing.async.async_test(timeout=DEFAULT_TIMEOUT)
    def test_base_engine_concurrency_under(self):
        engine = MockEngine()
        engine.concurrent = 2
        yield From(engine.run())

        self.assertFalse(engine.items)
        self.assertEqual([1, 2, 3, 4, 5], engine.processed_items)

    @wpull.testing.async.async_test(timeout=DEFAULT_TIMEOUT)
    def test_base_engine_concurrency_equal(self):
        engine = MockEngine()
        engine.concurrent = 4
        yield From(engine.run())

        self.assertFalse(engine.items)
        self.assertEqual([1, 2, 3, 4, 5], engine.processed_items)

    @wpull.testing.async.async_test(timeout=DEFAULT_TIMEOUT)
    def test_base_engine_concurrency_over(self):
        engine = MockEngine()
        engine.concurrent = 10
        yield From(engine.run())

        self.assertFalse(engine.items)
        self.assertEqual([1, 2, 3, 4, 5], engine.processed_items)

    @wpull.testing.async.async_test(timeout=DEFAULT_TIMEOUT)
    def test_base_engine_stop(self):
        engine = MockEngine(test_stop=True)
        yield From(engine.run())
        self.assertEqual([2, 3, 4], engine.items)
        self.assertEqual([1], engine.processed_items)

    @wpull.testing.async.async_test(timeout=DEFAULT_TIMEOUT)
    def test_base_engine_exception(self):
        engine = MockEngine(test_exception=True)
        try:
            yield From(engine.run())
        except MockEngineError:
            pass
        else:
            self.fail()
