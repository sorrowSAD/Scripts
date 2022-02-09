import vapoursynth as vs
import vsutil
import awsmfunc
import havsfunc
import vsTAAmbk as taa
import lvsfunc
import kagefunc as kgf
from cooldegrain import CoolDegrain
import vardefunc as vdf

from rekt import rektlvls, rekt_fast
from adptvgrnMod import *

core = vs.core
core.max_cache_size = 14000

###Ranges
text_1, text_2, text_3, text_4, text_5, text_6 = (73, 280), (475, 584), (589, 667), (679, 1069), (1358, 1575), (1576, 1679)
transistion_1 = (463, 470)
deband_1 = (326, 471)
###

###Inputs
jpn = core.lsmas.LWLibavSource(r'G:\E\00000.m2ts')[1776:3456]
jpn = core.std.Crop(jpn, left=240, right=240)
jpn = vsutil.depth(jpn, 16)
###

###Edge fixing from ZQ's scripts but with more accurate values
dln = rektlvls(jpn, rownum=[0,1,2,3,4,6,1078,1077,1076,1074,1072,1079], rowval=[39,13,-5,5,2,2,7,-3,2,-1,-1,22],
    colnum=[5,4,1,0,1439,1438,1437,1436,1435,1434,1433], colval=[1,-1,-3,33,51,3,-1,3,0,1,1])
dln = awsmfunc.bbmod(dln, planes=[1,2], top=2, bottom=2, left=2, right=2)

cnr = rekt_fast(dln, lambda x: core.fb.FillBorders(x, top=1), left=1438)
cnr = rekt_fast(cnr, lambda x: core.fb.FillBorders(x, top=1), right=1438)
cnr = rekt_fast(cnr, lambda x: core.fb.FillBorders(x, left=1), top=1078)
cnr = rekt_fast(cnr, lambda x: core.fb.FillBorders(x, right=1), top=1078)
###

###Denoising to lower bitrate requirements for smaller encode, lowered settings for this OP
##Masks
blank		= core.std.BlankClip(cnr) #for no protect_mask
lumamask	= kgf.adaptive_grain(cnr, luma_scaling=27, show_mask=True)
brightmask	= vdf.noise.decsiz(cnr, sigmaS=0, min_in=160<<8, max_in=190<<8, show_mask=True, planes=[0])
brightavg	= core.resize.Bilinear(get_y(cnr), 1, 1).resize.Point(1440, 1080) #fast approximate average frame luma value, this is accurate to 16bits
brightscale	= vdf.noise.decsiz(brightavg, sigmaS=0, min_in=84<<8, max_in=112<<8, protect_mask=get_y(blank), show_mask=True)
darkmask	= vdf.noise.decsiz(cnr.std.Invert(), sigmaS=0, min_in=228<<8, max_in=237<<8, show_mask=True, planes=[0])
linemask	= kgf.retinex_edgemask(cnr, sigma=2).std.Deflate().std.Deflate().std.Binarize(18000,0).std.Deflate().std.Deflate().std.Inflate()
##Denoise steps
pf			= core.fmtc.bitdepth(cnr, bits=32).knlm.KNLMeansCL(d=3, a=3, s=1, h=1.1, channels = 'Y', device_type='gpu').fmtc.bitdepth(bits=16)
dna			= CoolDegrain(cnr, tr=2, thsad=160, thsadc=140, blksize=16, overlap=8, pf=pf)
dnb			= CoolDegrain(cnr, tr=2, thsad=72, thsadc=64, blksize=8, overlap=4)
dnc			= core.fmtc.bitdepth(dna, bits=32).knlm.KNLMeansCL(d=2, a=2, s=8, h=2, channels = 'Y', device_type='gpu').fmtc.bitdepth(bits=16)
darkgrain	= core.std.Merge(dnb, cnr, weight=3/4)
brightgrain	= core.std.Merge(dna, dnb, weight=2/3)
#Merging
dn			= core.std.MaskedMerge(dna, dnb, lumamask)
highlights	= core.std.MaskedMerge(dn, dnc, brightmask)
brightscene	= core.std.MaskedMerge(highlights, brightgrain, brightscale)
lines		= core.std.MaskedMerge(brightscene, dnb, linemask)
darks		= core.std.MaskedMerge(lines, darkgrain, darkmask)
###

###OP Scene filtering from ZQ's scripts
y = vsutil.get_y(darks)
msk_1 = core.tcanny.TCanny(y, sigma=1, t_h=115.0, t_l=50.0, op=1)
msk_1 = vsutil.iterate(msk_1, lambda x: core.std.Maximum(x), 7)
msk_1 = core.std.FreezeFrames(msk_1, [137, 273], [154, 281], [136, 268])

msk_2 = core.tcanny.TCanny(y, sigma=0, t_h=115.0, t_l=50.0, op=1)
msk_2 = vsutil.iterate(msk_2, lambda x: core.std.Maximum(x), 8)
msk_2 = core.std.FreezeFrames(msk_2, [591, 657], [596, 669], [600, 600])

msk_3 = core.tcanny.TCanny(y, sigma=1, t_h=65.0, t_l=40.0, op=0)
brize = core.std.Binarize(y, 95 << 8).std.Invert()
brize = vsutil.iterate(brize, lambda x: core.std.Maximum(x), 4)
msk_3 = core.std.Expr([msk_3, brize], 'x y -')
msk_3 = vsutil.iterate(msk_3, lambda x: core.std.Maximum(x), 15)
msk_3 = core.std.FreezeFrames(msk_3, 
    [676, 723, 734, 825, 859, 931, 965, 1034, 1359, 1428, 1456, 1526], 
    [687, 731, 744, 828, 867, 939, 981, 1046, 1368, 1438, 1464, 1535], 
    [700, 700, 773, 773, 879, 879, 981, 981, 1375, 1375, 1468, 1468])

msk_4 = core.tcanny.TCanny(y, sigma=1, t_h=65.0, t_l=40.0, op=0)
brize = core.std.Binarize(y, 108 << 8).std.Invert()
brize = vsutil.iterate(brize, lambda x: core.std.Maximum(x), 4)
msk_4 = core.std.Expr([msk_4, brize], 'x y -')
msk_4 = vsutil.iterate(msk_4, lambda x: core.std.Maximum(x), 13)
msk_4 = core.std.FreezeFrames(msk_4, [1577], [1678], [1616])

halos = havsfunc.DeHalo_alpha(darks)

scene_1 = havsfunc.DeHalo_alpha(darks, darkstr=.7, rx=1, ry=1.5, brightstr=1)
scene_1 = havsfunc.HQDeringmod(scene_1, mrad=3, mthr=100, nrmode=1, thr=25, show=False)
scene_1 = taa.TAAmbk(scene_1, 1)
scene_1 = core.std.MaskedMerge(darks, scene_1, msk_1)
scene_1 = lvsfunc.rfs(darks, scene_1, ranges=[text_1])

scene_2 = havsfunc.DeHalo_alpha(darks, darkstr=0)
scene_2 = core.std.MaskedMerge(darks, scene_2, msk_2)
scene_2 = lvsfunc.rfs(scene_1, scene_2, ranges=[text_2])

scene_3 = havsfunc.DeHalo_alpha(darks, darkstr=.7)
scene_3 = core.std.MaskedMerge(darks, scene_3, msk_2)
scene_3 = lvsfunc.rfs(scene_2, scene_3, ranges=[text_3])

scene_4 = havsfunc.DeHalo_alpha(darks, darkstr=.7, brightstr=0.2) #ZQ's dehaloing was detroying too much detail so I lowered it
scene_4 = core.std.Merge(scene_4, scene_3, weight=0.5) #and added this merge, which does bring some haloing back, but some detail too
scene_4 = core.std.MaskedMerge(darks, scene_4, msk_3)
scene_4 = lvsfunc.rfs(scene_3, scene_4, ranges=[text_4])

scene_5 = core.std.MaskedMerge(darks, halos, msk_3)
scene_5 = lvsfunc.rfs(scene_4, scene_5, ranges=[text_5])

scene_6 = havsfunc.DeHalo_alpha(darks, darkstr=.7, rx=1.5, ry=1.5, brightstr=.2) #ZQ's dehaloing was detroying too much detail so I lowered it
scene_6 = core.std.MaskedMerge(darks, scene_6, msk_4)
scene_6 = lvsfunc.rfs(scene_5, scene_6, ranges=[text_6])

scene_7 = havsfunc.HQDeringmod(scene_6, mrad=4, thr=5, planes=[0,1,2], show=False)
scene_7 = havsfunc.FineDehalo(scene_7)
scene_7_aa = lvsfunc.aa.upscaled_sraa(scene_7)
scene_7 = core.std.MaskedMerge(scene_7, scene_7_aa, core.std.Prewitt(y, 0, 2).std.Maximum())
scene_7 = lvsfunc.rfs(scene_6, scene_7, ranges=[transistion_1])

ringing = havsfunc.HQDeringmod(scene_7)
ringing = lvsfunc.rfs(ringing, scene_7, ranges=[text_1, text_3, transistion_1])

dbn = core.f3kdb.Deband(ringing, preset='nograin')
dbn = adptvgrnMod(dbn, size=1.8, strength=1, luma_scaling=.20, static=True, show_mask=False) #increased grain size, lower strength, and scaling, static for smaller encode
dbn = core.std.MaskedMerge(dbn, ringing, core.std.Sobel(darks, 0, 2))
dbn = lvsfunc.rfs(ringing, dbn, ranges=[deband_1])
###

###Outputs
out = vsutil.depth(dbn, 16, dither_type='none')
yt, ut, vt = kgf.split(out) #for tests
out.set_output()