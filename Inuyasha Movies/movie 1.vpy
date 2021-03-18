import vapoursynth as vs
core = vs.get_core()
import importlib.machinery
import havsfunc as hvf
import kagefunc as kgf
import fvsfunc as fvf
from awsmfunc import bbmod
from adptvgrnMod import *
from vsutil import *
from xaa import xaa
from xaa import xaa as cxaa

src 	= core.lsmas.LWLibavSource(r'F:\Encode\Inuyasha Movies\[BDMV][InuYasha Movies]\DISC 1\BDMV\STREAM\00012.m2ts')
vfm 	= core.vivtc.VFM(src, order=1)
deci	= core.vivtc.VDecimate(vfm)
yuv16	= core.fmtc.bitdepth(deci, bits=16)
crop 	= core.std.Crop(yuv16, 0, 0, 16, 16)


#mov 1
ef 		 = bbmod(crop, top=4, bottom=0, left=4, right=8, thresh=124, blur=80, y=True, u=True, v=True, scale_thresh=True)
xaa 	 = xaa(ef, mode='drv nnedi3cl', csharp=0, mask=0, chroma=1)
uvdn 	 = core.fmtc.bitdepth(xaa, bits=32).knlm.KNLMeansCL(d=3, a=3, h=1.12, channels = 'UV', device_type='gpu')
pf 		 = core.knlm.KNLMeansCL(uvdn, d=3, a=3, h=1.06, channels = 'Y', device_type='gpu').fmtc.bitdepth(bits=16)
uv16 	 = core.fmtc.bitdepth(uvdn, bits=16)
ydn 	 = hvf.SMDegrain(uv16, tr=2, thSAD=86, blksize=16, overlap=8, Str=3, Amp=0.6, prefilter=pf, contrasharp=True, RefineMotion=True, chroma=False, pel=1, plane=0, Globals=2)
ydn2 	 = hvf.SMDegrain(uv16, tr=1, thSAD=18, blksize=16, overlap=8, prefilter=pf, contrasharp=True, RefineMotion=True, chroma=False, pel=1, plane=0, Globals=1)
ydnmask	 = get_y(xaa).std.Binarize(24575,0).std.BoxBlur(hradius=4, vradius=4).std.BoxBlur(hradius=2, vradius=2)
ydnmerge = core.std.MaskedMerge(ydn2, ydn, ydnmask, planes=[0,1,2], first_plane=True)
db 		 = core.f3kdb.Deband(ydnmerge, 18, grainc=27, grainy=27, y=56, cb=56, cr=56, output_depth=16)
dbmask 	 = kgf.retinex_edgemask(ydnmerge, sigma=3).std.Binarize(16666,0)
dbmerge  = core.std.MaskedMerge(db, ydnmerge, dbmask, planes=[0,1,2], first_plane=True)
grain	 = adptvgrnMod(dbmerge, strength=0.13, size=1.4, luma_scaling=26, static=True, grain_chroma=False, show_mask=False)

#credits 138877:142255 - 0.64
#cef		  = bbmod(crop, top=2, bottom=2, left=5, right=8, thresh=112, blur=120, y=True, u=True, v=True, scale_thresh=True)
#cxaa	  = cxaa(cef, mode='drv nnedi3cl', csharp=0, mask=0, chroma=1)
#cuvdn	  = core.knlm.KNLMeansCL(cxaa, d=4, a=3, h=1.48, channels = 'UV', device_type='gpu')
#cydn	  = core.knlm.KNLMeansCL(cuvdn, d=5, a =3, h=1.64, channels = 'Y', device_type='gpu')
#cyuv16 	  = core.fmtc.bitdepth(cydn, bits=16)
#cdb		  = core.f3kdb.Deband(cyuv16, 12, grainc=32, grainy=32, y=72, cb=64, cr=64, output_depth=16)
#cdbmask   = kgf.retinex_edgemask(cyuv16, sigma=9).std.Binarize(65000,0)
#cdbmerge  = core.std.MaskedMerge(cdb, cyuv16, cdbmask, planes=[0,1,2], first_plane=True)
#cgrain	  = adptvgrnMod(dbmerge, strength=0.16, size=1.6, luma_scaling=24, static=True, grain_chroma=False, show_mask=False)
#crf		  = fvf.rfs(cgrain, cdbmerge, '[138877:142255] [138877:142255]')

yt, ut, vt = kgf.split(grain) #for testing
out10 = core.fmtc.bitdepth(grain, bits=10)
cut  = out10[0:2424] #for tests
out10.set_output()