import os, sys
import vapoursynth as vs
core = vs.get_core()
import importlib.machinery
import kagefunc as kgf
import havsfunc as hvf
import fvsfunc as fvf
src = core.lsmas.LWLibavSource(r"F:\enc\PSYCHO-PASS-EE\Eps\E11.m2ts", fpsnum=24000, fpsden=1001)
src16 = core.fmtc.bitdepth(src, bits=16) #for tests
src32 = core.fmtc.bitdepth(src, bits=32)

#ep11
y, u, v = kgf.split(src32)
dsc = kgf.inverse_scale(src32, width=1280, height=720, kernel='bicubic', b=0.33, c=0.33, mask_detail=True, denoise=False, use_gpu=True)
y16 = core.fmtc.bitdepth(dsc, bits=16)
pf = core.knlm.KNLMeansCL(dsc, d = 3, a = 3, h = 0.32, channels = 'Y', device_type="gpu")
pf16 = core.fmtc.bitdepth(pf, bits=16)
ydn = hvf.SMDegrain(y16, tr=2, thSAD=44, blksize=8, overlap=4, prefilter=pf16, contrasharp=False, RefineMotion=True, chroma=False, pel=2, plane=0)
dnmask = kgf.retinex_edgemask(y16)
dnmask2 = core.std.Binarize(dnmask,13067,0)
dnmerge = core.std.MaskedMerge(ydn, y16, dnmask2, planes=[0,1,2], first_plane=True)
y2, u2, v2 = kgf.split(dnmerge)
y444 = core.resize.Point(y2, format=vs.YUV444P16, dither_type=None)
rsc = core.placebo.Shader(y444, shader=r'C:\Users\User\AppData\Roaming\mpv\shaders\FSRCNNX_x2_56-16-4-1.glsl', width=2560, height=1440)
y420 = core.resize.Point(rsc, format=vs.YUV420P16, dither_type=None)
y1080 = core.resize.Spline36(y420, 1920, 1080)
y32 = core.fmtc.bitdepth(y1080, bits=32)
joinyuv = kgf.join([y32, u, v])
uvdn = core.knlm.KNLMeansCL(joinyuv, d = 3, a = 2, h = 0.40, channels = 'UV', device_type="gpu")
yuv16 = core.fmtc.bitdepth(uvdn, bits=16)
db = core.f3kdb.Deband(yuv16, 24, grainc=16, grainy=32, y=34, cb=28, cr=28, output_depth=16)
dbmask = kgf.retinex_edgemask(yuv16, sigma=0.1)
dbmask2 = core.std.Binarize(dbmask,9825,0)
dbmerge = core.std.MaskedMerge(db, yuv16, dbmask2, planes=[0,1,2], first_plane=True)

#op3 6761:8919 - 0.80
opuvdn = core.knlm.KNLMeansCL(src32, d = 4, a = 3, h = 0.54, channels = 'UV', device_type="gpu")
op16 = core.fmtc.bitdepth(opuvdn, bits=16)
oppf = core.knlm.KNLMeansCL(src32, d = 4, a = 4, h = 1.06, channels = 'Y', device_type="gpu")
oppf16 = core.fmtc.bitdepth(oppf, bits=16)
opydn = hvf.SMDegrain(op16, tr=2, thSAD=67, blksize=16, overlap=4, prefilter=oppf16, contrasharp=True, RefineMotion=True, chroma=False, pel=1, plane=0)
opdnmask = kgf.retinex_edgemask(op16, sigma=2.6)
opdnmask2 = core.std.Binarize(opdnmask,59450,0)
opdnmerge = core.std.MaskedMerge(opydn, op16, opdnmask2, planes=[0,1,2], first_plane=True)
opdb = core.f3kdb.Deband(opdnmerge, 31, grainc=10, grainy=30, y=64, cb=48, cr=48, output_depth=16)
opdbmask = kgf.retinex_edgemask(op16, sigma=2.2)
opdbmask2 = core.std.Binarize(opdbmask,50000,0)
opdbmerge = core.std.MaskedMerge(opdb, opdnmerge, opdbmask2, planes=[0,1,2], first_plane=True)
oprf = fvf.rfs(dbmerge, opdbmerge, "[6761:8919] [6761:8919]")

#ed3 64191:65961 - 1.00
eduvdn = core.knlm.KNLMeansCL(src32, d = 3, a = 2, h = 0.40, channels = 'UV', device_type="gpu")
ed16 = core.fmtc.bitdepth(eduvdn, bits=16)
edpf = core.knlm.KNLMeansCL(src32, d = 3, a = 4, h = 0.44, channels = 'Y', device_type="gpu")
edpf16 = core.fmtc.bitdepth(edpf, bits=16)
edydn = hvf.SMDegrain(ed16, tr=2, thSAD=52, blksize=8, overlap=4, prefilter=edpf16, contrasharp=False, RefineMotion=True, chroma=False, pel=1, plane=0)
eddnmask = kgf.retinex_edgemask(ed16)
eddnmask2 = core.std.Binarize(eddnmask,14444,0)
eddnmerge = core.std.MaskedMerge(edydn, ed16, eddnmask2, planes=[0,1,2], first_plane=True)
eddb = core.f3kdb.Deband(eddnmerge, 28, grainc=20, grainy=36, y=48, cb=33, cr=33, output_depth=16)
eddbmask = kgf.retinex_edgemask(ed16, sigma=1)
eddbmask2 = core.std.Binarize(eddbmask,12222,0)
eddbmerge = core.std.MaskedMerge(eddb, eddnmerge, eddbmask2, planes=[0,1,2], first_plane=True)
edrf = fvf.rfs(oprf, eddbmerge, "[64191:65961] [64191:65961]")

#output
out10 = core.fmtc.bitdepth(edrf, bits=10)

y3, u3, v3 = kgf.split(edydn) #for tests
cut = out10[64191:65961] #for tests
out10.set_output()