"""Build "Bath Time Song": vocals -> audio mix -> frames -> MP4.

    python3 build.py --voice-dir /path/to/kokoro            # full video
    python3 build.py --voice-dir ... --vertical              # 9:16 for TikTok
    python3 build.py --voice-dir ... --start 10 --end 15     # render a clip
"""
import argparse
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
import soundfile as sf

from bath_time import song, music
from bath_time.gfx import W, H

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')


def _init(fmt):
    from bath_time import render
    render.set_format(fmt)


def _frame(i):
    from bath_time import render
    return render.render_frame(i)


def build_audio(voice_dir):
    os.makedirs(OUT, exist_ok=True)
    vpath = os.path.join(OUT, 'vocals.wav')
    if os.path.exists(vpath):
        vocals, _ = sf.read(vpath, dtype='float32')
    else:
        from bath_time import vocals as V
        vocals = V.build_vocals(voice_dir, music.SR)
        sf.write(vpath, vocals, music.SR)
    mix = music.mix(vocals)
    apath = os.path.join(OUT, 'audio.wav')
    sf.write(apath, mix, music.SR)
    return apath


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--voice-dir', required=True, help='folder with kokoro-v1.0.onnx and voices-v1.0.bin')
    ap.add_argument('--start', type=float, default=0.0)
    ap.add_argument('--end', type=float, default=song.DURATION)
    ap.add_argument('--jobs', type=int, default=os.cpu_count())
    ap.add_argument('--vertical', action='store_true', help='9:16 1080x1920 for TikTok / Reels / Shorts')
    ap.add_argument('--out', default=None)
    ap.add_argument('--mux-only', action='store_true', help='reuse the rendered video, rebuild audio only')
    args = ap.parse_args()

    fmt = 'vertical' if args.vertical else 'wide'
    out = args.out or os.path.join(OUT, 'bath_time_song_tiktok.mp4' if args.vertical else 'bath_time_song.mp4')
    apath = build_audio(args.voice_dir)
    vpath = os.path.join(OUT, '_video_vertical.mp4' if args.vertical else '_video.mp4')
    if not args.mux_only:
        render_video(vpath, args.start, args.end, args.jobs, fmt)
    mux(vpath, apath, args.start, args.end, out)


def render_video(vpath, start, end, jobs, fmt):
    from bath_time.render import FPS
    size = '1080x1920' if fmt == 'vertical' else f'{W}x{H}'
    frames = range(int(start * FPS), int(end * FPS))
    cmd = ['ffmpeg', '-y', '-loglevel', 'error',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', size, '-r', str(FPS), '-i', '-',
           '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-tune', 'animation', vpath]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = len(frames)
    with Pool(jobs, initializer=_init, initargs=(fmt,)) as pool:
        for k, buf in enumerate(pool.imap(_frame, frames, chunksize=4)):
            ff.stdin.write(buf)
            if k % 60 == 0:
                print(f'frame {k}/{n}', flush=True)
    ff.stdin.close()
    if ff.wait():
        sys.exit('ffmpeg failed')


def mux(vpath, apath, start, end, out):
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-i', vpath,
           '-ss', str(start), '-t', str(end - start), '-i', apath,
           '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
           '-c:a', 'aac', '-b:a', '192k', '-af', 'loudnorm=I=-15:TP=-1.5:LRA=11',
           '-movflags', '+faststart', '-shortest', out]
    subprocess.run(cmd, check=True)
    print('wrote', out)


if __name__ == '__main__':
    main()
