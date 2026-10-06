"""Transactional outbox publisher and durable idempotent consumer."""
import os,json,time,argparse
import pika
from .store import Store

QUEUE='interceptiq.alerts'
def connect():
    connection=pika.BlockingConnection(pika.URLParameters(os.environ['RABBITMQ_URL']))
    channel=connection.channel()
    channel.exchange_declare(exchange='interceptiq.dead',exchange_type='fanout',durable=True)
    channel.queue_declare(queue='interceptiq.dead.alerts',durable=True)
    channel.queue_bind(queue='interceptiq.dead.alerts',exchange='interceptiq.dead')
    channel.queue_declare(queue=QUEUE,durable=True,arguments={'x-dead-letter-exchange':'interceptiq.dead'})
    return connection,channel

def publisher(store):
    connection,channel=connect(); channel.confirm_delivery()
    def send(message_id,payload):
        channel.basic_publish(exchange='',routing_key=QUEUE,body=json.dumps(payload),properties=pika.BasicProperties(content_type='application/json',delivery_mode=2,message_id=message_id),mandatory=True)
    try: return store.dispatch(send)
    finally: connection.close()

def consumer(store):
    connection,channel=connect(); channel.basic_qos(prefetch_count=1)
    def receive(ch,method,properties,body):
        try:
            message=json.loads(body)
            if not isinstance(message,dict) or not isinstance(message.get('message_id'),str): raise ValueError('Missing message identifier.')
        except (ValueError,TypeError):
            ch.basic_nack(delivery_tag=method.delivery_tag,requeue=False)
            print('Malformed message sent to dead-letter queue.',flush=True); return
        try:
            fresh=store.consume(message)
            print('stored' if fresh else 'duplicate',message['message_id'],flush=True)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception:
            ch.basic_nack(delivery_tag=method.delivery_tag,requeue=True)
            print('Storage failed; message requeued.',flush=True)
    channel.basic_consume(queue=QUEUE,on_message_callback=receive,auto_ack=False)
    try: channel.start_consuming()
    finally: connection.close()

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('mode',choices=['publish','consume']); parser.add_argument('--once',action='store_true'); args=parser.parse_args()
    store=Store(os.getenv('DATABASE_URL','sqlite:///interceptiq.db'))
    if args.mode=='consume': return consumer(store)
    while True:
        try: print('Published:',publisher(store),flush=True)
        except Exception as exc: print('Retrying broker connection:',type(exc).__name__,flush=True)
        if args.once: break
        time.sleep(3)
if __name__=='__main__': main()
