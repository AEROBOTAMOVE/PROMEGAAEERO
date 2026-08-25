import sys, io
sys.stdout.reconfigure(encoding='utf-8')
sys.argv=["x"]
import live_bot as lb
print("OK", lb.__file__)
print("VER", getattr(lb,"VERSION",None) or getattr(lb,"ВЕРСИЯ",None))
