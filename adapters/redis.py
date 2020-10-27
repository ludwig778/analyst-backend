import logging

from redis import StrictRedis

logger = logging.getLogger(__name__)


class RedisAdapter(object):
    def __init__(self, prefix=None, **kwargs):
        self.redis = StrictRedis(**kwargs)
        self.prefix = f"{prefix}:" if prefix else ""

    def _set_prefix(self, value):
        return f"{self.prefix}{value}"

    def set(self, key, value, **kwargs):
        return self.redis.set(self._set_prefix(key), value, **kwargs)

    def get(self, key):
        return self.redis.get(self._set_prefix(key))

    def delete(self, key):
        return self.redis.delete(self._set_prefix(key))

    def list(self, pattern="*"):
        return self.redis.keys(self._set_prefix(pattern))

    def delete_all(self):
        for k in self.list():
            self.redis.delete(k)
