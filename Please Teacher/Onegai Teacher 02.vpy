import vapoursynth as vs
core = vs.core
import lvsfunc as lvf
import kagefunc as kgf
import havsfunc as hvf
import vardefunc as vdf
import debandshit as dbs
from vsutil import get_y, split, join
from fine_dehalo import fine_dehalo #Varde's rewrite https://gist.github.com/Ichunjo/6422f49d994acce63600c0cc40b43209
from adptvgrnMod import adptvgrnMod
from awsmfunc import bbmod
from rekt import rektlvls
from ccd import ccd
###CPU management
import psutil
p_handle = psutil.Process()
#p_handle.cpu_affinity([0, 2, 4, 6, 8, 10, 12, 14]) #p-cores no mt
#p_handle.cpu_affinity([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]) #p-cores mt
#p_handle.cpu_affinity([0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 19]) #p+e cores no mt minus 1 e-core
p_handle.cpu_affinity([0, 2, 4, 6, 8, 10, 12, 14, 16, 17, 18, 19]) #p+e cores no mt #this is fastest for this
#p_handle.cpu_affinity([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]) #p+e cores mt
core.num_threads = 12
###

###Ranges
op_start, op_end = 2259, 4219
ed_start, ed_end = 29669, 31586
ncop_start, ncop_end = 465, 2425
nced_start, nced_end = 4874, 6791
###

###Source
ncoped = core.lsmas.LWLibavSource('F:\\F Entertainment\\Anime\\Onegai Teacher Blu-ray BOX Complete Edition\\Onegai Teacher Blu-ray BOX  Complete Edition Disc3 CD3\\ONEGAI_TEACHER_3\\BDMV\\STREAM\\00005.m2ts')
src   = core.lsmas.LWLibavSource('F:\\F Entertainment\\Anime\\Onegai Teacher Blu-ray BOX Complete Edition\\Onegai Teacher Blu-ray BOX  Complete Edition Disc1 CD1\\ONEGAI_TEACHER_1\\BDMV\\STREAM\\00001.m2ts')
#
ncoped32 = core.fmtc.bitdepth(ncoped, bits=32)
src32    = core.fmtc.bitdepth(src, bits=32)
#
ncop = ncoped32[ncop_start:ncop_end].resize.Bicubic(src32.width-247*2, src32.height-4*2, src_left=247, src_top=4, src_width=src32.width-247*2, src_height=src32.height-4*2).resize.Bicubic(1440, 1080).fmtc.bitdepth(bits=16)
nced = ncoped32[nced_start:nced_end].resize.Bicubic(src32.width-247*2, src32.height-4*2, src_left=247, src_top=4, src_width=src32.width-247*2, src_height=src32.height-4*2).resize.Bicubic(1440, 1080).fmtc.bitdepth(bits=16)
op   = src32[op_start:op_end].resize.Bicubic(src32.width-247*2, src32.height-4*2, src_left=247, src_top=4, src_width=src32.width-247*2, src_height=src32.height-4*2).resize.Bicubic(1440, 1080).fmtc.bitdepth(bits=16)
ed   = src32[ed_start:ed_end].resize.Bicubic(src32.width-247*2, src32.height-4*2, src_left=247, src_top=4, src_width=src32.width-247*2, src_height=src32.height-4*2).resize.Bicubic(1440, 1080).fmtc.bitdepth(bits=16)
###

###Crop + Edge fixing
##Crop
crop = core.resize.Bicubic(src32, src32.width-247*2, src32.height-4*2, src_left=247, src_top=4, src_width=src32.width-247*2, src_height=src32.height-4*2) #non-mod2 crop :)
##Edge fixing
ef_uv = bbmod(crop, planes=[1,2], top=0, bottom=0, left=6, right=4, blur=32, scale_thresh=True, thresh=10)
ef_uv = bbmod(ef_uv, planes=[1,2], top=0, bottom=0, left=2, right=0, blur=6, scale_thresh=True, thresh=10)
rkt_y = rektlvls(ef_uv, colnum=[0,1,2,3,4,-3,-2,-1], colval=[12,0.66,-2,-2,-1,-1,-2,-2])
ef_y  = bbmod(rkt_y, planes=[0], top=0, bottom=1, left=3, right=0, blur=32, scale_thresh=True, thresh=5) #seems like some deadzone sometimes but not always? just gonna keep it...
ef_y  = bbmod(ef_y, planes=[0], top=1, bottom=0, left=1, right=1, blur=4, scale_thresh=True, thresh=10)
###

###Chroma fix + Deshimmmering + Anti-Aliasing + Credits Protection + Dehalo
##Chroma fix + Light AA for all planes
nn3     = core.nnedi3cl.NNEDI3CL(ef_y, 0, dh=True, dw=True, nsize=4, nns=4, qual=2, pscrn=1).fmtc.resample(sy=[0.5, 1,  1], sx=[0.5,  1.5,  1.5], cplaced='mpeg2') #more precise warp + light AA + resize to 1440x1080
warp_uv = core.warp.AWarpSharp2(nn3.fmtc.bitdepth(bits=16), thresh=86, blur=8, chroma=0, depth=19, type=1, planes=[1,2]) #sorta "fix" the bad chroma around lines, tried shifting first but didn't get good results across the board
cropped = core.resize.Bicubic(warp_uv.fmtc.bitdepth(bits=32), 1440, 1080).fmtc.bitdepth(bits=16)
#
y, u, v = split(cropped)
##Supersampled Single-Rate Anti-Aliasing
s36ss   = core.resize.Spline36(get_y(ef_y.fmtc.bitdepth(bits=32)), y.width*1.5, y.height*1.5)
top2_m  = core.std.BlankClip(s36ss.std.Crop(top=2), keep=True).std.AddBorders(top=2, color=0.80)
ss      = core.nnedi3cl.NNEDI3CL(y.fmtc.bitdepth(bits=32), 0, dh=True, dw=True, nsize=4, nns=4, qual=2, pscrn=1).resize.Bicubic(src_top=.5, src_left=.5).resize.Bicubic(y.width*1.5, y.height*1.5)
top_fix = core.std.MaskedMerge(ss, s36ss, top2_m) #fixing some distortion caused by nn3 across the top 2 pixels
nn3sr_v = core.std.MaskedMerge(core.nnedi3cl.NNEDI3CL(top_fix, 0, dh=False, dw=False, nsize=5, nns=4, qual=2, pscrn=1), s36ss, top2_m) #fixing top 2 pixels again
nn3sr_h = core.nnedi3cl.NNEDI3CL(nn3sr_v.std.Transpose(), 0, dh=False, dw=False, nsize=5, nns=4, qual=2, pscrn=1)
nn3sraa = core.std.Transpose(nn3sr_h)
ee3sr_v = core.eedi3m.EEDI3CL(top_fix, 0, dh=False, alpha=0.4, beta=0.2, gamma=0, nrad=2, mdis=20, sclip=nn3sr_v).std.Transpose()
ee3sr_h = core.eedi3m.EEDI3CL(ee3sr_v, 0, dh=False, alpha=0.4, beta=0.2, gamma=0, nrad=2, mdis=20, sclip=nn3sr_h).std.Transpose() #was supposed to have gamma=40 but I must've messed with it at some point and forgot to set it back... I don't care enough about this show to redo the 50ish hours of encodes for 2-13+1-4 eps of teacher+twins over this
#Mix AA
weak_aa   = core.std.Merge(lvf.aa.clamp_aa(get_y(ef_y).resize.Spline36(1440, 1080).fmtc.bitdepth(bits=16), y, nn3sraa.resize.Bicubic(1440,1080).fmtc.bitdepth(bits=16), strength=4), y, 1/3)
medium_aa = core.std.Merge(lvf.aa.clamp_aa(ss, nn3sraa, ee3sr_h, strength=2.4), lvf.aa.clamp_aa(ss, nn3sraa, ee3sr_h, strength=8.6), 2/3) #clamps can be pretty weak since the downscale hides most artifacts anyway
strong_aa = core.std.Merge(ee3sr_h, core.std.Merge(lvf.aa.clamp_aa(ss, medium_aa, ee3sr_h, strength=6), lvf.aa.clamp_aa(ss, medium_aa, ee3sr_h, strength=12), 3/5), 2/3).resize.Bicubic(1440, 1080)
#Mask AA
aa_ret    = kgf.retinex_edgemask(y, sigma=2)
aa_w_mask = core.std.Inflate(aa_ret.rgvs.RemoveGrain(3).rgvs.RemoveGrain(3).rgvs.RemoveGrain(11)).std.Deflate()
aa_m_mask = core.std.Binarize(aa_ret, 9001,0).rgvs.RemoveGrain(3).rgvs.RemoveGrain(3).rgvs.RemoveGrain(11)
aa_s_mask = core.std.Binarize(aa_ret, 54006,0).rgvs.RemoveGrain(3).rgvs.RemoveGrain(3).rgvs.RemoveGrain(11).std.Maximum().std.Median().std.Maximum().std.Minimum().std.Deflate()
#Merge AA
aa_w_merge = core.std.MaskedMerge(y, weak_aa, aa_w_mask)
aa_m_merge = core.std.MaskedMerge(aa_w_merge, medium_aa.resize.Bicubic(1440,1080).fmtc.bitdepth(bits=16), aa_m_mask)
aa_s_merge = core.std.MaskedMerge(aa_m_merge, strong_aa.fmtc.bitdepth(bits=16), aa_s_mask)
aa         = join([aa_s_merge, u, v])
##Credits Protection even though thanks to the text thickness AA looks mostly fine on it
skip_aa = core.resize.Bicubic(ef_y, 1440, 1080, filter_param_a=0, filter_param_b=3/5).fmtc.bitdepth(bits=16) #almost as sharp but much less haloing than spline36 around the text
op_mask = vdf.mask.diff_creditless_mask(skip_aa, op, ncop, op_start, thr=52<<8, expand=0, prefilter=True).std.Deflate().std.Deflate()
ed_mask = vdf.mask.diff_creditless_mask(skip_aa, ed, nced, ed_start, thr=52<<8, expand=0, prefilter=True).std.Deflate().std.Deflate()
op_pro  = core.std.MaskedMerge(aa, core.std.Merge(skip_aa, core.std.Merge(aa, nn3.resize.Bicubic(1440,1080).fmtc.bitdepth(bits=16), 1/2), 3/5), op_mask)
ed_pro  = core.std.MaskedMerge(aa, core.std.Merge(skip_aa, core.std.Merge(aa, nn3.resize.Bicubic(1440,1080).fmtc.bitdepth(bits=16), 1/2), 3/5), ed_mask) #merging in some of the AA looks pretty good thanks to the thick font
op_rfs  = lvf.rfs(aa, op_pro, ranges=[(op_start, op_end)])
ed_rfs  = lvf.rfs(op_rfs, ed_pro, ranges=[(ed_start, ed_end)])
##Dehalo
dehalo = fine_dehalo(ed_rfs, rx=2.7, ry=2.7, brightstr=0.8, darkstr=0.0, thmi=20, thma=240, thlimi=20, thlima=80, excl=True, lowsens=50, highsens=50, showmask=0) #darks seem too destructive to do without scenefiltering, so I'm just not gonna
###

###Denoising
dftt = core.dfttest.DFTTest(dehalo, smode=0, sosize=0, sbsize=9, tosize=0, tmode=0, tbsize=1, slocation=[0.0, .1, 0.25, 3, 0.40, 9, 0.50, 20, 0.60, 10, 0.75, 5, 1.0, .5])
smdg = hvf.SMDegrain(dehalo, tr=3, thSAD=94, thSADC=54, blksize=8, overlap=4, prefilter=dftt, contrasharp=True, RefineMotion=True, chroma=True, pel=2, plane=4)
opdn = hvf.SMDegrain(dehalo, tr=3, thSAD=84, thSADC=48, blksize=8, overlap=4, prefilter=-1, contrasharp=True, RefineMotion=True, chroma=True, pel=2, plane=4)
dnrf = lvf.rfs(smdg, opdn, ranges=[(op_start, op_end)])
uvdn = core.std.Merge(dnrf, ccd(dnrf, threshold=3, matrix='709'), weight=3/5)
###Tried to figure out if I could kill the dither with dftt but ended up not being happy with it, looks alright when extended as a prefilter though

###Debanding
db_f3kpf  = dbs.f3kpf(uvdn, 13, [27,11], 0)
db_f3kpf2 = dbs.f3kpf(db_f3kpf, 17, [33,14], 0) #2 passes works better than 1 stronger pass for this
db_mask   = lvf.mask.detail_mask_neo(db_f3kpf, sigma=1.4, detail_brz=0.00045, lines_brz=0.050) #cope mask
db        = core.std.MaskedMerge(db_f3kpf2, uvdn, db_mask)
grain     = adptvgrnMod(db, strength=0.125, size=1.25, luma_scaling=48, sharp=40, static=True, grain_chroma=False, show_mask=False, seed=333)
###

###Outputs
#yt, ut, vt = split(uvdn.fmtc.bitdepth(bits=32)) #for testing
#
out = core.fmtc.bitdepth(grain, bits=10)#.std.Invert()
#cut  = out[1234:2345] #for testing
#
out.set_output()
###


#x265
#--preset slower --output-depth 10
#--rd 3 --psy-rd 1.75 --psy-rdoq 1.15
#--aq-mode 3 --aq-strength 0.90 --qcomp 0.70
#--ipratio 1.40 --pbratio 1.30
#--merange 48
#--ref 4 --bframes 8
#--cbqpoffs -2 --crqpoffs -2
#--deblock 2:1 --no-sao --strong-intra-smoothing
#--min-keyint 23 --keyint 240
#--no-cutree --rc-lookahead 60
#--subme 5 --max-merge 5
#--rect --amp --ctu 32 --tskip
#--tu-intra-depth 2 --tu-inter-depth 2 --limit-tu 0
#--sar 1 --videoformat ntsc --range limited --fps 24000/1001
#--colormatrix bt709 --colorprim bt709 --transfer bt709