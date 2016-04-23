from setuptools import setup


setup(
    name='lunchclub',
    version='0.1',
    py_modules=['cli'],
    entry_points="""
        [console_scripts]
        lunchclub=cli:cli
    """,
    packages=['lunchclub',]
)