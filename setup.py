from setuptools import setup, find_packages

setup(
    name="rpgm-transpiler",
    version="0.1.0",
    description="RPG Maker MV to Ren'Py Transpiler",
    author="Reaver",
    packages=find_packages(),
    py_modules=["transpiler_rpy"],
    install_requires=[],
    entry_points={
        "console_scripts": [
            "rpgm-transpile=transpiler_rpy:main",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)