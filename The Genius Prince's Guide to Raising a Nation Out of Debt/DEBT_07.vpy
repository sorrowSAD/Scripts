import vapoursynth as vs
core = vs.core
import vsmask as vsm
import jvsfunc as jvs
import lvsfunc as lvf
import vardefunc as vdf
import debandshit as dbs
from vsutil import get_y, get_w, split, join, depth
from adptvgrnMod import adptvgrnMod
from EoEfunc.denoise import BM3D
from havsfunc import SMDegrain
###CPU management
import psutil
p_handle = psutil.Process()
#p_handle.cpu_affinity([0, 2, 4, 6, 8, 10, 12, 14]) #p-cores no mt
#p_handle.cpu_affinity([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]) #p-cores mt
#p_handle.cpu_affinity([0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 19]) #p+e cores no mt minus 1 e-core
#p_handle.cpu_affinity([0, 2, 4, 6, 8, 10, 12, 14, 16, 17, 18, 19]) #p+e cores no mt
p_handle.cpu_affinity([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]) #p+e cores mt
core.num_threads = 20
###

###Ranges
op_start, op_end = 1569, 3692
#ed_start, ed_end = 31887, 34045
ncop_start, ncop_end = 35, 2158
nced_start, nced_end = 0, 2158
#
low_aa = [(11386, 11597)]
high_aa = [(op_start, op_start+170), (op_start+264, op_start+1928), (113, 1533), (3806, 11385), (11597, 16528), (16661, 16903), (17186, 19662), (19692, 23143), (24938, 25535), (25711, 26459)]
giga_aa = [(19663, 19691), (28521, 28663)]
#
weak_db = [(op_start+981, op_start+1032), (11386, 11596)]
strong_db = [(op_start+503, op_start+578), (op_start+1113, op_start+1167), (op_start+1767, op_start+1834), (op_start+1865, op_start+1928), (6431, 6876), (16543, 16593), (28664, 28712), (31846, 31862)]
giga_db   = []
#
denoise_strong = [(op_start+503, op_start+578), (op_start+643, op_start+775), (op_start+971, op_start+1167), (op_start+1217, op_start+1268), (op_start+1388, op_start+1484), (op_start+1767, op_start+1928), (6431, 6876), (16545, 16593), (28664, 28712), (31855, 31862)]
###

###Sources
ncop = core.lsmas.LWLibavSource(r"E:\Entertainment\Anime\TENSAI_OUJI_1\BDMV\STREAM\00010.m2ts").std.SetFrameProp(prop='_Matrix', intval=1).std.SetFrameProp(prop='_Transfer', intval=1).std.SetFrameProp(prop='_ColorRange', intval=1)
nced = core.lsmas.LWLibavSource(r"E:\Entertainment\Anime\TENSAI_OUJI_1\BDMV\STREAM\00011.m2ts").std.SetFrameProp(prop='_Matrix', intval=1).std.SetFrameProp(prop='_Transfer', intval=1).std.SetFrameProp(prop='_ColorRange', intval=1)
#
src   = core.lsmas.LWLibavSource(r"E:\Entertainment\Anime\TENSAI_OUJI_3\BDMV\STREAM\00003.m2ts").std.SetFrameProp(prop='_Matrix', intval=1).std.SetFrameProp(prop='_Transfer', intval=1).std.SetFrameProp(prop='_ColorRange', intval=1)
src16 = core.fmtc.bitdepth(src, bits=16)
src32 = core.fmtc.bitdepth(src, bits=32)
#
y, u, v       = split(src16)
y32, u32, v32 = split(src32)
##
ncop_cut = ncop[ncop_start:ncop_end].fmtc.bitdepth(bits=16)
nced_cut = nced[nced_start:nced_end].fmtc.bitdepth(bits=16)
op_cut   = src[op_start:op_end].fmtc.bitdepth(bits=16)
#ed_cut   = src[ed_start:ed_end].fmtc.bitdepth(bits=16)
###

###Luma Anti-Aliasing
##Supersampling
nn3ss_v = core.nnedi3cl.NNEDI3CL(y, 1, dh=True, dw=False, nsize=5, nns=4, qual=2, pscrn=1)
nn3ss_h = core.nnedi3cl.NNEDI3CL(nn3ss_v.std.Transpose(), 1, dh=True, dw=False, nsize=5, nns=4, qual=2, pscrn=1)
nn3ssaa = core.std.Transpose(nn3ss_h).resize.Bicubic(src_top=-.5, src_left=-.5)
#
ee3ss_v = core.eedi3m.EEDI3(y, 1, dh=True, alpha=0.5, beta=0.25, gamma=80, nrad=1, mdis=16, sclip=nn3ss_v).std.Transpose()
ee3ss_h = core.eedi3m.EEDI3(ee3ss_v, 1, dh=True, alpha=0.5, beta=0.25, gamma=80, nrad=1, mdis=16, sclip=nn3ss_h).std.Transpose().resize.Bicubic(src_top=-.5, src_left=-.5)
#
fsrcnnx = vdf.fsrcnnx_upscale(y, shader_file=r'C:\Users\User\AppData\Roaming\mpv.net\shaders\FSRCNNX_x2_56-16-4-1.glsl', upscaled_smooth=nn3ssaa, downscaler=None, profile='slow', overshoot=1.1, undershoot=1.1, strength=45)
#
nn3ss_v_2 = core.nnedi3cl.NNEDI3CL(fsrcnnx, 1, dh=True, dw=False, nsize=6, nns=4, qual=2, pscrn=1)
nn3ss_h_2 = core.nnedi3cl.NNEDI3CL(nn3ss_v_2.std.Transpose(), 1, dh=True, dw=False, nsize=6, nns=4, qual=2, pscrn=1)
nn3ssaa_2 = core.std.Transpose(nn3ss_h_2).resize.Bicubic(src_top=-.5, src_left=-.5).resize.Bicubic(3840,2160, filter_param_a=-0.36, filter_param_b=0.18)
##Supersampled Single-Rate AA
#High
nn3sr_v = core.nnedi3cl.NNEDI3CL(nn3ssaa_2, 1, dh=False, dw=False, nsize=6, nns=4, qual=2, pscrn=1)
nn3sr_h = core.nnedi3cl.NNEDI3CL(nn3sr_v.std.Transpose(), 1, dh=False, dw=False, nsize=6, nns=4, qual=2, pscrn=1)
nn3sraa = core.std.Transpose(nn3sr_h)
#
ee3sr_v = core.eedi3m.EEDI3(nn3ssaa_2, 1, dh=False, alpha=0.6, beta=0.2, gamma=60, nrad=2, mdis=20, sclip=nn3sr_v)
ee3sr_h = core.eedi3m.EEDI3(ee3sr_v.std.Transpose(), 1, dh=False, alpha=0.6, beta=0.2, gamma=60, nrad=2, mdis=20, sclip=nn3sr_h).std.Transpose()
#Supersampled Double-Rate AA
#Giga
nn3dr_v = core.nnedi3cl.NNEDI3CL(nn3sraa, 0, dh=False, dw=False, nsize=6, nns=4, qual=2, pscrn=1)
nn3dr_h = core.nnedi3cl.NNEDI3CL(nn3dr_v.std.Transpose(), 0, dh=False, dw=False, nsize=6, nns=4, qual=2, pscrn=1)
nn3draa = core.std.Transpose(nn3dr_h)
#
ee3dr_v_g = core.eedi3m.EEDI3(nn3sraa, 1, dh=False, alpha=0.65, beta=0.15, gamma=20, nrad=2, mdis=24, sclip=nn3sr_v)
ee3dr_h_g = core.eedi3m.EEDI3(ee3dr_v_g.std.Transpose(), 1, dh=False, alpha=0.65, beta=0.15, gamma=20, nrad=2, mdis=24, sclip=nn3sr_h)
#
ee3dr_v_g_2 = core.eedi3m.EEDI3(ee3dr_h_g.std.Transpose(), 0, dh=False, alpha=0.65, beta=0.15, gamma=20, nrad=2, mdis=25, sclip=nn3dr_v)
ee3dr_h_g_2 = core.eedi3m.EEDI3(ee3dr_v_g_2.std.Transpose(), 0, dh=False, alpha=0.65, beta=0.15, gamma=20, nrad=2, mdis=25, sclip=nn3dr_h).std.Transpose()
##AA Mix
clamp_ss    = lvf.clamp_aa(y, nn3ssaa.resize.Bicubic(1920,1080, filter_param_a=-0.44, filter_param_b=0.22), ee3ss_h.resize.Bicubic(1920,1080, filter_param_a=-0.44, filter_param_b=0.22), 1.333)
clamp_sr    = lvf.clamp_aa(nn3ssaa_2.resize.Bicubic(1920,1080, filter_param_a=-0.44, filter_param_b=0.22), nn3sraa.resize.Bicubic(1920,1080, filter_param_a=-0.44, filter_param_b=0.22), ee3sr_h.resize.Bicubic(1920,1080, filter_param_a=-0.44, filter_param_b=0.22), 1.666)
clamp_sr_g = lvf.clamp_aa(nn3sraa.resize.Bicubic(1920,1080, filter_param_a=-0.38, filter_param_b=0.19), nn3draa.resize.Bicubic(1920,1080, filter_param_a=-0.38, filter_param_b=0.19), ee3dr_h_g_2.resize.Bicubic(1920,1080, filter_param_a=-0.38, filter_param_b=0.19), 3)
##AA rfs
low_aa  = lvf.rfs(clamp_ss, fsrcnnx.resize.Bicubic(1920,1080, filter_param_a=-0.44, filter_param_b=0.22), ranges=low_aa)
high_aa = lvf.rfs(low_aa, clamp_sr, ranges=high_aa)
giga_aa = lvf.rfs(high_aa, clamp_sr_g, ranges=giga_aa)
##AA #Masking
sobel = vsm.edge.Sobel().edgemask(y.fmtc.bitdepth(bits=32), multi=2, lthr=0.080, hthr=0.140).fmtc.bitdepth(bits=16).rgvs.RemoveGrain(3).rgvs.RemoveGrain(11) #Orginally made this at 32b before dropping to 16b for the AA don't feel like messing with it
##AA Merge
aa_merge = core.std.MaskedMerge(y, giga_aa, sobel)
aa       = join([aa_merge, u, v])
###

###Credits Protection
op_mask = vdf.mask.diff_creditless_mask(aa, op_cut, ncop_cut, op_start, thr=52<<8, expand=0, prefilter=True).std.Deflate().std.Deflate()
#ed_mask = vdf.mask.diff_creditless_mask(aa, ed_cut, nced_cut, ed_start, thr=52<<8, expand=0, prefilter=True).std.Deflate().std.Deflate()
op_pro  = core.std.MaskedMerge(aa, src16, op_mask)
#ed_pro  = core.std.MaskedMerge(aa, src16, ed_mask)
op_rfs  = lvf.rfs(aa, op_pro, ranges=[(op_start, op_end)])
#ed_rfs  = lvf.rfs(op_rfs, ed_pro, ranges=[(ed_start, ed_end)])
###

###Denoising
smdg     = SMDegrain(op_rfs, tr=3, thSAD=106, blksize=16, overlap=8, pel=1, prefilter=2, contrasharp=False, RefineMotion=True, chroma=False, plane=0).fmtc.bitdepth(bits=32)
bm3d     = BM3D(op_rfs.fmtc.bitdepth(bits=32), sigma=[0.56,0.0,0.0], profile='np', radius=2, block_step=2, bm_range=12, ps_range=6, CUDA=True, ref=smdg, chroma=False, Fast=False)
smdg_2   = SMDegrain(op_rfs, tr=3, thSAD=270, blksize=16, overlap=8, pel=1, prefilter=2, contrasharp=False, RefineMotion=True, chroma=False, plane=0).fmtc.bitdepth(bits=32)
bm3d_2   = BM3D(op_rfs.fmtc.bitdepth(bits=32), sigma=[0.96,0.0,0.0], profile='np', radius=3, block_step=2, bm_range=12, ps_range=6, CUDA=True, ref=smdg_2, chroma=False, Fast=False)
knlm     = core.knlm.KNLMeansCL(op_rfs.fmtc.bitdepth(bits=32), d=3, a=2, s=3, h=0.26, channels = 'UV', device_type='gpu')
knlm     = split(knlm)
bm3d_rfs = lvf.rfs(bm3d, bm3d_2, ranges=denoise_strong)
bm3d_yuv = split(bm3d_rfs)
ydn      = join([bm3d_yuv[0],knlm[1],knlm[2]])
uvdn     = core.std.Merge(ydn, core.std.Merge(jvs.ccd(ydn, threshold=4, matrix=1), jvs.ccd(join([get_y(ydn), u32, v32]), threshold=6, scale=1.25, matrix=1), weight=2/5), weight=2/3).fmtc.bitdepth(bits=16)
###

###Debanding + Regrain
db_d3kdb   = dbs.dumb3kdb(uvdn, 16, [42,42], grain=[4,2])
db_d3kdb_2 = dbs.dumb3kdb(uvdn, 24, [45,45], grain=[5,3])
db_pdb     = dbs.placebo_deband(uvdn, 12, [2.45,2.45], iterations=4, grain=[2,1])
db_pdb_2   = dbs.placebo_deband(uvdn, 20, [2.65,2.65], iterations=4, grain=[3,2])
db_mix     = core.average.Mean([db_d3kdb, db_d3kdb_2, db_pdb, db_pdb_2])
db_mask    = lvf.mask.detail_mask_neo(uvdn, sigma=2.2, detail_brz=0.000985, lines_brz=0.00785).rgvs.RemoveGrain(11).std.Inflate().std.Inflate()
db         = core.std.MaskedMerge(db_mix, uvdn, db_mask)
#Weak
db_d3kdb_w   = dbs.dumb3kdb(uvdn, 12, [33,33], grain=[3,2])
db_d3kdb_2_w = dbs.dumb3kdb(uvdn, 16, [35,35], grain=[4,2])
db_pdb_w     = dbs.placebo_deband(uvdn, 12, [1.65,1.65], iterations=2, grain=[1,1])
db_pdb_2_w   = dbs.placebo_deband(uvdn, 20, [2.00,2.00], iterations=2, grain=[2,2])
db_mix_w     = core.average.Mean([db_d3kdb_w, db_d3kdb_2_w, db_pdb_w, db_pdb_2_w])
db_mask_w    = lvf.mask.detail_mask_neo(uvdn, sigma=2.2, detail_brz=0.000600, lines_brz=0.00720).rgvs.RemoveGrain(11).std.Inflate().std.Inflate()
db_w         = core.std.MaskedMerge(db_mix_w, uvdn, db_mask_w)
#Strong
db_d3kdb_s   = dbs.dumb3kdb(uvdn, 16, [56,56], grain=[5,3])
db_d3kdb_2_s = dbs.dumb3kdb(uvdn, 31, [58,58], grain=[7,4])
db_pdb_s     = dbs.placebo_deband(uvdn, 16, [3.85,3.85], iterations=6, grain=[3,2])
db_pdb_2_s   = dbs.placebo_deband(uvdn, 24, [3.95,3.95], iterations=6, grain=[5,3])
db_mix_s     = core.average.Mean([db_d3kdb_s, db_d3kdb_2_s, db_pdb_s, db_pdb_2_s])
db_mask_s    = lvf.mask.detail_mask_neo(uvdn, sigma=2.2, detail_brz=0.000985, lines_brz=0.00985).rgvs.RemoveGrain(11).std.Inflate().std.Inflate()
db_s         = core.std.MaskedMerge(db_mix_s, uvdn, db_mask_s)
#Giga
db_pdb_g     = dbs.placebo_deband(uvdn, 12, [4.75,4.75], iterations=7, grain=[3,2])
db_pdb_2_g   = dbs.placebo_deband(uvdn, 16, [4.90,4.90], iterations=7, grain=[2,1])
db_pdb_3_g   = dbs.placebo_deband(uvdn, 20, [5.05,5.05], iterations=6, grain=[4,2])
db_pdb_4_g   = dbs.placebo_deband(uvdn, 24, [5.20,5.20], iterations=6, grain=[5,3])
db_mix_g     = core.average.Mean([db_pdb_g, db_pdb_2_g, db_pdb_3_g, db_pdb_4_g])
db_mask_g    = lvf.mask.detail_mask_neo(uvdn, sigma=2.2, detail_brz=0.001125, lines_brz=0.01050).rgvs.RemoveGrain(11).std.Inflate().std.Inflate()
db_g         = core.std.MaskedMerge(db_mix_g, uvdn, db_mask_g)
##Deband rfs
weak_db   = lvf.rfs(db, db_w, ranges=weak_db)
strong_db = lvf.rfs(weak_db, db_s, ranges=strong_db)
giga_db   = lvf.rfs(strong_db, db_g, ranges=giga_db)
##Regrain
grain = adptvgrnMod(giga_db, strength=[0.22,0.07], size=1.15, luma_scaling=15, sharp=44, static=True, fade_edges=True, show_mask=False, seed=333)
###

###Outputs
yt, ut, vt = split(src.fmtc.bitdepth(bits=32)) #for testing
yt2, ut2, vt2 = split(op_rfs.fmtc.bitdepth(bits=32)) #for testing
yt3, ut3, vt3 = split(ydn.fmtc.bitdepth(bits=32)) #for testing
yt4, ut4, vt4 = split(uvdn.fmtc.bitdepth(bits=32)) #for testing
#
out = core.fmtc.bitdepth(grain, bits=10)
#
out.set_output()
#
#src16[op_start:op_end].set_output(0)
#aa[op_start:op_end].set_output(1)
#bm3d[op_start:op_end].set_output(1)
#bm3d_2[op_start:op_end].set_output(2)
#uvdn[op_start:op_end].set_output(2)
#db[op_start:op_end].set_output(3)
#db_w[op_start:op_end].set_output(4)
#db_s[op_start:op_end].set_output(5)
#db_g[op_start:op_end].set_output(6)
#clamp_ss[op_start:op_end].set_output(7)
#clamp_sr[op_start:op_end].set_output(8)
#clamp_sr_g[op_start:op_end].set_output(9)
#
#op_cut.set_output(1)
#ncop_cut.set_output(2)
#ed_cut.set_output(3)
#nced_cut.set_output(4)
###