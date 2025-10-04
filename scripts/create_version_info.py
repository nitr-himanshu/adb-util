#!/usr/bin/env python3
"""
Generate version info file for PyInstaller on Windows
"""

def create_version_info():
    """Create version_info.py file for PyInstaller."""
    version_info_content = '''VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x4,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u"040904B0",
        [StringStruct(u"CompanyName", u"ADB-UTIL Project"),
         StringStruct(u"FileDescription", u"Android Debug Bridge Utility"),
         StringStruct(u"FileVersion", u"1.0.0.0"),
         StringStruct(u"InternalName", u"adb-util"),
         StringStruct(u"LegalCopyright", u"MIT License"),
         StringStruct(u"OriginalFilename", u"adb-util.exe"),
         StringStruct(u"ProductName", u"ADB-UTIL"),
         StringStruct(u"ProductVersion", u"1.0.0.0")])
    ]),
    VarFileInfo([VarStruct(u"Translation", [1033, 1200])])
  ]
)'''
    
    with open('version_info.py', 'w', encoding='utf-8') as f:
        f.write(version_info_content)
    
    print("Created version_info.py successfully")

if __name__ == "__main__":
    create_version_info()