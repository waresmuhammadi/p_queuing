import os
import threading
import pika

# -----------------------------------------------------------------------------
# RabbitMQ Connection Pool
# -----------------------------------------------------------------------------

_connection_pool = []
_pool_lock = threading.Lock()
MAX_POOL_SIZE = int(os.getenv("RABBITMQ_POOL_SIZE", 5))

def get_connection():
    """
    Get a pika BlockingConnection from the pool or create a new one.
    """
    with _pool_lock:
        if _connection_pool:
            return _connection_pool.pop()

    creds = pika.PlainCredentials(
        os.getenv("RABBITMQ_USER", "guest"),
        os.getenv("RABBITMQ_PASS", "guest")
    )
    params = pika.ConnectionParameters(
        host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
        port=int(os.getenv("RABBITMQ_PORT", 5672)),
        credentials=creds,
        heartbeat=600,
        blocked_connection_timeout=300
    )
    return pika.BlockingConnection(params)

def return_connection(conn):
    """
    Return a connection to the pool or close if pool is full or connection is closed.
    """
    with _pool_lock:
        if conn.is_open and len(_connection_pool) < MAX_POOL_SIZE:
            _connection_pool.append(conn)
        else:
            try:
                conn.close()
            except:
                pass

# -----------------------------------------------------------------------------
# In-Memory Task Result Store
# -----------------------------------------------------------------------------

_RESULTS = {}
_RESULTS_LOCK = threading.Lock()

def update_result(task_id, status, result=None, error=None):
    """
    Create or update a task result entry.

    - status: one of 'queued', 'processing', 'success', 'error'
    - result: arbitrary payload (e.g., base64-encoded data) or None
    - error: error message string or None
    """
    entry = {
        "status": status,
        "result": result,
        "error": error
    }
    with _RESULTS_LOCK:
        _RESULTS[task_id] = entry

def get_result(task_id):
    """
    Retrieve the task result entry for a given task_id.
    Returns None if not found.
    """
    with _RESULTS_LOCK:
        return _RESULTS.get(task_id)
