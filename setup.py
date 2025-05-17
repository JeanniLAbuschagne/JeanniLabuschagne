from setuptools import setup, find_packages

setup(
    name="habit-tracker",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
    ],
    entry_points={
        "console_scripts": [
            "habit-tracker=habit_tracker:cli",
        ],
    },
    python_requires=">=3.7",
    author="Jeanni Labuschagne",
    author_email="jeanni1234@icloud.com",
    description="A habit tracking application using object-oriented and functional programming",
    keywords="habit, tracker, cli",
    url="https://github.com/JeanniLAbuschagne/JeanniLabuschagne.git",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)