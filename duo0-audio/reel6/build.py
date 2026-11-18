import subprocess, os, json
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H=1080,1920; FPS=30
V='/tmp/claude-0/-home-user-Prep-Course/b6f0f4eb-f511-5f0d-b969-417055985b66/scratchpad/videos/'
V2='/tmp/claude-0/-home-user-Prep-Course/b6f0f4eb-f511-5f0d-b969-417055985b66/scratchpad/videos2/'
R='/home/user/Prep-Course/duo0-audio/reel6/'; T='/tmp/claude-0/r6/'; os.makedirs(T,exist_ok=True)
F='/usr/local/share/fonts/montserrat/Montserrat-'; PINK=(216,119,154); LOGO_W='/home/user/Prep-Course/duo0-audio/logo-duo0-blanco.png'
OUT='/home/user/Prep-Course/Videos con Claude/exportados/duo0-reel6-franquicia.mp4'
def run(c): subprocess.run(c,check=True)
def font(w,s): return ImageFont.truetype(F+w+'.ttf',s)
CROP='crop=956:1700:602:180,'   # SF05: crop to the face, leaves out the burned-in subtitles
# (src, start, dur, crop, keep_audio)
segs=[(V2+'SF05.mov',0.0,2.4,CROP,1),(V2+'SF05.mov',5.2,2.8,CROP,1),(V2+'SF05.mov',8.1,2.7,CROP,1),
      (V2+'SF05.mov',12.1,2.9,CROP,1),('BROLL',15.0,6.4,'',1),(V2+'SF05.mov',21.4,4.3,CROP,1),
      (V2+'SF05.mov',40.1,2.1,CROP,1),(V2+'SF03.mov',7.0,2.6,'',0)]
broll=[(V2+'SF03.mov',23.0,2.0),(V+'IMG_8795.mov',2.5,2.2),(V+'IMG_8809.mov',7.0,2.2)]
vparts=[]; aparts=[]
def vclip(src,ss,d,crop,o):
    run(['ffmpeg','-v','error','-y','-ss',str(ss),'-i',src,'-t',str(d),'-an','-vf',f'{crop}scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},format=yuv420p,eq=brightness=0.01:contrast=1.03','-c:v','libx264','-crf','18','-preset','fast',o])
for i,(src,ss,d,crop,ka) in enumerate(segs):
    if src=='BROLL':
        for j,(bs,bss,bd) in enumerate(broll):
            o=f'{T}v{i:02d}{j}.mp4'; vclip(bs,bss,bd,'',o); vparts.append(o)
        src=V2+'SF05.mov'
    else:
        o=f'{T}v{i:02d}.mp4'; vclip(src,ss,d,crop,o); vparts.append(o)
    a=f'{T}a{i:02d}.wav'
    if ka: run(['ffmpeg','-v','error','-y','-ss',str(ss),'-i',src,'-t',str(d),'-vn','-ac','2','-ar','48000',a])
    else: run(['ffmpeg','-v','error','-y','-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-t',str(d),a])
    aparts.append(a)
open(T+'vl.txt','w').write(''.join(f"file '{p}'\n" for p in vparts)); open(T+'al.txt','w').write(''.join(f"file '{p}'\n" for p in aparts))
run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',T+'vl.txt','-c','copy',T+'base.mp4'])
run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',T+'al.txt','-c','pcm_s16le',T+'voces.wav'])
END=round(sum(s[2] for s in segs),2)
def card(name, lines, y, box=None):
    im=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    if box:
        txt,fnt,bg,fg,pad=box; bb=d.textbbox((W/2,y),txt,font=fnt,anchor='mm')
        d.rounded_rectangle((bb[0]-pad,bb[1]-pad*0.7,bb[2]+pad,bb[3]+pad*0.7),radius=26,fill=bg); d.text((W/2,y),txt,font=fnt,fill=fg,anchor='mm')
    else:
        sh=Image.new('RGBA',(W,H),(0,0,0,0)); sd=ImageDraw.Draw(sh); yy=y
        for txt,fnt in lines: sd.text((W/2+3,yy+4),txt,font=fnt,fill=(0,0,0,235),anchor='mm'); yy+=fnt.size*1.25
        shb=sh.filter(ImageFilter.GaussianBlur(7)); im=Image.alpha_composite(Image.alpha_composite(im,shb),shb); d=ImageDraw.Draw(im); yy=y
        for txt,fnt in lines: d.text((W/2,yy),txt,font=fnt,fill='white',anchor='mm'); yy+=fnt.size*1.25
    im.save(T+name+'.png'); return T+name+'.png'
B54,EB68=font('Bold',54),font('ExtraBold',68)
o=7.9-12.1  # offset of the long testimony segment on the output timeline
caps=[('Hay semanas que',' ganamos $400.000',0,2.4),('Me llamo Vanesa','y tengo 42 años',2.4,5.2),('Claudia Marcela,','58 años',5.2,7.9),
 ('Y eso depende de los','clientes que tengamos',12.18+o,14.74+o),('Hay semanas que sacamos','$100.000 cada una',14.88+o,18.54+o),
 ('y hay semanas que','ganamos $400.000',18.54+o,21.52+o),('Todo depende de nuestra','disponibilidad y los clientes',21.68+o,25.7+o),
 ('A cada servicio','vamos dos personas',21.5,23.6)]
ov=[(card(f'cap{i}',[(a,B54),(b.strip(),B54)],1370),s,e) for i,(a,b,s,e) in enumerate(caps)]
ov.append((card('fr',[('+35 franquicias',EB68),('Alta sin costo',B54)],420),23.6,END))
ov.append((card('cta',None,1180,('Comentá INFO',font('ExtraBold',84),PINK,'white',40)),23.6,END))
wm=Image.new('RGBA',(W,H),(0,0,0,0)); lg=Image.open(LOGO_W); lg=lg.resize((170,round(170*lg.height/lg.width))); lg.putalpha(lg.split()[3].point(lambda v:int(v*0.4))); wm.paste(lg,(70,250),lg); wm.save(T+'wm.png'); ov.append((T+'wm.png',0,END))
inp=['-i',T+'base.mp4']; fc=''; last='0:v'
for i,(p,a,b) in enumerate(ov):
    inp+=['-i',p]; fc+=f"[{last}][{i+1}:v]overlay=0:0:enable='between(t,{a:.2f},{b:.2f})'[v{i}];"; last=f'v{i}'
inp+=['-i',T+'voces.wav','-i','/home/user/Prep-Course/duo0-audio/reel1/musica.mp3']; n=len(ov)+1
fc+=f"[{n}:a]highpass=f=80,acompressor=threshold=-20dB:ratio=3[vo];[{n+1}:a]volume=-17dB,atrim=0:{END},afade=t=out:st={END-1.5}:d=1.5[mu];[vo][mu]amix=inputs=2:duration=longest:normalize=0,atrim=0:{END},loudnorm=I=-14:TP=-1.5:LRA=11[a]"
tmp=T+'tmp.mp4'
run(['ffmpeg','-v','error','-y',*inp,'-filter_complex',fc,'-map',f'[{last}]','-map','[a]','-t',str(END),'-c:v','libx264','-crf','19','-preset','medium','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',tmp])
m=subprocess.run(['ffmpeg','-nostats','-i',tmp,'-af','loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json','-f','null','-'],capture_output=True,text=True).stderr
d=json.loads(m[m.rindex('{'):m.rindex('}')+1])
P=f"measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}:offset={d['target_offset']}"
run(['ffmpeg','-v','error','-y','-i',tmp,'-c:v','copy','-af',f'loudnorm=I=-14:TP=-1.5:LRA=11:{P}:linear=true','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',OUT])
print('ok',END)
