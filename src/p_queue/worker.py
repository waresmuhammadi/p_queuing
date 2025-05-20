import os
import json
from p_queue.utils import get_connection, return_connection, update_result
import pika

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
TASK_QUEUE = os.getenv("RABBITMQ_QUEUE", "pataka-tasks")

# -----------------------------------------------------------------------------
# Override this in your microservice
# -----------------------------------------------------------------------------
def process_task(payload):
    """
    Process the payload that was enqueued.
    Must return the result (e.g. a base64 image string) or
    raise an Exception on failure.
    """
    raise NotImplementedError("Please override process_task() with your logic")

# -----------------------------------------------------------------------------
# RabbitMQ Consumer Callback
# -----------------------------------------------------------------------------
def _on_message(ch, method, props, body):
    task_id = props.correlation_id

    # mark as processing
    update_result(task_id, "processing")

    try:
        task = json.loads(body)
        result = process_task(task.get("payload"))
        update_result(task_id, "success", result=result)
    except Exception as e:
        update_result(task_id, "error", error=str(e))

    ch.basic_ack(delivery_tag=method.delivery_tag)

# -----------------------------------------------------------------------------
# Worker Loop
# -----------------------------------------------------------------------------
def worker_loop():
    conn = get_connection()
    ch   = conn.channel()
    # ensure the queue exists
    ch.queue_declare(queue=TASK_QUEUE, durable=True)
    # only fetch one un‐acked message at a time
    ch.basic_qos(prefetch_count=1)
    # register the callback
    ch.basic_consume(queue=TASK_QUEUE, on_message_callback=_on_message)
    # start consuming (blocking)
    ch.start_consuming()

def main():
    """
    Entry point for the worker. Simply starts the loop.
    """
    print(f"[pataka-queuing] Worker starting, consuming from '{TASK_QUEUE}'…")
    worker_loop()

if __name__ == "__main__":
    main()
