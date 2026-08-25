# -*- coding: utf-8 -*-
import io,sys
sys.stdout.reconfigure(encoding='utf-8')
f=sys.argv[1]; a=int(sys.argv[2]); b=int(sys.argv[3])
L=io.open(f,encoding='utf-8').read().split('\n')
for i in range(a-1,min(b,len(L))):
    print(i+1, L[i])
