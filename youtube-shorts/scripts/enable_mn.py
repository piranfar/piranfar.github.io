import bpy, addon_utils, traceback

mods = [m.__name__ for m in addon_utils.modules() if 'molecular' in m.__name__.lower()]
print('MN_MODULES_FOUND:', mods)

for name in mods:
    try:
        addon_utils.enable(name, default_set=True, persistent=True)
        print('ENABLED:', name)
    except Exception:
        traceback.print_exc()
        print('ENABLE_FAILED:', name)

bpy.ops.wm.save_userpref()
print('PREFS_SAVED')
