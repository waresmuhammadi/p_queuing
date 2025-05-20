import os
import json
import uuid
from flask import Flask, request, jsonify
from p_queue.utils import get_connection, return_connection, update_result, get_result

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
TASK_QUEUE = os.getenv("RABBITMQ_QUEUE", "pataka-tasks")

# -----------------------------------------------------------------------------
# Flask App Initialization
# -----------------------------------------------------------------------------
app = Flask(__name__)

@app.route("/enqueue", methods=["POST"])
def enqueue():
    """
    Enqueue a new task. Expects JSON or form fields:
      - 'payload': any JSON-serializable object

    Returns 202 with { status: "queued", task_id }.
    """
    data = request.get_json() or request.form.to_dict()
    if "payload" not in data:
        return jsonify(status="error", message="Missing 'payload'"), 400

    # Create a unique task ID
    task_id = str(uuid.uuid4())
    task = {
        "task_id": task_id,
        "payload": data["payload"]
    }

    # Mark it as queued
    update_result(task_id, "queued")

    # Publish to RabbitMQ
    conn = get_connection()
    ch = conn.channel()
    ch.queue_declare(queue=TASK_QUEUE, durable=True)
    ch.basic_publish(
        exchange="",
        routing_key=TASK_QUEUE,
        properties=pika.BasicProperties(
            correlation_id=task_id,
            content_type="application/json",
            delivery_mode=2
        ),
        body=json.dumps(task)
    )
    return_connection(conn)

    return jsonify(status="queued", task_id=task_id), 202

@app.route("/status/<task_id>", methods=["GET"])
def status(task_id):
    """
    Poll the status of a previously enqueued task.
    Returns JSON:
      - status: "queued" | "processing" | "success" | "error"
      - result (on success)
      - message (on error)
    """
    entry = get_result(task_id)
    if not entry:
        return jsonify(status="error", message="task_id not found"), 404

    status = entry["status"]
    if status in ("queued", "processing"):
        return jsonify(status=status), 200
    if status == "success":
        return jsonify(status="success", result=entry["result"]), 200
    # status == "error"
    return jsonify(status="error", message=entry["error"]), 500

@app.route("/", methods=["GET"])
def health():
    """Simple health check."""
    return jsonify(service="Pataka Queuing", status="active")

def main():
    port = int(os.getenv("SERVICE_PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True, debug=True)

if __name__ == "__main__":
    main()
