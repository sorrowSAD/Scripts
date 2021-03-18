import vapoursynth as vs
core = vs.get_core()
import importlib.machinery
import mvsfunc as mvf
import havsfunc as hvf
import kagefunc as kgf
import vsTAAmbk as taa
import fvsfunc as fvf
from awsmfunc import bbmod
from xaa import xaa
from xaa import xaa as cxaa
src 	= core.lsmas.LWLibavSource(r'F:\Encode\Inuyasha Movies\[BDMV][InuYasha Movies]\DISC 1\BDMV\STREAM\00000.m2ts')
vfm 	= core.vivtc.VFM(src, order=1)
deci	= core.vivtc.VDecimate(vfm)
yuv32	= core.fmtc.bitdepth(deci, bits=32)
crop 	= core.std.Crop(yuv32, 0, 0, 18, 24)

#mov 2
ef 		= bbmod(crop, top=4, bottom=0, left=5, right=6, thresh=124, blur=80, y=True, u=True, v=True, scale_thresh=True)
uvdn 	= core.knlm.KNLMeansCL(ef, d=3, a=3, h=0.64, channels = 'UV', device_type='gpu')
uv16 	= core.fmtc.bitdepth(uvdn, bits=16)
xaa 	= xaa(uv16, mode='drv nnedi3cl', csharp=0, mask=0, chroma=2)
y, u, v = kgf.split(xaa)
dsc 	= kgf.inverse_scale(y, width=1024, height=553, kernel='bicubic', b=0.20, c=0.50, mask_detail=False, denoise=False, use_gpu=True)
y16 	= core.fmtc.bitdepth(dsc, bits=16)
dr 		= hvf.HQDeringmod(y16, show=False, nrmode=1, sharp=1,  mthr=64, minp=1.3, mrad=1.3, msmooth=1, thr=9, darkthr=0)
taa		= taa.TAAmbk(dr, showmask=0, aatype='Nnedi3', mtype=3, mthr=136, opencl=True)
pf 		= core.fmtc.bitdepth(dr, bits=32).knlm.KNLMeansCL(d=3, a=3, h=0.48, channels = 'Y', device_type='gpu').fmtc.bitdepth(bits=16)
ydn 	= hvf.SMDegrain(taa, tr=2, thSAD=48, blksize=8, overlap=4, contrasharp=True, RefineMotion=True, prefilter=pf, chroma=False, pel=2, plane=0)
rsc 	= ydn.nnedi3cl.NNEDI3CL(0, dh=True, dw=True, nsize=4, nns=4, qual=2, pscrn=1).resize.Spline36(src_top=.5, src_left=.5).resize.Spline36(1920, 1038)
joinyuv = kgf.join([rsc, u, v])
db 		= core.f3kdb.Deband(joinyuv, 18, grainc=24, grainy=56, y=56, cb=48, cr=48, output_depth=16)
dbmask 	= kgf.retinex_edgemask(joinyuv, sigma=3).std.Binarize(11111,0)
dbmerge = core.std.MaskedMerge(db, joinyuv, dbmask, planes=[0,1,2], first_plane=True)

#credits 137665:141055 - 0.44
cef		  = bbmod(crop, top=3, bottom=0, left=4, right=5, thresh=112, blur=120, y=True, u=True, v=True, scale_thresh=True)
cuvdn	  = core.knlm.KNLMeansCL(cef, d=4, a=3, h=1.48, channels = 'UV', device_type='gpu')
cydn	  = core.knlm.KNLMeansCL(cuvdn, d =5, a =4, h=1.48, channels = 'Y', device_type='gpu')
cuv16 	  = core.fmtc.bitdepth(cydn, bits=16)
cxaa	  = cxaa(cuv16, mode='drv nnedi3cl', csharp=0, mask=0, chroma=1)
cdb		  = core.f3kdb.Deband(cxaa, 12, grainc=32, grainy=64, y=72, cb=64, cr=64, output_depth=16)
cdbmask   = kgf.retinex_edgemask(cxaa, sigma=9).std.Binarize(65000,0)
cdbmerge  = core.std.MaskedMerge(cdb, cxaa, cdbmask, planes=[0,1,2], first_plane=True)
crf		  = fvf.rfs(dbmerge, cdbmerge, '[137665:141055] [137665:141055]')

yt, ut, vt = kgf.split(uv16) #for testing
out10 = core.fmtc.bitdepth(crf, bits=10)
cut  = out10[378:1831] #for tests
out10.set_output()