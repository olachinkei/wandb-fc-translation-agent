from setuptools import setup, find_packages

setup(
    name="wandb_translator",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "wandb==0.18.0",
        "weave==0.51.44",
        "wandb_workspaces",
        "slack-sdk>=3.21.3",
        "boto3>=1.28.0",
        "python-dotenv>=1.0.0",
        "pytest>=7.4.0",
        "slack_bolt",
        "slack_sdk"
    ],
) 