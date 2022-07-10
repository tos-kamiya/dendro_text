from setuptools import Extension, setup

try:
    from Cython.Build import cythonize

    ext_modules = [Extension("dendro_text.dld", ["dendro_text/dld.pyx"], extra_compile_args=["-O3"])]

    setup(
        ext_modules=cythonize(ext_modules),
    )
except ImportError as e:
    setup()

