import sys,io
sys.argv=["x"]; sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
sys.path.insert(0,'brain')
import b_сливане as SL
print("ПРАГОВЕ:",SL.ПРАГОВЕ)
print("СТЕПЕНИ:",SL.СТЕПЕНИ)
for t in (9,11,12,13,14,16):
    print(" точки",t,"->",SL.f_степен(t))
import live_bot as lb
print("МОЗЪК_ПРАГ =",lb.МОЗЪК_ПРАГ,"->",SL.f_степен(lb.МОЗЪК_ПРАГ))
print("МОЗЪК_ПРАГ_РАМКА =",lb.МОЗЪК_ПРАГ_РАМКА)
