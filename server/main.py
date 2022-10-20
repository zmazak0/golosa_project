from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel

from encoder.params_model import model_embedding_size as speaker_embedding_size
from utils.argutils import print_args
from synthesizer.inference import Synthesizer
from encoder import inference as encoder
from vocoder import inference as vocoder
from pathlib import Path

import librosa
import argparse
import torch
import sys
from g2p.train import g2p
import soundfile as sf

class Item(BaseModel):
    text: str

device_id = torch.cuda.current_device()
gpu_properties = torch.cuda.get_device_properties(device_id)

def initialize():
    encoder.load_model("encoder/saved_models/pretrained.pt")
    synthesizer = Synthesizer("synthesizer/saved_models/logs-pretrained/".joinpath("taco_pretrained"), low_mem=True)
    vocoder.load_model("vocoder/saved_models/pretrained/pretrained.pt")

    encoder.embed_utterance(np.zeros(encoder.sampling_rate))
    in_fpath = "ex.wav"
    preprocessed_wav = encoder.preprocess_wav(in_fpath)
    original_wav, sampling_rate = librosa.load(in_fpath)
    preprocessed_wav = encoder.preprocess_wav(original_wav, sampling_rate)
    embed = encoder.embed_utterance(preprocessed_wav)
    return embed
    

app = FastAPI()
embed = initialize()

@app.post("/syntesys/")
async def create_item(item: Item, embed=embed):
    texts = [item.text]
    texts = g2p(texts)
    embeds = [embed]
    specs = synthesizer.synthesize_spectrograms(texts, embeds)
    spec = specs[0]
    generated_wav = vocoder.infer_waveform(spec)
    generated_wav = np.pad(generated_wav, (0, synthesizer.sample_rate), mode="constant")
    return generated_wav