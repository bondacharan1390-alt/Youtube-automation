import subprocess
import imageio_ffmpeg
import os

srt = os.path.abspath('test.srt')
with open(srt, 'w', encoding='utf-8') as f:
    f.write('1\n00:00:00,000 --> 00:00:02,000\nHello World\n')

# In FFmpeg, filename with drive letter C:\... needs:
# 1. Forward slashes
# 2. Escaping the colon: C\:
# 3. Filename quoted with single quotes or no quotes
clean_path = srt.replace('\\', '/')
# In ffmpeg filter syntax: subtitles=filename='C\:/path/to/file.srt'
esc = clean_path.replace(':', r'\:')

cmd = [
    imageio_ffmpeg.get_ffmpeg_exe(),
    '-y',
    '-f', 'lavfi',
    '-i', 'color=c=black:s=640x360:d=2',
    '-vf', f"subtitles=filename='{esc}'",
    '-c:v', 'libx264',
    'test_sub.mp4'
]
res = subprocess.run(cmd, capture_output=True, text=True)
print('Return:', res.returncode)
if res.returncode != 0:
    print('Stderr:', res.stderr[-400:])
else:
    print('Success! File size:', os.path.getsize('test_sub.mp4'))
