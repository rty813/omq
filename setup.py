import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="omq",  # Replace with your own username
    version="0.2.1",
    author="rty813",
    author_email="zjy523213189zjy@gmail.com",
    description="A package wrap zmq",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rty813/omq",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=['cffi', 'nnpy'],
    python_requires='>=3.6',
)
