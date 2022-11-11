import os
import wave
import json

import ffmpeg
from pytube import YouTube
from tqdm import tqdm
from vosk import Model, KaldiRecognizer

model = Model("models/vosk-model-en-us-0.22-lgraph", lang="en-us")


# model = Model(lang="en-us")


def analyze_yt(link, progbar=None, verbose=False):
    yt = YouTube(link)
    outfile = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().last().download(
        "download", skip_existing=True, filename=f"{yt.video_id}.mp4")
    return yt.title, analyze_video(outfile, progbar=progbar, verbose=verbose)


def analyze_video(video, progbar=None, verbose=False):
    print("analyze_video", video)
    audio = prep_audio(video)
    return os.path.basename(video), analyze_audio(audio, progbar=progbar, verbose=verbose)


def prep_audio(video):
    audio_track = video.replace(".mp4", ".wav")
    input = ffmpeg.input(video)
    stream = ffmpeg.output(input.audio, audio_track)
    ffmpeg.run(stream, overwrite_output=True)
    return audio_track


def analyze_audio(audio, progbar=None, verbose=False):
    global bar
    wf = wave.open(audio, "rb")
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
        print("Audio file must be WAV format mono PCM.")
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)
    rec.SetPartialWords(True)

    # get the list of JSON dictionaries
    results = []
    # recognize speech using vosk model
    c = 0
    if verbose: bar = tqdm(total=wf.getnframes())
    while True:
        data = wf.readframes(4000)
        c += 4000
        if verbose: bar.update(c)
        if len(data) == 0:
            break
        if progbar:
            progbar.UpdateBar(c, wf.getnframes())
        if rec.AcceptWaveform(data):
            part_result = json.loads(rec.Result())
            results.append(part_result)
        # else:
        #     results.append(json.load(rec.PartialResult()))

    part_result = json.loads(rec.FinalResult())
    results.append(part_result)
    with open(audio.replace(".wav", ".json"), "w") as f:
        json.dump(results, f)
    wf.close()  # close audiofile
    return results
