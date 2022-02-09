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
deband = [(0, 0)]
card_1, card_2, card_3 = (3456, 3551), (19752, 19871), (33912, 33983)
op_start, op_end = 1776, 3456
ed = (31344, 33264)
damaged_start, damaged_end = 16513, 16800
###

###Source
src 	= core.lsmas.LWLibavSource(r'F:\enc\[BDMV][120118] BERSERK BD-BOX\[BDMV][120118] BERSERK BD-BOX VOL4\BERSERK_VOL4\BERSERK_VOL4\BDMV\STREAM\00003.m2ts')
dvd 	= core.d2v.Source(r'C:\Users\DaSkyBro\Desktop\bbb\e18-d2vw.d2v') #R1 DISC 5 VTS_01_1.VOB
dvd		= core.vivtc.VFM(dvd, order=1).vivtc.VDecimate()[16481:16770]
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
brightmask	= vdf.noise.decsiz(cnr, sigmaS=0, min_in=165<<8, max_in=195<<8, show_mask=True, planes=[0])
brightavg	= core.resize.Bilinear(get_y(cnr), 1, 1).resize.Point(1440, 1080) #fast approximate average frame luma value. accurate to 16bits
brightscale	= vdf.noise.decsiz(brightavg, sigmaS=0, min_in=67<<8, max_in=100<<8, protect_mask=get_y(blank), show_mask=True, planes=[0])
darkmask	= vdf.noise.decsiz(cnr.std.Invert(), sigmaS=0, min_in=220<<8, max_in=230<<8, show_mask=True, planes=[0])
linemask	= kgf.retinex_edgemask(cnr, sigma=2).std.Deflate().std.Deflate().std.Binarize(18000,0).std.Deflate().std.Deflate().std.Inflate()
##Denoise steps
pf				= core.fmtc.bitdepth(cnr, bits=32).knlm.KNLMeansCL(d=3, a=3, s=1, h=1.3, channels = 'Y', device_type='gpu').fmtc.bitdepth(bits=16)
dna				= CoolDegrain(cnr, tr=2, thsad=175, thsadc=165, blksize=16, overlap=8, pf=pf)
dnb				= CoolDegrain(cnr, tr=2, thsad=72, thsadc=70, blksize=8, overlap=4)
dnc				= core.fmtc.bitdepth(dna, bits=32).knlm.KNLMeansCL(d=2, a=2, s=8, h=3, channels = 'Y', device_type='gpu').fmtc.bitdepth(bits=16)
darkgrain		= core.std.Merge(dnb, cnr, weight=2/3)
brightgrain		= core.std.Merge(dna, dnb, weight=4/5)
brightbright	= core.std.Merge(brightgrain, dnc, weight=1/4)
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
cardrfs	 = lvf.rfs(edrfs, cardtaa, ranges=[card_1, card_2, card_3])
###

###Replace damaged BD scene with cleaned up DVD version
##Reformat from ZQ
dvd_crop = core.std.Crop(dvd, top=10, bottom=18, left=12, right=22)
dvd_fmt = core.resize.Bicubic(dvd_crop, format=vs.YUV420P16, matrix_s='470bg')
##Degrain
dvd32 = core.fmtc.bitdepth(dvd_fmt, bits=32)
pf		= core.knlm.KNLMeansCL(dvd32, d=4, a=2, s=3, h=2, channels = 'Y', device_type='gpu')
pf		= core.knlm.KNLMeansCL(pf, d=4, a=2, s=5, h=2, channels = 'UV', device_type='gpu').fmtc.bitdepth(bits=16)
ref		= hvf.SMDegrain(dvd_fmt, tr=3, thSAD=300, thSADC=300, blksize=8, overlap=4, prefilter=pf, RefineMotion=True).fmtc.bitdepth(bits=32)
bm3d	= core.bm3dcuda.BM3D(dvd32, sigma=[9,7,7], radius=6, ref=ref, fast=0, block_step=8, bm_range=12, ps_num=2, ps_range=6).bm3d.VAggregate(radius=6, sample=1).fmtc.bitdepth(bits=16)[1:288]
clean	= core.f3kdb.Deband(bm3d, 15, grainc=0, grainy=0, y=44, cb=44, cr=44, output_depth=16)
y, u, v = split(clean)
##Upscaling luma with RealSR with the generic JPEG model works better than fsrcnnx/nn3 and cleans up minor noise leftover after degraining. chroma with nn3 twice
rsr = core.rsnv.RealSR(core.resize.Point(y, format=vs.RGBS), tilesize_x=98, tilesize_y=113, model=1, tta=False).resize.Point(format=vs.GRAY16, matrix=5, dither_type='error_diffusion')
unn3 = core.nnedi3cl.NNEDI3CL(u, 0, dh=True, dw=True, nsize=4, nns=4, qual=2, pscrn=1).resize.Spline36(src_top=.5, src_left=.5)
unn3x2 = core.nnedi3cl.NNEDI3CL(unn3, 0, dh=True, dw=True, nsize=4, nns=4, qual=2, pscrn=1).resize.Spline36(src_top=.5, src_left=.5)
vnn3 = core.nnedi3cl.NNEDI3CL(v, 0, dh=True, dw=True, nsize=4, nns=4, qual=2, pscrn=1).resize.Spline36(src_top=.5, src_left=.5)
vnn3x2 = core.nnedi3cl.NNEDI3CL(vnn3, 0, dh=True, dw=True, nsize=4, nns=4, qual=2, pscrn=1).resize.Spline36(src_top=.5, src_left=.5)
yuv = join([rsr, unn3x2, vnn3x2])
##Correct Gamma and levels from ZQ
dvd_lvl = fixlvls(yuv, gamma=1, min_in=[16, 16], min_out=[2, 16], max_in=[255, 255], max_out=[220, 240])
dvd_lvl = adjust.Tweak(dvd_lvl, sat=0.75)
dvd_clr = iterate(dvd_lvl, partial(core.resize.Point, matrix_in_s='709', matrix_s='470bg'), 2)
##Fix chroma and downscale
dvd_warpuv	= core.warp.AWarpSharp2(dvd_clr, blur=2, chroma=0, depth=14, planes=[1,2]).resize.Bicubic(1440, 1080, filter_param_a=0, filter_param_b=0, filter_param_a_uv=-0.5, filter_param_b_uv=0.25)
##Deband with regrain
dvd_db		= core.f3kdb.Deband(dvd_warpuv, 25, grainc=0, grainy=0, y=11, cb=33, cr=33, output_depth=16).std.Invert()
dvd_dirty	= adptvgrnMod(dvd_db, strength=1.33, size=2.33, luma_scaling=1, sharp=67, static=False, grain_chroma=True, show_mask=False).std.Invert()
dvd_grain	= adptvgrnMod(dvd_dirty, strength=0.80, size=1.45, luma_scaling=2, sharp=60, static=False, grain_chroma=False, show_mask=False)
dvd_grainuv	= adptvgrnMod(dvd_grain, strength=0.00, cstrength=0.48, size=1.25, luma_scaling=1, sharp=25, static=False, grain_chroma=True, show_mask=False)
##splice in cleaned DVD scene
dvd_merge = cardrfs[0:damaged_start] + dvd_grainuv + cardrfs[damaged_end:]
###

###Debanding of select few scenes I've found with banding in the source
#db			= core.f3kdb.Deband(cardrfs, 25, grainc=0, grainy=0, y=66, cb=66, cr=66, output_depth=16)
#grain		= adptvgrnMod(db, strength=0.50, size=1.4, luma_scaling=99, sharp=40, static=False, grain_chroma=False, show_mask=False)
#grainuv	= adptvgrnMod(grain, strength=0.00, cstrength=0.30, size=1.2, luma_scaling=99, sharp=20, static=False, grain_chroma=True, show_mask=False)
#dbmask		= core.std.MaskedMerge(grainuv, cardrfs, linemask)
#dbrfs		= lvf.rfs(cardrfs, dbmask, ranges=deband)
###

###Outputs
yt, ut, vt = kgf.split(src16) #for testing
out8 = core.fmtc.bitdepth(dvd_merge, bits=8)#.std.Invert()
cut  = out8[21412:22009] #for testing
out8.set_output()
###