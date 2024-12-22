import redis

redis_host = 'redis-16245.c246.us-east-1-4.ec2.redns.redis-cloud.com'
redis_port = 16245
redis_password = 'ZU76astAMvUtcrRnjvzR3AlhvAHoQA4s'

redis_client = redis.StrictRedis(
    host=redis_host,
    port=redis_port,
    password=redis_password,
    decode_responses=True
)

def test_redis_connection():
    try:
        # Attempt to use CLIENT LIST to check connectivity
        client_list = redis_client.client_list()
        print("Successfully connected to Redis. Client list:")
        print(client_list)
    except redis.exceptions.AuthenticationError:
        print("Authentication failed. Please check your password.")
    except redis.exceptions.ConnectionError:
        print("Connection error. Unable to reach Redis server.")
    except redis.exceptions.ResponseError as e:
        print("ResponseError:", e)
    except Exception as e:
        print("An error occurred:", e)

test_redis_connection()
