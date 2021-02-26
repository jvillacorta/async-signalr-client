import setuptools


setuptools.setup(
    name="async-signalr-async_signalr_client",
    author="Jorge Villacorta",
    description="Websocket Python Async Client for the DotNet Code SignalR Protocol",
    keywords="async signalr async_signalr_client",
    author_email="javm02@gmail.com",
    version="0.0.1",
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
        "aiohttp==3.7.4"
    ],
    tests_requires=[
        "requests==2.22.0",
        "pytest==4.1.0",
        "pytest-asyncio==0.10.0",
        "pytest-html==1.21.1",
        "asynctest==0.13.0"
    ]
)
