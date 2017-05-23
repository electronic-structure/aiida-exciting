from setuptools import setup, find_packages

if __name__ == '__main__':
    setup(
        name='aiida_exciting',
        version='0.0.1',
        url='http://www.aiida.net/',
        license='MIT License',
        author="The AiiDA team",
        author_email='developers@aiida.net',
        include_package_data=True, # puts non-code files into the distribution, reads list from MANIFEST.in
        classifiers=[
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
        ],
        install_requires=['aiida', 'click', 'click-plugins', 'click-completion', 'click-spinner'],
        packages=find_packages(),
        entry_points={
            "aiida.data": [
                "exciting.lapwbasis = aiida_exciting.data.lapwbasis:LapwbasisData"
            ],
            "aiida.cmdline.data": [
                "lapwbasis = aiida_exciting.commands.lapwbasis:lapwbasis"
            ],
            "aiida.calculations": [
                "exciting.exciting = aiida_exciting.calculations.exciting:ExcitingCalculation"
            ],
            "aiida.parsers" : [
                "exciting.output =  aiida_exciting.parsers.output:OutputParser"
            ]
        }
   )
