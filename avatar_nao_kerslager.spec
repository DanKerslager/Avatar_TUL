# -*- mode: python -*-

block_cipher = None

a = Analysis(['avatar_nao_kerslager.py'],
             pathex=['C:\\Users\\danke\\Downloads\\PRJ\\BP_APP\\Avatar_Nao_Kerslager'],
             binaries=[],
             datas=[
                 ('.\\dependencies\\naoqi.py', 'naoqi')  # Only the .py file
             ],
             hiddenimports=['naoqi'],  # Ensure naoqi is bundled
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
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
          console=True,  # Change to False if this is a GUI app
)
