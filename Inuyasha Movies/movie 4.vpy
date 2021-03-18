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
src 	= core.lsmas.LWLibavSource(r'F:\Encode\Inuyasha Movies\[BDMV][InuYasha Movies]\DISC 2\BDMV\STREAM\00000.m2ts')
vfm 	= core.vivtc.VFM(src, order=1)
deci	= core.vivtc.VDecimate(vfm)
yuv32	= core.fmtc.bitdepth(deci, bits=32)
crop	= core.resize.Spline36(yuv32, 1920, 1036, src_top=23, src_width=1920, src_height=1036) #not being able to crop by odd values is retarded

#mov 4
ef 			= bbmod(crop, top=0, bottom=1, left=11, right=10, thresh=124, blur=80, y=True, u=True, v=True, scale_thresh=True)
uvdn 		= core.knlm.KNLMeansCL(ef, d=3, a=3, h=0.64, channels = 'UV', device_type='gpu')
uv16 		= core.fmtc.bitdepth(uvdn, bits=16)
xaa 		= xaa(uv16, mode='drv nnedi3cl', csharp=0, mask=0, chroma=2)
y, u, v 	= kgf.split(xaa)
dsc 		= kgf.inverse_scale(y, width=1024, height=552, kernel='bicubic', b=0.20, c=0.50, mask_detail=False, denoise=False, use_gpu=True)
y16 		= core.fmtc.bitdepth(dsc, bits=16)
dr 			= hvf.HQDeringmod(y16, show=False, nrmode=1, sharp=1,  mthr=64, minp=1.3, mrad=1.3, msmooth=1, thr=9, darkthr=0)
taa			= taa.TAAmbk(dr, showmask=0, aatype='Nnedi3', mtype=3, mthr=136, opencl=True)
pf 			= core.fmtc.bitdepth(taa, bits=32).knlm.KNLMeansCL(d=3, a=3, h=0.50, channels = 'Y', device_type='gpu').fmtc.bitdepth(bits=16)
ydn 		= hvf.SMDegrain(taa, tr=2, thSAD=50, blksize=8, overlap=4, contrasharp=True, RefineMotion=True, prefilter=pf, chroma=False, pel=2, plane=0)
rsc 		= taa.nnedi3cl.NNEDI3CL(0, dh=True, dw=True, nsize=4, nns=4, qual=2, pscrn=1).resize.Spline36(src_top=.5, src_left=.5).resize.Spline36(1920, 1036)
rszuv		= core.resize.Spline36(xaa, 960, 518, format=vs.YUV444P16)
y2, u2, v2	= kgf.split(rszuv)
joinyuv		= kgf.join([rsc, u, v])
db 			= core.f3kdb.Deband(joinyuv, 18, grainc=24, grainy=56, y=64, cb=52, cr=52, output_depth=16)
dbmask 		= kgf.retinex_edgemask(joinyuv, sigma=3).std.Binarize(11111,0)
dbmerge 	= core.std.MaskedMerge(db, joinyuv, dbmask, planes=[0,1,2], first_plane=True)

#scene that i randomly found with a fucked color band artifact that i can't ignore 104724:104859
fuckeddb		= core.f3kdb.Deband(joinyuv, 31, grainc=28, grainy=60, y=96, cb=64, cr=64, output_depth=16)
fuckeddbmask	= kgf.retinex_edgemask(joinyuv, sigma=4).std.Binarize(16666,0)
fuckeddbmerge	= core.std.MaskedMerge(fuckeddb, dbmerge, fuckeddbmask, planes=[0,1,2], first_plane=True)
fuckedrf		= fvf.rfs(dbmerge, fuckeddbmerge, '[104724:104859] [104724:104859]')

#credits 119127:124020 - 0.56
cef		  = bbmod(crop, top=0, bottom=2, left=12, right=0, thresh=112, blur=120, y=True, u=True, v=True, scale_thresh=True)
cuvdn	  = core.knlm.KNLMeansCL(cef, d=4, a=3, h=1.48, channels = 'UV', device_type='gpu')
cydn	  = core.knlm.KNLMeansCL(cuvdn, d =5, a =4, h=1.48, channels = 'Y', device_type='gpu')
cuv16 	  = core.fmtc.bitdepth(cydn, bits=16)
cxaa	  = cxaa(cuv16, mode='drv nnedi3cl', csharp=0, mask=0, chroma=1)
cdb		  = core.f3kdb.Deband(cxaa, 12, grainc=32, grainy=64, y=72, cb=64, cr=64, output_depth=16)
cdbmask   = kgf.retinex_edgemask(cxaa, sigma=9).std.Binarize(54000,0)
cdbmerge  = core.std.MaskedMerge(cdb, cxaa, cdbmask, planes=[0,1,2], first_plane=True)
crf		  = fvf.rfs(fuckedrf, cdbmerge, '[119127:124020] [119127:124020]')

yt, ut, vt = kgf.split(joinyuv) #for testing
out10 = core.fmtc.bitdepth(crf, bits=10)
cut  = out10[378:1831] #for tests
out10.set_output()