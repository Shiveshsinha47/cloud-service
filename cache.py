import redis
import json

r = redis.Redis(host="redis", port=6379, decode_responses=True)

def cache_file_list(user_id, data):
    r.set(f"user_files:{user_id}", json.dumps(data))

def get_cached_file_list(user_id):
    data = r.get(f"user_files:{user_id}")
    return json.loads(data) if data else None

def clear_user_cache(user_id):
    r.delete(f"user_files:{user_id}")