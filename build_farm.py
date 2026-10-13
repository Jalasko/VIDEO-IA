"""Build « La dernière pomme » (vertical 1080x1920 TikTok video).

    python3 build_farm.py --voice-dir /path/to/kokoro
    python3 build_farm.py --voice-dir ... --start 28 --end 38     # a clip
    python3 build_farm.py --voice-dir ... --mux-only               # audio only
"""
import argparse
import os
import subprocess
import sys
from multiprocessing import Pool

import soundfile as sf

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')


def _frame(i):
    from farm import render
    return render.render_frame(i)


def build_audio(voice_dir):
    from farm import voices, sound, scenes
    tracks, meta = voices.build(voice_dir)
    voices.save_meta(scenes.META, meta, voices.envelopes(tracks))
    path = os.path.join(OUT, 'farm_audio.wav')
    sf.write(path, sound.mix(tracks), sound.SR)
    return path


def main():
    from farm import story
    ap = argparse.ArgumentParser()
    ap.add_argument('--voice-dir', required=True)
    ap.add_argument('--start', type=float, default=0.0)
    ap.add_argument('--end', type=float, default=story.DURATION)
    ap.add_argument('--jobs', type=int, default=os.cpu_count())
    ap.add_argument('--out', default=os.path.join(OUT, 'la_derniere_pomme.mp4'))
    ap.add_argument('--mux-only', action='store_true')
    ap.add_argument('--skip-audio', action='store_true', help='reuse output/farm_audio.wav')
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    apath = os.path.join(OUT, 'farm_audio.wav') if a.skip_audio else build_audio(a.voice_dir)
    vpath = os.path.join(OUT, '_farm_video.mp4')
    if not a.mux_only:
        frames = range(int(a.start * story.FPS), int(a.end * story.FPS))
        ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                               '-s', '1080x1920', '-r', str(story.FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'slow',
                               '-crf', '18', '-pix_fmt', 'yuv420p', '-tune', 'animation', vpath], stdin=subprocess.PIPE)
        with Pool(a.jobs) as pool:
            for k, buf in enumerate(pool.imap(_frame, frames, chunksize=4)):
                ff.stdin.write(buf)
                if k % 60 == 0:
                    print(f'frame {k}/{len(frames)}', flush=True)
        ff.stdin.close()
        if ff.wait():
            sys.exit('ffmpeg failed')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', vpath, '-ss', str(a.start), '-t', str(a.end - a.start),
                    '-i', apath, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                    '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-movflags', '+faststart', '-shortest', a.out], check=True)
    print('wrote', a.out)


if __name__ == '__main__':
    main()
