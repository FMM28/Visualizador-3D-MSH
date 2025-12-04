python -m nuitka main.py ^
  --standalone ^
  --msvc=latest ^
  --jobs=8 ^
  --prefer-source-code ^
  --enable-plugin=pyqt6 ^
  --include-package=OpenGL ^
  --include-package=OpenGL_accelerate ^
  --include-package=numpy ^
  --follow-imports
