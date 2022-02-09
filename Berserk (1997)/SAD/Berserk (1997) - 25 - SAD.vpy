import vapoursynth as vs
core = vs.get_core()
import importlib.machinery
import kagefunc as kgf
import havsfunc as hvf
import vardefunc as vdf
import lvsfunc as lvf
import mvsfunc as mvf
import adjust
from cooldegrain import CoolDegrain
from awsmfunc import bbmod, fixlvls
import vsTAAmbk as taa
from rekt import rektlvls, rekt_fast
from adptvgrnMod import *
from vsutil import *

###Ranges
deband = [(8696, 8871), (9900, 10019), (11242, 11558), (11816, 12074), (12753, 13039), (16114, 16253), (20616, 21122), (21314, 21539), (22315, 22666), (23274, 23320), (28035, 28123), (28722, 28747)]
card_1, card_2 = (3216, 3311), (17424, 17543)
op_start, op_end = 1536, 3216
damaged_start, damaged_end = 19216, 19755 #19467
ed = (30336, 32255)
###

###Source
src 	= core.lsmas.LWLibavSource(r'F:\enc\[BDMV][120118] BERSERK BD-BOX\[BDMV][120118] BERSERK BD-BOX VOL5\BERSERK_VOL5\BERSERK_VOL5\BDMV\STREAM\00004.m2ts')
dvd 	= core.d2v.Source(r'C:\Users\DaSkyBro\Desktop\bbb\e25-d2vw.d2v') #R1 DISC 6 VTS_02-6.VOB
dvd		= core.vivtc.VFM(dvd, order=1).vivtc.VDecimate()[3764:4303]
crop 	= core.std.Crop(src, 240, 240, 0, 0)
src16	= core.fmtc.bitdepth(crop, bits=16)
###

###Edge fixing from ZQ's scripts but with more accurate values
dln = rektlvls(src16, rownum=[0,1,2,3,4,6,1078,1077,1076,1074,1072,1079], rowval=[39,13,-5,5,2,2,7,-3,2,-1,-1,22],
    colnum=[5,4,1,0,1439,1438,1437,1436,1435,1434,1433], colval=[1,-1,-3,33,51,3,-1,3,0,1,1])
dln = bbmod(dln, planes=[1,2], top=2, bottom=2, left=2, right=2)

cnr = rekt_fast(dln, lambda x: core.fb.FillBorders(x, top=1), left=1438)
cnr = rekt_fast(cnr, lambda x: core.fb.FillBorders(x, top=1), right=1438)
cnr = rekt_fast(cnr, lambda x: core.fb.FillBorders(x, left=1), top=1078)
cnr = rekt_fast(cnr, lambda x: core.fb.FillBorders(x, right=1), top=1078)
###

###Denoising to lower bitrate requirements for smaller encode
##Masks
blank		= core.std.BlankClip(cnr) #for no protect_mask
lumascale	= kgf.adaptive_grain(cnr, luma_scaling=30, show_mask=True)
brightmask	= vdf.noise.decsiz(cnr, sigmaS=0, min_in=170<<8, max_in=200<<8, show_mask=True, planes=[0])
brightavg	= core.resize.Bilinear(get_y(cnr), 1, 1).resize.Point(1440, 1080) #fast approximate average frame luma value. accurate to 16bits
brightscale	= vdf.noise.decsiz(brightavg, sigmaS=0, min_in=63<<8, max_in=96<<8, protect_mask=get_y(blank), show_mask=True, planes=[0])
darkmask	= vdf.noise.decsiz(cnr.std.Invert(), sigmaS=0, min_in=210<<8, max_in=220<<8, show_mask=True, planes=[0])
linemask	= kgf.retinex_edgemask(cnr, sigma=2).std.Deflate().std.Deflate().std.Binarize(18000,0).std.Deflate().std.Deflate().std.Inflate()
##Denoise steps
pf				= core.fmtc.bitdepth(cnr, bits=32).knlm.KNLMeansCL(d=3, a=3, s=1, h=1.3, channels = 'Y', device_type='gpu').fmtc.bitdepth(bits=16)
dna				= CoolDegrain(cnr, tr=2, thsad=156, thsadc=148, blksize=16, overlap=8, pf=pf)
dnb				= CoolDegrain(cnr, tr=2, thsad=62, thsadc=58, blksize=8, overlap=4)
dnc				= core.fmtc.bitdepth(dna, bits=32).knlm.KNLMeansCL(d=2, a=2, s=7, h=1.8, channels = 'Y', device_type='gpu').fmtc.bitdepth(bits=16)
darkgrain		= core.std.Merge(dnb, cnr, weight=2/3)
brightgrain		= core.std.Merge(dna, dnb, weight=4/5)
brightbright	= core.std.Merge(brightgrain, dnc, weight=1/5)
##Merging
dn			= core.std.MaskedMerge(dna, dnb, lumascale)
highlights	= core.std.MaskedMerge(dn, dnc, brightmask)
brightscene	= core.std.MaskedMerge(highlights, brightgrain, brightscale)
brightlight	= core.std.MaskedMerge(brightscene, brightbright, brightmask)
lines		= core.std.MaskedMerge(brightlight, dnb, linemask)
darks		= core.std.MaskedMerge(lines, darkgrain, darkmask)
###

###Opening
splice = darks[0:op_start] + core.ffms2.Source(r'F:\E\VS64P\OP small.ffv1.mkv') + darks[op_end:]
###

###Ending
eddb		= core.f3kdb.Deband(dna, 25, grainc=0, grainy=0, y=33, cb=33, cr=33, output_depth=16)
eddbmask	= core.std.MaskedMerge(eddb, dna, linemask)
edgrain		= adptvgrnMod(eddbmask, strength=0.40, size=1.20, luma_scaling=3, sharp=50, static=True, grain_chroma=False, show_mask=False)
edrfs		= lvf.rfs(splice, edgrain, ranges=ed)
###

###Card cleaning from ZQ's scripts but modified to not dehalo uv and by altering the deringing
cardyuv	 = split(edrfs)
carddh	 = hvf.DeHalo_alpha(cardyuv[0], darkstr=1.5, rx=2.7, ry=1.5, brightstr=0)
cardjoin = join([carddh, cardyuv[1], cardyuv[2]])
carddr	 = hvf.HQDeringmod(cardjoin, mrad=3, minp=0.3, msmooth=1, mthr=115, nrmode=1, thr=128, darkthr=3, sharp=0, show=False)
cardtaa	 = taa.TAAmbk(carddr, 6, 4, 4)
cardrfs	 = lvf.rfs(edrfs, cardtaa, ranges=[card_1, card_2])
###

###Replace damaged BD scene with cleaned up DVD version
dvd_format = core.resize.Bicubic(dvd, format=vs.YUV420P16, matrix_s='470bg')
##Degrain
dvd32 = core.fmtc.bitdepth(dvd_format, bits=32)
pf		= core.knlm.KNLMeansCL(dvd32, d=5, a=4, s=6, h=2.66, channels = 'Y', device_type='gpu')
pf		= core.knlm.KNLMeansCL(pf, d=4, a=2, s=6, h=2, channels = 'UV', device_type='gpu').fmtc.bitdepth(bits=16)
dna		= hvf.SMDegrain(dvd_format, tr=3, thSAD=300, thSADC=300, blksize=8, overlap=4, prefilter=pf, RefineMotion=True)#.fmtc.bitdepth(bits=32)
pf2		= core.knlm.KNLMeansCL(dvd32, d=6, a=4, s=8, h=4, channels = 'Y', device_type='gpu')
pf2		= core.knlm.KNLMeansCL(pf2, d=4, a=2, s=7, h=2.5, channels = 'UV', device_type='gpu').fmtc.bitdepth(bits=16)
dnb		= hvf.SMDegrain(dvd_format, tr=3, thSAD=1200, thSADC=1600, blksize=4, overlap=2, prefilter=pf2, RefineMotion=False)#.fmtc.bitdepth(bits=32)
blend	= core.std.Merge(dna, dnb, weight=0.5)
mix		= lvf.rfs(dna, blend, ranges=(192,195))
mix		= lvf.rfs(mix, dnb, ranges=(195,223))
mix		= lvf.rfs(mix, blend, ranges=(223,226)) #i didn't feel like doing real transitions
y, u, v = split(mix)
##Upscaling #luma with RealSR with the generic JPEG model works better than fsrcnnx/nn3 and cleans up minor noise leftover after degraining. chroma with nn3 twice
rsr		= core.rsnv.RealSR(core.resize.Point(y, format=vs.RGBS), tilesize_x=120, tilesize_y=120, model=1, tta=False).resize.Point(format=vs.GRAY16, matrix=5, dither_type='error_diffusion')
unn3	= core.nnedi3cl.NNEDI3CL(u, 0, dh=True, dw=True, nsize=4, nns=4, qual=2, pscrn=1).resize.Spline36(src_top=.5, src_left=.5)
unn3x4	= core.nnedi3cl.NNEDI3CL(unn3, 0, dh=True, dw=True, nsize=4, nns=4, qual=2, pscrn=1).resize.Spline36(src_top=.5, src_left=.5)
vnn3	= core.nnedi3cl.NNEDI3CL(v, 0, dh=True, dw=True, nsize=4, nns=4, qual=2, pscrn=1).resize.Spline36(src_top=.5, src_left=.5)
vnn3x4	= core.nnedi3cl.NNEDI3CL(vnn3, 0, dh=True, dw=True, nsize=4, nns=4, qual=2, pscrn=1).resize.Spline36(src_top=.5, src_left=.5)
yuv		= join([rsr, unn3x4, vnn3x4])
##Correct Gamma and levels from ZQ
dvd_levels	= fixlvls(yuv, gamma=1, min_in=[16, 16], min_out=[2, 16])
dvd_matrix	= core.resize.Point(dvd_levels, matrix_in_s='470bg', matrix_s='709')
##Fix chroma and downscale
dvd_warpuv	= core.warp.AWarpSharp2(dvd_matrix, blur=2, chroma=0, depth=14, planes=[1,2]).resize.Bicubic(1440, 1080, filter_param_a=0, filter_param_b=0, filter_param_a_uv=-0.5, filter_param_b_uv=0.25)
ff = core.std.FreezeFrames(dvd_warpuv, first=[0, 538], last=[0, 538], replacement=[1, 537])
##Deband with regrain
dvd_db		= core.f3kdb.Deband(ff, 31, grainc=0, grainy=0, y=66, cb=33, cr=33, output_depth=16).std.Invert()
dvd_dirty	= adptvgrnMod(dvd_db, strength=2.22, size=2.67, luma_scaling=1, sharp=75, static=False, grain_chroma=True, show_mask=False).std.Invert()
dvd_grain	= adptvgrnMod(dvd_dirty, strength=0.80, size=1.45, luma_scaling=33, sharp=60, static=False, grain_chroma=False, show_mask=False)
dvd_grainuv	= adptvgrnMod(dvd_grain, strength=0.00, cstrength=0.48, size=1.25, luma_scaling=33, sharp=25, static=False, grain_chroma=True, show_mask=False)
##splice in cleaned DVD scene
dvd_merge = cardrfs[0:damaged_start] + dvd_grainuv + cardrfs[damaged_end:]
###

###Debanding of select few scenes I've found with banding in the source
db			= core.f3kdb.Deband(cardrfs, 25, grainc=0, grainy=0, y=66, cb=66, cr=66, output_depth=16)
grain		= adptvgrnMod(db, strength=0.50, size=1.4, luma_scaling=99, sharp=40, static=False, grain_chroma=False, show_mask=False)
grainuv		= adptvgrnMod(grain, strength=0.00, cstrength=0.30, size=1.2, luma_scaling=99, sharp=20, static=False, grain_chroma=True, show_mask=False)
dbmask		= core.std.MaskedMerge(grainuv, cardrfs, linemask)
dbrfs		= lvf.rfs(dvd_merge, dbmask, ranges=deband)
###

###Outputs
yt, ut, vt = kgf.split(src16) #for testing
out8 = core.fmtc.bitdepth(dbrfs, bits=8)#.std.Invert()
cut  = out8[21412:22009] #for testing
out8.set_output()
###