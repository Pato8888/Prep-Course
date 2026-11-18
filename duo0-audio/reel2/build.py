import subprocess, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H=1080,1920; FPS=30
V='/tmp/claude-0/-home-user-Prep-Course/b6f0f4eb-f511-5f0d-b969-417055985b66/scratchpad/videos/'
HF='/home/user/Prep-Course/duo0-audio/higgsfield/'
R='/home/user/Prep-Course/duo0-audio/reel2/'
T='/tmp/claude-0/r2/'; os.makedirs(T,exist_ok=True)
F='/usr/local/share/fonts/montserrat/Montserrat-'
PINK=(216,119,154); LOGO_W='/home/user/Prep-Course/duo0-audio/logo-duo0-blanco.png'
OUT='/home/user/Prep-Course/Videos con Claude/exportados/'
def run(c): subprocess.run(c,check=True)
def font(w,s): return ImageFont.truetype(F+w+'.ttf',s)
shots=[(V+'IMG_8799.mov',9.0,2.0),(V+'IMG_8799.mov',68.0,1.5),(V+'IMG_8795.mov',2.5,1.5),
       (V+'IMG_8809.mov',7.0,1.5),(V+'IMG_8809.mov',25.0,1.5),(HF+'kling25-cierre.mp4',0,2.5)]
END=sum(s[2] for s in shots)  # 10.5
parts=[]
for i,(s,ss,d) in enumerate(shots):
    o=f'{T}s{i:02d}.mp4'; parts.append(o)
    run(['ffmpeg','-v','error','-y','-ss',str(ss),'-i',s,'-t',str(d),'-an','-vf',f'scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},format=yuv420p,eq=brightness=0.01:contrast=1.03','-c:v','libx264','-crf','18','-preset','fast',o])
ec=Image.new('RGB',(W,H),PINK); lg=Image.open(LOGO_W); lg=lg.resize((640,round(640*lg.height/lg.width))); ec.paste(lg,((W-640)//2,H//2-40-lg.height//2),lg)
ImageDraw.Draw(ec).text((W/2,H/2+110),'duo0.co',font=font('Regular',54),fill='white',anchor='mm'); ec.save(T+'endcard.png')

open(T+'list.txt','w').write(''.join(f"file '{p}'\n" for p in parts))
run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',T+'list.txt','-c','copy',T+'base.mp4'])
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
EB,EB68,R56,B54=font('ExtraBold',76),font('ExtraBold',68),font('Bold',54),font('Bold',54)
HOOKS_ALL={'A':[('Discutir quién limpia',EB),('el baño:',EB),('3 días sin hablarse',R56)],
       'B':[('¿Quién limpia',EB),('el baño hoy?',EB),('Spoiler: ninguno de los dos',R56)]}
HOOKS={'A':HOOKS_ALL['A']}
wm=Image.new('RGBA',(W,H),(0,0,0,0)); lg=Image.open(LOGO_W); lg=lg.resize((170,round(170*lg.height/lg.width))); lg.putalpha(lg.split()[3].point(lambda v:int(v*0.4))); wm.paste(lg,(70,250),lg); wm.save(T+'wm.png')
for v,hook in HOOKS.items():
    ov=[(card('hook'+v,hook,400),0,3.5),
        (card('duo',[('Un Duo0:',EB68),('1 hora · 2 personas · $31.000',R56)],400),3.5,6.5),
        (card('vienen',[('Vienen dos.',EB68),('Nadie discute.',R56)],400),6.5,8.0),
        (card('cta',None,820,('Comentá PAZ',font('ExtraBold',84),PINK,'white',40)),8.0,END),
        (T+'wm.png',0,END)]
    inp=['-i',T+'base.mp4']; fc=''; last='0:v'
    for i,(p,a,b) in enumerate(ov):
        inp+=['-i',p]; fc+=f"[{last}][{i+1}:v]overlay=0:0:enable='between(t,{a},{b})'[v{i}];"; last=f'v{i}'
    inp+=['-i',R+'musica.mp3']; n=len(ov)+1
    fc+=f"[{n}:a]atrim=0:{END},afade=t=out:st={END-1.6}:d=1.6,loudnorm=I=-14:TP=-1.5:LRA=11[a]"
    tmp=T+f'v{v}.mp4'
    run(['ffmpeg','-v','error','-y',*inp,'-filter_complex',fc,'-map',f'[{last}]','-map','[a]','-t',str(END),'-c:v','libx264','-crf','19','-preset','medium','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',tmp])
    # second-pass loudness
    import json,re
    m=subprocess.run(['ffmpeg','-nostats','-i',tmp,'-af','loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json','-f','null','-'],capture_output=True,text=True).stderr
    d=json.loads(m[m.rindex('{'):m.rindex('}')+1])
    P=f"measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}:offset={d['target_offset']}"
    out=OUT+f'duo0-reel2-bano-{v}-v2.mp4'
    run(['ffmpeg','-v','error','-y','-i',tmp,'-c:v','copy','-af',f'loudnorm=I=-14:TP=-1.5:LRA=11:{P}:linear=true','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',out])
    print('ok',out)
