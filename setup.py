from setuptools import setup, find_packages

setup(
    name='prometheus-mysql-exporter',
    version='0.2.0',
    description='MySQL query Prometheus exporter',
    url='https://github.com/braedon/prometheus-mysql-exporter',
    author='Braedon Vickers',
    author_email='braedon.vickers@gmal.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Monitoring',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='monitoring prometheus exporter mysql',
    packages=find_packages(exclude=['tests']),
    python_requires='>=3.5',
    install_requires=[
        'click',
        'jog',
        'mysqlclient',
        'prometheus-client >= 0.6.0',
    ],
    entry_points={
        'console_scripts': [
            'prometheus-mysql-exporter=prometheus_mysql_exporter:main',
        ],
    },
)
