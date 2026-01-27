# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for KIAS Dørkonfigurator.
Bygger standalone Windows-applikasjon med --onedir modus.

Kjør med:
    uv run pyinstaller kias_dorkonfigurator.spec --noconfirm
"""
import sys
from pathlib import Path

# Finn pakkestier dynamisk
import qt_material
import qtawesome
import reportlab

qt_material_path = Path(qt_material.__file__).parent
qtawesome_path = Path(qtawesome.__file__).parent
reportlab_path = Path(reportlab.__file__).parent

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Applikasjonens egne ressurser
        ('assets', 'assets'),

        # qt-material tema-filer (QSS, fonter, ressurser)
        (str(qt_material_path / 'themes'), 'qt_material/themes'),
        (str(qt_material_path / 'fonts'), 'qt_material/fonts'),
        (str(qt_material_path / 'resources'), 'qt_material/resources'),
        (str(qt_material_path / 'material.qss.template'), 'qt_material'),
        (str(qt_material_path / 'dock_theme.ui'), 'qt_material'),

        # qtawesome ikon-fonter
        (str(qtawesome_path / 'fonts'), 'qtawesome/fonts'),

        # reportlab PDF-fonter
        (str(reportlab_path / 'fonts'), 'reportlab/fonts'),
    ],
    hiddenimports=[
        # PyQt6
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtOpenGL',
        'PyQt6.QtOpenGLWidgets',
        'PyQt6.sip',

        # PyOpenGL (bruker runtime platform-deteksjon og lazy imports)
        'OpenGL',
        'OpenGL.GL',
        'OpenGL.GLU',
        'OpenGL.platform',
        'OpenGL.platform.win32',
        'OpenGL.arrays',
        'OpenGL.arrays.ctypesarrays',
        'OpenGL.arrays.ctypesparameters',
        'OpenGL.arrays.ctypespointers',
        'OpenGL.arrays.numpymodule',
        'OpenGL.arrays.lists',
        'OpenGL.arrays.numbers',
        'OpenGL.arrays.strings',
        'OpenGL.converters',

        # pyqtgraph (bruker __import__ for OpenGL-items)
        'pyqtgraph',
        'pyqtgraph.opengl',
        'pyqtgraph.opengl.GLViewWidget',
        'pyqtgraph.opengl.GLGraphicsItem',
        'pyqtgraph.opengl.MeshData',
        'pyqtgraph.opengl.items',
        'pyqtgraph.opengl.items.GLMeshItem',
        'pyqtgraph.opengl.items.GLGridItem',
        'pyqtgraph.opengl.shaders',

        # qt-material, qtawesome
        'qt_material',
        'qtawesome',

        # reportlab (PDF-generering)
        'reportlab',
        'reportlab.lib',
        'reportlab.pdfgen',
        'reportlab.graphics',
        'reportlab.rl_config',

        # svglib (SVG-import for logo i PDF)
        'svglib',
        'svglib.svglib',
        'lxml',
        'lxml.etree',

        # numpy (brukes av pyqtgraph)
        'numpy',

        # openpyxl (Excel-eksport)
        'openpyxl',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
        'IPython',
        'jupyter',
        'pytest',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='KIAS Dørkonfigurator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/KIAS-dorer-logo.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='KIAS Dørkonfigurator',
)
