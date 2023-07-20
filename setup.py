import setuptools


setuptools.setup(
    name="async-signalr-async_signalr_client",
    author="Jorge Villacorta",
    description="Websocket Python Async Client for the DotNet Code SignalR Protocol",
    keywords="async signalr async_signalr_client",
    author_email="javm02@gmail.com",
    version="0.1.0",
    license="MIT",
    url="https://github.com/jvillacorta/async-signalr-client",
    packages=[
        "async_signalr_client",
        "async_signalr_client.models",
        "async_signalr_client.models.futures",
        "async_signalr_client.models.messages",
        "async_signalr_client.protocols"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Internet"
    ],
    install_requires=[
        "websockets>=7.0.0",
        "aiohttp==3.8.5"
    ],
    tests_requires=[
        "requests==2.22.0",
        "pytest==7.1.2",
        "pytest-asyncio==0.18.3",
        "pytest-aiohttp==1.0.4",
        "pytest-html==1.21.1"
    ]
)
