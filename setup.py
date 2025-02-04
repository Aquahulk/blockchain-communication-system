from setuptools import setup, find_packages

setup(
    name="blockchain_communication_system",  # Replace with your package name
    version="0.1.0",                         # Replace with your package version
    packages=find_packages(),                # Automatically find packages in the directory
    install_requires=[                       # List your dependencies here
        "flask",
        "web3",
        "flask-sqlalchemy",
        "flask-migrate",
    ],
    python_requires=">=3.7",                 # Specify Python version compatibility
)