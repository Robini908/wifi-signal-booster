from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="signal-booster",
    version="1.0.0",
    author="Signal Booster Team",
    author_email="support@signal-booster.example.com",
    description="Advanced network signal and speed optimization suite",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/signal-booster",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Networking",
    ],
    python_requires=">=3.7",
    install_requires=[
        "psutil>=5.9.0",
        "speedtest-cli>=2.1.3",
        "scapy>=2.4.5",
        # "netifaces>=0.11.0",  # Made optional due to C++ build requirements
        "numpy>=1.24.0",
        "netaddr>=0.8.0",
        "click>=8.1.3",
        "colorama>=0.4.6",
        "rich>=12.6.0",
        "pywin32>=305;platform_system=='Windows'",
        "matplotlib>=3.7.0",
        "seaborn>=0.12.0",
        "pandas>=2.0.0",
        # Modern UI libraries
        "customtkinter>=5.2.0",
        "darkdetect>=0.8.0",
        "pillow>=9.5.0",
        # Advanced visualization
        "plotly>=5.14.0",
        "kaleido>=0.2.1",
        # Tooltip component for advanced settings
        "CTkToolTip>=0.7.0",
    ],
    extras_require={
        "full": ["netifaces>=0.11.0"]
    },
    entry_points={
        "console_scripts": [
            "signal-booster=signal_booster.cli:main",
            "signal-booster-gui=signal_booster.gui:run_gui",
        ],
    },
) 