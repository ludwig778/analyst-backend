import logging

from redis import StrictRedis

logger = logging.getLogger(__name__)


class RedisAdapter(object):
    def __init__(self, **kwargs):
        self.redis = StrictRedis(**kwargs)

    def set(self, key, value, **kwargs):
        return self.redis.set(key, value, **kwargs)

    def get(self, key):
        return self.redis.get(key)

    def delete(self, key):
        return self.redis.delete(key)

    def list(self, pattern="*"):
        return self.redis.keys(pattern)
