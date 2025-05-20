from setuptools import setup, find_packages

setup(
    name="p-queuing",
    version="0.1.0",
    description="A generic RabbitMQ-based queuing framework for p microservices",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Wares",
    url="",
    license="MIT",
    package_dir={"": "src"},
    packages=find_packages("src"),
    python_requires=">=3.8",
    install_requires=[
        "flask",
        "pika",
    ],
    entry_points={
        "console_scripts": [
            "p-queuing-service=p_queuing.app:main",
            "p-queuing-worker=p_queuing.worker:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
