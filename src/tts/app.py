import os
from redis import Redis
import json
from gtts import gTTS

redis_client = Redis(host="0.0.0.0", port=6379, db=0)
redis_subscriber = redis_client.pubsub()
redis_subscriber.subscribe("text")

while True:
    message = redis_subscriber.get_message()
    if message and message['type'] == "message":
        channel = message['channel'].decode("utf-8")
        request = json.loads(message['data'].decode("utf-8"))
        print("Input:", request)
        if channel == "text":
            tts = gTTS(text=request['text'], lang='ru')
            tts.save('response.mp3')
            with open("response.mp3", 'rb') as f:
                response = {
                    'audio': list(f.read()),
                    'chat_id': request['chat_id']
                }
                print("Output:", response)
                redis_client.publish(channel="audio", message=json.dumps(response))
            os.remove("response.mp3")