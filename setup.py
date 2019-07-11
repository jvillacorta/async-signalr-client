import setuptools


setuptools.setup(
    name="async-signalr-client",
    author="Jorge Villacorta",
    description="Websocket Python Async Client for the DotNet Code SignalR Protocol",
    keywords="async signalr client",
    author_email="javm02@gmail.com",
    version="0.0.1",
    license="MIT",
    url="https://github.com/jvillacorta/async-signalr-client",
    packages=[
        "client",
        "client.models",
        "client.models.futures",
        "client.models.messages",
        "client.protocols"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Internet"
    ],
    install_requires=[
        "websockets>=7.0.0",
        "aiohttp==3.0.9"
    ],
    tests_requires=[
        "requests==2.22.0",
        "pytest==4.1.0",
        "pytest-asyncio==0.10.0"
    ]
)
