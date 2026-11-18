import subprocess, os, json
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H=1080,1920; FPS=30
V='/tmp/claude-0/-home-user-Prep-Course/b6f0f4eb-f511-5f0d-b969-417055985b66/scratchpad/videos/'
HF='/home/user/Prep-Course/duo0-audio/higgsfield/'
R='/home/user/Prep-Course/duo0-audio/reel2/'
T='/tmp/claude-0/r2r/'; os.makedirs(T,exist_ok=True)
F='/usr/local/share/fonts/montserrat/Montserrat-'
LOGO_W='/home/user/Prep-Course/duo0-audio/logo-duo0-blanco.png'
OUT='/home/user/Prep-Course/Videos con Claude/exportados/duo0-reel2-reina.mp4'
def run(c): subprocess.run(c,check=True)
def font(w,s): return ImageFont.truetype(F+w+'.ttf',s)
shots=[(V+'IMG_8799.mov',9.0,1.8),(V+'IMG_8799.mov',68.0,1.7),(V+'IMG_8795.mov',2.5,1.5),(V+'IMG_8809.mov',7.0,1.5),(HF+'kling25-cierre.mp4',0,2.5)]
END=round(sum(s[2] for s in shots),2)
parts=[]
for i,(s,ss,d) in enumerate(shots):
    o=f'{T}s{i:02d}.mp4'; parts.append(o)
    run(['ffmpeg','-v','error','-y','-ss',str(ss),'-i',s,'-t',str(d),'-an','-vf',f'scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},format=yuv420p,eq=brightness=0.01:contrast=1.03','-c:v','libx264','-crf','18','-preset','fast',o])
open(T+'list.txt','w').write(''.join(f"file '{p}'\n" for p in parts))
run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',T+'list.txt','-c','copy',T+'base.mp4'])
def card(name, lines, y, emoji=None):
    im=Image.new('RGBA',(W,H),(0,0,0,0))
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); sd=ImageDraw.Draw(sh); yy=y
    for txt,fnt in lines: sd.text((W/2+3,yy+4),txt,font=fnt,fill=(0,0,0,235),anchor='mm'); yy+=fnt.size*1.25
    shb=sh.filter(ImageFilter.GaussianBlur(7)); im=Image.alpha_composite(Image.alpha_composite(im,shb),shb); d=ImageDraw.Draw(im); yy=y
    for txt,fnt in lines: d.text((W/2,yy),txt,font=fnt,fill='white',anchor='mm'); last=(txt,fnt,yy); yy+=fnt.size*1.25
    if emoji:
        txt,fnt,ly=last; bb=d.textbbox((W/2,ly),txt,font=fnt,anchor='mm')
        e=Image.new('RGBA',(160,160),(0,0,0,0)); ImageDraw.Draw(e).text((0,0),emoji,font=ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',109),embedded_color=True)
        e=e.crop(e.getbbox()); sz=int(fnt.size*1.05); e=e.resize((sz,sz)); im.alpha_composite(e,(int(bb[2]+14),int(ly-sz/2)))
    im.save(T+name+'.png'); return T+name+'.png'
EB80,EB68,B56=font('ExtraBold',84),font('ExtraBold',68),font('Bold',56)
wm=Image.new('RGBA',(W,H),(0,0,0,0)); lg=Image.open(LOGO_W); lg=lg.resize((170,round(170*lg.height/lg.width))); lg.putalpha(lg.split()[3].point(lambda v:int(v*0.4))); wm.paste(lg,(70,250),lg); wm.save(T+'wm.png')
ov=[(card('hook',[('Reina,',EB80),('podés evitarte pelear',B56),('con tu marido por $31.000',B56)],400),0,3.5),
    (card('dos',[('vienen dos',EB68)],420,emoji='✨'),3.5,6.5),
    (card('final',[('Él va a decir',EB68),('que fue idea suya.',EB68),('Dejalo.',B56)],1130),6.5,END),
    (T+'wm.png',0,END)]
inp=['-i',T+'base.mp4']; fc=''; last='0:v'
for i,(p,a,b) in enumerate(ov):
    inp+=['-i',p]; fc+=f"[{last}][{i+1}:v]overlay=0:0:enable='between(t,{a},{b})'[v{i}];"; last=f'v{i}'
inp+=['-i',R+'musica.mp3']; n=len(ov)+1
fc+=f"[{n}:a]atrim=0:{END},afade=t=out:st={END-1.5}:d=1.5,loudnorm=I=-14:TP=-1.5:LRA=11[a]"
tmp=T+'tmp.mp4'
run(['ffmpeg','-v','error','-y',*inp,'-filter_complex',fc,'-map',f'[{last}]','-map','[a]','-t',str(END),'-c:v','libx264','-crf','19','-preset','medium','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',tmp])
m=subprocess.run(['ffmpeg','-nostats','-i',tmp,'-af','loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json','-f','null','-'],capture_output=True,text=True).stderr
d=json.loads(m[m.rindex('{'):m.rindex('}')+1])
P=f"measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}:offset={d['target_offset']}"
run(['ffmpeg','-v','error','-y','-i',tmp,'-c:v','copy','-af',f'loudnorm=I=-14:TP=-1.5:LRA=11:{P}:linear=true','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',OUT])
print('ok',END)
