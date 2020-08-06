import os
import re
import shutil
import subprocess
from concurrent import futures

from jinja2 import Environment, FileSystemLoader, select_autoescape
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip

pool = futures.ThreadPoolExecutor(max_workers=3)
titleExp = re.compile(r'(.*?) - (.*?) \((.*?)\)')

env = Environment(
    loader= FileSystemLoader('./templates'),
    autoescape=select_autoescape(['svg'])
)


def make_video(file):
    match = titleExp.match(str(file))
    if not match:
        print(f'{file} did not match the regex')
        raise ()
    print('')
    projectName = match.group(1)
    students = match.group(2)
    mentor = match.group(3)
    print(f'Generating video for project {projectName} ({students}) mentor {mentor}')

    template = env.get_template('titletemplate.svg')
    fileName = f'{projectName} - {students}'
    with open(fileName + '.svg', 'w+') as f:
        f.write(template.render(students=students, mentor=mentor))
    subprocess.run(['inkscape', '-z', '-f', f'./{fileName}.svg', '-e', f'./output/{fileName}.png'], shell=True)

    clip1 = ImageClip(f'output/{fileName}.png').set_duration(5)
    clip2 = VideoFileClip('input/' + file).resize(width=1920)
    clip3 = ImageClip('output/title.png').set_duration(5)
    final_clip = CompositeVideoClip([clip1,
                                     clip2.set_start(clip1.end - 1).crossfadein(1),
                                     clip3.set_start(clip1.end - 1 + clip2.end - 1).crossfadein(1)]).set_fps(30)
    final_clip.write_videofile(f"output/{fileName}.mp4")
    shutil.move(f'input/{file}',f'completed/{file}')


for file in os.listdir('input'):
    pool.submit(make_video, file)
