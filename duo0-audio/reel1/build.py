import subprocess, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H=1080,1920; FPS=30
V='/tmp/claude-0/-home-user-Prep-Course/b6f0f4eb-f511-5f0d-b969-417055985b66/scratchpad/videos/'
HF='/home/user/Prep-Course/duo0-audio/higgsfield/'
R='/home/user/Prep-Course/duo0-audio/reel1/'
T='/tmp/claude-0/r1/'
F='/usr/local/share/fonts/montserrat/Montserrat-'
PINK=(216,119,154)
LOGO_W='/home/user/Prep-Course/duo0-audio/logo-duo0-blanco.png'
def run(c): subprocess.run(c,check=True)
# (src, start, dur)
import json
M=json.load(open(R+'marks.json')); END=round(M['fin']+0.25,2)
mid=round((M['precio']+M['vos'])/2,2)
shots=[(HF+'kling25-llegada.mp4',0,M['bano']),(V+'IMG_8799.mov',40.0,M['cocina']-M['bano']),(V+'IMG_8795.mov',6.0,1.32),
 (V+'IMG_8794.mov',13.0,M['living']-M['cocina']-1.32),(V+'IMG_8783.mov',11.5,M['tapiz']-M['living']),(V+'IMG_8809.mov',18.0,M['vidrios']-M['tapiz']),(V+'IMG_8807.mov',2.0,M['once']-M['vidrios']),
 (HF+'kling25-cierre.mp4',0,M['precio']-M['once']),(V+'IMG_8809.mov',28.0,mid-M['precio']),(V+'IMG_8794.mov',30.0,M['vos']-mid),(V+'IMG_8773.mov',0.5,M['cta']-M['vos']),
 (HF+'kling25-cierre.mp4',5.0-(END-M['cta']),END-M['cta'])]
parts=[]
for i,(s,ss,d) in enumerate(shots):
    o=f'{T}s{i:02d}.mp4'; parts.append(o)
    run(['ffmpeg','-v','error','-y','-ss',str(ss),'-i',s,'-t',str(d),'-an','-vf',f'scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},format=yuv420p,eq=brightness=0.01:contrast=1.03','-c:v','libx264','-crf','18','-preset','fast',o])
# end card
def font(w,s): return ImageFont.truetype(F+w+'.ttf',s)
ec=Image.new('RGB',(W,H),PINK); d=ImageDraw.Draw(ec)
lg=Image.open(LOGO_W); lg=lg.resize((640,round(640*lg.height/lg.width))); ec.paste(lg,((W-640)//2,H//2-40-lg.height//2),lg)
d.text((W/2,H/2+110),'duo0.co',font=font('Regular',54),fill='white',anchor='mm'); ec.save(T+'endcard.png')
run(['ffmpeg','-v','error','-y','-loop','1','-i',T+'endcard.png','-t','1.0','-vf',f'fps={FPS},format=yuv420p','-c:v','libx264','-crf','18',T+'s99.mp4']); parts.append(T+'s99.mp4')
open(T+'list.txt','w').write(''.join(f"file '{p}'\n" for p in parts))
run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',T+'list.txt','-c','copy',T+'base.mp4'])
# overlays
def card(name, lines, y, box=None):
    im=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    if box:
        txt,fnt,bg,fg,pad=box; bb=d.textbbox((W/2,y),txt,font=fnt,anchor='mm')
        d.rounded_rectangle((bb[0]-pad,bb[1]-pad*0.7,bb[2]+pad,bb[3]+pad*0.7),radius=26,fill=bg)
        d.text((W/2,y),txt,font=fnt,fill=fg,anchor='mm')
    else:
        sh=Image.new('RGBA',(W,H),(0,0,0,0)); sd=ImageDraw.Draw(sh); yy=y
        for txt,fnt in lines: sd.text((W/2+3,yy+4),txt,font=fnt,fill=(0,0,0,170),anchor='mm'); yy+=fnt.size*1.25
        im=Image.alpha_composite(im,sh.filter(ImageFilter.GaussianBlur(5))); d=ImageDraw.Draw(im); yy=y
        for txt,fnt in lines: d.text((W/2,yy),txt,font=fnt,fill='white',anchor='mm'); yy+=fnt.size*1.25
    im.save(T+name+'.png'); return T+name+'.png'
EB68,R56,B54,B52=font('ExtraBold',68),font('Regular',56),font('Bold',54),font('Bold',52)
ov=[]
ov.append((card('hook',[('Una hora.',font('ExtraBold',80)),('Limpiamos un 2 ambientes',R56),('entero.',R56)],380),0,M['bano']))
for t,a,b in [('10:00',0,M['bano']),('10:10',M['bano'],M['cocina']),('10:25',M['cocina'],M['living']),('10:40',M['living'],M['vidrios']),('10:55',M['vidrios'],M['once']),('11:00',M['once'],M['precio'])]:
    ov.append((card('clk'+t.replace(':',''),None,265,(t,B52,'white',PINK,26)),a,b))
for i,(txt,a,b) in enumerate([('Baño',M['bano'],M['cocina']),('Cocina',M['cocina'],M['living']),('Living',M['living'],M['tapiz']),('Tapizados',M['tapiz'],M['vidrios']),('Vidrios',M['vidrios'],M['once'])]):
    ov.append((card(f'cap{i}',[(txt,B54)],1180),a,b))
ov.append((card('listo',[('Once en punto.',B54),('Listo.',B54)],1150),M['once'],M['precio']))
ov.append((card('precio',None,330,('$31.000 · 1 hora · 2 personas',B52,PINK,'white',30)),M['precio'],M['vos']))
ov.append((card('capprecio',[('Una hora de Duo0: $31.000',B54),('y vienen dos',B54)],1150),M['precio'],M['vos']))
ov.append((card('elegis',[('Vos elegís',B54),('qué se limpia',B54)],1150),M['vos'],M['cta']))
ov.append((card('cta',None,820,('Comentá HORA',font('ExtraBold',84),PINK,'white',40)),M['cta'],END))
ov.append((card('ctacap',[('y te paso cómo reservar',B54)],1150),M['cta'],END))
wm=Image.new('RGBA',(W,H),(0,0,0,0)); lg=Image.open(LOGO_W); lg=lg.resize((170,round(170*lg.height/lg.width))); a=lg.split()[3].point(lambda v:int(v*0.4)); lg.putalpha(a); wm.paste(lg,(70,250),lg); wm.save(T+'wm.png'); ov.append((T+'wm.png',0,END))
inp=['-i',T+'base.mp4']; fc=''; last='0:v'
for i,(p,a,b) in enumerate(ov):
    inp+=['-i',p]; fc+=f"[{last}][{i+1}:v]overlay=0:0:enable='between(t,{a},{b})'[v{i}];"; last=f'v{i}'
inp+=['-i',R+'voz.mp3','-i',R+'musica.mp3']; nv=len(ov)+1
fc+=f"[{nv}:a]apad[vo];[{nv+1}:a]volume=-15dB,afade=t=out:st={END-0.4}:d=1.4[mu];[vo][mu]amix=inputs=2:duration=first:normalize=0,atrim=0:{END+1.0},loudnorm=I=-14:TP=-1.5:LRA=11[a]"
run(['ffmpeg','-v','error','-y',*inp,'-filter_complex',fc,'-map',f'[{last}]','-map','[a]','-t',str(END+1.0),'-c:v','libx264','-crf','19','-preset','medium','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart','/home/user/Prep-Course/Videos con Claude/exportados/duo0-reel1-una-hora-v2.mp4'])
print('ok')
