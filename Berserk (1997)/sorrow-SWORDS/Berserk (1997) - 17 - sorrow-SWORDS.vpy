import vapoursynth as vs
core = vs.get_core()
import importlib.machinery
import kagefunc as kgf
import havsfunc as hvf
import vardefunc as vdf
import lvsfunc as lvf
from cooldegrain import CoolDegrain
from awsmfunc import bbmod
import vsTAAmbk as taa
from rekt import rektlvls, rekt_fast
from adptvgrnMod import *
from vsutil import *

###Ranges
deband = [(0, 0)]
card_1, card_2, card_3 = (3240, 3335), (16800, 16919), (33912, 33983)
op_start, op_end = 1560, 3240
ed = (31344, 33264)
###

###Source
src 	= core.lsmas.LWLibavSource(r'F:\enc\[BDMV][120118] BERSERK BD-BOX\[BDMV][120118] BERSERK BD-BOX VOL4\BERSERK_VOL4\BERSERK_VOL4\BDMV\STREAM\00002.m2ts')
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

###Masks
linemask	= kgf.retinex_edgemask(cnr, sigma=2).std.Deflate().std.Deflate().std.Binarize(18000,0).std.Deflate().std.Deflate().std.Inflate()
###

###Opening
splice = cnr[0:op_start] + core.ffms2.Source(r'F:\E\VS64P\OP large.ffv1.mkv') + cnr[op_end:]
###

###Ending
eddb		= core.f3kdb.Deband(cnr, 25, grainc=0, grainy=0, y=33, cb=33, cr=33, output_depth=16)
eddbmask	= core.std.MaskedMerge(eddb, cnr, linemask)
#edgrain		= adptvgrnMod(eddbmask, strength=0.40, size=1.20, luma_scaling=3, sharp=50, static=True, grain_chroma=False, show_mask=False)
edrfs		= lvf.rfs(splice, eddbmask, ranges=ed)
###

###Card cleaning from ZQ's scripts but modified to not dehalo uv and by altering the deringing
cardyuv	 = split(edrfs)
carddh	 = hvf.DeHalo_alpha(cardyuv[0], darkstr=1.5, rx=2.7, ry=1.5, brightstr=0)
cardjoin = join([carddh, cardyuv[1], cardyuv[2]])
carddr	 = hvf.HQDeringmod(cardjoin, mrad=3, minp=0.3, msmooth=1, mthr=115, nrmode=1, thr=128, darkthr=3, sharp=0, show=False)
cardtaa	 = taa.TAAmbk(carddr, 6, 4, 4)
cardrfs	 = lvf.rfs(edrfs, cardtaa, ranges=[card_1, card_2, card_3])
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
out8 = core.fmtc.bitdepth(cardrfs, bits=8)#.std.Invert()
cut  = out8[21412:22009] #for testing
out8.set_output()
###