import os
import re
import subprocess
from concurrent import futures

from jinja2 import Environment, FileSystemLoader, select_autoescape

pool = futures.ThreadPoolExecutor(max_workers=1)
titleExp = re.compile(r'(.*?) - (.*?) \((.*?)\)')

env = Environment(
    loader= FileSystemLoader('./templates'),
    autoescape=select_autoescape(['svg'])
)


def make_video(file):
    match = titleExp.match(str(file))
    if not match:
        print(f'{file} did not match the regex')
        return
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
    width = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=width', '-of', 'csv=p=0:s=,',f'./input/{file}'], shell=True, stdout = subprocess.PIPE).stdout
    if width == b'\r\n1280\r\n1280\r\n':
        width = 1280
    else:
        width = int(width)
    height = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'stream=height', '-of', 'csv=p=0:s=,', f'./input/{file}'],
        shell=True, stdout=subprocess.PIPE).stdout
    if height == b'\r\n720\r\n720\r\n':
        height = 720
    else:
        height=int(height)
    cleanFileName = fileName.replace(' ','').replace(',','').replace('-','')
    subprocess.run(['ffmpeg', '-n','-loop', '1', '-i', f'./output/{fileName}.png', '-c:v', 'libx264', '-t', '5', '-pix_fmt', 'yuv420p', '-vf', f'scale={width}:{height}', f'title-{fileName}.mp4'], shell=True)
    #subprocess.run(['ffmpeg', '-safe', '0', '-f', 'concat', '-i', f'title-{fileName}.mp4', '-i', f'./input/{file}', '-c', 'copy', f'./output/{fileName}.mp4'], shell=True)
    subprocess.run(['ffmpeg', '-n', '-i', f'title-{fileName}.mp4', '-c', 'copy', '-bsf:v', 'h264_mp4toannexb', '-f', 'mpegts', f'i1{cleanFileName}.ts'], shell=True)
    subprocess.run(['ffmpeg', '-n', '-i', f'./input/{file}', '-c', 'copy', '-bsf:v', 'h264_mp4toannexb', '-f', 'mpegts', f'i2{cleanFileName}.ts'], shell=True)
    with open('transcodecmds.bat','a+') as f:
        f.writelines(str(f'ffmpeg -i "concat:i1{cleanFileName}.ts|i2{cleanFileName}.ts" -c copy -bsf:a aac_adtstoasc "output/{fileName}.mp4"\n'))
    #subprocess.run(['ffmpeg', '-i', f'concat:i1{cleanFileName}.ts|i2{cleanFileName}.ts', '-c', 'copy', '-bsf:a', 'aac_adtstoasc', f'output/{fileName}.mp4'], shell=True)
for file in os.listdir('input'):
    make_video(file)
