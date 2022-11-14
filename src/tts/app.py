import os
from redis import Redis
import json
from fairseq.checkpoint_utils import load_model_ensemble_and_task_from_hf_hub
from fairseq.models.text_to_speech.hub_interface import TTSHubInterface
import torchaudio
import torch
from dotenv import load_dotenv
from pathlib import Path

if Path("../.env").is_file():
    load_dotenv("../.env")
REDIS_HOSTNAME = os.environ['REDIS_HOSTNAME']
REDIS_PORT = int(os.environ['REDIS_PORT'])

models, cfg, task = load_model_ensemble_and_task_from_hf_hub(
    "facebook/tts_transformer-ru-cv7_css10",
    arg_overrides={"vocoder": "hifigan", "fp16": False, }
)
TTSHubInterface.update_cfg_with_data_cfg(cfg, task.data_cfg)
generator = task.build_generator(models, cfg)

redis_client = Redis(host=REDIS_HOSTNAME, port=REDIS_PORT, db=0)
redis_subscriber = redis_client.pubsub()
redis_subscriber.subscribe("text")

while True:
    message = redis_subscriber.get_message()
    if message and message['type'] == "message":
        channel = message['channel'].decode("utf-8")
        request = json.loads(message['data'].decode("utf-8"))
        print("Input:", request)
        if channel == "text":
            sample = TTSHubInterface.get_model_input(task, request['text'])
            waveform, sample_rate = TTSHubInterface.get_prediction(task, models[0], generator, sample)
            torchaudio.save('response.mp3', torch.unsqueeze(waveform, 0), sample_rate, format='mp3')
            with open("response.mp3", 'rb') as f:
                response = {
                    'audio': list(f.read()),
                    'chat_id': request['chat_id']
                }
                print("Output:", response)
                redis_client.publish(channel="audio", message=json.dumps(response))
            os.remove("response.mp3")