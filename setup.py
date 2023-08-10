from setuptools import setup, find_packages

setup(
    name="gacha-simulator",
    version="0.1",
    author="Sprite",
    author_email="583882690s@gmail.com",
    description="A gacha simulator for mobile games.",
    url="https://github.com/ShirleySprite/gacha-simulator.git",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "numpy",
        "pandas",
        "tqdm",
    ],
    python_requires='>=3.9',
)
