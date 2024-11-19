# -*- mode: python -*-

block_cipher = None

a = Analysis(['avatar_nao_kerslager.py'],
             pathex=['C:\\Users\\danke\\Downloads\\PRJ\\BP_APP\\Avatar_Nao_Kerslager'],
             binaries=[
                 ('.\\dependencies\\libvlc.dll', '.'),
                 ('.\\dependencies\\libvlccore.dll', '.'),
                 ('.\\dependencies\\vlc_plugins', 'vlc_plugins'),  # Added plugins directory
             ],
             datas=[
                 ('.\\dependencies\\naoqi.py', 'naoqi'),
                 ('.\\dependencies\\vlc.py', 'vlc'),  # Only the .py file
             ],
             hiddenimports=['naoqi', 'vlc'],  # Ensure naoqi and vlc are bundled
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='avatar_nao_kerslager',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True)
