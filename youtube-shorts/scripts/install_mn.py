import bpy, addon_utils, traceback

ZIP = r'E:\Github Project\piranfar.github.io\youtube-shorts\tools\molecularnodes.zip'

try:
    bpy.ops.extensions.package_install_files(filepath=ZIP, enable_on_install=True)
    print('EXTENSION_INSTALL_OK')
except Exception:
    traceback.print_exc()
    print('EXTENSION_INSTALL_FAILED')

try:
    addon_utils.enable('molecularnodes')
    bpy.ops.wm.save_userpref()
    print('ADDON_ENABLE_OK')
except Exception:
    traceback.print_exc()
    print('ADDON_ENABLE_FAILED')

try:
    import molecularnodes as mn
    print('MN_IMPORT_OK', getattr(mn, '__version__', 'unknown'))
except Exception:
    traceback.print_exc()
    print('MN_IMPORT_FAILED')
