import vapoursynth as vs
core = vs.get_core()
import importlib.machinery
import mvsfunc as mvf
import havsfunc as hvf
import kagefunc as kgf
import vsTAAmbk as taa
import fvsfunc as fvf
from awsmfunc import bbmod
from adptvgrnMod import *
from vsutil import *
from xaa import xaa as oxaa
from xaa import xaa as exaa
src 	= core.lsmas.LWLibavSource(r'F:\F Entertainment\Anime\[BDMV] Inuyasha The Final Act - The Complete Series [USA]\INUYASHA_FINAL_ACT_14_20\BDMV\STREAM\00000.m2ts')
src32	= core.fmtc.bitdepth(src, bits=32)
ef		= bbmod(src32, top=2, bottom=2, left=4, right=4, thresh=33, blur=222, y=False, u=True, v=True, scale_thresh=True)
ef1		= bbmod(ef, top=0, bottom=0, left=12, right=12, thresh=5, blur=20, y=False, u=True, v=True, scale_thresh=True)
ef2		= bbmod(ef1, top=1, bottom=1, left=2, right=2, thresh=148, blur=222, y=True, u=False, v=False, scale_thresh=True)
ef3		= bbmod(ef2, top=0, bottom=0, left=8, right=11, thresh=8, blur=20, y=True, u=False, v=False, scale_thresh=True)
src16	= core.fmtc.bitdepth(ef3, bits=16)
txtmask	= get_y(src16).std.Binarize(50250,0).std.Maximum().std.Inflate().std.Inflate().std.Inflate().std.Inflate().std.BoxBlur(hradius=2, vradius=2) #this seems retarded but works well enough lol

#ep 18
uvdn 	= core.knlm.KNLMeansCL(ef3, d=3, a=3, h=0.44, channels = 'UV', device_type='gpu')
uv16 	= core.fmtc.bitdepth(uvdn, bits=16)
y, u, v = kgf.split(uv16)
dsc 	= kgf.inverse_scale(y, width=1280, height=720, kernel='bilinear', mask_detail=False, denoise=False, use_gpu=True)
y16 	= core.fmtc.bitdepth(dsc, bits=16)
pf 		= core.knlm.KNLMeansCL(dsc, d=3, a=3, h=0.77, channels = 'Y', device_type='gpu').fmtc.bitdepth(bits=16)
ydn 	= hvf.SMDegrain(y16, tr=2, thSAD=70, blksize=8, overlap=4, contrasharp=True, RefineMotion=True, prefilter=pf, chroma=False, pel=2, plane=0)
y420 	= core.resize.Point(ydn, format=vs.YUV420P16, dither_type=None)
rscfsr	= core.placebo.Shader(y420, shader=r'C:\Users\User\AppData\Roaming\mpv\shaders\FSRCNNX_x2_56-16-4-1.glsl', width=2560, height=1440)
rscnn3 	= ydn.nnedi3cl.NNEDI3CL(0, dh=True, dw=True, nsize=4, nns=4, qual=2, pscrn=1).resize.Spline36(src_top=.5, src_left=.5)
rscmerge = core.std.Merge(rscnn3, get_y(rscfsr), weight=0.5).resize.Spline36(1920, 1080)
joinyuv = kgf.join([rscmerge, u, v])
db 		= core.f3kdb.Deband(joinyuv, 18, grainc=16, grainy=0, y=64, cb=56, cr=56, output_depth=16)
dbmask 	= kgf.retinex_edgemask(joinyuv, sigma=3).std.Binarize(18888,0).std.BoxBlur(hradius=1, vradius=1)
dbmerge = core.std.MaskedMerge(db, joinyuv, dbmask, planes=[0,1,2], first_plane=True)
grain	= adptvgrnMod(dbmerge, strength=0.22, size=1.30, luma_scaling=33, static=True, grain_chroma=False, show_mask=False)

#op 23:2061 - 0.82
ouvdn		= core.knlm.KNLMeansCL(ef3, d=3, a=3, h=0.50, channels = 'UV', device_type='gpu')
ouv16		= core.fmtc.bitdepth(ouvdn, bits=16)
otxtdr		= hvf.HQDeringmod(ouv16, show=False, nrmode=2, sharp=1,  mthr=64, minp=1.3, mrad=1.3, msmooth=1, thr=20, darkthr=0)
otxtaa		= oxaa(otxtdr, mode='drh nnedi3cl', csharp=1, mask=0, chroma=0)
otxtdn		= core.fmtc.bitdepth(otxtaa, bits=32).knlm.KNLMeansCL(d=3, a=3, h=0.48, channels = 'Y', device_type='gpu').fmtc.bitdepth(bits=16)
oy, ou, ov	= kgf.split(ouv16)
odsc 		= kgf.inverse_scale(oy, width=1280, height=720, kernel='bilinear', mask_detail=True, denoise=False, use_gpu=True)
oy16 		= core.fmtc.bitdepth(odsc, bits=16)
opf 		= core.knlm.KNLMeansCL(odsc, d=3, a=3, h=0.82, channels = 'Y', device_type='gpu').fmtc.bitdepth(bits=16)
oydn 		= hvf.SMDegrain(oy16, tr=2, thSAD=74, blksize=8, overlap=4, contrasharp=True, RefineMotion=True, prefilter=opf, chroma=False, pel=2, plane=0)
oy420 	= core.resize.Point(oydn, format=vs.YUV420P16, dither_type=None)
orscfsr	= core.placebo.Shader(oy420, shader=r'C:\Users\User\AppData\Roaming\mpv\shaders\FSRCNNX_x2_56-16-4-1.glsl', width=2560, height=1440)
orscnn3 	= oydn.nnedi3cl.NNEDI3CL(0, dh=True, dw=True, nsize=4, nns=4, qual=2, pscrn=1).resize.Spline36(src_top=.5, src_left=.5)
orscmerge = core.std.Merge(orscnn3, get_y(orscfsr), weight=0.5).resize.Spline36(1920, 1080)
ojoinyuv	= kgf.join([orscmerge, ou, ov])
otxtsafe 	= core.std.MaskedMerge(ojoinyuv, otxtdn, txtmask, planes=[0], first_plane=True)
odb 		= core.f3kdb.Deband(otxtsafe, 18, grainc=20, grainy=0, y=80, cb=64, cr=64, output_depth=16)
odbmask 	= kgf.retinex_edgemask(otxtsafe, sigma=3.3).std.Binarize(21111,0).std.BoxBlur(hradius=1, vradius=1)
odbmerge 	= core.std.MaskedMerge(odb, otxtsafe, odbmask, planes=[0,1,2], first_plane=True)
ograin		= adptvgrnMod(odbmerge, strength=0.26, size=1.45, luma_scaling=27, static=True, grain_chroma=False, show_mask=False)
orf		  	= fvf.rfs(grain, ograin, '[23:2061] [23:2061]')

#ed 3 31580:34525 - 1.00
euvdn 		= core.knlm.KNLMeansCL(ef3, d=3, a=3, h=0.64, channels = 'UV', device_type='gpu')
euv16 		= core.fmtc.bitdepth(euvdn, bits=16)
etxtdr		= hvf.HQDeringmod(euv16, show=False, nrmode=2, sharp=1,  mthr=64, minp=1.3, mrad=1.3, msmooth=1, thr=20, darkthr=0)
etxtaa		= exaa(etxtdr, mode='drh nnedi3cl', csharp=1, mask=0, chroma=0)
etxtdn		= core.fmtc.bitdepth(etxtaa, bits=32).knlm.KNLMeansCL(d=3, a=3, h=0.50, channels = 'Y', device_type='gpu').fmtc.bitdepth(bits=16)
ey, eu, ev 	= kgf.split(euv16)
edsc 		= kgf.inverse_scale(ey, width=1280, height=720, kernel='bilinear', mask_detail=True, denoise=False, use_gpu=True)
ey16 		= core.fmtc.bitdepth(edsc, bits=16)
etaa		= taa.TAAmbk(ey16, showmask=0, aatype='Nnedi3', mtype=3, mthr=72, opencl=True)
epf 		= core.knlm.KNLMeansCL(etaa, d=4, a=4, h=0.96, channels = 'Y', device_type='gpu').fmtc.bitdepth(bits=16)
eydn 		= hvf.SMDegrain(etaa, tr=2, thSAD=84, blksize=8, overlap=4, contrasharp=True, RefineMotion=True, prefilter=epf, chroma=False, pel=2, plane=0)
edn2mask 	= kgf.retinex_edgemask(etaa, sigma=1.5).std.Binarize(16666,0).std.BoxBlur(hradius=1, vradius=1)
ednmerge 	= core.std.MaskedMerge(epf, eydn, edn2mask, planes=[0], first_plane=True)
erfdn	  	= fvf.rfs(eydn, epf, '[33028:33207] [33028:33207]')
ey420 		= core.resize.Point(erfdn, format=vs.YUV420P16, dither_type=None)
erscfsr		= core.placebo.Shader(ey420, shader=r'C:\Users\User\AppData\Roaming\mpv\shaders\FSRCNNX_x2_56-16-4-1.glsl', width=2560, height=1440)
erscnn3 	= erfdn.nnedi3cl.NNEDI3CL(0, dh=True, dw=True, nsize=4, nns=4, qual=2, pscrn=1).resize.Spline36(src_top=.5, src_left=.5)
erscmerge 	= core.std.Merge(erscnn3, get_y(erscfsr), weight=0.5).resize.Spline36(1920, 1080)
ejoinyuv 	= kgf.join([erscmerge, eu, ev])
etxtsafe 	= core.std.MaskedMerge(ejoinyuv, etxtdn, txtmask, planes=[0], first_plane=True)
edb 		= core.f3kdb.Deband(etxtsafe, 18, grainc=27, grainy=0, y=88, cb=72, cr=72, output_depth=16)
edbmask 	= kgf.retinex_edgemask(etxtsafe, sigma=3).std.Binarize(18888,0).std.BoxBlur(hradius=1, vradius=1)
edbmerge 	= core.std.MaskedMerge(edb, etxtsafe, edbmask, planes=[0,1,2], first_plane=True)
egrain		= adptvgrnMod(edbmerge, strength=0.40, size=1.55, luma_scaling=20, static=True, grain_chroma=False, show_mask=False)
erf		  	= fvf.rfs(orf, egrain, '[31580:34525] [31580:34525]')


#out
yt, ut, vt = kgf.split(ef3) #for tests
out10 = core.fmtc.bitdepth(erf, bits=10)
cut  = out10[0:4444] #for tests
out10.set_output()