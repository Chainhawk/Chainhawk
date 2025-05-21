from setuptools import setup, find_packages

setup(
    name='chainhawk',
    version='0.1.0',
    description='스마트 컨트랙트 멀티 분석 통합 플랫폼 (Phase 0)',
    author='lmxx',
    packages=find_packages(),
    install_requires=[
        'semgrep',
        'click',
        'docker',
    ],
    entry_points={
        'console_scripts': [
            'chainhawk=chainhawk.cli:main',
        ],
    },
)
