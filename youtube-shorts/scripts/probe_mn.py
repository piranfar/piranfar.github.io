import importlib, traceback

m = importlib.import_module('bl_ext.user_default.molecularnodes')
names = [n for n in dir(m) if not n.startswith('_')]
print('TOPLEVEL:', names[:50])

for sub in ['entities', 'io', 'session', 'utils', 'nodes', 'blender']:
    try:
        mod = importlib.import_module('.' + sub, m.__name__)
        print('SUB_OK:', sub, '->', [n for n in dir(mod) if not n.startswith('_')][:25])
    except Exception as e:
        print('SUB_FAIL:', sub, type(e).__name__, str(e)[:120])

# does plain import work after extension import?
try:
    import molecularnodes as mn
    print('PLAIN_IMPORT_OK')
except Exception as e:
    print('PLAIN_IMPORT_FAIL:', str(e)[:80])

# check operators
import bpy
ops = [op for op in dir(bpy.ops.mn)] if hasattr(bpy.ops, 'mn') else []
print('MN_OPS:', ops[:30])
